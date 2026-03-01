# ==============================================================================
# KatilimALM - (c) 2024-2026 Salih Say
# GitHub: github.com/SalihSay
# Bu yazilim telif haklari ile korunmaktadir.
# Izinsiz kopyalanmasi, dagitilmasi veya degistirilmesi yasaktir.
# ==============================================================================
"""
KatılımALM — KPI Kartları & Metrik Bileşenleri
"""
import streamlit as st


def render_kpi_card(
    title: str,
    value: str,
    target: str = None,
    status: str = "success",
    delta: str = None,
    icon: str = "📊",
):
    """
    KPI kartı render eder.
    
    Args:
        status: "success" (yeşil), "warning" (sarı), "danger" (kırmızı)
    """
    status_colors = {
        "success": ("#2ECC71", "#D5F5E3", "✅"),
        "warning": ("#F39C12", "#FEF3CD", "⚠️"),
        "danger": ("#E74C3C", "#FADBD8", "❌"),
    }
    
    color, bg_color, status_icon = status_colors.get(status, status_colors["success"])
    
    target_html = ""
    if target:
        target_html = f'<div style="font-size: 11px; color: #666;">Hedef: {target}</div>'
    
    delta_html = ""
    if delta:
        delta_color = "#2ECC71" if not delta.startswith("-") else "#E74C3C"
        delta_html = f'<span style="font-size: 13px; color: {delta_color}; margin-left: 8px;">{delta}</span>'
    
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, {bg_color} 0%, #FFFFFF 100%);
        border-left: 4px solid {color};
        border-radius: 10px;
        padding: 18px 20px;
        margin-bottom: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    ">
        <div style="font-size: 12px; color: #888; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 4px;">
            {icon} {title}
        </div>
        <div style="font-size: 28px; font-weight: 700; color: #1B2A4A;">
            {value} {delta_html}
        </div>
        <div style="font-size: 13px; color: {color}; margin-top: 4px;">
            {status_icon} {_get_status_text(status)}
        </div>
        {target_html}
    </div>
    """, unsafe_allow_html=True)


def render_traffic_light(value: float, thresholds: dict = None):
    """
    Trafik ışığı göstergesi.
    
    Args:
        thresholds: {"green": 100, "yellow": 80} — yeşil eşik, sarı eşik
    """
    if thresholds is None:
        thresholds = {"green": 100, "yellow": 80}
    
    if value >= thresholds["green"]:
        color = "#2ECC71"
        label = "UYGUN"
    elif value >= thresholds["yellow"]:
        color = "#F39C12"
        label = "DİKKAT"
    else:
        color = "#E74C3C"
        label = "UYARI"
    
    st.markdown(f"""
    <div style="text-align: center; padding: 8px;">
        <div style="
            width: 20px; height: 20px; border-radius: 50%;
            background: {color};
            display: inline-block;
            box-shadow: 0 0 8px {color};
            margin-right: 8px;
            vertical-align: middle;
        "></div>
        <span style="font-size: 14px; font-weight: 600; color: {color}; vertical-align: middle;">
            {label}
        </span>
    </div>
    """, unsafe_allow_html=True)


def render_comparison_card(
    base_value: float,
    stress_value: float,
    label: str,
    suffix: str = "%",
):
    """Baz durum vs. stres karşılaştırma kartı."""
    diff = stress_value - base_value
    diff_color = "#2ECC71" if diff >= 0 else "#E74C3C"
    diff_sign = "+" if diff >= 0 else ""
    
    st.markdown(f"""
    <div style="
        background: #FFFFFF;
        border-radius: 10px;
        padding: 16px;
        margin-bottom: 10px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.06);
        border: 1px solid #E8E8E8;
    ">
        <div style="font-size: 12px; color: #888; margin-bottom: 6px;">{label}</div>
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <span style="font-size: 14px; color: #666;">Baz: </span>
                <span style="font-size: 18px; font-weight: 600; color: #1B2A4A;">{base_value:.1f}{suffix}</span>
            </div>
            <div style="font-size: 20px; color: #ccc;">→</div>
            <div>
                <span style="font-size: 14px; color: #666;">Stres: </span>
                <span style="font-size: 18px; font-weight: 600; color: {diff_color};">{stress_value:.1f}{suffix}</span>
            </div>
            <div style="
                background: {diff_color}22;
                padding: 4px 10px;
                border-radius: 15px;
                font-size: 13px;
                font-weight: 600;
                color: {diff_color};
            ">
                {diff_sign}{diff:.1f}{suffix}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def _get_status_text(status: str) -> str:
    """Durum açıklaması."""
    texts = {
        "success": "Uygun — BDDK limitinin üzerinde",
        "warning": "Dikkat — BDDK limitine yaklaşıyor",
        "danger": "Uyarı — BDDK limitinin altında!",
    }
    return texts.get(status, "")
