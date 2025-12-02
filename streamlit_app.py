import streamlit as st
import requests
from datetime import datetime
import pandas as pd 

WEBHOOK_URL = "https://k123c4.app.n8n.cloud/webhook/streamlit-chat"

CSV_URL = "https://www.google.com/url?q=https://docs.google.com/spreadsheets/d/e/2PACX-1vRs5rxWD1MRUbwNPmXkM0Dn6OSAuvpI865UZ0jBG-acmEjzlq5DXuxR8HnoANv1eJcJmpG3y1Q7D_Ab/pub?output%3Dcsv&sa=D&source=docs&ust=1764717778302365&usg=AOvVaw0YRUX8-og2gM20vB5XlqWq"

DEBUG_SHOW_WEBHOOK_RESPONSE = False

# ⚙️ Page config
st.set_page_config(
    page_title="My Wishlist",
    page_icon="📝",
    layout="centered",
)

# 🧠 In-memory wishlist (optional – for instant local feedback)
if "wishlist" not in st.session_state:
    st.session_state["wishlist"] = []  # list of dicts


# ---------- Helper functions ----------

def format_timestamp(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d %H:%M")


def send_to_n8n(item: dict):
    payload = {
        "event": "wishlist_item_added",
        "source": "streamlit",
        "item": item,
    }
    try:
        resp = requests.post(WEBHOOK_URL, json=payload, timeout=10)
        resp.raise_for_status()
        return True, resp
    except requests.exceptions.RequestException as e:
        return False, e


def add_item(url: str, title: str, note: str):
    # Basic validation
    if not url:
        st.error("URL is required.")
        return

    if not (url.startswith("http://") or url.startswith("https://")):
        st.error("Please enter a valid URL starting with http:// or https://")
        return

    item = {
        "url": url.strip(),
        "title": title.strip() or None,
        "note": note.strip() or None,
        "added_at": format_timestamp(datetime.utcnow()),
        "status": "pending",
        "error": None,
    }

    # Local wishlist for immediate UI
    st.session_state["wishlist"].append(item)

    with st.spinner("Sending to n8n..."):
        ok, result = send_to_n8n(item)

    if ok:
        item["status"] = "sent"
        st.success("Item added and sent to n8n ✅")

        if DEBUG_SHOW_WEBHOOK_RESPONSE:
            with st.expander("n8n response"):
                try:
                    st.json(result.json())
                except Exception:
                    st.write(result.text)
    else:
        item["status"] = "error"
        item["error"] = str(result)
        st.warning(
            "Item saved locally, but there was an error sending to n8n. "
            "You can retry or check the workflow."
        )
        if DEBUG_SHOW_WEBHOOK_RESPONSE:
            with st.expander("Error details"):
                st.code(str(result))


@st.cache_data(ttl=60)
def load_wishlist_from_sheet():
    """Load wishlist data from the published Google Sheet (CSV)."""
    df = pd.read_csv(CSV_URL)

    # If your headers are different, adjust them here.
    # Example expected columns: url, name/title, price, image_url, note, added_at
    return df


def render_local_wishlist():
    """Show the in-session wishlist (just for local feedback)."""
    st.subheader("📋 Current Session Wishlist (local)")

    wishlist = st.session_state["wishlist"]
    if not wishlist:
        st.info("No local items yet. Add something above!")
        return

    for idx, item in enumerate(wishlist):
        st.markdown("---")
        cols = st.columns([4, 1.5])

        with cols[0]:
            display_title = item["title"] or f"Item {idx + 1}"
            st.markdown(f"### {display_title}")
            st.markdown(f"[🔗 Open link]({item['url']})")

            if item.get("note"):
                st.write(f"📝 {item['note']}")

            st.caption(f"Added at: {item.get('added_at', 'Unknown')}")

            status = item.get("status", "unknown")
            if status == "sent":
                st.markdown("✅ **Sent to n8n**")
            elif status == "pending":
                st.markdown("⏳ **Pending send**")
            elif status == "error":
                st.markdown("⚠️ **Error sending to n8n**")
                if item.get("error"):
                    with st.expander("Error details"):
                        st.code(item["error"])
            else:
                st.markdown("❔ **Unknown status**")

        with cols[1]:
            st.caption("URL")
            st.code(item["url"], language="text")


def render_sheet_wishlist():
    """Show wishlist from the Google Sheet (source of truth)."""
    st.subheader("📄 Wishlist from Google Sheet")

    try:
        df = load_wishlist_from_sheet()
    except Exception as e:
        st.error(f"Error loading Google Sheet: {e}")
        return

    if df.empty:
        st.info("Google Sheet is empty (no wishlist items yet).")
        return

    # Optional: show raw table
    with st.expander("View raw table", expanded=False):
        st.dataframe(df, use_container_width=True)

    st.markdown("---")

    # Render as nice cards
    for _, row in df.iterrows():
        cols = st.columns([4, 1.5])

        with cols[0]:
            # Adjust these column names to match your actual headers
            name = (
                row.get("name")
                or row.get("title")
                or row.get("product_name")
                or "Unnamed item"
            )

            st.markdown(f"### {name}")

            url = row.get("url") or row.get("link")
            if isinstance(url, str) and url.startswith("http"):
                st.markdown(f"[🔗 Open link]({url})")

            price = row.get("price") or row.get("Price")
            if pd.notna(price):
                st.write(f"💸 **Price:** {price}")

            note = row.get("note") or row.get("notes")
            if isinstance(note, str) and note.strip():
                st.write(f"📝 {note}")

            added_at = row.get("added_at") or row.get("Added At")
            if isinstance(added_at, str) and added_at.strip():
                st.caption(f"Added at: {added_at}")

        with cols[1]:
            image_url = row.get("image_url") or row.get("image") or row.get("Image URL")
            if isinstance(image_url, str) and image_url.startswith("http"):
                st.image(image_url, caption="Product", use_container_width=True)


# ---------- UI Layout ----------

st.title("📝 My Visual Wishlist")
st.caption(
    "Paste a product URL, send it to your **n8n** workflow, and build a wishlist "
    "backed by a Google Sheet."
)

with st.expander("How this works", expanded=True):
    st.markdown(
        """
1. You paste a **product URL** below.  
2. Streamlit sends it to an **n8n webhook**.  
3. n8n extracts **name, price, image, etc.** and writes a row into a **Google Sheet**.  
4. This app reads the Sheet (as CSV) and shows a **wishlist** based on it.
        """
    )

st.markdown("### ➕ Add a new item")

with st.form("add_wishlist_item", clear_on_submit=True):
    url = st.text_input(
        "Item URL",
        placeholder="https://example.com/product/123",
    )
    title = st.text_input(
        "Item name (optional)",
        placeholder="Can be auto-filled later by n8n",
    )
    note = st.text_area(
        "Notes (optional)",
        placeholder="Why do you want this? Size / color / options, etc.",
    )

    submitted = st.form_submit_button("Add to wishlist & send to n8n 🚀")

    if submitted:
        add_item(url, title, note)

# Local session wishlist (optional)
render_local_wishlist()

st.markdown("## ")

# Wishlist from Google Sheet (source of truth)
render_sheet_wishlist()
