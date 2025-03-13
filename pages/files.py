import streamlit as st
import os
import tempfile
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

# Use a writable directory for file storage
UPLOAD_FOLDER = os.path.join(os.getcwd(), "uploaded_files")

# If the above path is not writable, fall back to a temporary directory
if not os.access(os.getcwd(), os.W_OK):
    UPLOAD_FOLDER = tempfile.gettempdir()

# Ensure the directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Function to get the list of files
def get_files():
    return os.listdir(UPLOAD_FOLDER)

# Function to delete a file
def delete_file(file_name):
    file_path = os.path.join(UPLOAD_FOLDER, file_name)
    if os.path.exists(file_path):
        os.remove(file_path)

# Streamlit UI
st.title("Simple File Manager")

# Tabs for different file categories
tabs = ["General", "Insurance", "Upcoming", "Job Related", "Photos"]
selected_tab = st.tabs(tabs)

for tab in selected_tab:
    with tab:
        st.header(f"{tab} Files")

        # File uploader
        uploaded_file = st.file_uploader("Upload a file", type=None, key=f"upload_{tab}")
        
        if uploaded_file:
            file_path = os.path.join(UPLOAD_FOLDER, uploaded_file.name)
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            st.success(f"File '{uploaded_file.name}' uploaded successfully!")
            st.rerun()  # Updated function call
        
        st.subheader("Uploaded Files")
        
        # Display file list with download and delete buttons
        files = get_files()
        
        if not files:
            st.write("No files uploaded yet.")
        else:
            for file_name in files:
                file_path = os.path.join(UPLOAD_FOLDER, file_name)
                col1, col2, col3 = st.columns([4, 1, 1])
                
                with col1:
                    st.write(file_name)
                
                with col2:
                    with open(file_path, "rb") as f:
                        st.download_button("Download", f, file_name)
                
                with col3:
                    if st.button("Delete", key=f"delete_{file_name}"):
                        delete_file(file_name)
                        st.rerun()  # Updated function call
