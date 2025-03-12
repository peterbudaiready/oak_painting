import streamlit as st
import requests
import base64
import json
from auth import login_popup  # Import authentication function

st.set_page_config(initial_sidebar_state="collapsed", layout="wide")

# Define a CSS snippet to hide Streamlit's default menu, footer, and header
hide_st_style = """
<style>
#MainMenu {visibility: hidden;}     /* Hide the hamburger menu */
footer {visibility: hidden;}        /* Hide the “Made with Streamlit” footer */
header {visibility: hidden;}        /* Hide the header */
</style>
"""

# Apply the custom styling globally
st.markdown(hide_st_style, unsafe_allow_html=True)

# Ensure authentication before rendering any UI
login_popup()

# Replace with your actual Make.com webhook URL
WEBHOOK_URL = "https://hook.eu2.make.com/sg2oc9evhq2q4mhlljd9vuwgunfusakh"

st.title("📢 Social Media Post Uploader")

# Input for text content
post_text = st.text_area(
    "Write your post:",
    height=200,
    placeholder="Type your social media post here..."
)

# Image uploader
uploaded_image = st.file_uploader("Upload an image", type=["jpg", "jpeg", "png"])

if st.button("📤 Post"):
    if not post_text.strip():
        st.warning("⚠️ Post text cannot be empty!")
    else:
        # Prepare JSON payload with standard naming
        payload = {
            "text": post_text,
            "attachments": None  # Will replace with base64 if an image is uploaded
        }

        # Convert image to Base64 if uploaded
        if uploaded_image:
            img_bytes = uploaded_image.read()
            img_base64 = base64.b64encode(img_bytes).decode("utf-8")
            payload["image_base64"] = img_base64

        # Send JSON payload with explicit headers
        headers = {"Content-Type": "application/json"}
        try:
            response = requests.post(WEBHOOK_URL, json=payload, headers=headers)

            if response.status_code == 200:
                st.success("✅ Post successfully sent!")
            else:
                st.error(
                    f"❌ Failed to post! "
                    f"Server responded with status code {response.status_code}."
                )

        except Exception as e:
            st.error(f"⚠️ Error: {e}")
