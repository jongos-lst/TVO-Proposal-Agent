import json
import logging
from langchain_core.messages import SystemMessage, AIMessage
from app.agent.state import AgentState
from app.agent.prompts import RECOMMENDATION_SYSTEM_PROMPT
from app.services.llm import get_llm
from app.services.product_catalog import get_all_products, get_product, get_all_competitors
from app.services.rag import search_or_scrape


PRODUCT_SELECTION_PROMPT = """Determine if the sales rep has confirmed or selected specific Getac product(s) to proceed with.

A selection means the rep said something like "let's go with the B360", "recommend the F110 and B360", "those two work", "approve the recommendations", "yes", or named specific products. Do NOT assume selection from the agent's recommendation alone — the rep must confirm it.

The rep may select ONE product or MULTIPLE products (e.g., "let's go with both the B360 and the F110", "add the S410 too").

Available products (id -> name):
{product_names}

Already selected products: {already_selected}

If new product(s) were clearly selected/confirmed, return: {{"selected": ["product_id1", "product_id2"]}}
If the rep wants to remove a product, return: {{"remove": ["product_id"]}}
If no product selected yet, return: {{"selected": []}}

Return ONLY valid JSON, no other text."""


async def recommendation_node(state: AgentState) -> dict:
    """Phase 02: Product recommendation and competitive analysis (multi-product)."""
    llm = get_llm()
    persona = state.get("persona")
    selected_products = list(state.get("selected_products") or [])
    messages = state["messages"]

    # Try to detect product selection from conversation
    products = get_all_products()
    product_names = {p.id: p.name for p in products}
    already_selected_ids = [p.id for p in selected_products]

    extraction_llm = get_llm(streaming=False, temperature=0).with_config(tags=["extraction"])

    selection_prompt = PRODUCT_SELECTION_PROMPT.format(
        product_names=json.dumps(product_names),
        already_selected=json.dumps(already_selected_ids) if already_selected_ids else "none",
    )
    from langchain_core.messages import HumanMessage as _HM
    human_messages = [m for m in messages if isinstance(m, _HM)][-3:]
    extract_messages = human_messages + [SystemMessage(content=selection_prompt)]
    result = await extraction_llm.ainvoke(extract_messages)

    try:
        content = result.content
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
        parsed = json.loads(content.strip())

        # Handle removals
        if parsed.get("remove"):
            remove_ids = parsed["remove"]
            selected_products = [p for p in selected_products if p.id not in remove_ids]

        # Handle new selections
        if parsed.get("selected"):
            for pid in parsed["selected"]:
                prod = get_product(pid)
                if prod and prod.id not in [p.id for p in selected_products]:
                    selected_products.append(prod)
    except (json.JSONDecodeError, IndexError) as e:
        import logging
        logging.warning(f"Product extraction failed: {e}, raw: {result.content[:200]}")

    # Build product list for the prompt
    computing_products = [p for p in products if any(
        kw in p.category.lower() for kw in ("laptop", "tablet", "convertible", "server")
    )]
    video_products = [p for p in products if any(
        kw in p.category.lower() for kw in ("camera", "video", "display", "edge")
    )]

    product_lines = []
    for p in computing_products:
        weight_str = f", {p.weight}" if getattr(p, "weight", None) else ""
        brightness_str = f", {p.display_brightness}" if getattr(p, "display_brightness", None) else ""
        selected_marker = " [SELECTED]" if p.id in [sp.id for sp in selected_products] else ""
        product_lines.append(
            f"- **{p.name}** (id: {p.id}){selected_marker}: {p.category}, ${p.base_price:,.0f}, "
            f"{p.display_size}{brightness_str}{weight_str}, {p.rugged_rating}, "
            f"{p.warranty_standard}. Key: {', '.join(p.key_features[:4])}"
        )
    if video_products:
        product_lines.append("\nVIDEO & CAMERA SOLUTIONS:")
        for p in video_products:
            selected_marker = " [SELECTED]" if p.id in [sp.id for sp in selected_products] else ""
            product_lines.append(
                f"- **{p.name}** (id: {p.id}){selected_marker}: {p.category}, ${p.base_price:,.0f}. "
                f"Key: {', '.join(p.key_features[:3])}"
            )
    product_list = "\n".join(product_lines)

    # Persona summary
    persona_summary = "Not available"
    if persona:
        pd = persona.model_dump()
        persona_summary = "\n".join(
            f"  {k.replace('_', ' ').title()}: {v}" for k, v in pd.items() if v is not None and v != []
        )

    # RAG context — semantic search from ChromaDB knowledge base
    rag_query_parts = []
    if persona:
        if persona.pain_points:
            rag_query_parts.append("Pain points: " + ", ".join(persona.pain_points[:3]))
        if persona.use_scenarios:
            rag_query_parts.append("Use scenarios: " + ", ".join(persona.use_scenarios[:2]))
        if persona.current_devices:
            rag_query_parts.append("Current devices: " + ", ".join(persona.current_devices))
    rag_query = " | ".join(rag_query_parts) if rag_query_parts else "rugged laptop/tablet competitor comparison"

    # Determine primary competitor for fallback scraping
    primary_competitor = None
    if persona and persona.current_devices:
        primary_competitor = persona.current_devices[0]

    rag_context = search_or_scrape(rag_query, competitor_name=primary_competitor, k=6)

    # Fallback: if RAG returned nothing, use structured competitor catalog
    competitors = get_all_competitors()
    if rag_context == "No relevant information found in knowledge base.":
        rag_context = "\n".join(
            f"- **{c.name}** ({c.category}): ${c.base_price:,.0f}, "
            f"Failure rate: {c.annual_failure_rate*100:.0f}%, "
            f"Weaknesses: {'; '.join(c.weaknesses[:3])}"
            for c in competitors
        )
        data_confidence = (
            "LOW — The competitive intelligence above comes from the internal product catalog, "
            "not from verified knowledge base documents. If the customer's current device is not "
            "listed above, clearly state that you do not have verified competitive data for that "
            "specific product and recommend the sales rep verify specs independently before "
            "presenting to the customer."
        )
    else:
        data_confidence = (
            "HIGH — The competitive intelligence above was retrieved from the verified knowledge "
            "base using semantic search matched to this customer's specific situation."
        )

    system = RECOMMENDATION_SYSTEM_PROMPT.format(
        persona_summary=persona_summary,
        product_list=product_list,
        rag_context=rag_context,
        data_confidence=data_confidence,
        selected_count=len(selected_products),
        selected_names=", ".join(p.name for p in selected_products) if selected_products else "none yet",
    )

    response = await llm.ainvoke([SystemMessage(content=system)] + list(messages))

    # Determine competitive advantages for each selected product
    competitor_names = dict(state.get("competitor_product_names") or {})
    advantages = dict(state.get("competitive_advantages") or {})
    fallback_notices: list[str] = []

    for prod in selected_products:
        if prod.id not in competitor_names and persona and persona.current_devices:
            comp_name = persona.current_devices[0]
            matched = False
            for c in competitors:
                if any(part.lower() in comp_name.lower() for part in c.name.lower().split()):
                    competitor_names[prod.id] = c.name
                    advantages[prod.id] = c.weaknesses
                    matched = True
                    break
            if not matched:
                # No matching competitor found — notify user and fall back to general competitor
                if competitors:
                    fallback = competitors[0]
                    competitor_names[prod.id] = fallback.name
                    advantages[prod.id] = fallback.weaknesses
                    fallback_notices.append(
                        f"**\u26A0\uFE0F Competitor not found:** No competitive data found for "
                        f"\"{comp_name}\" in our database. Using **{fallback.name}** as the "
                        f"default competitor for {prod.name}. You can specify a different "
                        f"competitor if needed."
                    )
                else:
                    competitor_names[prod.id] = comp_name
        elif prod.id not in competitor_names:
            # No current devices specified — default to first competitor
            if competitors:
                competitor_names[prod.id] = competitors[0].name
                advantages[prod.id] = competitors[0].weaknesses

    # Clean up removed products from maps
    active_ids = {p.id for p in selected_products}
    competitor_names = {k: v for k, v in competitor_names.items() if k in active_ids}
    advantages = {k: v for k, v in advantages.items() if k in active_ids}

    # Append fallback notices to the response if any competitor wasn't found
    if fallback_notices:
        notice_text = "\n\n---\n\n" + "\n\n".join(fallback_notices)
        response = AIMessage(content=response.content + notice_text)

    new_phase = "recommendation"

    return {
        "messages": [response],
        "selected_products": selected_products,
        "competitor_product_names": competitor_names,
        "competitive_advantages": advantages,
        "current_phase": new_phase,
    }
