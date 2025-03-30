import streamlit as st
import pandas as pd
from supabase import create_client, Client

# For Postgres (psycopg2)
import psycopg2
from psycopg2 import sql

# If you prefer SQLAlchemy, uncomment these:
# from sqlalchemy import create_engine, text

# -------------------------------------------------------------------------
# HARD-CODED SUPABASE CREDENTIALS & POSTGRES URI (FOR DEMO ONLY!)
# -------------------------------------------------------------------------
SUPABASE_URL = "https://pckftxhpmfebxlnfhepq.supabase.co"
SUPABASE_ANON_KEY = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
    "eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBja2Z0eGhwbWZlYnhsbmZoZXBxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDMzNjQxNjMsImV4cCI6MjA1ODk0MDE2M30."
    "5QhW4hOEpDg1CVHZuC_4-pgQ8LiX4f2EFFBq1R2gBJA"
)

BUCKET_NAME = "jobphotos"

# Postgres URI
POSTGRES_URI = "postgresql://postgres:[9607222009Loko.]@db.pckftxhpmfebxlnfhepq.supabase.co:5432/postgres"


# -------------------------------------------------------------------------
# INIT SUPABASE CONNECTION
# -------------------------------------------------------------------------
@st.cache_resource
def init_supabase_client() -> Client:
    """Creates and caches the Supabase client."""
    return create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

supabase = init_supabase_client()


# -------------------------------------------------------------------------
# INIT POSTGRES CONNECTION (PSYCOPG2 EXAMPLE)
# -------------------------------------------------------------------------
@st.cache_resource
def init_postgres_connection():
    """
    Creates and caches a psycopg2 connection to Postgres.
    If you prefer SQLAlchemy, you can do:
       engine = create_engine(POSTGRES_URI)
       return engine
    """
    conn = psycopg2.connect(POSTGRES_URI)
    return conn

postgres_conn = init_postgres_connection()


# -------------------------------------------------------------------------
# FETCH FILES FROM BUCKET
# -------------------------------------------------------------------------
def fetch_files_from_bucket(bucket_name: str) -> pd.DataFrame:
    """
    Fetches the list of objects from the given Supabase Storage bucket.
    Returns a DataFrame of file info (name, size, updated_at, etc.).
    
    If your files are in a subfolder, specify path="subfolder/" in the .list() call.
    """
    # Try listing everything at top-level. If your files are nested in a folder,
    # specify path="folder_name/" or something similar.
    response = supabase.storage.from_(bucket_name).list(path="", limit=1000)
    if not response:
        return pd.DataFrame(columns=["name", "size", "updated_at"])

    file_list = []
    for item in response:
        # item typically has keys: 'name', 'id', 'updated_at', 'metadata', 'created_at', ...
        file_list.append({
            "name": item["name"],
            "size": (item["metadata"].get("size") if "metadata" in item else None),
            "updated_at": item.get("updated_at"),
        })
    return pd.DataFrame(file_list)


# -------------------------------------------------------------------------
# RENAME FILE IN SUPABASE STORAGE
# (Supabase's python client doesn't have "move",
#  so we use "copy" + "remove" to emulate rename.)
# -------------------------------------------------------------------------
def rename_file_in_bucket(bucket_name: str, old_name: str, new_name: str):
    """
    Emulates a file 'move/rename' by copying old_name to new_name,
    then removing the old_name.
    """
    # Copy old -> new
    copy_resp = supabase.storage.from_(bucket_name).copy(old_name, new_name)
    # copy_resp can be None or { 'Key': '<new path>' } depending on success/failure
    # Next remove old
    remove_resp = supabase.storage.from_(bucket_name).remove(old_name)
    # remove_resp might be something like {'data': [...], 'error': None} or similar

    return (copy_resp, remove_resp)


# -------------------------------------------------------------------------
# OPTIONAL: EXAMPLE POSTGRES QUERY
# (You can adapt this to store the new file name in your DB, etc.)
# -------------------------------------------------------------------------
def example_postgres_query(conn, old_name, new_name):
    """
    You can adapt this to store info in your own table. For example:
      - Insert a log entry about the rename.
      - Update a row in a 'files' table with the new filename.
    
    This is just a placeholder for demonstration.
    """
    with conn.cursor() as cur:
        # Example: create a table if it doesn't exist
        cur.execute("""
            CREATE TABLE IF NOT EXISTS file_rename_log(
                id SERIAL PRIMARY KEY,
                old_name TEXT,
                new_name TEXT,
                renamed_at TIMESTAMP DEFAULT NOW()
            )
        """)
        conn.commit()

        # Insert a row for the rename event
        insert_query = """
            INSERT INTO file_rename_log(old_name, new_name)
            VALUES (%s, %s)
        """
        cur.execute(insert_query, (old_name, new_name))
        conn.commit()


# -------------------------------------------------------------------------
# MAIN STREAMLIT APP
# -------------------------------------------------------------------------
def main():
    st.title("Supabase File Viewer & Editor")

    # STEP 1: Fetch files
    df = fetch_files_from_bucket(BUCKET_NAME)

    if df.empty:
        st.warning("No files found. Are they in a subfolder? "
                   "If so, change 'path' in fetch_files_from_bucket().")
    else:
        st.info(f"Fetched {len(df)} file(s) from bucket '{BUCKET_NAME}'.")

    # STEP 2: Display data_editor with an 'Apply Changes' button
    st.subheader("Edit File Names in the Table Below")

    # We'll keep the row count fixed so users can't add/remove rows in the UI
    edited_df = st.data_editor(
        df,
        num_rows="fixed",
        use_container_width=True,
        height=300,
        column_config={
            "name": "File Name",
            "size": "Size (bytes)",
            "updated_at": "Last Updated",
        },
        key="jobphotos_editor",
    )

    st.caption(
        "You can edit the 'File Name' column above. "
        "Then click 'Apply Changes' to rename those files in Supabase."
    )

    apply_changes = st.button("Apply Changes")
    if apply_changes:
        # Compare each row with original df
        # If the name has changed, rename the file in Supabase
        for i in range(len(df)):
            old_name = df.loc[i, "name"]
            new_name = edited_df.loc[i, "name"]

            if new_name != old_name:
                st.write(f"Renaming '{old_name}' -> '{new_name}'...")
                try:
                    rename_file_in_bucket(BUCKET_NAME, old_name, new_name)
                    st.success(f"Renamed '{old_name}' to '{new_name}' in bucket.")
                    # Also log or update Postgres if you wish
                    example_postgres_query(postgres_conn, old_name, new_name)
                except Exception as e:
                    st.error(f"Error renaming '{old_name}': {e}")

        # Refresh page (optional) to see new file names
        st.experimental_rerun()

    st.divider()

    # STEP 3: Provide row-by-row Download & Delete
    st.subheader("Download or Delete Files")

    for index, row in edited_df.iterrows():
        col1, col2 = st.columns([1, 1])

        file_name = row["name"]

        # Download
        with col1:
            download_label = f"Download '{file_name}'"
            if st.button(download_label, key=f"download_button_{index}"):
                try:
                    file_data = supabase.storage.from_(BUCKET_NAME).download(file_name)
                    st.download_button(
                        label="Confirm Download",
                        data=file_data,
                        file_name=file_name,
                        mime="application/octet-stream",
                        key=f"download_file_{index}"
                    )
                except Exception as e:
                    st.error(f"Error downloading file '{file_name}': {e}")

        # Delete
        with col2:
            delete_label = f"Delete '{file_name}'"
            if st.button(delete_label, key=f"delete_button_{index}"):
                try:
                    supabase.storage.from_(BUCKET_NAME).remove(file_name)
                    st.success(f"Deleted '{file_name}' from bucket.")
                    st.experimental_rerun()
                except Exception as e:
                    st.error(f"Error deleting '{file_name}': {e}")


if __name__ == "__main__":
    main()
