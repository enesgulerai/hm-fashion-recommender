import os
import time

import requests
import streamlit as st

# --- SETTINGS ---
BASE_URL = os.getenv("BACKEND_URL", "http://localhost:8001")
ENDPOINT = "/recommend"
FULL_API_URL = f"{BASE_URL.rstrip('/')}{ENDPOINT}"

# Page Configuration
st.set_page_config(page_title="H&M AI Fashion Stylist", page_icon="🛍️", layout="wide")

# --- SESSION STATE (Memory Management) ---
if "results" not in st.session_state:
    st.session_state.results = None
if "source" not in st.session_state:
    st.session_state.source = None
if "latency" not in st.session_state:
    st.session_state.latency = None

# --- TITLE & HEADER ---
st.title("🛍️ H&M AI Personal Stylist")
st.markdown(
    "Describe what you're looking for in natural language, and I'll find the perfect outfits in milliseconds. *(Example: A casual red summer dress)*"
)

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Settings")
    top_k = st.slider(
        "How many products to fetch?", min_value=1, max_value=9, value=3, step=3
    )

    st.markdown("---")
    st.markdown("""
    **Architecture Info:**
    * 🧠 **Model:** all-MiniLM-L6-v2
    * 🗄️ **DB:** Qdrant Vector Search
    * ⚡ **Cache:** Redis
    """)

# --- MAIN SEARCH PART (Form) ---
with st.form(key="search_form"):
    col_input, col_btn = st.columns([5, 1])
    with col_input:
        query = st.text_input(
            "What kind of outfit are you looking for?",
            placeholder="Comfortable gym wear...",
            label_visibility="collapsed",
        )
    with col_btn:
        submit_btn = st.form_submit_button("🔎 Find My Style", use_container_width=True)

if submit_btn and query:
    with st.spinner("AI is scanning the wardrobe..."):
        try:
            payload = {"text": query, "top_k": top_k}

            # Real-time latency measurement
            start_time = time.time()
            response = requests.post(FULL_API_URL, json=payload, timeout=10)
            end_time = time.time()

            if response.status_code == 200:
                data = response.json()
                # Save results to session state
                st.session_state.results = data.get("results", [])
                st.session_state.source = data.get("source", "Unknown")
                st.session_state.latency = end_time - start_time
            else:
                st.error(f"❌ API Error: {response.status_code}")
                st.session_state.results = None

        except requests.exceptions.ConnectionError:
            st.error(f"🚨 Connection Error! Cannot reach API: {FULL_API_URL}")
            st.session_state.results = None

# --- DISPLAY RESULTS ---
if st.session_state.results is not None:
    results = st.session_state.results
    source = st.session_state.source
    latency = st.session_state.latency

    if not results:
        st.warning("Sorry, I couldn't find any items matching your description.")
    else:
        st.markdown("---")

        # 1. THE BACKEND SHOW (Performance Metrics)
        m1, m2, m3 = st.columns(3)
        with m1:
            st.metric(label="⏱️ Response Time", value=f"{latency:.3f} sec")
        with m2:
            if source == "redis_cache":
                st.metric(label="⚡ Data Source", value="Redis (Cache)")
            else:
                st.metric(label="🧠 Data Source", value="Qdrant (AI Model)")
        with m3:
            st.metric(label="🛍️ Items Found", value=len(results))

        st.markdown("<br>", unsafe_allow_html=True)

        # 2. THE GRID LAYOUT
        cols_per_row = 3

        for i in range(0, len(results), cols_per_row):
            cols = st.columns(cols_per_row)
            row_items = results[i : i + cols_per_row]

            for col, item in zip(cols, row_items):
                with col:
                    details = item.get("details", {})
                    # Clean cards with container borders
                    with st.container(border=True):
                        st.subheader(item.get("product_name", "Unknown Product"))
                        st.caption(
                            f"{details.get('product_group_name', '-')} | {details.get('product_type_name', '-')}"
                        )

                        st.metric("Match Score", f"{item.get('score', 0)*100:.1f}%")

                        desc = details.get("detail_desc", "No description available.")
                        st.write(
                            f"*{desc[:100]}...*" if len(desc) > 100 else f"*{desc}*"
                        )
