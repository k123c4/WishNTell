import streamlit as st 
import requests
import pytz
from datetime import datetime
import pandas as pd
from html import unescape  # for decoding &#x27; into apostrophes

WEBHOOK_URL = "https://wishntelldemo.app.n8n.cloud/webhook-test/5a5fc4d0-e5da-40a6-b440-907481907d27"
# 🔌 Webhook URLs
TEST_WEBHOOK_URL = "https://wishntelldemo.app.n8n.cloud/webhook-test/5a5fc4d0-e5da-40a6-b440-907481907d27"
PROD_WEBHOOK_URL = "https://wishntelldemo.app.n8n.cloud/webhook/5a5fc4d0-e5da-40a6-b440-907481907d27"

st.markdown("### Webhook Mode")
mode = st.radio(
    "Choose webhook destination:",
    ["Production", "Test"],
    horizontal=True
)

WEBHOOK_URL = PROD_WEBHOOK_URL if mode == "Production" else TEST_WEBHOOK_URL
st.caption(f"Current webhook URL: `{WEBHOOK_URL}`")


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

# 🎨 Custom soft pastel theme
custom_css = """
<style>
/* Overall app background and typography */
[data-testid="stAppViewContainer"] {
    background-color: #f1efe9;
    color: #167a5f;
}

/* Main content area */
.block-container {
    padding-top: 2rem;
    padding-bottom: 4rem;
}

/* Header bar */
[data-testid="stHeader"] {
    background: rgba(241, 239, 233, 0.9);
    backdrop-filter: blur(6px);
    border-bottom: 1px solid rgba(22, 122, 95, 0.08);
}

/* Sidebar */
[data-testid="stSidebar"] {
    background-color: #f1efe9;
}
[data-testid="stSidebar"] * {
    color: #167a5f !important;
}

/* Generic text */
html, body, p, span, div, label {
    color: #167a5f;
    font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}

/* Titles */
h1, h2, h3, h4, h5, h6 {
    color: #167a5f !important;
    font-weight: 700;
}

/* Buttons */
.stButton>button, button[kind="primary"] {
    background-color: #fdfcf8 !important;
    color: #ffffff !important;
    border-radius: 999px !important;
    border: none !important;
    padding: 0.4rem 1.3rem !important;
    font-weight: 600 !important;
    box-shadow: 0 4px 10px rgba(22, 122, 95, 0.25);
}
.stButton>button:hover, button[kind="primary"]:hover {
    background-color: #0f5a45 !important;
    box-shadow: 0 6px 14px rgba(22, 122, 95, 0.35);
}

/* Inputs & text areas */
.stTextInput>div>div>input,
.stTextArea>div>textarea {
    background-color: #fdfcf8 !important;
    border-radius: 12px !important;
    border: 1px solid rgba(22, 122, 95, 0.25) !important;
    color: #167a5f !important;
}
.stTextInput>label, .stTextArea>label {
    color: #167a5f !important;
    font-weight: 600;
}

/* Expander */
.streamlit-expanderHeader {
    background-color: rgba(255, 255, 255, 0.75) !important;
    border-radius: 12px !important;
}
.streamlit-expanderContent {
    background-color: rgba(255, 255, 255, 0.6) !important;
    border-radius: 0 0 12px 12px !important;
}

/* Wishlist "cards" */
.wishlist-card {
    background: rgba(255, 255, 255, 0.88);
    border-radius: 18px;
    padding: 1.1rem 1.3rem;
    margin-bottom: 1rem;
    border: 1px solid rgba(22, 122, 95, 0.08);
    box-shadow: 0 6px 18px rgba(0, 0, 0, 0.04);
}
.wishlist-card h3, .wishlist-card h4 {
    margin-top: 0.2rem;
    margin-bottom: 0.3rem;
}

/* Subtle section separators */
hr {
    border: none;
    border-top: 1px solid rgba(22, 122, 95, 0.12);
    margin: 1rem 0;
}

/* Captions and meta text */
small, .caption, .stMarkdown>p>em {
    color: rgba(22, 122, 95, 0.8) !important;
}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# 🧠 In-memory wishlist (optional – for instant local feedback)
if "wishlist" not in st.session_state:
    st.session_state["wishlist"] = []  # list of dicts


# ---------- Helper functions ----------

def format_timestamp(dt: datetime) -> str:
    tz = pytz.timezone("America/Chicago")  # <-- your timezone here
    local_time = dt.astimezone(tz)
    return local_time.strftime("%Y-%m-%d %H:%M")



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


def add_item(url: str):
    # Basic validation
    if not url:
        st.error("URL is required.")
        return

    if not (url.startswith("http://") or url.startswith("https://")):
        st.error("Please enter a valid URL starting with http:// or https://")
        return

    item = {
        "url": url.strip(),
        "added_at": format_timestamp(datetime.now()),
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


def render_local_wishlist():  # optional
    """Show the in-session wishlist (just for local feedback)."""
    st.subheader("🧠 Session-only items (local)")

    wishlist = st.session_state["wishlist"]
    if not wishlist:
        st.info("No local items yet. Add something above!")
        return

    for idx, item in enumerate(wishlist):
        # Card wrapper
        st.markdown('<div class="wishlist-card">', unsafe_allow_html=True)

        cols = st.columns([4, 1.5])

        with cols[0]:
            # 🔗 Link only (no title anymore)
            st.markdown(f"[🔗 Open link]({item['url']})")

            # Timestamp
            st.caption(f"Added at: {item.get('added_at', 'Unknown')}")

            # Status
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

        st.markdown("</div>", unsafe_allow_html=True)



def render_sheet_wishlist(): #optional
    st.subheader("📄 Wishlist")

    # 🔄 Reload button lives right above the sheet view
    with st.container():
        col_reload, col_spacer = st.columns([1, 5])
        with col_reload:
            if st.button(" Reload Sheet"):
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

    # Helper to clean NaN → "" and strip
    def clean(value):
        import pandas as pd
        if pd.isna(value):
            return ""
        return str(value).strip()

    # Use column positions dynamically (row 1 = headers, rows 2+ = data)
    # Make sure your sheet has these in this order:
    # 0: name, 1: price, 2: currency, 3: image_url, 4: product_url, 5: added_at
    name_col = df.columns[0]
    price_col = df.columns[1]
    currency_col = df.columns[2]
    image_col = df.columns[3]
    url_col = df.columns[4]
    added_at_col = df.columns[5]

    for _, row in df.iterrows():  # iterates over data rows only
        product_name = unescape(clean(row.get(name_col)))
        price = clean(row.get(price_col))
        currency = clean(row.get(currency_col))
        image_url = clean(row.get(image_col))
        product_url = clean(row.get(url_col))
        added_at = clean(row.get(added_at_col))

        # Card wrapper
        st.markdown('<div class="wishlist-card">', unsafe_allow_html=True)

        cols = st.columns([4, 1.5])

        with cols[0]:
            title = product_name or "Unnamed item"
            st.markdown(f"### {title}")

            # Show price if present
            if price:
                price_display = f"{price} {currency}".strip()
                st.write(f"💸 **Price:** {price_display}")


            # Product link
            if product_url.startswith("http"):
                st.markdown(f"[🔗 Open link]({product_url})")

            # Added timestamp
            if added_at:
                st.caption(f"Added: {added_at}")

        with cols[1]:
            if image_url.startswith("http"):
                st.image(image_url, caption="Product", use_container_width=True)

                

        st.markdown("</div>", unsafe_allow_html=True)



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



st.markdown("---")

st.markdown("### ➕ Add a new item")

with st.form("add_wishlist_item", clear_on_submit=True):
    url = st.text_input(
        "Item URL",
        placeholder="https://example.com/product/123",
    )

    submitted = st.form_submit_button("Add to wishlist & send to n8n 🚀")

    if submitted:
        add_item(url)

# 👉 Google Sheet wishlist FIRST
st.markdown("## Saved Wishlist (Google Sheet)")
render_sheet_wishlist()


st.markdown("## ")

render_local_wishlist()  # optional local wishlist display
