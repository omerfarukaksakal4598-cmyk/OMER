import streamlit as st
import requests
import streamlit.components.v1 as components

st.set_page_config(page_title="📖 Kuran Okuyucu", layout="wide")

# Başlık
st.title("📖 Kuran Okuyucu")
st.write("Kuran'dan istediğiniz Sure ve Ayeti kesintisiz bir şekilde dinleyin.")

# Ayet numaralarını Arapça rakamlara çeviren yardımcı fonksiyon
def to_arabic_number(num):
    arabic_digits = ['٠', '١', '٢', '٣', '٤', '٥', '٦', '٧', '٨', '٩']
    return ''.join(arabic_digits[int(d)] for d in str(num))

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

# Okuyucu seçimi
st.subheader("🎤 Okuyucu Seç")
qari_options = {
    "Mishari Rashid Alafasy": 7,
    "Abdul Basit (Murattal)": 1,
    "Ahmed Al Ajmi": 3,
    "Saad Al Ghamdi": 4,
}
selected_qari_name = st.selectbox("Okuyucu:", list(qari_options.keys()))
selected_qari_id = qari_options[selected_qari_name]

# Metinleri çek
@st.cache_data
def get_all_verses_uthmani(sure_num):
    try:
        response = requests.get(f"https://api.quran.com/api/v4/quran/verses/uthmani?chapter_number={sure_num}", timeout=10)
        if response.status_code == 200:
            return response.json().get('verses', [])
    except Exception as e:
        st.error(f"Ayet metinleri çekilemedi: {e}")
    return []

# Ses URL'sini al
def get_ayah_audio_url(recitation_id, verse_key):
    try:
        response = requests.get(f"https://api.quran.com/api/v4/recitations/{recitation_id}/by_ayah/{verse_key}", timeout=10)
        if response.status_code == 200:
            audio_files = response.json().get('audio_files', [])
            if audio_files:
                url = audio_files[0].get('url', '')
                if url.startswith('//'):
                    return f"https:{url}"
                elif not url.startswith('http'):
                    return f"https://audio.qurancdn.com/{url}"
                return url
    except:
        pass
    return None

all_verses = get_all_verses_uthmani(selected_sure_num)
filtered_verses = all_verses[start_verse - 1 : end_verse]

if not filtered_verses:
    st.error("❌ Ayetler filtrelenemedi veya yüklenemedi.")
    st.stop()

st.divider()

# 1. BÖLÜM: SES LİSTESİNİ HAZIRLA VE TEK OYNATICIYI OLUŞTUR
audio_urls = []
combined_arabic_text = ""

with st.spinner("Metinler ve ses bağlantıları hazırlanıyor... Lütfen bekleyin."):
    for verse in filtered_verses:
        verse_key = verse.get('verse_key', '?:?')
        verse_text = verse.get('text_uthmani', '')
        verse_num = verse_key.split(':')[1] if ':' in verse_key else '?'
        
        # Arapça rakamlarla ayet sonu süsünü ekle ﴿١﴾
        arabic_num_symbol = f" ﴿{to_arabic_number(verse_num)}﴾ "
        combined_arabic_text += verse_text + arabic_num_symbol
        
        # Ses linkini al
        url = get_ayah_audio_url(selected_qari_id, verse_key)
        if url:
            audio_urls.append(url)

if audio_urls:
    # Kesintisiz çalma özelliği için HTML/JavaScript kod bloğu
    js_audio_list = str(audio_urls) # Python listesini JavaScript formatına uygun string'e çevirir
    
    html_player = f"""
    <div style="background-color: #1e1e1e; padding: 15px; border-radius: 10px; margin-bottom: 20px; text-align: center; border: 1px solid #333;">
        <h3 style="color: white; margin-top: 0; font-family: sans-serif;">🔊 Kesintisiz Oynatıcı</h3>
        <audio id="quranPlayer" controls style="width: 100%; outline: none;">
            <source src="{audio_urls[0]}" type="audio/mpeg">
            Tarayıcınız ses oynatıcıyı desteklemiyor.
        </audio>
        <div style="color: #bbb; margin-top: 10px; font-family: sans-serif; font-size: 14px;">
            Şu an oynatılan ayet sırası: <span id="currentCount" style="color: #4CAF50; font-weight: bold; font-size: 16px;">1</span> / {len(audio_urls)}
        </div>
    </div>

    <script>
        var urls = {js_audio_list};
        var currentIndex = 0;
        var player = document.getElementById("quranPlayer");
        var counter = document.getElementById("currentCount");

        player.addEventListener('ended', function() {{
            currentIndex++;
            if (currentIndex < urls.length) {{
                player.src = urls[currentIndex];
                player.play();
                counter.innerText = currentIndex + 1;
            }} else {{
                // Tüm ayetler bitince başa dön ama dur
                currentIndex = 0;
                player.src = urls[0];
                counter.innerText = 1;
            }}
        }});
    </script>
    """
    # HTML oynatıcıyı ekrana bas
    components.html(html_player, height=150)
else:
    st.warning("⚠️ Bu aralık için ses bağlantıları bulunamadı.")

# 2. BÖLÜM: BÜTÜNLEŞİK ARAPÇA METNİ GÖSTER
st.markdown("<h3 style='text-align: right; color: gray;'>📖 Okunuş</h3>", unsafe_allow_html=True)

# Tek parça, Mushaf düzeninde (sağa yatık, büyük fontlu) metin
st.markdown(
    f"<div style='text-align: justify; text-justify: inter-word; direction: rtl; font-size: 32px; font-family: Arial, sans-serif; line-height: 2.2; padding: 20px; background-color: rgba(0,0,0,0.05); border-radius: 10px;'>{combined_arabic_text}</div>", 
    unsafe_allow_html=True
)

st.divider()
st.write("💡 **Kullanım:** Oynatıcıdan 'Play' tuşuna bastığınızda seçtiğiniz aralıktaki tüm ayetler sırasıyla otomatik çalacaktır.")
