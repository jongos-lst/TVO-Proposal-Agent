"""Generate professional charts for TVO proposal PowerPoint decks.

Uses Getac corporate brand colors: orange #D74B00 accent, blue #0066B3 for
Getac data, red #B8352A for competitor data, green #1A8754 for savings.
All charts render on clean white backgrounds for professional printing.
"""

import os
from io import BytesIO

import matplotlib
matplotlib.use("Agg")  # Non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np

from app.models.tvo import TVOCalculation

# ── Getac Corporate Brand Palette ────────────────────────────────
GETAC_BLUE = "#0066B3"
GETAC_LIGHT_BLUE = "#4A9BD9"
GETAC_ORANGE = "#D74B00"
COMPETITOR_RED = "#B8352A"
COMPETITOR_LIGHT = "#D9534F"
SAVINGS_GREEN = "#1A8754"
BG_COLOR = "#FFFFFF"
TEXT_COLOR = "#2C2C2C"
GRID_COLOR = "#E2E4E8"
MUTED_TEXT = "#6B7080"

# Chart output settings
CHART_DPI = 200


def _apply_style(ax: plt.Axes, title: str = "", dollar_fmt: bool = True):
    """Apply consistent Getac brand styling to axes."""
    ax.set_facecolor(BG_COLOR)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color(GRID_COLOR)
    ax.spines["bottom"].set_color(GRID_COLOR)
    ax.tick_params(colors=TEXT_COLOR, labelsize=10)
    if dollar_fmt:
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x:,.0f}"))
    ax.grid(axis="y", color=GRID_COLOR, linewidth=0.5, alpha=0.7)
    if title:
        ax.set_title(title, fontsize=14, fontweight="bold", color=TEXT_COLOR, pad=15)


def generate_tco_comparison_chart(tvo: TVOCalculation) -> BytesIO:
    """Bar chart comparing TCO line items between Getac and competitor."""
    fig, ax = plt.subplots(figsize=(8, 4.5))
    fig.patch.set_facecolor(BG_COLOR)

    labels = [item.label for item in tvo.tco_line_items]
    getac_vals = [item.getac_value for item in tvo.tco_line_items]
    comp_vals = [item.competitor_value for item in tvo.tco_line_items]

    x = np.arange(len(labels))
    width = 0.35

    bars1 = ax.bar(x - width / 2, getac_vals, width, label="Getac",
                   color=GETAC_BLUE, edgecolor="white", linewidth=0.5, zorder=3)
    bars2 = ax.bar(x + width / 2, comp_vals, width, label="Competitor",
                   color=COMPETITOR_RED, edgecolor="white", linewidth=0.5, zorder=3)

    # Value labels on bars
    max_val = max(getac_vals + comp_vals) if (getac_vals + comp_vals) else 1
    for bar in bars1:
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2, h + max_val * 0.01,
                f"${h:,.0f}", ha="center", va="bottom", fontsize=7.5,
                color=GETAC_BLUE, fontweight="bold")
    for bar in bars2:
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2, h + max_val * 0.01,
                f"${h:,.0f}", ha="center", va="bottom", fontsize=7.5,
                color=COMPETITOR_RED, fontweight="bold")

    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=9, color=TEXT_COLOR)
    _apply_style(ax, f"TCO Comparison \u2014 {tvo.deployment_years}-Year / {tvo.fleet_size} Units")
    ax.legend(frameon=True, facecolor="white", edgecolor=GRID_COLOR, fontsize=10)

    # Annotation: biggest savings driver
    diffs = [item.difference for item in tvo.tco_line_items]
    if diffs and max(diffs) > 0:
        max_idx = diffs.index(max(diffs))
        max_label = tvo.tco_line_items[max_idx].label
        max_diff = max(diffs)
        ax.text(0.5, -0.18, f"Biggest savings driver: {max_label} (${max_diff:,.0f})",
                transform=ax.transAxes, ha="center", fontsize=9, fontstyle="italic",
                color=SAVINGS_GREEN, fontweight="bold")

    plt.tight_layout()
    buf = BytesIO()
    fig.savefig(buf, format="png", dpi=CHART_DPI, bbox_inches="tight", facecolor=BG_COLOR)
    plt.close(fig)
    buf.seek(0)
    return buf


def generate_total_tco_chart(tvo: TVOCalculation) -> BytesIO:
    """Side-by-side total TCO with savings callout."""
    fig, ax = plt.subplots(figsize=(5, 4.5))
    fig.patch.set_facecolor(BG_COLOR)

    categories = ["Getac", "Competitor"]
    values = [tvo.getac_total_tco, tvo.competitor_total_tco]
    colors = [GETAC_BLUE, COMPETITOR_RED]

    bars = ax.bar(categories, values, color=colors, width=0.5,
                  edgecolor="white", linewidth=0.5, zorder=3)

    for bar, val in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, val + max(values) * 0.02,
                f"${val:,.0f}", ha="center", va="bottom", fontsize=12,
                fontweight="bold", color=TEXT_COLOR)

    # Savings annotation arrow
    mid_x = 0.5
    ax.annotate(
        f"Save ${tvo.tco_savings:,.0f}\n({tvo.tco_savings_percent:.1f}%)",
        xy=(1, tvo.competitor_total_tco * 0.5),
        xytext=(mid_x, tvo.competitor_total_tco * 0.75),
        fontsize=12, fontweight="bold", color=SAVINGS_GREEN,
        ha="center",
        arrowprops=dict(arrowstyle="->", color=SAVINGS_GREEN, lw=2),
    )

    _apply_style(ax, "Total Cost of Ownership")
    plt.tight_layout()
    buf = BytesIO()
    fig.savefig(buf, format="png", dpi=CHART_DPI, bbox_inches="tight", facecolor=BG_COLOR)
    plt.close(fig)
    buf.seek(0)
    return buf


def generate_savings_breakdown_chart(tvo: TVOCalculation) -> BytesIO:
    """Pie/donut chart showing where savings come from."""
    fig, ax = plt.subplots(figsize=(5, 4.5))
    fig.patch.set_facecolor(BG_COLOR)

    # Build savings categories
    savings_items = []
    for item in tvo.tco_line_items:
        if item.difference > 0:
            savings_items.append((item.label, item.difference))

    if tvo.productivity_savings_total > 0:
        savings_items.append(("Productivity Gains", tvo.productivity_savings_total))

    if not savings_items:
        plt.close(fig)
        return BytesIO()

    labels = [s[0] for s in savings_items]
    values = [s[1] for s in savings_items]
    colors_palette = [GETAC_BLUE, GETAC_LIGHT_BLUE, SAVINGS_GREEN, GETAC_ORANGE, "#6C5CE7", "#00B894"]
    colors = colors_palette[:len(values)]

    wedges, texts, autotexts = ax.pie(
        values, labels=None, autopct=lambda p: f"${p * sum(values) / 100:,.0f}",
        colors=colors, startangle=90, pctdistance=0.75,
        wedgeprops=dict(width=0.45, edgecolor="white", linewidth=2),
    )
    for t in autotexts:
        t.set_fontsize(8)
        t.set_fontweight("bold")
        t.set_color("white")

    # Center text in donut hole
    total = sum(values)
    ax.text(0, 0, f"Total\n${total:,.0f}", ha="center", va="center",
            fontsize=12, fontweight="bold", color=TEXT_COLOR)

    ax.legend(labels, loc="center left", bbox_to_anchor=(1, 0.5), frameon=False, fontsize=9)
    ax.set_title("Savings Breakdown", fontsize=14, fontweight="bold", color=TEXT_COLOR, pad=15)

    plt.tight_layout()
    buf = BytesIO()
    fig.savefig(buf, format="png", dpi=CHART_DPI, bbox_inches="tight", facecolor=BG_COLOR)
    plt.close(fig)
    buf.seek(0)
    return buf


def generate_productivity_chart(tvo: TVOCalculation) -> BytesIO:
    """Horizontal bar chart comparing downtime, failures, and productivity factor breakdown."""
    applicable_factors = [
        f for f in (tvo.productivity_breakdown or []) if f.applies and f.total_value > 0
    ]
    has_breakdown = len(applicable_factors) > 0
    ncols = 3 if has_breakdown else 2
    fig_w = 12 if has_breakdown else 8
    fig, axes = plt.subplots(1, ncols, figsize=(fig_w, 4))
    fig.patch.set_facecolor(BG_COLOR)

    if ncols == 2:
        ax1, ax2 = axes
    else:
        ax1, ax2, ax3 = axes

    # Panel 1: Downtime comparison
    categories = ["Getac", "Competitor"]
    downtime = [tvo.getac_annual_downtime_hours, tvo.competitor_annual_downtime_hours]
    colors = [GETAC_BLUE, COMPETITOR_RED]

    bars = ax1.barh(categories, downtime, color=colors, height=0.4,
                    edgecolor="white", zorder=3)
    max_dt = max(downtime) if max(downtime) > 0 else 1
    for bar, val in zip(bars, downtime):
        ax1.text(val + max_dt * 0.02, bar.get_y() + bar.get_height() / 2,
                 f"{val:.0f} hrs/yr", va="center", fontsize=10,
                 fontweight="bold", color=TEXT_COLOR)

    ax1.set_facecolor(BG_COLOR)
    ax1.spines["top"].set_visible(False)
    ax1.spines["right"].set_visible(False)
    ax1.spines["left"].set_color(GRID_COLOR)
    ax1.spines["bottom"].set_color(GRID_COLOR)
    ax1.tick_params(colors=TEXT_COLOR, labelsize=10)
    ax1.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:.0f}h"))
    ax1.set_title("Annual Downtime per Unit", fontsize=11, fontweight="bold",
                  color=TEXT_COLOR, pad=10)

    # Panel 2: Failure rate comparison
    failures = [tvo.getac_expected_failures, tvo.competitor_expected_failures]
    bars2 = ax2.barh(categories, failures, color=colors, height=0.4,
                     edgecolor="white", zorder=3)
    max_f = max(failures) if max(failures) > 0 else 1
    for bar, val in zip(bars2, failures):
        ax2.text(val + max_f * 0.02, bar.get_y() + bar.get_height() / 2,
                 f"{val:.1f}", va="center", fontsize=10,
                 fontweight="bold", color=TEXT_COLOR)

    ax2.set_facecolor(BG_COLOR)
    ax2.spines["top"].set_visible(False)
    ax2.spines["right"].set_visible(False)
    ax2.spines["left"].set_color(GRID_COLOR)
    ax2.spines["bottom"].set_color(GRID_COLOR)
    ax2.tick_params(colors=TEXT_COLOR, labelsize=10)
    ax2.set_title(f"Expected Failures ({tvo.deployment_years}yr)", fontsize=11,
                  fontweight="bold", color=TEXT_COLOR, pad=10)

    # Panel 3: Productivity factor breakdown (when data available)
    if has_breakdown:
        factor_colors = [SAVINGS_GREEN, GETAC_BLUE, GETAC_LIGHT_BLUE,
                         GETAC_ORANGE, "#6C5CE7"]
        names = [f.name for f in applicable_factors]
        values = [f.total_value for f in applicable_factors]
        bar_colors = factor_colors[:len(names)]

        bars3 = ax3.barh(names, values, color=bar_colors, height=0.5,
                         edgecolor="white", linewidth=0.5, zorder=3)
        max_v = max(values) if values else 1
        for bar, val in zip(bars3, values):
            ax3.text(val + max_v * 0.02, bar.get_y() + bar.get_height() / 2,
                     f"${val:,.0f}", va="center", fontsize=9,
                     fontweight="bold", color=TEXT_COLOR)

        ax3.set_facecolor(BG_COLOR)
        ax3.spines["top"].set_visible(False)
        ax3.spines["right"].set_visible(False)
        ax3.spines["left"].set_color(GRID_COLOR)
        ax3.spines["bottom"].set_color(GRID_COLOR)
        ax3.tick_params(colors=TEXT_COLOR, labelsize=9)
        ax3.xaxis.set_major_formatter(
            mticker.FuncFormatter(lambda x, _: f"${x:,.0f}"))
        ax3.set_title(f"Productivity Value ({tvo.deployment_years}yr)",
                      fontsize=11, fontweight="bold", color=TEXT_COLOR, pad=10)

    # Annotation: downtime reduction percentage
    if tvo.competitor_annual_downtime_hours > 0:
        reduction_pct = ((tvo.competitor_annual_downtime_hours - tvo.getac_annual_downtime_hours)
                         / tvo.competitor_annual_downtime_hours * 100)
        fig.text(0.5, 0.02, f"Getac reduces downtime by {reduction_pct:.0f}%",
                 ha="center", fontsize=10, fontstyle="italic",
                 color=SAVINGS_GREEN, fontweight="bold")

    plt.tight_layout()
    buf = BytesIO()
    fig.savefig(buf, format="png", dpi=CHART_DPI, bbox_inches="tight", facecolor=BG_COLOR)
    plt.close(fig)
    buf.seek(0)
    return buf


def generate_roi_timeline_chart(tvo: TVOCalculation) -> BytesIO:
    """Line chart showing cumulative cost over time with break-even annotation."""
    fig, ax = plt.subplots(figsize=(8, 4.5))
    fig.patch.set_facecolor(BG_COLOR)

    years = list(range(0, tvo.deployment_years + 1))
    # Year 0 = hardware acquisition only
    getac_hw = tvo.yearly_getac_cumulative[0] - (tvo.yearly_getac_cumulative[1] - tvo.yearly_getac_cumulative[0]) if len(tvo.yearly_getac_cumulative) > 1 else tvo.getac_total_tco / tvo.deployment_years
    comp_hw = tvo.yearly_competitor_cumulative[0] - (tvo.yearly_competitor_cumulative[1] - tvo.yearly_competitor_cumulative[0]) if len(tvo.yearly_competitor_cumulative) > 1 else tvo.competitor_total_tco / tvo.deployment_years
    getac_vals = [getac_hw] + tvo.yearly_getac_cumulative
    comp_vals = [comp_hw] + tvo.yearly_competitor_cumulative

    ax.plot(years, getac_vals, color=GETAC_BLUE, linewidth=2.5, marker="o",
            markersize=6, label="Getac", zorder=5)
    ax.plot(years, comp_vals, color=COMPETITOR_RED, linewidth=2.5, marker="s",
            markersize=6, label="Competitor", zorder=5)

    # Shade savings zone where competitor > getac
    getac_arr = np.array(getac_vals, dtype=float)
    comp_arr = np.array(comp_vals, dtype=float)
    mask = comp_arr > getac_arr
    if mask.any():
        ax.fill_between(years, getac_vals, comp_vals, where=mask,
                        alpha=0.12, color=SAVINGS_GREEN, zorder=2)

    # Break-even annotation
    if 0 < tvo.roi_payback_months < tvo.deployment_years * 12:
        breakeven_yr = tvo.roi_payback_months / 12
        yr_floor = int(breakeven_yr)
        yr_ceil = min(yr_floor + 1, len(getac_vals) - 1)
        frac = breakeven_yr - yr_floor
        be_cost = getac_vals[yr_floor] + frac * (getac_vals[yr_ceil] - getac_vals[yr_floor])

        ax.annotate(
            f"Break-even\nMonth {tvo.roi_payback_months:.0f}",
            xy=(breakeven_yr, be_cost),
            xytext=(breakeven_yr + 0.4, be_cost - (max(comp_vals) - min(getac_vals)) * 0.15),
            fontsize=10, fontweight="bold", color=GETAC_ORANGE,
            ha="left",
            arrowprops=dict(arrowstyle="->", color=GETAC_ORANGE, lw=2),
        )
        ax.axvline(x=breakeven_yr, color=GETAC_ORANGE, linestyle="--",
                   linewidth=1, alpha=0.5)

    ax.set_xticks(years)
    ax.set_xticklabels([f"Yr {y}" if y > 0 else "Purchase" for y in years],
                       fontsize=9, color=TEXT_COLOR)
    _apply_style(ax, f"ROI Timeline \u2014 {tvo.fleet_size} Units")
    ax.legend(frameon=True, facecolor="white", edgecolor=GRID_COLOR,
              fontsize=10, loc="upper left")

    plt.tight_layout()
    buf = BytesIO()
    fig.savefig(buf, format="png", dpi=CHART_DPI, bbox_inches="tight", facecolor=BG_COLOR)
    plt.close(fig)
    buf.seek(0)
    return buf


def generate_cost_waterfall_chart(tvo: TVOCalculation) -> BytesIO:
    """Grouped bar chart showing year-by-year cumulative costs."""
    fig, ax = plt.subplots(figsize=(8, 4.5))
    fig.patch.set_facecolor(BG_COLOR)

    n_years = tvo.deployment_years
    labels = [f"Year {y}" for y in range(1, n_years + 1)]
    getac_vals = tvo.yearly_getac_cumulative
    comp_vals = tvo.yearly_competitor_cumulative

    x = np.arange(n_years)
    width = 0.35

    bars1 = ax.bar(x - width / 2, getac_vals, width, label="Getac",
                   color=GETAC_BLUE, edgecolor="white", linewidth=0.5, zorder=3)
    bars2 = ax.bar(x + width / 2, comp_vals, width, label="Competitor",
                   color=COMPETITOR_RED, edgecolor="white", linewidth=0.5, zorder=3)

    # Value labels on final year bars
    for i, (b1, b2) in enumerate(zip(bars1, bars2)):
        if i == n_years - 1:
            ax.text(b1.get_x() + b1.get_width() / 2, b1.get_height() + max(comp_vals) * 0.01,
                    f"${b1.get_height():,.0f}", ha="center", va="bottom", fontsize=8,
                    color=GETAC_BLUE, fontweight="bold")
            ax.text(b2.get_x() + b2.get_width() / 2, b2.get_height() + max(comp_vals) * 0.01,
                    f"${b2.get_height():,.0f}", ha="center", va="bottom", fontsize=8,
                    color=COMPETITOR_RED, fontweight="bold")

    # Savings annotation at final year
    if n_years > 0:
        final_savings = comp_vals[-1] - getac_vals[-1]
        if final_savings > 0:
            mid_y = (getac_vals[-1] + comp_vals[-1]) / 2
            ax.annotate(
                f"Save ${final_savings:,.0f}",
                xy=(n_years - 1 + width / 2, comp_vals[-1]),
                xytext=(n_years - 1 + 0.6, mid_y),
                fontsize=11, fontweight="bold", color=SAVINGS_GREEN, ha="left",
                arrowprops=dict(arrowstyle="->", color=SAVINGS_GREEN, lw=1.5),
            )

    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=9, color=TEXT_COLOR)
    _apply_style(ax, f"Cumulative Cost \u2014 {tvo.deployment_years}-Year / {tvo.fleet_size} Units")
    ax.legend(frameon=True, facecolor="white", edgecolor=GRID_COLOR, fontsize=10)

    plt.tight_layout()
    buf = BytesIO()
    fig.savefig(buf, format="png", dpi=CHART_DPI, bbox_inches="tight", facecolor=BG_COLOR)
    plt.close(fig)
    buf.seek(0)
    return buf


def generate_risk_gauge_chart(tvo: TVOCalculation) -> BytesIO:
    """Semi-circle gauge showing risk reduction percentage."""
    fig, ax = plt.subplots(figsize=(5, 4.5), subplot_kw={"projection": "polar"})
    fig.patch.set_facecolor(BG_COLOR)

    pct = min(tvo.risk_reduction_percent, 100.0)
    theta_full = np.pi
    theta_fill = theta_full * (pct / 100.0)

    # Background arc (gray)
    theta_bg = np.linspace(0, np.pi, 100)
    ax.fill_between(theta_bg, 0.6, 1.0, color=GRID_COLOR, alpha=0.4)

    # Filled arc (orange — Getac brand)
    theta_val = np.linspace(0, theta_fill, 100)
    ax.fill_between(theta_val, 0.6, 1.0, color=GETAC_ORANGE, alpha=0.9)

    # Center text
    ax.text(np.pi / 2, 0.2, f"{pct:.0f}%", ha="center", va="center",
            fontsize=28, fontweight="bold", color=GETAC_ORANGE,
            transform=ax.transData)
    ax.text(np.pi / 2, -0.1, "Fewer Failures", ha="center", va="center",
            fontsize=10, color=TEXT_COLOR, transform=ax.transData)

    # Failure comparison text below
    ax.text(np.pi / 2, -0.35,
            f"Getac: {tvo.getac_expected_failures:.0f}  |  Competitor: {tvo.competitor_expected_failures:.0f}",
            ha="center", va="center", fontsize=9, color=TEXT_COLOR,
            transform=ax.transData)

    ax.set_ylim(-.6, 1.1)
    ax.set_thetamin(0)
    ax.set_thetamax(180)
    ax.set_rticks([])
    ax.set_thetagrids([])
    ax.spines["polar"].set_visible(False)
    ax.grid(False)
    ax.set_facecolor(BG_COLOR)

    plt.tight_layout()
    buf = BytesIO()
    fig.savefig(buf, format="png", dpi=CHART_DPI, bbox_inches="tight", facecolor=BG_COLOR)
    plt.close(fig)
    buf.seek(0)
    return buf


def generate_all_charts(tvo: TVOCalculation, output_dir: str) -> dict[str, str]:
    """Generate all charts and save to output_dir. Returns dict of chart_name -> file_path."""
    os.makedirs(output_dir, exist_ok=True)
    charts = {}

    chart_funcs = {
        "tco_comparison": generate_tco_comparison_chart,
        "total_tco": generate_total_tco_chart,
        "savings_breakdown": generate_savings_breakdown_chart,
        "productivity": generate_productivity_chart,
        "roi_timeline": generate_roi_timeline_chart,
        "cost_waterfall": generate_cost_waterfall_chart,
        "risk_gauge": generate_risk_gauge_chart,
    }

    for name, func in chart_funcs.items():
        try:
            buf = func(tvo)
            if buf.getbuffer().nbytes > 0:
                path = os.path.join(output_dir, f"{name}.png")
                with open(path, "wb") as f:
                    f.write(buf.read())
                charts[name] = path
        except Exception as e:
            print(f"Warning: Failed to generate {name} chart: {e}")

    return charts
