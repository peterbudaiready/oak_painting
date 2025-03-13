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
BASE_UPLOAD_FOLDER = os.path.join(os.getcwd(), "uploaded_files")

# If the above path is not writable, fall back to a temporary directory
if not os.access(os.getcwd(), os.W_OK):
    BASE_UPLOAD_FOLDER = tempfile.gettempdir()

# Ensure the base directory exists
os.makedirs(BASE_UPLOAD_FOLDER, exist_ok=True)

# Tabs for different file categories
tabs = ["General", "Insurance", "Upcoming", "Job Related", "Photos"]

# Function to get the list of files for a specific category
def get_files(category):
    category_folder = os.path.join(BASE_UPLOAD_FOLDER, category)
    os.makedirs(category_folder, exist_ok=True)
    return os.listdir(category_folder)

# Function to delete a file
def delete_file(category, file_name):
    file_path = os.path.join(BASE_UPLOAD_FOLDER, category, file_name)
    if os.path.exists(file_path):
        os.remove(file_path)

# Streamlit UI
st.title("Simple File Manager")

tab_container = st.tabs(tabs)

for index, tab in enumerate(tab_container):
    with tab:
        category = tabs[index]
        st.header(f"{category} Files")

        # File uploader
        uploaded_file = st.file_uploader("Upload a file", type=None, key=f"upload_{category}")
        
        if uploaded_file:
            category_folder = os.path.join(BASE_UPLOAD_FOLDER, category)
            os.makedirs(category_folder, exist_ok=True)
            file_path = os.path.join(category_folder, uploaded_file.name)
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            st.success(f"File '{uploaded_file.name}' uploaded successfully to {category}!")
            st.rerun()
        
        st.subheader("Uploaded Files")
        
        # Display file list with download and delete buttons
        files = get_files(category)
        
        if not files:
            st.write("No files uploaded yet.")
        else:
            for file_name in files:
                file_path = os.path.join(BASE_UPLOAD_FOLDER, category, file_name)
                col1, col2, col3 = st.columns([4, 1, 1])
                
                with col1:
                    st.write(file_name)
                
                with col2:
                    with open(file_path, "rb") as f:
                        st.download_button("Download", f, file_name, key=f"download_{file_name}_{category}")
                
                with col3:
                    if st.button("Delete", key=f"delete_{file_name}_{category}"):
                        delete_file(category, file_name)
                        st.rerun()
