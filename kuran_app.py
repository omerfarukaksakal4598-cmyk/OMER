import streamlit as st
import requests
import yt_dlp
import google.generativeai as genai

st.set_page_config(page_title="📖 Kuran Okuyucu AI", layout="wide")

# Google Gemini API Key - ENTEGRE EDİLMİŞ
GOOGLE_API_KEY = "AQ.Ab8RN6IUHeBgmmGxCD20VueZySfB8nCIVSnYsw16y5b6xWaLnA"

try:
    genai.configure(api_key=GOOGLE_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error(f"❌ Google API Hatası: {e}")
    st.stop()

# Başlık
st.title("📖 Kuran Okuyucu - AI Analiz")
st.write("Sureyi seçin, AI YouTube'dan bulsun ve analiz yapsın!")

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
st.subheader("📚 Sura Seç")

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
    st.error("❌ Sura seçilemedi")
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
    "Abdul Basit": "Abdul Basit",
    "Mishari Rashid": "Mishari Rashid",
    "Ahmed Al Ajmi": "Ahmed Al Ajmi",
    "Saad Al Ghamdi": "Saad Al Ghamdi",
}

selected_qari = st.selectbox("Okuyucu:", list(qari_options.keys()))

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

# Ayetleri metin olarak hazırla
verses_text = ""
for verse in verses:
    verse_key = verse.get('verse_key', '?:?')
    verse_text = verse.get('text_uthmani', 'N/A')
    
    if ':' in verse_key:
        verse_num = verse_key.split(':')[1]
    else:
        verse_num = '?'
    
    verses_text += f"Ayet {verse_num}: {verse_text}\n"

# AI Analiz Butonu
if st.button("🤖 AI ile Analiz Et"):
    with st.spinner("🧠 Google Gemini analiz ediyor..."):
        try:
            # YouTube'da video ara
            search_query = f"{sura_arabic} {start_verse}:{end_verse} {selected_qari}"
            
            st.info(f"📱 YouTube'da aranan: {search_query}")
            
            video_info = ""
            try:
                ydl_opts = {
                    'format': 'bestaudio/best',
                    'quiet': True,
                    'no_warnings': True,
                    'extract_flat': False,
                }
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    search_results = ydl.extract_info(f"ytsearch:{search_query}", download=False)
                    
                    if search_results and 'entries' in search_results and len(search_results['entries']) > 0:
                        first_video = search_results['entries'][0]
                        video_title = first_video.get('title', 'Video')
                        video_desc = first_video.get('description', '')[:500]
                        video_duration = first_video.get('duration', 0)
                        
                        video_info = f"""
VIDEO BİLGİSİ:
Başlık: {video_title}
Süresi: {video_duration // 60} dakika
Açıklaması: {video_desc}
"""
                        st.success(f"✅ Bulundu: {video_title}")
            except:
                st.warning("⚠️ YouTube video bulunamadı ama analiz yapılacak")
            
            # AI ile analiz et
            st.subheader("🤖 Google Gemini Analizi")
            
            prompt = f"""
Kuran'ın {sura_arabic} Suresi, {start_verse}. ayetten {end_verse}. ayete kadarki bölümü hakkında detaylı analiz yap.

AYETLER:
{verses_text}

{video_info}

Lütfen Türkçe ve detaylı bir analiz yap:

1. **Ayet Anlamı**: Bu ayet aralığının Kuran'daki yeri ve anlamı nedir?

2. **Temel Mesaj**: Surenin bu bölümünün temel konusu ve mesajı ne?

3. **İçeriği**: Ayetlerde anlatılan başlıca temalar nelerdir?

4. **Okuyuş Kalitesi**: {selected_qari}'nin bu okuyuşu nasıl değerlendirirsin?

5. **Günümüze Uygulanabilirlik**: Bu ayetler günümüzde nasıl uygulanabilir?

6. **Tarihsel Bağlam**: Bu ayetlerin indiği dönem hakkında ne söyleyebilirsin?

Detaylı, akademik ve anlaşılır bir şekilde yanıt ver.
"""
            
            try:
                response = model.generate_content(prompt)
                ai_response = response.text
                
                st.write(ai_response)
                
            except Exception as ai_error:
                st.error(f"❌ AI Hatası: {str(ai_error)}")
                st.info("💡 Lütfen tekrar deneyin")
        
        except Exception as e:
            st.error(f"❌ Hata: {str(e)}")

# Ayet Metni Bölümü
st.subheader("📖 Ayet Metni")

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

# Alt bilgi
st.divider()
st.write(" **Kullanım:** Sure seçin → Ayet aralığı → Okuyucu → 'AI ile Analiz Et'")
