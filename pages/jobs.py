import streamlit as st
import sqlite3
import os
import pandas as pd
from datetime import date
from typing import List
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

DB_FILE = 'jobs.db'
PHOTOS_FOLDER = 'photos'

# -----------------------------------------------------------------------------
# 1. DATABASE SETUP
# -----------------------------------------------------------------------------
def init_db():
    """Initialize the SQLite database and create tables if needed."""
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
    c.execute('''
        CREATE TABLE IF NOT EXISTS job_photos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id INTEGER,
            photo_path TEXT,
            FOREIGN KEY(job_id) REFERENCES jobs(id) ON DELETE CASCADE
        )
    ''')
    conn.commit()
    conn.close()

    # Ensure photos folder exists
    if not os.path.exists(PHOTOS_FOLDER):
        os.makedirs(PHOTOS_FOLDER)

def get_connection():
    return sqlite3.connect(DB_FILE)

# -----------------------------------------------------------------------------
# 2. CRUD: JOBS
# -----------------------------------------------------------------------------
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
    """Delete a job and its associated photos (database + files)."""
    conn = get_connection()
    c = conn.cursor()

    # Remove any related photos from disk
    c.execute("SELECT photo_path FROM job_photos WHERE job_id = ?", (job_id,))
    rows = c.fetchall()
    for (p_path,) in rows:
        if os.path.exists(p_path):
            os.remove(p_path)

    # Remove from DB
    c.execute("DELETE FROM jobs WHERE id = ?", (job_id,))
    c.execute("DELETE FROM job_photos WHERE job_id = ?", (job_id,))
    conn.commit()
    conn.close()

# -----------------------------------------------------------------------------
# 3. CRUD: PHOTOS
# -----------------------------------------------------------------------------
def add_photo_to_job(job_id: int, photo_path: str):
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        INSERT INTO job_photos (job_id, photo_path) 
        VALUES (?, ?)
    ''', (job_id, photo_path))
    conn.commit()
    conn.close()

def get_photos_for_job(job_id: int) -> List:
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id, job_id, photo_path FROM job_photos WHERE job_id = ?", (job_id,))
    photos = c.fetchall()
    conn.close()
    return photos

def delete_photo(photo_id: int):
    """Delete a single photo from DB and disk."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT photo_path FROM job_photos WHERE id = ?", (photo_id,))
    row = c.fetchone()
    if row:
        path = row[0]
        if os.path.exists(path):
            os.remove(path)
    c.execute("DELETE FROM job_photos WHERE id = ?", (photo_id,))
    conn.commit()
    conn.close()

# -----------------------------------------------------------------------------
# 4. STREAMLIT APP
# -----------------------------------------------------------------------------
def main():
    st.title("Job Management")

    # Initialize DB + Folders
    init_db()

    # Session state to toggle between "Jobs Table" and "Photos Management"
    if "in_photos_mode" not in st.session_state:
        st.session_state["in_photos_mode"] = False
    if "photos_job_id" not in st.session_state:
        st.session_state["photos_job_id"] = None

    if st.session_state["in_photos_mode"] == False:
        # Show the EDITABLE JOBS TABLE
        show_jobs_table()

        # Provide a dropdown + button to switch to PHOTOS MODE
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
                        st.rerun()
        else:
            st.info("No jobs available to manage photos.")
    else:
        # PHOTOS MODE
        st.button("Back to Jobs", on_click=back_to_jobs)
        show_photos_management(st.session_state["photos_job_id"])


def show_jobs_table():
    """Displays an editable table of jobs + 'Save Changes' button."""
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
        disabled=["ID"],       # ID is auto-generated
        key="jobs_table_editor"
    )
    st.caption("Add, edit, or delete rows. Then click **Save Changes** below.")

    if st.button("Save Changes"):
        save_job_table_changes(df_jobs, edited_df)
        st.success("Changes saved successfully!")
        st.rerun()


def back_to_jobs():
    """Callback to return to the main jobs table."""
    st.session_state["in_photos_mode"] = False
    st.session_state["photos_job_id"] = None
    st.rerun()

# -----------------------------------------------------------------------------
# 5. SAVE JOB TABLE CHANGES
# -----------------------------------------------------------------------------
def save_job_table_changes(original_df: pd.DataFrame, edited_df: pd.DataFrame):
    """Compare old vs new dataframes and update the DB accordingly."""
    old_ids = set(original_df["ID"].dropna().astype(int))
    new_ids = set(edited_df["ID"].dropna().astype(int))

    # 1. Detect deleted rows
    deleted_ids = old_ids - new_ids
    for d_id in deleted_ids:
        delete_job(d_id)

    # 2. Detect new rows (these have no ID or ID not in old_ids)
    for i, row in edited_df.iterrows():
        id_val = row["ID"]
        if pd.isna(id_val) or id_val == "":
            # It's a new row
            name = row["Name"] if pd.notna(row["Name"]) else ""
            address = row["Address"] if pd.notna(row["Address"]) else ""
            client = row["Client"] if pd.notna(row["Client"]) else ""
            price = float(row["Price"]) if pd.notna(row["Price"]) else 0.0
            date_val = str(row["Date"]) if pd.notna(row["Date"]) else str(date.today())
            if name or address or client:
                create_job(name, address, client, price, date_val)
            continue

    # 3. Detect modifications of existing rows
    old_rows = {int(r[0]): r for r in original_df.values if not pd.isna(r[0])}
    # old_rows: { job_id -> (id, name, address, client, price, date) }
    for i, row in edited_df.iterrows():
        if pd.isna(row["ID"]):
            continue  # new row - handled above
        job_id = int(row["ID"])
        if job_id in old_rows:
            old_id, old_name, old_addr, old_client, old_price, old_date = old_rows[job_id]
            new_name = str(row["Name"]) if pd.notna(row["Name"]) else ""
            new_addr = str(row["Address"]) if pd.notna(row["Address"]) else ""
            new_client = str(row["Client"]) if pd.notna(row["Client"]) else ""
            new_price = float(row["Price"]) if pd.notna(row["Price"]) else 0.0
            new_date = str(row["Date"]) if pd.notna(row["Date"]) else str(date.today())

            # Compare
            if (new_name != old_name or
                new_addr != old_addr or
                new_client != old_client or
                abs(new_price - old_price) > 1e-9 or
                new_date != old_date):
                update_job(job_id, new_name, new_addr, new_client, new_price, new_date)

# -----------------------------------------------------------------------------
# 6. PHOTOS MANAGEMENT
# -----------------------------------------------------------------------------
def show_photos_management(job_id: int):
    """Display and manage photos for the selected job."""
    st.markdown(f"### Manage Photos for Job ID: {job_id}")
    photos = get_photos_for_job(job_id)

    if photos:
        st.write("Existing Photos:")
        # Show them in a 3-column grid
        for i, (photo_id, _, photo_path) in enumerate(photos):
            if i % 3 == 0:
                cols = st.columns(3, gap="medium")
            col = cols[i % 3]

            if os.path.exists(photo_path):
                with col:
                    try:
                        col.image(photo_path, use_container_width=True)
                    except Exception as e:
                        col.warning(f"Error displaying image: {e}")
                    # Download
                    with open(photo_path, "rb") as f:
                        photo_bytes = f.read()
                    filename = os.path.basename(photo_path)
                    col.download_button(
                        label="Download",
                        data=photo_bytes,
                        file_name=filename,
                        mime="image/*",
                        key=f"download_{photo_id}"
                    )
                    # Delete
                    if col.button("Delete Photo", key=f"del_{photo_id}"):
                        delete_photo(photo_id)
                        st.success(f"Deleted photo {photo_id}.")
                        st.rerun()
            else:
                col.warning(f"File not found: {photo_path}")
    else:
        st.info("No photos for this job yet.")

    st.write("---")
    st.markdown("**Add New Photos**")
    new_photos = st.file_uploader("Upload new photos", accept_multiple_files=True, key=f"photo_uploader_{job_id}")
    if new_photos:
        if st.button("Save New Photos", key=f"save_photos_{job_id}"):
            for file in new_photos:
                save_path = os.path.join(PHOTOS_FOLDER, f"job_{job_id}_{file.name}")
                with open(save_path, "wb") as f:
                    f.write(file.getbuffer())
                add_photo_to_job(job_id, save_path)
            st.success("Added new photos.")
            st.rerun()

# -----------------------------------------------------------------------------
# 7. RUN
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    main()
