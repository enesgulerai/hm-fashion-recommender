import os
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import PointStruct

# --- SETTINGS ---
LOCAL_HOST = "localhost"
LOCAL_PORT = 6333
COLLECTION_NAME = "hm_items"
BATCH_SIZE = 500

CLOUD_URL = "YOUR_URL_HERE"
CLOUD_API_KEY = "YOUR_API_KEY_HERE"


def migrate():
    print("--- Migration Started ---")

    try:
        local_client = QdrantClient(host=LOCAL_HOST, port=LOCAL_PORT)
        cloud_client = QdrantClient(
            url=CLOUD_URL.strip(), api_key=CLOUD_API_KEY.strip(), timeout=60
        )
        cloud_client.get_collections()
        print("✅ Cloud connection successful!")
    except Exception as e:
        print(f"❌ Connection Error: {e}")
        return

    print(f"Reading points from local '{COLLECTION_NAME}'...")
    points, _ = local_client.scroll(
        collection_name=COLLECTION_NAME, limit=10000, with_vectors=True
    )

    if not points:
        print("No data was found locally!")
        return

    points_to_upsert = [
        PointStruct(id=p.id, vector=p.vector, payload=p.payload) for p in points
    ]

    print("Configuring cloud collection...")
    local_info = local_client.get_collection(COLLECTION_NAME)

    if cloud_client.collection_exists(COLLECTION_NAME):
        cloud_client.delete_collection(COLLECTION_NAME)

    cloud_client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=models.VectorParams(
            size=local_info.config.params.vectors.size,
            distance=local_info.config.params.vectors.distance,
        ),
    )

    total_points = len(points_to_upsert)
    print(f"Uploading {total_points} points in batches of {BATCH_SIZE}...")

    for i in range(0, total_points, BATCH_SIZE):
        batch = points_to_upsert[i : i + BATCH_SIZE]
        cloud_client.upsert(collection_name=COLLECTION_NAME, points=batch)
        print(
            f"  > Progress: {min(i + BATCH_SIZE, total_points)} / {total_points} uploaded"
        )

    print("\n🚀 SUCCESS: Your data is officially in the cloud!")


if __name__ == "__main__":
    migrate()
