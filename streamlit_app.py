import streamlit as st
import requests
from datetime import datetime
import pandas as pd
from html import unescape  # for decoding &#x27; into apostrophes

WEBHOOK_URL = "https://k123c4.app.n8n.cloud/webhook/streamlit-chat"

CSV_URL = (
    "https://docs.google.com/spreadsheets/d/e/"
    "2PACX-1vRs5rxWD1MRUbwNPmXkM0Dn6OSAuvpI865UZ0jBG-acmEjzlq5DXuxR8HnoANv1eJcJmpG3y1Q7D_Ab/"
    "pub?output=csv"
)

DEBUG_SHOW_WEBHOOK_RESPONSE = False

# ⚙️ Page config (must be the first Streamlit call)
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
                st.code(item["error"])


@st.cache_data(ttl=60)
def load_wishlist_from_sheet():
    """
    Load wishlist data from Google Sheet.
    - Row 1 is treated as headers (default for read_csv).
    - Row 2+ are the actual data rows.
    """
    df = pd.read_csv(CSV_URL)
    df.columns = [c.strip() for c in df.columns]  # clean up header names
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
    st.subheader("📄 Wishlist from Google Sheet")

    # 🔄 Reload button lives right above the sheet view
    with st.container():
        col_reload, col_spacer = st.columns([1, 3])
        with col_reload:
            if st.button("🔄 Reload Sheet"):
                load_wishlist_from_sheet.clear()  # clears cache so next call is fresh
                st.rerun()

    try:
        df = load_wishlist_from_sheet()
    except Exception as e:
        st.error(f"Error loading Google Sheet CSV: {e}")
        return

    if df.empty:
        st.info("The Google Sheet is currently empty.")
        return

    # OPTIONAL: Let you inspect what columns it sees
    with st.expander("View raw sheet data", expanded=False):
        st.write("Detected columns:", list(df.columns))
        st.dataframe(df, use_container_width=True)

    st.markdown("---")

    # Use column positions dynamically (row 1 = headers, rows 2+ = data)
    name_col = df.columns[0]      # e.g. "product_name"
    price_col = df.columns[1]     # e.g. "price"
    currency_col = df.columns[2]  # e.g. "currency"
    image_col = df.columns[3]     # e.g. "image_url"

    for _, row in df.iterrows():  # iterates over data rows only
        product_name = unescape(str(row.get(name_col, "")).strip())
        price = str(row.get(price_col, "")).strip()
        currency = str(row.get(currency_col, "")).strip()
        image_url = str(row.get(image_col, "")).strip()

        cols = st.columns([4, 1.5])

        with cols[0]:
            title = product_name or "Unnamed item"
            st.markdown(f"### {title}")

            # Show price if present
            if price:
                price_display = f"{price} {currency}".strip()
                st.write(f"💸 **Price:** {price_display}")

        with cols[1]:
            if image_url.startswith("http"):
                st.image(image_url, caption="Product", use_container_width=True)

        st.markdown("---")


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
