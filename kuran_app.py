import streamlit as st
import requests

st.set_page_config(page_title="📖 Kuran Okuyucu", layout="wide")

# Başlık
st.title("📖 Kuran Okuyucu")
st.write("Kuran'dan istediğiniz Sure ve Ayeti okuyun")

# API'den Sureleri al
@st.cache_data
def get_suras():
    try:
        response = requests.get("https://api.quran.com/api/v4/chapters?language=tr", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if 'chapters' in data:
                return data['chapters']
    except Exception as e:
        st.error(f"API Hatası: {e}")
    return []

# Sureleri yükle
suras = get_suras()

if not suras:
    st.error("❌ Sureler yüklenemedi.")
    st.stop()

# Sura seç
st.subheader("📚 Sure Seç")

sura_names = []
for s in suras:
    sura_id = s.get('id', '?')
    sura_arabic = s.get('name_arabic', '?')
    sura_turkish = s.get('translated_name', {}).get('name', '?')
    name = f"{sura_id}. {sura_arabic} ({sura_turkish})"
    sura_names.append(name)

selected_sura_text = st.selectbox("Sura Seç:", sura_names)

selected_sura_num = int(selected_sura_text.split(".")[0].strip())
selected_sura = next((s for s in suras if s['id'] == selected_sura_num), None)

if not selected_sura:
    st.error("❌ Sure seçilemedi")
    st.stop()

# Seçilen Suranın Bilgileri
sura_name = selected_sura.get('translated_name', {}).get('name', 'N/A')
sura_arabic = selected_sura.get('name_arabic', 'N/A')
st.info(f"📖 {sura_name} Suresi ({sura_arabic})")
st.write(f"**Toplam Ayet:** {selected_sura.get('verses_count', 0)}")

# Ayet aralığı seç
st.subheader("📍 Ayet Aralığı Seç")

col1, col2 = st.columns(2)

verses_count = selected_sura.get('verses_count', 1)

with col1:
    start_verse = st.number_input(
        "Başlangıç Ayeti:",
        min_value=1,
        max_value=verses_count,
        value=1
    )

with col2:
    end_verse = st.number_input(
        "Bitiş Ayeti:",
        min_value=1,
        max_value=verses_count,
        value=min(5, verses_count)
    )

if start_verse > end_verse:
    st.error("❌ Başlangıç ayeti bitiş ayetinden küçük olmalı!")
    st.stop()

# Okuyucu seçimi
st.subheader("🎤 Okuyucu Seç")

qari_options = {
    "Abdul Basit": "abdulbasit",
    "Mishari Rashid": "mishari",
    "Ahmed Al Ajmi": "ajmi",
    "Saad Al Ghamdi": "ghamdi",
}

selected_qari_name = st.selectbox("Okuyucu:", list(qari_options.keys()))
selected_qari = qari_options[selected_qari_name]

# Ayetleri al
@st.cache_data
def get_verses(sura_num, start, end):
    verses_data = []
    for verse_num in range(start, end + 1):
        try:
            response = requests.get(
                f"https://api.quran.com/api/v4/quran/verses/uthmani?chapter_number={sura_num}&verse_number={verse_num}",
                timeout=10
            )
            if response.status_code == 200:
                verse_response = response.json()
                if 'verses' in verse_response and len(verse_response['verses']) > 0:
                    verses_data.append(verse_response['verses'][0])
        except:
            continue
    return verses_data

verses = get_verses(selected_sura_num, start_verse, end_verse)

if not verses:
    st.error("❌ Ayetler yüklenemedi")
    st.stop()

# Ayet Metni Göster
st.subheader("📖 Ayetler")

for verse in verses:
    verse_key = verse.get('verse_key', '?:?')
    verse_text = verse.get('text_uthmani', 'N/A')
    
    if ':' in verse_key:
        verse_num = verse_key.split(':')[1]
    else:
        verse_num = '?'
    
    st.write(f"**Ayet {verse_num}:**")
    st.write(f"### {verse_text}")
    st.divider()

# Ses Oynatma
st.subheader("🔊 Dinle")

audio_urls = []
for verse in verses:
    verse_key = verse.get('verse_key', '')
    
    if verse_key and ':' in verse_key:
        surah, ayah = verse_key.split(':')
        surah = surah.strip()
        ayah = ayah.strip()
        
        audio_url = f"https://cdn.alquran.cloud/media/audio/{selected_qari}/{surah}/{ayah}.mp3"
        audio_urls.append((ayah, audio_url))

if audio_urls:
    for ayah_num, audio_url in audio_urls:
        st.write(f"**Ayet {ayah_num}:**")
        st.audio(audio_url, format="audio/mp3")
else:
    st.warning("⚠️ Ses dosyaları bulunamadı")

# Alt bilgi
st.divider()
st.write("💡 **Kullanım:** Sura seçin → Ayet aralığı → Okuyucu → Sesli Dinleyin")
st.write("📱 **Teknoloji:** Streamlit + Quran API + Alquran.cloud Audio")
st.caption("📖 Kuran'ın metin ve sesi quran.com ve alquran.cloud API'lerinden alınmaktadır")
