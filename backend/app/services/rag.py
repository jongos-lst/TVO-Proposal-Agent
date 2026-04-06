from pathlib import Path
from langchain_chroma import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from app.config import settings

KNOWLEDGE_DIR = Path(__file__).parent.parent / "data" / "knowledge"

_vectorstore: Chroma | None = None


def get_embeddings():
    return HuggingFaceEmbeddings(model_name=settings.embedding_model)


def get_vectorstore() -> Chroma:
    global _vectorstore
    if _vectorstore is None:
        _vectorstore = Chroma(
            collection_name="getac_knowledge",
            embedding_function=get_embeddings(),
            persist_directory=settings.chroma_persist_dir,
        )
    return _vectorstore


def ingest_knowledge():
    """Load all knowledge base markdown files into ChromaDB."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        separators=["\n## ", "\n### ", "\n\n", "\n", " "],
    )

    documents: list[Document] = []
    for md_file in KNOWLEDGE_DIR.glob("*.md"):
        text = md_file.read_text()
        chunks = splitter.split_text(text)
        for chunk in chunks:
            documents.append(Document(
                page_content=chunk,
                metadata={"source": md_file.name},
            ))

    if documents:
        vectorstore = get_vectorstore()
        vectorstore.add_documents(documents)
        print(f"Ingested {len(documents)} chunks from {len(list(KNOWLEDGE_DIR.glob('*.md')))} files")

    return len(documents)


def search_knowledge(query: str, k: int = 4) -> str:
    """Search the knowledge base and return relevant content."""
    vectorstore = get_vectorstore()
    try:
        docs = vectorstore.similarity_search(query, k=k)
    except Exception:
        # ChromaDB may be empty or not initialized
        return "No relevant information found in knowledge base."
    if not docs:
        return "No relevant information found in knowledge base."
    return "\n---\n".join(d.page_content for d in docs)


NO_RESULTS_MSG = "No relevant information found in knowledge base."


def ingest_text(text: str, source: str) -> int:
    """Ingest a single text document into ChromaDB at runtime."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        separators=["\n## ", "\n### ", "\n\n", "\n", " "],
    )
    chunks = splitter.split_text(text)
    documents = [
        Document(page_content=c, metadata={"source": source})
        for c in chunks
    ]
    if documents:
        get_vectorstore().add_documents(documents)
    return len(documents)


def _results_mention_competitor(result: str, competitor_name: str) -> bool:
    """Check if RAG results actually contain content about the named competitor."""
    result_lower = result.lower()
    name_lower = competitor_name.lower()

    # Check full name
    if name_lower in result_lower:
        return True

    # Check significant name parts (skip common words)
    skip_words = {"the", "and", "or", "pro", "plus", "max", "air", "tab", "galaxy"}
    parts = [p for p in name_lower.split() if len(p) > 2 and p not in skip_words]
    if not parts:
        return False

    # Brand name is typically the first significant part
    # If the brand matches, that's a strong signal even if model numbers differ
    brand = parts[0]
    if brand in result_lower:
        return True

    # For multi-part names, require at least 1 significant match
    matches = sum(1 for p in parts if p in result_lower)
    return matches >= 1


def search_or_scrape(query: str, competitor_name: str | None = None, k: int = 4) -> str:
    """Search RAG. If results are irrelevant to the named competitor, scrape and retry."""
    result = search_knowledge(query, k=k)

    if not competitor_name:
        return result

    # If RAG returned content AND it's about the right competitor, use it
    if result != NO_RESULTS_MSG and _results_mention_competitor(result, competitor_name):
        return result

    # RAG returned nothing or irrelevant content — try scraping
    from app.services.competitor_scraper import scrape_competitor_for_rag

    content = scrape_competitor_for_rag(competitor_name)
    if content:
        source = f"web_scrape_{competitor_name.lower().replace(' ', '_')}"
        ingest_text(content, source=source)
        return search_knowledge(query, k=k)

    # Scrape failed too — return whatever RAG had (even if imperfect)
    return result
