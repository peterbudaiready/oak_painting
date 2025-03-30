import streamlit as st
import pandas as pd
from supabase import create_client, Client

# -------------------------------------------------------------------------
# HARD-CODED SUPABASE CREDENTIALS (FOR DEMO/TEST ONLY!)
# -------------------------------------------------------------------------
SUPABASE_URL = "https://pckftxhpmfebxlnfhepq.supabase.co"
SUPABASE_ANON_KEY = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9." 
    "eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBja2Z0eGhwbWZlYnhsbmZoZXBxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDMzNjQxNjMsImV4cCI6MjA1ODk0MDE2M30."
    "5QhW4hOEpDg1CVHZuC_4-pgQ8LiX4f2EFFBq1R2gBJA"
)

# Supabase storage bucket name
BUCKET_NAME = "jobphotos"

# This is the provided Postgres URI to the Supabase database.
# You only need this if you're connecting directly to Postgres 
# (for example, with psycopg2 or SQLAlchemy). Not strictly required 
# for basic storage bucket calls via supabase-py. 
POSTGRES_URI = "postgresql://postgres:[9607222009Loko.]@db.pckftxhpmfebxlnfhepq.supabase.co:5432/postgres"


# -------------------------------------------------------------------------
# INIT CONNECTION
# -------------------------------------------------------------------------
@st.cache_resource
def init_connection() -> Client:
    """
    Creates and caches the Supabase client.
    """
    supabase_client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    return supabase_client

supabase = init_connection()


# -------------------------------------------------------------------------
# FETCH FILES FROM BUCKET
# -------------------------------------------------------------------------
def fetch_files_from_bucket(bucket_name: str) -> pd.DataFrame:
    """
    Fetches the list of objects from the given Supabase Storage bucket.
    Returns a DataFrame of file info (name, size, updated_at, etc.).
    """
    response = supabase.storage.from_(bucket_name).list()
    if not response:
        return pd.DataFrame(columns=["name", "size", "updated_at"])

    file_list = []
    for item in response:
        file_list.append({
            "name": item["name"],
            "size": item["metadata"].get("size", None) if "metadata" in item else None,
            "updated_at": item.get("updated_at", None),
        })
    return pd.DataFrame(file_list)


# -------------------------------------------------------------------------
# MAIN STREAMLIT APP
# -------------------------------------------------------------------------
def main():
    st.title("Supabase File Viewer with st.data_editor")

    # Fetch files from the specified bucket
    df = fetch_files_from_bucket(BUCKET_NAME)

    # Display them in an editable table
    edited_df = st.data_editor(
        df,
        num_rows="fixed",  # Can't add or remove rows in the editor
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
        "Table is editable, but changes here do not automatically rename/update files in Supabase. "
        "You would need to add additional logic to push changes back to Supabase."
    )
    
    st.divider()
    st.subheader("Actions on each file")

    # Loop through rows to provide buttons for download & delete
    for index, row in edited_df.iterrows():
        col1, col2 = st.columns([1, 1])

        # Download button
        with col1:
            file_name = row["name"]
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

        # Delete button
        with col2:
            delete_label = f"Delete '{row['name']}'"
            if st.button(delete_label, key=f"delete_button_{index}"):
                try:
                    supabase.storage.from_(BUCKET_NAME).remove(row["name"])
                    st.success(f"Deleted '{row['name']}' from bucket.")
                    st.experimental_rerun()
                except Exception as e:
                    st.error(f"Error deleting '{row['name']}': {e}")


if __name__ == "__main__":
    main()
