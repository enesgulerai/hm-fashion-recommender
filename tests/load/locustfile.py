import random

from locust import HttpUser, between, task

SEARCH_TERMS = [
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
    "vintage sunglasses",
    "casual sneakers",
]


class FashionUser(HttpUser):
    wait_time = between(1, 3)

    @task
    def predict_fashion(self):
        term = random.choice(SEARCH_TERMS)

        with self.client.post(
            "/recommend", json={"text": term, "top_k": 5}, catch_response=True
        ) as response:

            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Hata kodu: {response.status_code}")
