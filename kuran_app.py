import streamlit as st
import requests
from gtts import gTTS
import tempfile
import os

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

# Sure seç
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
st.info(f"📖 {sure_name} Suresi ({sure_arabic})")
st.write(f"**Toplam Ayet:** {selected_sure.get('verses_count', 0)}")

# Ayet aralığı seç
st.subheader("📍 Ayet Aralığı Seç")

col1, col2 = st.columns(2)

verses_count = selected_sure.get('verses_count', 1)

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
def get_verses(sure_num, start, end):
    verses_data = []
    for verse_num in range(start, end + 1):
        try:
            response = requests.get(
                f"https://api.quran.com/api/v4/quran/verses/uthmani?chapter_number={sure_num}&verse_number={verse_num}",
                timeout=10
            )
            if response.status_code == 200:
                verse_response = response.json()
                if 'verses' in verse_response and len(verse_response['verses']) > 0:
                    verses_data.append(verse_response['verses'][0])
        except:
            continue
    return verses_data

verses = get_verses(selected_sure_num, start_verse, end_verse)

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

# Sesli Okuma - Hepsini Birleştir
st.subheader("🔊 Sesli Okuma")

if st.button("▶️ Tüm Ayetleri Sesli Oku"):
    with st.spinner("🎵 Ses hazırlanıyor..."):
        try:
            # Tüm ayetleri birleştir
            full_text = ""
            for verse in verses:
                verse_key = verse.get('verse_key', '?:?')
                verse_text = verse.get('text_uthmani', '')
                
                if ':' in verse_key:
                    verse_num = verse_key.split(':')[1]
                else:
                    verse_num = '?'
                
                full_text += f"Ayet {verse_num}: {verse_text}. "
            
            if full_text.strip():
                # Google Text-to-Speech ile Arapça ses oluştur
                try:
                    tts = gTTS(text=full_text, lang='ar', slow=False)
                    
                    # Temp dosyaya kaydet
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
                        temp_path = tmp_file.name
                        tts.save(temp_path)
                    
                    # Oynat
                    with open(temp_path, "rb") as audio_file:
                        st.audio(audio_file.read(), format="audio/mp3")
                    
                    st.success(f"✅ {len(verses)} ayet sesli okundu!")
                    
                    # Temp dosyayı sil
                    try:
                        os.remove(temp_path)
                    except:
                        pass
                        
                except Exception as audio_error:
                    st.error(f"❌ Ses oluşturma hatası: {str(audio_error)}")
            else:
                st.error("❌ Okunacak metin yok")
                
        except Exception as e:
            st.error(f"❌ Hata: {str(e)}")

# Alt bilgi
st.divider()
st.write("💡 **Kullanım:** Sure seçin → Ayet aralığı → Okuyucu → 'Tüm Ayetleri Sesli Oku'")
