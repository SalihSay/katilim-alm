# ==============================================================================
# KatilimALM - (c) 2024-2026 Salih Say
# GitHub: github.com/SalihSay
# Telif haklari ile korunmaktadir. Izinsiz kopyalanamaz.
# ==============================================================================
"""
KatılımALM — Metrik Açıklamaları & Yönetici Özetleri
Her metrik için halk dilinde açıklama ve 5-saniye kuralına uygun yorum.
"""
import streamlit as st


# ==============================================================================
# METRİK AÇIKLAMALARI (Halk dili)
# ==============================================================================

EXPLANATIONS = {
    "lcr": {
        "title": "💧 Likidite Karşılama Oranı (LCR)",
        "simple": "Bankanın 30 gün boyunca nakit ihtiyacını karşılayıp karşılayamayacağını gösterir.",
        "detail": "LCR, bankanın elindeki hızlı nakde çevrilebilir varlıkların (Devlet Sukuk, nakit vb.) 30 günlük net nakit çıkışına bölünmesiyle hesaplanır. BDDK'nın belirlediği minimum oran %100'dür.",
        "good": "✅ LCR %100'ün üzerinde — banka 30 günlük bir kriz durumunda bile nakit ihtiyacını karşılayabilir.",
        "warning": "⚠️ LCR %100'e yaklaşıyor — nakit tamponları azalıyor, hızlı varlık artışı gerekebilir.",
        "bad": "🚨 LCR %100'ün altında — banka yasal minimum limiti karşılamıyor! Acil önlem gerekli.",
    },
    "nsfr": {
        "title": "🏗️ Kararlı Fonlama Oranı (NSFR)",
        "simple": "Bankanın uzun vadeli varlıklarını uzun vadeli kaynaklarla ne kadar finanse edebildiğini gösterir.",
        "detail": "NSFR, kullanılabilir kararlı fonlamanın (ASF) gerekli kararlı fonlamaya (RSF) bölünmesiyle hesaplanır. Kısa vadeli mevduatla uzun vadeli kredi vermenin riskini ölçer.",
        "good": "✅ NSFR %100'ün üzerinde — varlık-kaynak vade uyumu sağlıklı.",
        "warning": "⚠️ NSFR %100'e yaklaşıyor — uzun vadeli fonlama kaynağı artırılmalı.",
        "bad": "🚨 NSFR %100'ün altında — vade uyumsuzluğu yüksek! Uzun vadeli fonlama yetersiz.",
    },
    "leverage": {
        "title": "⚖️ Kaldıraç Oranı",
        "simple": "Bankanın sermayesinin toplam varlıklarına oranını gösterir — ne kadar 'borçla büyüdüğünü' ölçer.",
        "detail": "Kaldıraç oranı = Çekirdek Sermaye / Toplam Risk Tutarı. BDDK minimum %3 gerektirir. Daha yüksek oran, bankanın daha güçlü sermaye tabanına sahip olduğunu gösterir.",
        "good": "✅ Kaldıraç oranı %3'ün üzerinde — sermaye yeterliliği sağlıklı.",
        "warning": "⚠️ Kaldıraç oranı %3'e yaklaşıyor — sermaye güçlendirme düşünülmeli.",
        "bad": "🚨 Kaldıraç oranı %3'ün altında — yasal minimum karşılanmıyor!",
    },
    "duration_gap": {
        "title": "📐 Vade Uyumsuzluğu (Duration Gap)",
        "simple": "Aktif ve pasif tarafın ortalama vadeleri arasındaki farkı gösterir. Fark büyükse, kâr payı oranı değişimlerinde risk artar.",
        "detail": "Pozitif gap: Aktifler pasiflerden uzun vadeli → oranlar yükselirse özkaynak değer kaybeder. Negatif gap: Aksi durum. İdeal olan sıfıra yakın bir değerdir.",
        "good": "✅ Vade uyumsuzluğu düşük (±2 yıl) — kâr payı oranı riski kontrol altında.",
        "warning": "⚠️ Vade uyumsuzluğu orta seviyede (2-4 yıl) — oran değişimlerine dikkat.",
        "bad": "🚨 Vade uyumsuzluğu yüksek (4+ yıl) — kâr payı değişimlerinde ciddi risk!",
    },
    "fx_position": {
        "title": "💱 Döviz Pozisyonu",
        "simple": "Bankanın döviz varlık ve borçları arasındaki farkın özkaynaklara oranıdır. Kur değişimlerinden ne kadar etkileneceğini gösterir.",
        "detail": "BDDK, net döviz pozisyonunun özkaynaklara oranını sınırlandırır. Yüksek oran, TL değer kaybettiğinde bankanın ciddi zarar göreceği anlamına gelir.",
        "good": "✅ Döviz pozisyonu limit içinde — kur riski yönetilebilir seviyede.",
        "bad": "🚨 Döviz pozisyonu BDDK limitini aşıyor — acil pozisyon kapatma gerekli!",
    },
    "hqla": {
        "title": "🏛️ HQLA (Yüksek Kaliteli Likit Varlıklar)",
        "simple": "Kriz anında hızlıca nakde çevrilebilen varlıklar: Devlet Sukuk, nakit, Merkez Bankası hesapları gibi. LCR'nin payını oluşturur.",
        "detail": "Level 1 (en likit): Nakit + Devlet sukukları. Level 2A: Yüksek notlu kurumsal sukuk (%15 kesinti). Level 2B: Diğer kabul edilebilir menkul kıymetler (%50 kesinti). Level 2 toplamı, HQLA'nın %40'ını aşamaz.",
    },
    "stress_test": {
        "title": "⚡ Stres Testi",
        "simple": "Kriz senaryolarında (kur şoku, mevduat kaçışı vb.) bankanın oranlarının ne olacağını simüle eder.",
        "detail": "Farklı şok senaryoları (2018 kur krizi, 2021 faiz artışı gibi) uygulanarak LCR, NSFR ve kaldıraç oranlarının ne kadar düşeceği hesaplanır. Bankanın krize dayanıklılığını test eder.",
    },
    "profit_pool": {
        "title": "💰 Kâr Payı Havuzu",
        "simple": "Katılım bankalarına özgü bir sistem: Müşteri mevduatları vade gruplarına göre havuzlarda toplanır, her havuzun kârı ayrı hesaplanır ve müşteriye dağıtılır.",
        "detail": "Alpha oranı, bankanın kârdan aldığı payı gösterir. Kalan müşteriye dağıtılır. Her vade grubunun (1 ay, 3 ay, 6 ay, 1 yıl) ayrı havuzu ve kâr payı oranı vardır.",
    },
    "dcr": {
        "title": "⚠️ Ticari Kayma Riski (DCR)",
        "simple": "Piyasa oranları yükseldiğinde bankanın müşteriye rekabetçi kâr payı verebilmek için kendi kârından feragat etme zorunluluğudur.",
        "detail": "DCR katılım bankalarına özgü bir risktir. PER (Kâr Dengeleme Yedeği) ve IRR (Yatırım Risk Yedeği) bu riski yönetmek için kullanılan tamponlardır.",
    },
    "gap_analysis": {
        "title": "📊 Vade Aralığı Analizi (Gap)",
        "simple": "Varlık ve borçları vade aralıklarına (0-1 ay, 1-3 ay, 3-6 ay...) göre gruplar. Her aralıkta varlıklar borçlardan fazlaysa 'fazla', azsa 'açık' vardır.",
        "detail": "Pozitif gap olan aralıklarda oranlar yükselirse gelir artar. Negatif gap'te ise maliyet artar. Kümülatif gap, toplam açık/fazla birikmesini gösterir.",
    },
    "irrbb": {
        "title": "🔥 Kâr Payı Oranı Riski (IRRBB)",
        "simple": "Kâr payı oranları değiştiğinde bankanın özkaynak değerinin (EVE) ve net gelirinin (NII) ne kadar etkileneceğini ölçer.",
        "detail": "Basel standardı 6 farklı şok senaryosu uygular: paralel artış/azalış, eğri dikleşme/düzleşme, kısa/uzun vade şoku. ΔEVE özkaynaklara oranı %15'i aşmamalıdır.",
    },
    "early_withdrawal": {
        "title": "🏃 Erken Çekim Riski",
        "simple": "Vadeli hesap sahibi müşterilerin vadesinden önce parasını çekme olasılığı. Bu durum bankanın nakit planlamasını bozar.",
        "detail": "Katılım bankalarında erken çekim yapan müşteri kâr payını kaybeder ama anaparasını alır. Piyasa oranları yükseldiğinde müşteriler daha iyi oranlar için başka bankaya geçebilir.",
    },
}


def render_metric_explanation(metric_key: str, value: float = None, expanded: bool = False):
    """
    Metrik açıklamasını sade, anlaşılır şekilde gösterir.
    5-saniye kuralı: Önce sonuç (iyi/kötü), sonra açıklama.
    """
    info = EXPLANATIONS.get(metric_key, {})
    if not info:
        return
    
    with st.expander(f"ℹ️ {info.get('title', '')} — Bu ne anlama geliyor?", expanded=expanded):
        st.markdown(f"**{info.get('simple', '')}**")
        st.caption(info.get('detail', ''))


def get_verdict(metric_key: str, value: float) -> str:
    """
    5-saniye kuralı: Yöneticinin anında anlayacağı tek satırlık yorum döndürür.
    """
    info = EXPLANATIONS.get(metric_key, {})
    
    if metric_key == "lcr":
        if value >= 100:
            return info.get("good", "")
        elif value >= 80:
            return info.get("warning", "")
        else:
            return info.get("bad", "")
    
    elif metric_key == "nsfr":
        if value >= 100:
            return info.get("good", "")
        elif value >= 80:
            return info.get("warning", "")
        else:
            return info.get("bad", "")
    
    elif metric_key == "leverage":
        if value >= 3:
            return info.get("good", "")
        elif value >= 2.5:
            return info.get("warning", "")
        else:
            return info.get("bad", "")
    
    elif metric_key == "duration_gap":
        abs_val = abs(value)
        if abs_val < 2:
            return info.get("good", "")
        elif abs_val < 4:
            return info.get("warning", "")
        else:
            return info.get("bad", "")
    
    elif metric_key == "fx_position":
        if abs(value) < 20:
            return info.get("good", "")
        else:
            return info.get("bad", "")
    
    return ""


def render_executive_summary(lcr, nsfr, leverage, dur_gap, fx_pos):
    """
    5-saniye yönetici özeti — tek bakışta tüm durum.
    Yeşil/Sarı/Kırmızı ışıklarla anında anlaşılır.
    """
    # RİSK skoru hesapla (0-100, düşük = iyi)
    risk_items = []
    
    # LCR
    if lcr >= 120:
        risk_items.append(("Likidite", "🟢", "İyi"))
    elif lcr >= 100:
        risk_items.append(("Likidite", "🟡", "Dikkat"))
    else:
        risk_items.append(("Likidite", "🔴", "Risk"))
    
    # NSFR
    if nsfr >= 120:
        risk_items.append(("Fonlama", "🟢", "İyi"))
    elif nsfr >= 100:
        risk_items.append(("Fonlama", "🟡", "Dikkat"))
    else:
        risk_items.append(("Fonlama", "🔴", "Risk"))
    
    # Kaldıraç
    if leverage >= 5:
        risk_items.append(("Sermaye", "🟢", "İyi"))
    elif leverage >= 3:
        risk_items.append(("Sermaye", "🟡", "Yeterli"))
    else:
        risk_items.append(("Sermaye", "🔴", "Risk"))
    
    # Duration Gap
    if abs(dur_gap) < 2:
        risk_items.append(("Vade Riski", "🟢", "Düşük"))
    elif abs(dur_gap) < 4:
        risk_items.append(("Vade Riski", "🟡", "Orta"))
    else:
        risk_items.append(("Vade Riski", "🔴", "Yüksek"))
    
    # FX
    if abs(fx_pos) < 15:
        risk_items.append(("Kur Riski", "🟢", "Düşük"))
    elif abs(fx_pos) < 20:
        risk_items.append(("Kur Riski", "🟡", "Orta"))
    else:
        risk_items.append(("Kur Riski", "🔴", "Yüksek"))
    
    # Genel durum
    reds = sum(1 for _, light, _ in risk_items if light == "🔴")
    yellows = sum(1 for _, light, _ in risk_items if light == "🟡")
    
    if reds >= 2:
        overall_color = "#E74C3C"
        overall_text = "⚠️ DİKKAT — Birden fazla risk alanında uyarı var"
        overall_bg = "#FADBD8"
    elif reds == 1 or yellows >= 2:
        overall_color = "#F39C12"
        overall_text = "⚡ İZLENMELİ — Bazı göstergeler dikkat gerektiriyor"
        overall_bg = "#FEF3CD"
    else:
        overall_color = "#2ECC71"
        overall_text = "✅ SAĞLIKLI — Tüm göstergeler güvenli aralıkta"
        overall_bg = "#D5F5E3"
    
    # Trafik ışıkları HTML
    lights_html = ""
    for name, light, status in risk_items:
        lights_html += f'<div style="text-align:center;flex:1;min-width:100px;"><div style="font-size:28px;margin-bottom:4px;">{light}</div><div style="font-size:12px;font-weight:600;color:#1B2A4A;">{name}</div><div style="font-size:11px;color:#666;">{status}</div></div>'

    html = f'<div style="background:{overall_bg};border:2px solid {overall_color};border-radius:12px;padding:20px 24px;margin-bottom:20px;"><div style="font-size:16px;font-weight:700;color:{overall_color};margin-bottom:14px;">{overall_text}</div><div style="display:flex;justify-content:space-around;flex-wrap:wrap;gap:8px;">{lights_html}</div></div>'
    st.markdown(html, unsafe_allow_html=True)


def render_chart_title(title: str, explanation: str):
    """Grafik başlığı + kısa açıklama — 5 saniye kuralı."""
    html = f'<div style="margin-bottom:8px;"><span style="font-size:18px;font-weight:700;color:#1B2A4A;">{title}</span><span style="font-size:12px;color:#888;margin-left:10px;">{explanation}</span></div>'
    st.markdown(html, unsafe_allow_html=True)
