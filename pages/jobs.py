import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import date
import os
from auth import login_popup  # Authentication function

st.set_page_config(initial_sidebar_state="collapsed", layout="wide")

# Hide Streamlit default menu, footer, and header
hide_st_style = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
</style>
"""
st.markdown(hide_st_style, unsafe_allow_html=True)

# Ensure authentication before rendering any UI
login_popup()

# -------------------------------------------------------------------
# SUPABASE SETUP
# -------------------------------------------------------------------
SUPABASE_URL = "https://pckftxhpmfebxlnfhepq.supabase.co"
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBja2Z0eGhwbWZlYnhsbmZoZXBxIiwicm9sIjoiaW50ZXJuYWwiLCJpYXQiOjE3NDMzNjQxNjMsImV4cCI6MjA1ODk0MDE2M30.5QhW4hOEpDg1CVHZuC_4-pgQ8LiX4f2EFFBq1R2gBJA"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

# -----------------------------------------------------------------------------
# 6. PHOTOS MANAGEMENT WITH SUPABASE + st.data_editor
# -----------------------------------------------------------------------------
def show_photos_management_supabase(job_id: int):
    st.markdown(f"### Manage Photos for Job ID: {job_id} (Supabase Storage)")
    
    # Use a folder per job to organize files in the bucket.
    folder_path = f"job_{job_id}"
    
    # List files from the bucket folder "job_{job_id}"
    list_response = supabase.storage.from_("jobphotos").list(folder_path)
    files = list_response if list_response is not None else []
    
    # Build a DataFrame of file information.
    data = []
    for f in files:
        # Each file record should include at least the file name.
        file_name = f.get("name", "")
        full_path = f"{folder_path}/{file_name}"
        public_url_resp = supabase.storage.from_("jobphotos").get_public_url(full_path)
        public_url = public_url_resp.get("publicURL", "")
        data.append({
            "File Name": file_name,
            "File Path": full_path,
            "Public URL": public_url
        })
    
    df_files = pd.DataFrame(data)
    
    if df_files.empty:
        st.info("No photos found for this job.")
    else:
        st.subheader("Photos Data Editor")
        # Display the file data (read-only) with st.data_editor.
        edited_df = st.data_editor(
            df_files,
            use_container_width=True,
            disabled=True,
            key="photos_data_editor"
        )
        
        st.markdown("### Actions")
        # For each file row, display download and delete buttons in a row layout.
        for idx, row in edited_df.iterrows():
            file_name = row["File Name"]
            file_path = row["File Path"]
            cols = st.columns([2, 1, 1])
            cols[0].write(file_name)
            
            # Download: get file data via Supabase.
            download_resp = supabase.storage.from_("jobphotos").download(file_path)
            file_data = download_resp.get("data", None)
            if file_data is not None:
                cols[1].download_button(
                    label="Download",
                    data=file_data,
                    file_name=file_name,
                    mime="application/octet-stream",
                    key=f"download_{idx}"
                )
            else:
                cols[1].warning("Download failed")
            
            # Delete: remove file from Supabase storage.
            if cols[2].button("Delete", key=f"delete_{idx}"):
                remove_resp = supabase.storage.from_("jobphotos").remove([file_path])
                st.success(f"Deleted {file_name}")
                st.experimental_rerun()
    
    st.markdown("---")
    st.markdown("**Upload New Photos**")
    new_photos = st.file_uploader("Upload photos", accept_multiple_files=True, key=f"upload_{job_id}")
    if new_photos:
        if st.button("Save New Photos", key=f"save_upload_{job_id}"):
            for file in new_photos:
                upload_path = f"{folder_path}/{file.name}"
                upload_resp = supabase.storage.from_("jobphotos").upload(upload_path, file)
            st.success("Uploaded new photos.")
            st.experimental_rerun()

# -----------------------------------------------------------------------------
# 4. STREAMLIT APP (Modified)
# -----------------------------------------------------------------------------
def main():
    st.title("Job Management")
    # ... (your DB initialization and jobs table UI remain unchanged)
    # For example, show_jobs_table() continues to work with your SQLite jobs.
    
    # Use session state to toggle between "Jobs Table" and "Photos Management"
    if "in_photos_mode" not in st.session_state:
        st.session_state["in_photos_mode"] = False
    if "photos_job_id" not in st.session_state:
        st.session_state["photos_job_id"] = None

    if st.session_state["in_photos_mode"] == False:
        # Show your editable jobs table (existing functionality)
        show_jobs_table()
        # Dropdown + button to switch to PHOTOS MODE
        jobs_data = get_all_jobs()
        if jobs_data:
            job_ids = [str(j[0]) for j in jobs_data]
            st.write("---")
            col1, col2 = st.columns([3,1])
            with col1:
                selected_job_id_str = st.selectbox(
                    "Select a Job ID to Manage Photos",
                    options=["--Select--"] + job_ids
                )
            with col2:
                if st.button("Manage Photos"):
                    if selected_job_id_str == "--Select--":
                        st.warning("Please select a valid job ID.")
                    else:
                        st.session_state["photos_job_id"] = int(selected_job_id_str)
                        st.session_state["in_photos_mode"] = True
                        st.experimental_rerun()
        else:
            st.info("No jobs available to manage photos.")
    else:
        # PHOTOS MODE using Supabase storage.
        st.button("Back to Jobs", on_click=back_to_jobs)
        show_photos_management_supabase(st.session_state["photos_job_id"])

def back_to_jobs():
    st.session_state["in_photos_mode"] = False
    st.session_state["photos_job_id"] = None
    st.experimental_rerun()

# -----------------------------------------------------------------------------
# RUN
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    main()
