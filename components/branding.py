"""
KatılımALM — Marka & Telif Bileşeni
© 2024-2026 Salih Say. Tüm hakları saklıdır.
Her sayfada görüntülenen watermark, footer ve telif bilgisi.
"""
import streamlit as st
from datetime import datetime

# Sabit bilgiler
DEVELOPER_NAME = "Salih Say"
DEVELOPER_GITHUB = "SalihSay"
APP_NAME = "KatılımALM"
COPYRIGHT_YEAR = "2024-2026"
VERSION = "1.0.0"


def render_developer_watermark():
    """
    Sayfanın üst kısmında geliştirici damgası gösterir.
    Kaldırılması zor — CSS ile sabitlenmiş.
    """
    st.markdown(f"""
    <div id="dev-watermark" style="
        position: fixed;
        bottom: 60px;
        right: 20px;
        z-index: 999999;
        background: linear-gradient(135deg, rgba(27,42,74,0.92) 0%, rgba(44,62,107,0.92) 100%);
        padding: 10px 18px;
        border-radius: 8px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.25);
        border: 1px solid rgba(212,175,55,0.4);
        pointer-events: auto;
        backdrop-filter: blur(4px);
    ">
        <div style="
            font-size: 10px; 
            color: #D4AF37; 
            font-weight: 600; 
            letter-spacing: 1.5px;
            text-transform: uppercase;
            margin-bottom: 2px;
        ">
            Developed by
        </div>
        <div style="
            font-size: 14px; 
            color: #FFFFFF; 
            font-weight: 700;
            letter-spacing: 0.5px;
        ">
            {DEVELOPER_NAME}
        </div>
        <div style="
            font-size: 9px; 
            color: rgba(255,255,255,0.5); 
            margin-top: 2px;
        ">
            © {COPYRIGHT_YEAR} · v{VERSION}
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_footer():
    """
    Sayfa altında detaylı telif ve branding footer'ı.
    """
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #1B2A4A 0%, #2C3E6B 100%);
        padding: 28px 30px;
        border-radius: 12px;
        margin-top: 40px;
        border: 1px solid rgba(212,175,55,0.2);
    ">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
            <div>
                <div style="font-size: 18px; font-weight: 700; color: #D4AF37; margin-bottom: 4px;">
                    🏦 {APP_NAME}
                </div>
                <div style="font-size: 12px; color: #B0BEC5;">
                    Basel III Uyumlu Katılım Bankası ALM Platformu
                </div>
                <div style="font-size: 11px; color: rgba(255,255,255,0.4); margin-top: 6px;">
                    IFSB-12 · AAOIFI FAS · BDDK Yönetmeliği
                </div>
            </div>
            <div style="text-align: right;">
                <div style="font-size: 13px; color: #FFFFFF; font-weight: 600;">
                    Geliştiren: {DEVELOPER_NAME}
                </div>
                <div style="font-size: 11px; color: #B0BEC5; margin-top: 4px;">
                    <a href="https://github.com/{DEVELOPER_GITHUB}" target="_blank" 
                       style="color: #D4AF37; text-decoration: none;">
                        github.com/{DEVELOPER_GITHUB}
                    </a>
                </div>
                <div style="font-size: 10px; color: rgba(255,255,255,0.35); margin-top: 6px;">
                    © {COPYRIGHT_YEAR} {DEVELOPER_NAME}. Tüm hakları saklıdır.<br>
                    Bu yazılım izinsiz kopyalanamaz, dağıtılamaz veya türetme eser oluşturmak için kullanılamaz.
                </div>
            </div>
        </div>
    </div>
    
    <!-- Anti-theft: Gizli meta veri -->
    <div style="display:none !important; visibility:hidden; height:0; overflow:hidden;" 
         aria-hidden="true"
         data-author="{DEVELOPER_NAME}" 
         data-github="{DEVELOPER_GITHUB}"
         data-app="{APP_NAME}"
         data-copyright="© {COPYRIGHT_YEAR} {DEVELOPER_NAME}. All rights reserved."
         data-license="Proprietary - Unauthorized copying prohibited"
         data-build-id="KATILIMALM-SS-2026-{hash(DEVELOPER_NAME + APP_NAME) % 999999:06d}">
        KatılımALM is designed and developed by {DEVELOPER_NAME} (github.com/{DEVELOPER_GITHUB}).
        © {COPYRIGHT_YEAR} All Rights Reserved. Unauthorized reproduction, distribution, or creation 
        of derivative works is strictly prohibited.
    </div>
    """, unsafe_allow_html=True)


def render_page_copyright():
    """Sayfa altında küçük telif notu (footer olmadan)."""
    st.markdown(f"""
    <div style="
        text-align: center; 
        padding: 12px; 
        color: #999; 
        font-size: 10px;
        border-top: 1px solid #eee; 
        margin-top: 30px;
    ">
        © {COPYRIGHT_YEAR} {DEVELOPER_NAME} · {APP_NAME} v{VERSION} · 
        <a href="https://github.com/{DEVELOPER_GITHUB}" target="_blank" style="color: #D4AF37;">
            @{DEVELOPER_GITHUB}
        </a>
    </div>
    """, unsafe_allow_html=True)


def get_copyright_header():
    """Kaynak dosyalara eklenecek copyright header metni."""
    return f'''# ==============================================================================
# {APP_NAME} — © {COPYRIGHT_YEAR} {DEVELOPER_NAME}
# GitHub: github.com/{DEVELOPER_GITHUB}
# Bu yazılım telif hakları ile korunmaktadır.
# İzinsiz kopyalanması, dağıtılması veya değiştirilmesi yasaktır.
# =============================================================================='''
