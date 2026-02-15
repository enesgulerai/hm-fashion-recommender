import random
import time

import requests

# API Adresi
url = "http://localhost:8001/recommend"

# Rastgele veri üretmek için kelime havuzu
colors = ["red", "blue", "black", "white", "green", "yellow", "purple"]
items = ["dress", "jeans", "t-shirt", "jacket", "shoes", "skirt", "coat"]
occasions = ["summer", "winter", "party", "casual", "office", "wedding"]

print("🚀 Trafik simülasyonu başlıyor... (50 İstek)")

for i in range(50):
    # Rastgele bir sorgu oluştur: Örn: "Red summer dress"
    text = f"{random.choice(colors)} {random.choice(occasions)} {random.choice(items)}"
    top_k = random.randint(1, 10)

    payload = {"text": text, "top_k": top_k}

    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            print(f"✅ İstek {i+1}/50: '{text}' gönderildi.")
        else:
            print(f"❌ Hata: {response.status_code}")
    except Exception as e:
        print(f"Bağlantı hatası: {e}")

    # Gerçekçi olsun diye araya minik beklemeler koyalım
    time.sleep(random.uniform(0.1, 0.5))

print("🏁 Simülasyon bitti! Dashboard'u yenile.")
