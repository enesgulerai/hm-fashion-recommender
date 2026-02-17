import random
import time

import requests

# API Address
url = "http://localhost:8001/recommend"

# Word pool for generating random data.
colors = ["red", "blue", "black", "white", "green", "yellow", "purple"]
items = ["dress", "jeans", "t-shirt", "jacket", "shoes", "skirt", "coat"]
occasions = ["summer", "winter", "party", "casual", "office", "wedding"]

print("Traffic simulation is starting... (50 Requests)")

for i in range(50):
    # Generate a random query: Example: "Red summer dress"
    text = f"{random.choice(colors)} {random.choice(occasions)} {random.choice(items)}"
    top_k = random.randint(1, 10)

    payload = {"text": text, "top_k": top_k}

    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            print(f"Request {i+1}/50: '{text}' sent.")
        else:
            print(f"Error: {response.status_code}")
    except Exception as e:
        print(f"Connection Error: {e}")

    time.sleep(random.uniform(0.1, 0.5))

print("Simulation finished! Refresh the dashboard..")
