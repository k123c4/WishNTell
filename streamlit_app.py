import streamlit as st
import requests
from datetime import datetime

WEBHOOK_URL = "https://k123c4.app.n8n.cloud/webhook/streamlit-chat"

st.set_page_config(page_title="My Wishlist", page_icon="📝")

# 🧠 2) Keep wishlist items in session_state so they persist while the app is running
if "wishlist" not in st.session_state:
    st.session_state["wishlist"] = []  # list of dicts: {url, title, note, added_at}

st.title("📝 My Visual Wishlist")

st.write("Add items by URL and send them to n8n as you go.")

# --- 3) Input form for new wishlist item ---
with st.form("add_wishlist_item"):
    st.subheader("Add a new item")

    url = st.text_input("Item URL", placeholder="https://example.com/product/123")
    title = st.text_input("Item name (optional)")
    note = st.text_area("Notes (optional)")
    submitted = st.form_submit_button("➕ Add to wishlist & send to n8n")

    if submitted:
        # Basic validation
        if not url:
            st.error("URL is required.")
        elif not (url.startswith("http://") or url.startswith("https://")):
            st.error("Please enter a valid URL starting with http:// or https://")
        else:
            item = {
                "url": url,
                "title": title.strip() or None,
                "note": note.strip() or None,
                "added_at": datetime.utcnow().isoformat() + "Z",
            }

            # 4) Save in Streamlit session so it shows up visually
            st.session_state["wishlist"].append(item)

            # 5) Send to n8n webhook
            payload = {
                "event": "wishlist_item_added",
                "source": "streamlit",
                "item": item,
            }

            try:
                resp = requests.post(WEBHOOK_URL, json=payload, timeout=10)
                resp.raise_for_status()
                st.success("Item added and sent to n8n ✅")
                st.json(resp.json())  # shows what n8n responded with (optional)
            except requests.exceptions.RequestException as e:
                st.error(f"Error sending to n8n: {e}")
                # still keep it in the local wishlist UI


# --- 6) Visual Wishlist Display ---

st.subheader("📋 Current Wishlist")

if not st.session_state["wishlist"]:
    st.info("No items yet. Add something above!")
else:
    # Nice card-style display for each item
    for idx, item in enumerate(st.session_state["wishlist"], start=1):
        st.markdown("---")
        col1, col2 = st.columns([4, 1])

        with col1:
            title = item["title"] or f"Item {idx}"
            st.markdown(f"**{title}**")
            st.markdown(f"[Open link]({item['url']})")

            if item["note"]:
                st.write(f"📝 {item['note']}")

            if item["added_at"]:
                st.caption(f"Added at: {item['added_at']}")

        with col2:
            st.write("")  # spacing
            st.write("")  # spacing
            # later you could add a "Remove" button here if you want
            # if st.button("Remove", key=f"remove_{idx}"): ...
            st.code("URL\n" + item["url"], language="text")

