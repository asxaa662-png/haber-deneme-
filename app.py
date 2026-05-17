import streamlit as st
import requests
from bs4 import BeautifulSoup
import edge_tts
import google.generativeai as genai
import asyncio
import os

# --- API VE MODEL AYARI ---
# API anahtarı Streamlit Secrets üzerinden okunacak şekilde ayarlandı
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Haberden Podcaste", page_icon="🎙️", layout="centered")
st.title("🎙️ Haberden Podcast Üretici")
st.write("Link yapıştırın, kendi podcast'inizi dinleyin!")

# --- YARDIMCI FONKSİYONLAR ---
def haber_metni_cek(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            return None
        
        soup = BeautifulSoup(response.text, 'html.parser')
        paragraflar = soup.find_all('p')
        haber_metni = " ".join([p.text.strip() for p in paragraflar if len(p.text.strip()) > 40])
        return haber_metni if len(haber_metni) > 100 else None
    except:
        return None

def senaryo_uret(haber_metni, format_secimi):
    model = genai.GenerativeModel("gemini-1.5-flash-latest")
    
    if format_secimi == "Tek Sunucu":
        prompt = f"Aşağıdaki haberi, samimi bir dille aktaran tek kişilik bir podcast konuşmasına çevir. Sadece metni döndür:\n\n{haber_metni}"
    else:
        prompt = f"Aşağıdaki haberi, Emel ve Ahmet isimli iki sunucunun karşılıklı konuştuğu bir diyaloga çevir. Şu formatta yaz:\nEmel: (konuşma)\nAhmet: (konuşma)\n\nHaber:\n{haber_metni}"
        
    response = model.generate_content(prompt)
    return response.text

async def seslendir_tek_sunucu(metin, dosya_adi="podcast.mp3"):
    communicate = edge_tts.Communicate(metin, "tr-TR-AhmetNeural")
    await communicate.save(dosya_adi)

async def seslendir_cift_sunucu(senaryo, dosya_adi="podcast.mp3"):
    lines = senaryo.strip().split("\n")
    with open(dosya_adi, "wb") as master_file:
        for line in lines:
            if line.startswith("Emel:"):
                c = edge_tts.Communicate(line.replace("Emel:", ""), "tr-TR-EmelNeural")
            elif line.startswith("Ahmet:"):
                c = edge_tts.Communicate(line.replace("Ahmet:", ""), "tr-TR-AhmetNeural")
            else: continue
            async for chunk in c.stream():
                if chunk["type"] == "audio": master_file.write(chunk["data"])

# --- ARAYÜZ ---
url_input = st.text_input("Haber URL'sini yapıştırın:")
format_secimi = st.selectbox("Format:", ["Tek Sunucu", "Çift Sunucu"])

if st.button("🎙️ Podcast Oluştur"):
    if url_input:
        with st.spinner("İşleniyor..."):
            haber = haber_metni_cek(url_input)
            if haber:
                senaryo = senaryo_uret(haber, format_secimi)
                cikis = "gunun_podcasti.mp3"
                if format_secimi == "Tek Sunucu":
                    asyncio.run(seslendir_tek_sunucu(senaryo, cikis))
                else:
                    asyncio.run(seslendir_cift_sunucu(senaryo, cikis))
                
                st.success("Hazır!")
                st.audio(cikis)
            else:
                st.error("Haber çekilemedi.")
    else:
        st.warning("Link girin.")
