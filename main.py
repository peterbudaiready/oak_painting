import streamlit as st
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

login_popup()

# Apply the custom styling globally
st.markdown(hide_st_style, unsafe_allow_html=True)

# Display UI only if authenticated
st.title("🔗 Quick Access Links")

# First Row
col1, col2, col3 = st.columns(3)

# Add content to the first column
with col1:
    st.header("Website")
    st.write("Website related links")
    st.link_button('One of a Kind Painting.com', "https://www.1ofakindpainting.com")
    st.link_button('WordPress Edit mode', "https://hpanel.hostinger.com/redirect/1ofakindpainting.com?l=wpAdmin&source=website_list&directory=&isManagedUser=0&domain=1ofakindpainting.com&subdomain=")
    st.link_button('Hostinger', "https://hpanel.hostinger.com")
    st.link_button('Semrush(Website/SEO Audit)', "https://www.semrush.com/projects/")

# Add content to the second column
with col2:
    st.header("Google")
    st.write("Google related links")
    st.link_button('Google Ads', "https://business.google.com/us/google-ads/?authuser=0")
    st.link_button('Local service Ads', "https://ads.google.com/localservices")
    st.link_button('Google Analytics', "")
    st.link_button('Google profile', "https://maps.app.goo.gl/wCLCjzVck4A6rMUN9")

with col3:
    st.header("Meta")
    st.write("Meta related links")
    st.link_button('FB profile', "https://www.facebook.com/profile.php?id=61561895865484")
    st.link_button('IG profile', "https://www.instagram.com/one_of_a_kind_painting/")
    st.link_button('Meta Ads Manager', "https://business.meta.com/")

# Second Row
col4, col5, col6 = st.columns(3)

# Add content to the first column
with col4:
    st.header("Other tools")
    st.write("Other tool links")
    st.link_button('Apollo', "http://apollo.io/")
    st.write("⬆️ Email marketing")
    st.link_button('Bing business profile', "https://www.bingplaces.com/Authentication/Index")
    st.link_button('Apple business', "https://businessconnect.apple.com/")
    st.link_button('Alexa/Amazon', "https://alexabusiness.com")

# Add content to the second column
with col5:
    st.header("Physical")
    st.write("Physical material services")
    st.link_button('4imprints', "https://www.4imprint.com")
    st.link_button("VistaPrint", "https://www.vistaprint.com")

with col6:
    st.header("Commercial")
    st.write("Commercial services")
    st.link_button("KeyRenter", "https://keyrenterdenver.com")
    st.link_button("ColoradoRPM", "https://www.coloradorpm.com")
    
    
