import streamlit as st
import requests
import pyttsx3
import os

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
                            verses_data.append(response.json()['verses'][0])
                    return verses_data
                except:
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
                if st.button("🔊 Ayetleri Oku (Sesli)"):
                    st.info("⏳ Hazırlanıyor...")
                    
                    try:
                        # Text-to-speech engine
                        engine = pyttsx3.init()
                        engine.setProperty('rate', 150)  # Hız
                        
                        # Ayetleri birleştir
                        full_text = ""
                        for verse in verses:
                            full_text += f"Ayet {verse['verse_number']}: "
                            full_text += verse['text_uthmani'] + "\n"
                        
                        # Dosya adı
                        audio_file = "kuran_oku.mp3"
                        
                        # Sesi kaydet
                        engine.save_to_file(full_text, audio_file)
                        engine.runAndWait()
                        
                        # Oynat
                        if os.path.exists(audio_file):
                            with open(audio_file, "rb") as f:
                                st.audio(f.read(), format="audio/mp3")
                            st.success("✅ Başarıyla okundu!")
                            os.remove(audio_file)
                    except Exception as e:
                        st.error(f"❌ Ses çalma hatası: {e}")
                        st.info("💡 Google Translate sesini kullan:")
                        
                        # Alternatif: Google Translate API
                        try:
                            from google.cloud import texttospeech
                            st.write("Google Cloud Text-to-Speech kurulmalı")
                        except:
                            st.write("Alternatif olarak çevrimiçi okuyucu kullanabilirsiniz")
            else:
                st.error("❌ Ayetler yüklenemedi")
else:
    st.error("❌ Sureler yüklenemedi")

# Alt bilgi
st.divider()
st.write("💡 **Kullanım:** Sura seçin → Ayet aralığı girin → 'Oku' butonuna tıklayın")
st.write("📱 **Teknoloji:** Streamlit + Quran API + Python TTS")
