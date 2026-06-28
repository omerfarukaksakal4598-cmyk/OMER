import streamlit as st
import requests
from gtts import gTTS
import os
import tempfile

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
    st.error("❌ Sureler yüklenemedi. Lütfen sayfayı yenileyin.")
    st.stop()

# Sura seç
st.subheader("📚 Sura Seç")

# Sura isimlerini oluştur - DÜZELTILMIŞ
try:
    sura_names = []
    for s in suras:
        # Doğru anahtarları kullan
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
        
        # Oku butonu
        if st.button("🔊 Ayetleri Sesli Oku"):
            with st.spinner("⏳ Hazırlanıyor..."):
                try:
                    # Ayetleri birleştir
                    full_text = ""
                    for verse in verses:
                        verse_num = verse.get('verse_number', '?')
                        verse_text = verse.get('text_uthmani', '')
                        full_text += f"Ayet {verse_num}: {verse_text}. "
                    
                    if not full_text.strip():
                        st.error("❌ Okunacak metin yok")
                    else:
                        # Google Text-to-Speech ile ses oluştur
                        try:
                            tts = gTTS(text=full_text, lang='ar', slow=False)
                            
                            # Temp dosya oluştur
                            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
                                temp_path = tmp_file.name
                                tts.save(temp_path)
                            
                            # Sesli okumayı oynat
                            with open(temp_path, "rb") as audio_file:
                                st.audio(audio_file.read(), format="audio/mp3")
                            
                            st.success("✅ Başarıyla okundu!")
                            
                            # Temp dosyayı sil
                            try:
                                os.remove(temp_path)
                            except:
                                pass
                            
                        except Exception as audio_error:
                            st.error(f"❌ Ses oluşturma hatası: {str(audio_error)}")
                            st.info("💡 Lütfen daha az ayet seçin ve tekrar deneyin")
                        
                except Exception as e:
                    st.error(f"❌ Beklenmedik hata: {str(e)}")
    else:
        st.warning("⚠️ Ayetler yüklenemedi. Lütfen tekrar deneyin.")

# Alt bilgi
st.divider()
st.write("💡 **Kullanım:** Sura seçin → Ayet aralığı girin → 'Sesli Oku' butonuna tıklayın")
st.write("📱 **Teknoloji:** Streamlit + Quran API + Google Text-to-Speech")
st.caption("📖 Kuran'ın metin ve çevirisi quran.com API'sinden alınmaktadır")
