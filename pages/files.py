import streamlit as st
import psycopg2
from psycopg2 import Binary
import pandas as pd
import base64
import datetime

# Database connection using Streamlit Secrets
DATABASE_URL = st.secrets["DATABASE_URL"]

def get_connection():
    """Establishes a connection to the Supabase database."""
    return psycopg2.connect(DATABASE_URL)

def fetch_documents():
    """Retrieves all documents' metadata from the database."""
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, filename, filetype, uploaded_at, note, filedata FROM documents ORDER BY uploaded_at DESC")
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return rows
    except Exception as e:
        st.error(f"Error fetching documents: {e}")
        return []

def delete_document(doc_id):
    """Deletes a document from the database by its ID."""
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM documents WHERE id = %s", (doc_id,))
        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Delete error: {e}")
        return False

def get_download_link(filedata, filename, filetype):
    """Generates a download link for a file."""
    b64 = base64.b64encode(filedata).decode()
    href = f'<a href="data:{filetype};base64,{b64}" download="{filename}">📥 Download</a>'
    return href

def binary_to_image_data(filedata, filetype):
    """Converts binary data to a base64-encoded image string if the file is an image."""
    if filetype.startswith("image/"):
        b64 = base64.b64encode(filedata).decode()
        return f"data:{filetype};base64,{b64}"
    return ""

# ---------------- UI ----------------

st.title("📁 Document Manager (Supabase)")

st.markdown("---")
st.markdown("### 📑 Uploaded Documents")

# Load and prepare data
documents = fetch_documents()
if documents:
    records = []
    for row in documents:
        doc_id, filename, filetype, uploaded_at, note, filedata = row
        image_preview = binary_to_image_data(filedata, filetype)
        download_html = get_download_link(filedata, filename, filetype)
        records.append({
            "ID": doc_id,
            "Preview": image_preview,
            "Filename": filename,
            "Type": filetype,
            "Uploaded": uploaded_at.strftime("%Y-%m-%d %H:%M"),
            "Note": note,
            "Download": download_html
        })

    df = pd.DataFrame(records)

    # Display in editable table style (non-editable)
    edited_df = st.data_editor(
        df[["Preview", "Filename", "Type", "Uploaded", "Note", "Download"]],
        column_config={
            "Preview": st.column_config.ImageColumn("Preview", width="small", help="Image preview (if supported)"),
            "Download": st.column_config.LinkColumn("Download"),
        },
        hide_index=True,
        use_container_width=True,
        disabled=True
    )

    # Iterate over DataFrame rows to create delete buttons
    for index, row in df.iterrows():
        delete_button_key = f"delete_{row['ID']}"
        if st.button(f"Delete {row['Filename']}", key=delete_button_key):
            if delete_document(row["ID"]):
                st.success(f"Deleted {row['Filename']}")
                st.experimental_rerun()
else:
    st.info("No documents uploaded yet.")
