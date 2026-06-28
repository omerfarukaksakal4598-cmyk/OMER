import streamlit as st
import requests

st.title("📖 Kuran Okuyucu - Debug")

st.write("API'den veri alınıyor...")

try:
    response = requests.get("https://api.quran.com/api/v4/chapters?language=tr", timeout=10)
    st.write(f"**Status Code:** {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        st.write("**API Response Keys:**")
        st.write(list(data.keys()))
        
        if 'chapters' in data:
            st.write(f"**Toplam Sure Sayısı:** {len(data['chapters'])}")
            
            st.write("**İlk Sure Örneği:**")
            if len(data['chapters']) > 0:
                first_chapter = data['chapters'][0]
                st.json(first_chapter)
                
                # Anahtarları listele
                st.write("**Kullanılabilir Anahtarlar:**")
                st.write(list(first_chapter.keys()))
        else:
            st.error("'chapters' anahtarı bulunamadı!")
            st.write("Gelen veri:")
            st.json(data)
    else:
        st.error(f"❌ API Hatası: {response.status_code}")
        
except Exception as e:
    st.error(f"❌ Hata: {e}")

