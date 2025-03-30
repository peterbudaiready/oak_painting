import streamlit as st
import sqlite3
import os
import pandas as pd
from datetime import date
from typing import List
from auth import login_popup  # Authentication function
from supabase import create_client, Client

st.set_page_config(initial_sidebar_state="collapsed", layout="wide")

# Hide Streamlit's default menu, footer, and header
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

# -----------------------------------------------------------------------------
# 1. DATABASE SETUP for Jobs (SQLite)
# -----------------------------------------------------------------------------
DB_FILE = 'jobs.db'

def init_db():
    """Initialize the SQLite database and create the jobs table if needed."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            address TEXT NOT NULL,
            client_name TEXT NOT NULL,
            price REAL NOT NULL,
            date TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def get_connection():
    return sqlite3.connect(DB_FILE)

def get_all_jobs():
    """Retrieve all jobs from the database."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id, name, address, client_name, price, date FROM jobs")
    jobs = c.fetchall()
    conn.close()
    return jobs

def create_job(name: str, address: str, client_name: str, price: float, date_str: str):
    """Insert a new job into the database."""
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        INSERT INTO jobs (name, address, client_name, price, date)
        VALUES (?, ?, ?, ?, ?)
    ''', (name, address, client_name, price, date_str))
    conn.commit()
    conn.close()

def update_job(job_id: int, name: str, address: str, client_name: str, price: float, date_str: str):
    """Update an existing job."""
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        UPDATE jobs
        SET name = ?, address = ?, client_name = ?, price = ?, date = ?
        WHERE id = ?
    ''', (name, address, client_name, price, date_str, job_id))
    conn.commit()
    conn.close()

def delete_job(job_id: int):
    """Delete a job."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM jobs WHERE id = ?", (job_id,))
    conn.commit()
    conn.close()

def save_job_table_changes(original_df: pd.DataFrame, edited_df: pd.DataFrame):
    """Compare old vs new DataFrames and update the DB accordingly."""
    # 1. Detect deleted rows
    old_ids = set(original_df["ID"].dropna().astype(int))
    new_ids = set(edited_df["ID"].dropna().astype(int))
    deleted_ids = old_ids - new_ids
    for d_id in deleted_ids:
        delete_job(d_id)
    
    # 2. Handle new rows and modifications
    old_rows = {int(r[0]): r for r in original_df.values if not pd.isna(r[0])}
    for i, row in edited_df.iterrows():
        id_val = row["ID"]
        if pd.isna(id_val) or id_val == "":
            # New row
            name = row["Name"] if pd.notna(row["Name"]) else ""
            address = row["Address"] if pd.notna(row["Address"]) else ""
            client = row["Client"] if pd.notna(row["Client"]) else ""
            price = float(row["Price"]) if pd.notna(row["Price"]) else 0.0
            date_val = str(row["Date"]) if pd.notna(row["Date"]) else str(date.today())
            if name or address or client:
                create_job(name, address, client, price, date_val)
            continue

        job_id = int(row["ID"])
        if job_id in old_rows:
            old_id, old_name, old_addr, old_client, old_price, old_date = old_rows[job_id]
            new_name = str(row["Name"]) if pd.notna(row["Name"]) else ""
            new_addr = str(row["Address"]) if pd.notna(row["Address"]) else ""
            new_client = str(row["Client"]) if pd.notna(row["Client"]) else ""
            new_price = float(row["Price"]) if pd.notna(row["Price"]) else 0.0
            new_date = str(row["Date"]) if pd.notna(row["Date"]) else str(date.today())
            if (new_name != old_name or new_addr != old_addr or new_client != old_client or
                abs(new_price - old_price) > 1e-9 or new_date != old_date):
                update_job(job_id, new_name, new_addr, new_client, new_price, new_date)

def show_jobs_table():
    """Displays an editable table of jobs using st.data_editor."""
    jobs_data = get_all_jobs()
    if not jobs_data:
        st.info("No jobs found. Use the table below to add rows if needed.")
        columns = ["ID", "Name", "Address", "Client", "Price", "Date"]
        df_jobs = pd.DataFrame(columns=columns)
    else:
        columns = ["ID", "Name", "Address", "Client", "Price", "Date"]
        df_jobs = pd.DataFrame(jobs_data, columns=columns)
    
    st.subheader("Jobs Table (Editable)")
    edited_df = st.data_editor(
        df_jobs,
        num_rows="dynamic",    # allows adding new rows
        use_container_width=True,
        disabled=["ID"],       # ID is auto-generated and should not be editable
        key="jobs_table_editor"
    )
    st.caption("Add, edit, or delete rows. Then click **Save Changes** below.")
    
    if st.button("Save Changes"):
        save_job_table_changes(df_jobs, edited_df)
        st.success("Changes saved successfully!")
        st.experimental_rerun()

# -----------------------------------------------------------------------------
# 2. SUPABASE SETUP for Photos Management
# -----------------------------------------------------------------------------
SUPABASE_URL = "https://pckftxhpmfebxlnfhepq.supabase.co"
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBja2Z0eGhwbWZlYnhsbmZoZXBxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDMzNjQxNjMsImV4cCI6MjA1ODk0MDE2M30.5QhW4hOEpDg1CVHZuC_4-pgQ8LiX4f2EFFBq1R2gBJA"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

def show_photos_management_supabase(job_id: int):
    """Display and manage photos for the selected job via Supabase Storage."""
    st.markdown(f"### Manage Photos for Job ID: {job_id} (Supabase Storage)")
    
    # Define a folder for the job (e.g., "job_123")
    folder_path = f"job_{job_id}"
    
    # List files from the "jobphotos" bucket under the folder for the job.
    list_response = supabase.storage.from_("jobphotos").list(folder_path)
    files = list_response if list_response is not None else []
    
    # Build a DataFrame with file information.
    data = []
    for f in files:
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
        # Show the file information in a read-only data editor.
        edited_df = st.data_editor(
            df_files,
            use_container_width=True,
            disabled=True,
            key="photos_data_editor"
        )
        
        st.markdown("### Actions")
        # For each file, render download and delete buttons.
        for idx, row in edited_df.iterrows():
            file_name = row["File Name"]
            file_path = row["File Path"]
            cols = st.columns([2, 1, 1])
            cols[0].write(file_name)
            # Download file via Supabase storage
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
            # Delete file from Supabase storage
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
# 3. MAIN APP
# -----------------------------------------------------------------------------
def back_to_jobs():
    st.session_state["in_photos_mode"] = False
    st.session_state["photos_job_id"] = None
    st.experimental_rerun()

def main():
    st.title("Job Management")
    
    # Initialize jobs database if not already set up.
    init_db()
    
    # Session state to toggle between Jobs Table and Photos Management modes.
    if "in_photos_mode" not in st.session_state:
        st.session_state["in_photos_mode"] = False
    if "photos_job_id" not in st.session_state:
        st.session_state["photos_job_id"] = None

    if not st.session_state["in_photos_mode"]:
        # Show the editable jobs table.
        show_jobs_table()
        
        # Dropdown + button to switch to Photos Management mode.
        jobs_data = get_all_jobs()
        if jobs_data:
            job_ids = [str(j[0]) for j in jobs_data]
            st.write("---")
            col1, col2 = st.columns([3, 1])
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
        # In Photos Management mode.
        st.button("Back to Jobs", on_click=back_to_jobs)
        show_photos_management_supabase(st.session_state["photos_job_id"])

if __name__ == "__main__":
    main()
