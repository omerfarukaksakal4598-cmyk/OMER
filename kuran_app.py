import streamlit as st
import requests
import yt_dlp

st.set_page_config(page_title="📖 Kuran Okuyucu", layout="wide")

# Başlık
st.title("📖 Kuran Okuyucu - YouTube")
st.write("YouTube'dan Kuran okuyuşlarını dinleyin")

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
    st.error("❌ Sureler yüklenemedi. Lütfen sayfayı yenileyin.")
    st.stop()

# Sura seç
st.subheader("📚 Sura Seç")

# Sura isimlerini oluştur
try:
    sura_names = []
    for s in suras:
        sura_id = s.get('id', '?')
        sura_arabic = s.get('name_arabic', '?')
        sura_turkish = s.get('translated_name', {}).get('name', '?')
        name = f"{sura_id}. {sura_arabic} ({sura_turkish})"
        sura_names.append(name)
    
    if not sura_names:
        st.error("❌ Sura isimleri işlenemedi")
        st.stop()
        
except Exception as e:
    st.error(f"❌ Sura işleme hatası: {e}")
    st.stop()

# Sura seçimi
selected_sura_text = st.selectbox("Sura Seç:", sura_names)

# Seçilen suranın numarasını al
try:
    selected_sura_num = int(selected_sura_text.split(".")[0].strip())
    selected_sura = next((s for s in suras if s['id'] == selected_sura_num), None)
    
    if not selected_sura:
        st.error("❌ Sura seçilemedi")
        st.stop()
        
except Exception as e:
    st.error(f"❌ Sura seçim hatası: {e}")
    st.stop()

# Seçilen Suranın Bilgileri
sura_name = selected_sura.get('translated_name', {}).get('name', 'N/A')
sura_arabic = selected_sura.get('name_arabic', 'N/A')
st.info(f"📖 {sura_name} Suresi ({sura_arabic})")
st.write(f"**Toplam Ayet:** {selected_sura.get('verses_count', 0)}")

# Okuyucu seçimi
st.subheader("🎤 Okuyucu Seç")

qari_options = {
    "Abdul Basit": "Abdul Basit",
    "Mishari Rashid": "Mishari Rashid",
    "Ahmed Al Ajmi": "Ahmed Al Ajmi",
    "Saad Al Ghamdi": "Saad Al Ghamdi",
}

selected_qari = st.selectbox("Okuyucu:", list(qari_options.keys()))

if st.button("🔍 YouTube'da Ara ve Oynat"):
    with st.spinner("📱 YouTube'da arıyor..."):
        try:
            # YouTube'da ara
            search_query = f"{sura_arabic} {selected_qari}"
            
            st.info(f"🔍 Aranan: {search_query}")
            
            # Google API yerine yt-dlp ile direkt YouTube arama
            search_url = f"https://www.youtube.com/results?search_query={search_query.replace(' ', '+')}"
            
            st.write(f"YouTube linki: {search_url}")
            
            # yt-dlp ile YouTube'dan video ara ve oynat
            ydl_opts = {
                'format': 'bestaudio/best',
                'quiet': False,
                'no_warnings': False,
                'extract_flat': False,
            }
            
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    # Direkt URL yerine, yesearch ile ara
                    search_results = ydl.extract_info(f"ytsearch:{search_query}", download=False)
                    
                    if search_results and 'entries' in search_results and len(search_results['entries']) > 0:
                        first_video = search_results['entries'][0]
                        video_url = f"https://www.youtube.com/watch?v={first_video['id']}"
                        video_title = first_video.get('title', 'Video')
                        
                        st.success(f"✅ Bulundu: {video_title}")
                        st.write(f"**Video:** [{video_title}]({video_url})")
                        
                        # YouTube video embed
                        st.video(video_url)
                        
                    else:
                        st.error("❌ Video bulunamadı. YouTube'da el ile ara:")
                        st.write(f"🔗 {search_url}")
                        
            except Exception as ydl_error:
                st.error(f"❌ Video yüklenemiyor: {str(ydl_error)}")
                st.warning("YouTube'u el ile ziyaret edin:")
                st.write(f"🔗 {search_url}")
            
        except Exception as e:
            st.error(f"❌ Hata: {str(e)}")

# Alt bilgi
st.divider()
st.write("💡 **Kullanım:** Sura seçin → Okuyucu seçin → 'Ara ve Oynat' tuşuna tıklayın")
st.write("📱 **Teknoloji:** Streamlit + Quran API + YouTube")
st.caption("🎵 YouTube'dan profesyonel Kuran okuyuşlarını bulur ve oynatır")
