# ==============================================================================
# KatilimALM - (c) 2024-2026 Salih Say
# GitHub: github.com/SalihSay
# Bu yazilim telif haklari ile korunmaktadir.
# Izinsiz kopyalanmasi, dagitilmasi veya degistirilmesi yasaktir.
# ==============================================================================
"""
KatılımALM — Plotly Grafik Yardımcıları
Tekrar kullanılan dashboard grafikleri.
Renk Paleti: Koyu lacivert + Altın + Yeşil/Kırmızı trafik ışığı
"""
import plotly.graph_objects as go
import plotly.express as px
from typing import List, Dict
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import config

# Renk paleti
COLORS = {
    "primary": "#1B2A4A",
    "accent": "#D4AF37",
    "success": "#2ECC71",
    "warning": "#F39C12",
    "danger": "#E74C3C",
    "light_bg": "#F8F9FA",
    "dark_bg": "#0E1117",
    "level_1": "#1B6B93",
    "level_2a": "#58A399",
    "level_2b": "#A2C579",
    "outflow": "#E74C3C",
    "inflow": "#2ECC71",
    "neutral": "#95A5A6",
    "blue": "#3498DB",
    "purple": "#9B59B6",
    "teal": "#1ABC9C",
}

LAYOUT_DEFAULTS = dict(
    font=dict(family="Inter, Roboto, sans-serif", size=13),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    margin=dict(l=40, r=40, t=50, b=40),
)


def create_gauge_chart(
    value: float,
    title: str,
    min_val: float = 0,
    max_val: float = 200,
    threshold: float = 100,
    suffix: str = "%",
) -> go.Figure:
    """LCR/NSFR/Kaldıraç oranı gauge (ibre) grafik."""
    if value >= threshold:
        bar_color = COLORS["success"]
    elif value >= threshold * 0.9:
        bar_color = COLORS["warning"]
    else:
        bar_color = COLORS["danger"]
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=value,
        number={"suffix": suffix, "font": {"size": 28, "color": COLORS["primary"]}},
        delta={"reference": threshold, "increasing": {"color": COLORS["success"]}, "decreasing": {"color": COLORS["danger"]}},
        title={"text": title, "font": {"size": 16, "color": COLORS["primary"]}},
        gauge={
            "axis": {"range": [min_val, max_val], "tickwidth": 1, "tickcolor": COLORS["primary"]},
            "bar": {"color": bar_color, "thickness": 0.7},
            "bgcolor": "rgba(0,0,0,0)",
            "borderwidth": 2,
            "bordercolor": COLORS["primary"],
            "steps": [
                {"range": [min_val, threshold * 0.8], "color": "rgba(231,76,60,0.15)"},
                {"range": [threshold * 0.8, threshold], "color": "rgba(243,156,18,0.15)"},
                {"range": [threshold, max_val], "color": "rgba(46,204,113,0.10)"},
            ],
            "threshold": {
                "line": {"color": COLORS["danger"], "width": 3},
                "thickness": 0.8,
                "value": threshold,
            },
        },
    ))
    fig.update_layout(**LAYOUT_DEFAULTS, height=250)
    return fig


def create_waterfall_chart(data: Dict, title: str = "LCR Waterfall") -> go.Figure:
    """LCR waterfall chart (HQLA → Çıkışlar → Girişler → Net → LCR)."""
    labels = list(data.keys())
    values = list(data.values())
    
    measures = []
    for i, (label, val) in enumerate(data.items()):
        if i == 0:
            measures.append("absolute")
        elif i == len(data) - 1:
            measures.append("total")
        else:
            measures.append("relative")
    
    colors = []
    for val in values:
        if val >= 0:
            colors.append(COLORS["success"])
        else:
            colors.append(COLORS["danger"])
    
    fig = go.Figure(go.Waterfall(
        name="LCR",
        orientation="v",
        measure=measures,
        x=labels,
        y=values,
        connector={"line": {"color": COLORS["neutral"], "width": 1, "dash": "dot"}},
        increasing={"marker": {"color": COLORS["success"]}},
        decreasing={"marker": {"color": COLORS["danger"]}},
        totals={"marker": {"color": COLORS["accent"]}},
        textposition="outside",
        text=[f"{v:,.0f}" for v in values],
    ))
    fig.update_layout(
        **LAYOUT_DEFAULTS,
        title=dict(text=title, font=dict(size=18, color=COLORS["primary"])),
        height=400,
        showlegend=False,
    )
    return fig


def create_gap_bar_chart(gap_table: list, title: str = "Repricing Gap Analizi") -> go.Figure:
    """Gap analizi bar chart — her vade aralığı için RSA, RSL, Gap."""
    buckets = [g.bucket_name for g in gap_table]
    rsa = [g.rate_sensitive_assets for g in gap_table]
    rsl = [g.rate_sensitive_liabilities for g in gap_table]
    gaps = [g.gap for g in gap_table]
    cum_gap = [g.cumulative_gap for g in gap_table]
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        name="RSA (Aktif)", x=buckets, y=rsa,
        marker_color=COLORS["blue"], opacity=0.8,
    ))
    fig.add_trace(go.Bar(
        name="RSL (Pasif)", x=buckets, y=rsl,
        marker_color=COLORS["danger"], opacity=0.8,
    ))
    fig.add_trace(go.Bar(
        name="Gap", x=buckets, y=gaps,
        marker_color=[COLORS["success"] if g >= 0 else COLORS["warning"] for g in gaps],
        opacity=0.9,
    ))
    fig.add_trace(go.Scatter(
        name="Kümülatif Gap", x=buckets, y=cum_gap,
        mode="lines+markers",
        line=dict(color=COLORS["accent"], width=3),
        marker=dict(size=8),
        yaxis="y2",
    ))
    
    fig.update_layout(
        **LAYOUT_DEFAULTS,
        title=dict(text=title, font=dict(size=18, color=COLORS["primary"])),
        barmode="group",
        height=450,
        yaxis=dict(title="Tutar (TL)"),
        yaxis2=dict(title="Kümülatif Gap", overlaying="y", side="right"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0.5, xanchor="center"),
    )
    return fig


def create_heatmap(data: List[Dict], title: str = "IRRBB Heatmap") -> go.Figure:
    """Stres testi / IRRBB heatmap."""
    scenarios = [d.get("scenario", d.get("scenario_name", "")) for d in data]
    metrics = ["ΔEVE (%)", "ΔNII (%)"]
    
    z = []
    for d in data:
        z.append([
            d.get("delta_eve_pct", 0),
            d.get("delta_nii_pct", 0),
        ])
    
    fig = go.Figure(go.Heatmap(
        z=z,
        x=metrics,
        y=scenarios,
        colorscale=[
            [0, COLORS["danger"]],
            [0.5, COLORS["warning"]],
            [1, COLORS["success"]],
        ],
        text=[[f"{v:.1f}%" for v in row] for row in z],
        texttemplate="%{text}",
        textfont={"size": 14},
        hoverinfo="all",
    ))
    fig.update_layout(
        **LAYOUT_DEFAULTS,
        title=dict(text=title, font=dict(size=18, color=COLORS["primary"])),
        height=350,
    )
    return fig


def create_tornado_chart(
    sensitivities: Dict,
    title: str = "LCR Hassasiyet Analizi",
) -> go.Figure:
    """Tornado chart — her risk faktörünün LCR üzerindeki bireysel etkisi."""
    factors = list(sensitivities.keys())
    impacts = [sensitivities[f]["impact"] for f in factors]
    
    sorted_data = sorted(zip(factors, impacts), key=lambda x: abs(x[1]))
    factors = [d[0] for d in sorted_data]
    impacts = [d[1] for d in sorted_data]
    
    colors = [COLORS["danger"] if i < 0 else COLORS["success"] for i in impacts]
    
    fig = go.Figure(go.Bar(
        x=impacts,
        y=factors,
        orientation="h",
        marker_color=colors,
        text=[f"{i:+.1f}%" for i in impacts],
        textposition="outside",
    ))
    fig.update_layout(
        **LAYOUT_DEFAULTS,
        title=dict(text=title, font=dict(size=18, color=COLORS["primary"])),
        height=400,
        xaxis_title="LCR Etkisi (%)",
    )
    return fig


def create_donut_chart(data: Dict, title: str = "HQLA Dağılımı") -> go.Figure:
    """HQLA dağılımı donut chart."""
    labels = list(data.keys())
    values = list(data.values())
    
    chart_colors = [COLORS["level_1"], COLORS["level_2a"], COLORS["level_2b"], COLORS["neutral"]]
    
    fig = go.Figure(go.Pie(
        labels=labels,
        values=values,
        hole=0.5,
        marker=dict(colors=chart_colors[:len(labels)]),
        textinfo="label+percent",
        textfont=dict(size=13),
        hoverinfo="label+value+percent",
    ))
    fig.update_layout(
        **LAYOUT_DEFAULTS,
        title=dict(text=title, font=dict(size=18, color=COLORS["primary"])),
        height=350,
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.1, x=0.5, xanchor="center"),
    )
    return fig


def create_pool_comparison_chart(pools: list) -> go.Figure:
    """Kâr payı havuzu performans karşılaştırma bar chart."""
    names = [p.pool_name for p in pools]
    bank_shares = [p.bank_income for p in pools]
    cust_shares = [p.customer_income for p in pools]
    rates = [p.profit_rate * 100 for p in pools]
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Banka Payı", x=names, y=bank_shares,
        marker_color=COLORS["primary"], opacity=0.85,
    ))
    fig.add_trace(go.Bar(
        name="Müşteri Payı", x=names, y=cust_shares,
        marker_color=COLORS["accent"], opacity=0.85,
    ))
    fig.add_trace(go.Scatter(
        name="Kâr Payı Oranı (%)", x=names, y=rates,
        mode="lines+markers+text",
        text=[f"%{r:.1f}" for r in rates],
        textposition="top center",
        line=dict(color=COLORS["success"], width=3),
        marker=dict(size=10),
        yaxis="y2",
    ))
    
    fig.update_layout(
        **LAYOUT_DEFAULTS,
        title=dict(text="Kâr Payı Havuzu Karşılaştırması", font=dict(size=18, color=COLORS["primary"])),
        barmode="stack",
        height=400,
        yaxis=dict(title="Tutar (TL)"),
        yaxis2=dict(title="Kâr Payı Oranı (%)", overlaying="y", side="right"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0.5, xanchor="center"),
    )
    return fig


def create_stress_comparison_chart(results: list) -> go.Figure:
    """Stres testi senaryo karşılaştırma grouped bar chart."""
    scenarios = [r.scenario.name for r in results]
    lcr_vals = [r.stressed_lcr for r in results]
    nsfr_vals = [r.stressed_nsfr for r in results]
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="LCR (%)", x=scenarios, y=lcr_vals,
        marker_color=[COLORS["success"] if v >= 100 else COLORS["danger"] for v in lcr_vals],
        opacity=0.85,
    ))
    fig.add_trace(go.Bar(
        name="NSFR (%)", x=scenarios, y=nsfr_vals,
        marker_color=[COLORS["blue"] if v >= 100 else COLORS["warning"] for v in nsfr_vals],
        opacity=0.85,
    ))
    
    # Minimum oran çizgisi
    fig.add_hline(y=100, line_dash="dash", line_color=COLORS["danger"],
                  annotation_text="BDDK Minimum %100")
    
    fig.update_layout(
        **LAYOUT_DEFAULTS,
        title=dict(text="Stres Testi — Senaryo Karşılaştırması", font=dict(size=18, color=COLORS["primary"])),
        barmode="group",
        height=400,
        yaxis_title="Oran (%)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0.5, xanchor="center"),
    )
    return fig
