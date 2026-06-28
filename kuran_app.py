import streamlit as st
import requests

st.title("🔍 Debug - Ayet Yapısı")

# İlk ayeti al ve göster
st.write("Fatiha Suresi, Ayet 1'i alıyor...")

try:
    response = requests.get(
        "https://api.quran.com/api/v4/quran/verses/uthmani?chapter_number=1&verse_number=1",
        timeout=10
    )
    
    st.write(f"**Status Code:** {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        
        st.write("**API Response Keys:**")
        st.write(list(data.keys()))
        
        if 'verses' in data:
            st.write(f"**Verses sayısı:** {len(data['verses'])}")
            
            if len(data['verses']) > 0:
                verse = data['verses'][0]
                
                st.write("**Verse Objesi:**")
                st.json(verse)
                
                st.write("**Verse Keys (Anahtarlar):**")
                st.write(list(verse.keys()))
        else:
            st.error("'verses' key bulunamadı!")
            st.json(data)
    else:
        st.error(f"API Error: {response.status_code}")
        
except Exception as e:
    st.error(f"Hata: {e}")
