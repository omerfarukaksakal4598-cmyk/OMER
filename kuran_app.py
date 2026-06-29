import streamlit as st
import requests

st.set_page_config(page_title="📖 Kuran Okuyucu", layout="wide")

# Başlık
st.title("📖 Kuran Okuyucu")
st.write("Kuran'dan istediğiniz Sure ve Ayeti gerçek okuyucu sesleriyle dinleyin.")

# API'den Sure listesini al
@st.cache_data
def get_suras():
    try:
        response = requests.get("https://api.quran.com/api/v4/chapters?language=tr", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if 'chapters' in data:
                return data['chapters']
    except Exception as e:
        st.error(f"API Hatası (Sureler): {e}")
    return []

suras = get_suras()

if not suras:
    st.error("❌ Sureler yüklenemedi.")
    st.stop()

# Sure seçimi
st.subheader("📚 Sure Seç")

sure_names = []
for s in suras:
    sure_id = s.get('id', '?')
    sure_arabic = s.get('name_arabic', '?')
    sure_turkish = s.get('translated_name', {}).get('name', '?')
    name = f"{sure_id}. {sure_arabic} ({sure_turkish})"
    sure_names.append(name)

selected_sure_text = st.selectbox("Sure Seç:", sure_names)
selected_sure_num = int(selected_sure_text.split(".")[0].strip())
selected_sure = next((s for s in suras if s['id'] == selected_sure_num), None)

if not selected_sure:
    st.error("❌ Sure seçilemedi")
    st.stop()

# Seçilen Surenin Bilgileri
sure_name = selected_sure.get('translated_name', {}).get('name', 'N/A')
sure_arabic = selected_sure.get('name_arabic', 'N/A')
verses_count = selected_sure.get('verses_count', 1)

st.info(f"📖 {sure_name} Suresi ({sure_arabic}) — **Toplam Ayet:** {verses_count}")

# Ayet aralığı seç
st.subheader("📍 Ayet Aralığı Seç")
col1, col2 = st.columns(2)

with col1:
    start_verse = st.number_input("Başlangıç Ayeti:", min_value=1, max_value=verses_count, value=1)

with col2:
    end_verse = st.number_input("Bitiş Ayeti:", min_value=1, max_value=verses_count, value=min(5, verses_count))

if start_verse > end_verse:
    st.error("❌ Başlangıç ayeti bitiş ayetinden küçük veya eşit olmalı!")
    st.stop()

# Okuyucu seçimi (Quran.com API Recitation ID'leri)
st.subheader("🎤 Okuyucu Seç")
qari_options = {
    "Mishari Rashid Alafasy": 7,
    "Abdul Basit (Murattal)": 1,
    "Ahmed Al Ajmi": 3,
    "Saad Al Ghamdi": 4,
}
selected_qari_name = st.selectbox("Okuyucu:", list(qari_options.keys()))
selected_qari_id = qari_options[selected_qari_name]

# Surenin tüm ayet metinlerini TEK SEFERDE çek (Hızlı ve optimize)
@st.cache_data
def get_all_verses_uthmani(sure_num):
    try:
        response = requests.get(f"https://api.quran.com/api/v4/quran/verses/uthmani?chapter_number={sure_num}", timeout=10)
        if response.status_code == 200:
            return response.json().get('verses', [])
    except Exception as e:
        st.error(f"Ayet metinleri çekilemedi: {e}")
    return []

# Seçilen ayetin ses dosyasının URL'sini getiren fonksiyon
def get_ayah_audio_url(recitation_id, verse_key):
    try:
        response = requests.get(f"https://api.quran.com/api/v4/recitations/{recitation_id}/by_ayah/{verse_key}", timeout=10)
        if response.status_code == 200:
            audio_files = response.json().get('audio_files', [])
            if audio_files:
                url = audio_files[0].get('url', '')
                # Eğer gelen URL bağıl (relative) ise başına ana domaini ekliyoruz
                if url.startswith('//'):
                    return f"https:{url}"
                elif not url.startswith('http'):
                    return f"https://audio.qurancdn.com/{url}"
                return url
    except:
        pass
    return None

# Metinleri yükle ve seçilen aralığa göre filtrele
all_verses = get_all_verses_uthmani(selected_sure_num)
filtered_verses = all_verses[start_verse - 1 : end_verse]

if not filtered_verses:
    st.error("❌ Ayetler filtrelenemedi veya yüklenemedi.")
    st.stop()

# Ayetleri ve Sesleri Göster
st.subheader("📖 Ayetler ve Sesli Okuma")

for verse in filtered_verses:
    verse_key = verse.get('verse_key', '?:?')
    verse_text = verse.get('text_uthmani', 'N/A')
    verse_num = verse_key.split(':')[1] if ':' in verse_key else '?'
    
    # Ayet başlığı ve metni (Sağa yatık Arapça düzeni için markdown)
    st.markdown(f"**Ayet {verse_num}**")
    st.markdown(f"<div style='text-align: right; direction: rtl; font-size: 28px; font-family: sans-serif; line-height: 1.8; margin-bottom: 10px;'>{verse_text}</div>", unsafe_allow_html=True)
    
    # Her ayetin altına kendi okuyucu sesini yerleştiriyoruz
    with st.spinner(f"Ayet {verse_num} için ses yükleniyor..."):
        audio_url = get_ayah_audio_url(selected_qari_id, verse_key)
        if audio_url:
            st.audio(audio_url, format="audio/mp3")
        else:
            st.warning(f"⚠️ Ayet {verse_num} için ses dosyası bulunamadı.")
    
    st.write("---")

# Alt bilgi
st.divider()
st.write("💡 **Kullanım:** Sure seçin → Ayet aralığı seçin → Okuyucu seçin. Ayetler ve ses oynatıcılar otomatik olarak aşağıda listelenecektir.")
