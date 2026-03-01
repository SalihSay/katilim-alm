# 🏦 KatılımALM — Katılım Bankası Bilanço & Likidite Risk Dashboard'u

> **Katılım bankalarının BDDK raporlama ve likidite yönetim süreçlerini 3 saatten 5 dakikaya indiren, Basel III uyumlu interaktif analiz platformu.**

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.30+-red.svg)](https://streamlit.io)
[![License](https://img.shields.io/badge/License-Proprietary-red.svg)](LICENSE)
[![Basel III](https://img.shields.io/badge/Basel_III-Compliant-gold.svg)]()
[![Developer](https://img.shields.io/badge/Developer-Salih_Say-1B2A4A.svg)](https://github.com/SalihSay)

---

## 🎯 Problem

| Boyut | Açıklama |
|-------|----------|
| **Gerçek sorun** | Katılım bankalarında LCR/NSFR hesaplaması hâlâ büyük ölçüde Excel tabanlı yapılıyor |
| **Neden önemli?** | BDDK, katılım bankalarına konvansiyonel bankalarla aynı Basel III oranlarını uyguluyor; ancak İslami enstrümanlar (Murabaha, Sukuk, Wa'd) standart şablonlara oturmuyor |
| **Mevcut süreç** | CSV → Excel mapping → Manuel hesap → PDF export. **~3 saat/kişi/ay** |
| **Risk** | Manuel hata → BDDK cezası; senaryo analizi imkansız |

## 🚀 Çözüm

KatılımALM, İslami finans enstrümanlarını otomatik sınıflandıran, Basel III likidite oranlarını hesaplayan ve interaktif stres testi sunan bir Streamlit dashboard'udur. **3 saat → 5 dakika**.

### Ana Özellikler

| Özellik | Açıklama |
|---------|----------|
| 💧 **LCR & NSFR** | BDDK formüllerine göre anında hesaplama, **TL/YP ayrı LCR** |
| 🏗️ **İslami Mapping** | Murabaha, Sukuk, Wa'd, Wakala → HQLA / ASF / RSF otomatik atama |
| ⚡ **Stres Testi** | FX şoku, kâr payı şoku, mevduat kaçışı, kredi kaybı simülasyonu |
| 📐 **Duration & IRRBB** | Gap analizi, 6 Basel standart şok senaryosu, ΔEVE & ΔNII |
| 💰 **Kâr Payı Havuzu** | Havuz bazlı kâr dağıtımı, pool transfer pricing — **konvansiyonelde yok!** |
| ⚠️ **DCR** | Displaced Commercial Risk, PER/IRR yeterliliği |
| ⚖️ **Kaldıraç Oranı** | Basel III 3. sütun, bilanço dışı CCF |
| 🏃 **Erken Çekim Riski** | Vade bazlı modelleme, LCR etkisi |
| 📄 **BDDK Rapor** | Excel export (çok sayfalı, formatlı) |

## 📦 Kurulum

```bash
# Repo'yu klonlayın
git clone https://github.com/SalihSay/katilim-alm.git
cd katilim-alm

# Bağımlılıkları yükleyin
pip install -r requirements.txt

# Dashboard'u başlatın
streamlit run app.py
```

## 🌐 Canlı Demo (Streamlit Cloud)

Uygulamayı canlı olarak denemek için:
👉 **[katilim-alm.streamlit.app](https://katilim-alm.streamlit.app)**

> Streamlit Cloud'ça deploy etmek için: GitHub repo'nuzu Streamlit Cloud'a bağlayın → `app.py` seçin → Deploy!

## 🖥️ Kullanım

1. **Veri Yükleme**: Sidebar'dan "Örnek Veri Kullan" veya Excel/CSV yükleyin
2. **Ana Sayfa**: LCR, NSFR, Duration Gap, FX Pozisyon, Kaldıraç KPI'ları
3. **📊 LCR/NSFR**: HQLA dağılımı, waterfall, para birimi bazlı detay
4. **📈 Duration/Gap**: İnteraktif kâr payı şoku slider'ı, IRRBB heatmap
5. **⚡ Stres Testi**: Öntanımlı (2018/2021 krizi) veya özel senaryo, tornado chart
6. **💰 Kâr Payı Havuzu**: Alpha slider'ı, DCR analizi, erken çekim riski
7. **📄 Raporlar**: BDDK formatında Excel indir

## 🏗️ Teknik Mimari

```
┌──────────────────────────────────────────────┐
│                 STREAMLIT UI                  │
│  app.py + 5 sayfa + 3 bileşen                │
├──────────────────────────────────────────────┤
│              HESAPLAMA MOTORLARI (12 modül)   │
│  lcr_engine · nsfr_engine · duration_calc    │
│  gap_analysis · irrbb · stress_test          │
│  profit_pool · dcr_engine · leverage_ratio   │
│  off_balance_sheet · early_withdrawal        │
│  katilim_mapping · scenario_engine           │
├──────────────────────────────────────────────┤
│              VERİ KATMANI                     │
│  data_generator · bddk_mapping.json          │
├──────────────────────────────────────────────┤
│              KÜTÜPHANELER                     │
│  pandas · numpy · scipy · plotly · fpdf2     │
└──────────────────────────────────────────────┘
```

## 📊 İslami Enstrüman Mapping

| İslami Enstrüman | Basel III Karşılığı | HQLA Sınıfı |
|-----------------|---------------------|--------------|
| Devlet Sukuk | Devlet Tahvili | Level 1 |
| Kira Sertifikası | Devlet Tahvili | Level 1 |
| Özel Sektör Sukuk (AA-) | Kurumsal Bono | Level 2A |
| Murabaha Alacakları | Ticari Kredi | HQLA Dışı |
| Finansal Kiralama (İcara) | Leasing | HQLA Dışı |
| Katılma Hesabı | Vadeli Mevduat | — |
| Wa'd Taahhüdü | Forward Taahhüt | — |

## 🛠️ Teknoloji Stack

| Katman | Kütüphaneler |
|--------|-------------|
| UI | Streamlit, Plotly |
| Hesaplama | pandas, numpy, scipy |
| Rapor | openpyxl, fpdf2 |
| Test | pytest, pytest-cov |

## 🏦 Katılım Bankası Benzersizlikleri

Bu proje şu konvansiyonel ALM araçlarından **farklıdır**:

1. **İslami Mapping** — Murabaha, Sukuk, İcara, Wa'd, Wakala doğru Basel III kategorilerine eşlenir
2. **Kâr Payı Havuzu** — Konvansiyonel bankalarda karşılığı yok
3. **DCR** — Displaced Commercial Risk, PER/IRR yönetimi
4. **Kâr Payı ≠ Faiz** — Yield yerine profit rate kullanılır
5. **Altın Hesapları** — XAU cinsinden katılma hesapları özel muamele görür

## 📝 Lisans

© 2024-2026 Salih Say. Tüm hakları saklıdır. Bu yazılım izinsiz kopyalanamaz, dağıtılamaz veya türetme eser oluşturmak için kullanılamaz.

## 👤 Geliştirici

**Salih Say** — [github.com/SalihSay](https://github.com/SalihSay)

Bilgisayar Mühendisliği + Katılım Bankacılığı deneyimini birleştiren bir profesyonel tarafından geliştirilmiştir.

---

*BDDK · IFSB-12 · AAOIFI FAS · Basel III*

