import random
import sys
import time

import requests

URL = "http://localhost:8001/recommend"

search_terms = [
    "black dress",
    "blue jeans",
    "summer t-shirt",
    "leather jacket",
    "running shoes",
    "white hoodie",
    "floral skirt",
    "denim shorts",
    "winter coat",
    "red scarf",
    "gym wear",
    "office shirt",
    "silk pajamas",
]


def send_traffic():
    print("🚀 Traffic Generator Started!")
    counter = 0

    while True:
        try:
            query = random.choice(search_terms)
            k = random.randint(3, 10)

            payload = {"text": query, "top_k": k}

            start_time = time.time()
            response = requests.post(URL, json=payload)
            latency = (time.time() - start_time) * 1000

            if response.status_code == 200:
                source = response.json().get("source", "unknown")
                print(f"[{counter}] ✅ '{query}' ({latency:.1f}ms) -> {source}")
            else:
                print(f"[{counter}] ❌ Status: {response.status_code}")

            counter += 1
            time.sleep(random.uniform(0.1, 1.0))

        except Exception as e:
            print(f"⚠️ Connection Error: {e}")
            time.sleep(2)


if __name__ == "__main__":
    send_traffic()
