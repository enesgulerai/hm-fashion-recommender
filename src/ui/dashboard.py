import streamlit as st
import requests
import os

# --- SETTINGS ---
BASE_URL = os.getenv("BACKEND_URL", "http://localhost:8001")

ENDPOINT = "/recommend"

FULL_API_URL = f"{BASE_URL.rstrip('/')}{ENDPOINT}"

print(f"DEBUG: Gidilecek Adres -> {FULL_API_URL}")

# Page Configuration
st.set_page_config(
    page_title="H&M AI Fashion Stylist",
    page_icon="🛍️",
    layout="wide"
)

# --- DEBUGGING (Bunu hatayı çözmek için ekledik, sonra silebilirsin) ---
st.write(f"🔌 **Connected to:** `{FULL_API_URL}`")

# --- TITLE & HEADER ---
st.title("🛍️ H&M AI Personal Stylist")
st.markdown("""
**Welcome!** I'm your AI-powered style consultant. 
Describe what you're looking for in natural language, and I'll find the perfect outfit for you.
*(Example: 'I need a red dress for a wedding' or 'Sportswear for the gym')*
""")

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Settings")
    top_k = st.slider("How many products should be brought?", min_value=1, max_value=10, value=3)
    st.info("This system uses **Semantic Search**. It looks at the MEANING of words, not just their letters.")

# --- MAIN SEARCH PART ---
query = st.text_input("What kind of outfit are you looking for?", placeholder="Summer floral dress...")
search_btn = st.button("🔎 Find My Style")

if search_btn and query:
    with st.spinner('Artificial intelligence scans the wardrobe...'):
        try:
            # Send Request to Backend
            payload = {"text": query, "top_k": top_k}

            # DÜZELTME BURADA: API_URL yerine FULL_API_URL kullanıyoruz
            response = requests.post(FULL_API_URL, json=payload, timeout=10)

            if response.status_code == 200:
                data = response.json()
                results = data.get("results", [])
                source = data.get("source", "Unknown")  # Kaynak bilgisi (Redis/DB)

                if not results:
                    st.warning("Sorry, I couldn't find anything suitable for this.")
                else:
                    # Kaynak bilgisini gösterelim
                    if source == "redis_cache":
                        st.success(f"⚡ Found {len(results)} items (Loaded from Cache 🚀)!")
                    else:
                        st.success(f"🐢 Found {len(results)} items (Processed by AI Model 🧠)!")

                    # List Results
                    for item in results:
                        with st.container():
                            col1, col2 = st.columns([1, 4])

                            # Detayları güvenli çekelim (Hata almamak için .get kullanıyoruz)
                            details = item.get('details', {})

                            with col1:
                                st.markdown("# 👗")
                                st.metric(label="Match Score", value=f"{item.get('score', 0):.4f}")

                            with col2:
                                st.subheader(item.get('product_name', 'Unknown Product'))
                                st.caption(
                                    f"Category: {details.get('product_group_name', '-')} | Type: {details.get('product_type_name', '-')}")
                                st.write(f"**Description:** {details.get('detail_desc', 'No description available.')}")
                                st.markdown("---")

            else:
                st.error(f"❌ An error occurred! API Code: {response.status_code}")
                st.error(f"Server Message: {response.text}")

        except requests.exceptions.ConnectionError:
            st.error(f"🚨 Connection Error! Could not reach: {FULL_API_URL}")
            st.info("Check if Docker container 'hm_api' is running.")