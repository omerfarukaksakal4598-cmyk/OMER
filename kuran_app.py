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
        response = requests.get("https://api.quran.com/api/v4/chapters?language=tr")
        if response.status_code == 200:
            return response.json()['chapters']
    except:
        pass
    return []

# Sura seç
st.subheader("📚 Sura Seç")
suras = get_suras()

if suras:
    sura_names = [f"{s['number']}. {s['name_arabic']} ({s['name']})" for s in suras]
    selected_sura_text = st.selectbox("Sura Seç:", sura_names)
    
    # Seçilen suranın numarasını al
    selected_sura_num = int(selected_sura_text.split(".")[0])
    selected_sura = next((s for s in suras if s['number'] == selected_sura_num), None)
    
    if selected_sura:
        st.info(f"📖 {selected_sura['name']} Suresi ({selected_sura['name_arabic']})")
        st.write(f"**Toplam Ayet:** {selected_sura['verses_count']}")
        
        # Ayet aralığı seç
        st.subheader("📍 Ayet Seç")
        
        col1, col2 = st.columns(2)
        
        with col1:
            start_verse = st.number_input(
                "Başlangıç Ayeti:",
                min_value=1,
                max_value=selected_sura['verses_count'],
                value=1
            )
        
        with col2:
            end_verse = st.number_input(
                "Bitiş Ayeti:",
                min_value=1,
                max_value=selected_sura['verses_count'],
                value=min(5, selected_sura['verses_count'])
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
                        response = requests.get(
                            f"https://api.quran.com/api/v4/quran/verses/uthmani?chapter_number={sura_num}&verse_number={verse_num}"
                        )
                        if response.status_code == 200:
                            verse_data = response.json()['verses'][0]
                            verses_data.append(verse_data)
                    return verses_data
                except Exception as e:
                    st.error(f"Hata: {e}")
                    return []
            
            verses = get_verses(selected_sura_num, start_verse, end_verse)
            
            if verses:
                st.subheader("📖 Ayetler")
                
                # Ayetleri göster
                for verse in verses:
                    st.write(f"**Ayet {verse['verse_number']}:**")
                    st.write(f"### {verse['text_uthmani']}")
                    st.divider()
                
                # Oku butonu
                if st.button("🔊 Ayetleri Sesli Oku"):
                    with st.spinner("⏳ Hazırlanıyor..."):
                        try:
                            # Ayetleri birleştir
                            full_text = ""
                            for verse in verses:
                                full_text += f"Ayet {verse['verse_number']}: "
                                full_text += verse['text_uthmani'] + ". "
                            
                            # Google Text-to-Speech ile ses oluştur
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
                            os.remove(temp_path)
                            
                        except Exception as e:
                            st.error(f"❌ Ses oluşturma hatası: {str(e)}")
                            st.info("💡 Lütfen tekrar deneyin veya daha az ayet seçin")
            else:
                st.error("❌ Ayetler yüklenemedi")
else:
    st.error("❌ Sureler yüklenemedi. İnternet bağlantınızı kontrol edin.")

# Alt bilgi
st.divider()
st.write("💡 **Kullanım:** Sura seçin → Ayet aralığı girin → 'Sesli Oku' butonuna tıklayın")
st.write("📱 **Teknoloji:** Streamlit + Quran API + Google Text-to-Speech")
st.caption("📖 Kuran'ın metin ve çevirisi quran.com API'sinden alınmaktadır")
