import streamlit as st
import requests

st.set_page_config(page_title="📖 Kuran Okuyucu", layout="wide")

# Başlık
st.title("📖 Kuran Okuyucu")
st.write("Kuran'dan istediğiniz Sure ve Ayeti dinleyin")

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
st.subheader("📚 Sure Seç")

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

# Ayet aralığı seç
st.subheader("📍 Ayet Seç")

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
else:
    # Ayetleri al
    @st.cache_data
    def get_verses(sura_num, start, end):
        try:
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
        except Exception as e:
            st.error(f"Hata: {e}")
            return []
    
    verses = get_verses(selected_sura_num, start_verse, end_verse)
    
    if verses:
        st.subheader("📖 Ayetler")
        
        # Ayetleri göster
        for verse in verses:
            verse_num = verse.get('verse_number', '?')
            verse_text = verse.get('text_uthmani', 'N/A')
            st.write(f"**Ayet {verse_num}:**")
            st.write(f"### {verse_text}")
            st.divider()
        
        # Dinle butonu
        st.subheader("🔊 Dinleyin")
        
        # Qari (Okuyucu) seçimi - Alquran.cloud Okuyucuları
        qari_options = {
            "Abdul Basit": "abdulbasit",
            "Mishari Rashid": "mishari",
            "Ahmed Al Ajmi": "ajmi",
            "Saad Al Ghamdi": "ghamdi",
        }
        
        selected_qari = st.selectbox("Okuyucu Seç:", list(qari_options.keys()))
        qari_code = qari_options[selected_qari]
        
        if st.button("▶️ Ayetleri Dinle"):
            with st.spinner("⏳ Ses dosyaları yükleniyor..."):
                try:
                    audio_count = 0
                    
                    for verse in verses:
                        verse_num = verse.get('verse_number', '?')
                        
                        try:
                            # Alquran.cloud direct audio URL
                            audio_url = f"https://cdn.alquran.cloud/media/audio/{qari_code}/{selected_sura_num}/{verse_num}.mp3"
                            
                            # URL'nin çalışıp çalışmadığını kontrol et
                            head_response = requests.head(audio_url, timeout=5)
                            
                            if head_response.status_code == 200:
                                st.write(f"**Ayet {verse_num}:**")
                                st.audio(audio_url, format="audio/mp3")
                                audio_count += 1
                            else:
                                st.warning(f"❌ Ayet {verse_num} bulunamadı")
                                
                        except Exception as e:
                            st.warning(f"⚠️ Ayet {verse_num} yüklenemedi: {str(e)}")
                    
                    if audio_count > 0:
                        st.success(f"✅ {audio_count} ayet başarıyla yüklendi!")
                    else:
                        st.error("❌ Hiçbir ses dosyası yüklenemedi")
                        st.info("💡 Lütfen başka bir okuyucu seçmeyi deneyin")
                        
                except Exception as e:
                    st.error(f"❌ Ses yükleme hatası: {str(e)}")
                    st.info("💡 Lütfen interneti kontrol edip tekrar deneyin")
    else:
        st.warning("⚠️ Ayetler yüklenemedi. Lütfen tekrar deneyin.")

# Alt bilgi
st.divider()
st.write("💡 **Kullanım:** Sura seçin → Ayet aralığı girin → Okuyucu seçin → 'Dinle' tuşuna tıklayın")
st.write("📱 **Teknoloji:** Streamlit + Quran API + Alquran.cloud Audio")
st.caption("📖 Kuran'ın metin, çeviri ve sesi quran.com ve alquran.cloud API'lerinden alınmaktadır")
