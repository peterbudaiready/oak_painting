import streamlit as st
import psycopg2
from psycopg2 import Binary
import pandas as pd
import base64
import datetime
from io import BytesIO

# Use Streamlit Secrets (Cloud or local)
DATABASE_URL = st.secrets["DATABASE_URL"]

def get_connection():
    return psycopg2.connect(DATABASE_URL)

# Upload document into Supabase
def upload_file_to_supabase(file, note):
    try:
        conn = get_connection()
        cur = conn.cursor()
        query = """
            INSERT INTO documents (filename, filetype, filedata, uploaded_at, note)
            VALUES (%s, %s, %s, %s, %s)
        """
        filename = file.name
        filetype = file.type
        filedata = file.read()
        uploaded_at = datetime.datetime.now()

        cur.execute(query, (filename, filetype, Binary(filedata), uploaded_at, note))
        conn.commit()
        cur.close()
        conn.close()
        return True, "✅ File uploaded successfully!"
    except Exception as e:
        return False, f"❌ Upload error: {e}"

# Fetch documents metadata
def fetch_documents():
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

# Delete a document
def delete_document(doc_id):
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

# Download link
def get_download_link(filedata, filename, filetype):
    b64 = base64.b64encode(filedata).decode()
    href = f'<a href="data:{filetype};base64,{b64}" download="{filename}">📥 Download</a>'
    return href

# Convert binary to base64 image
def binary_to_image_data(filedata, filetype):
    if filetype.startswith("image/"):
        b64 = base64.b64encode(filedata).decode()
        return f"data:{filetype};base64,{b64}"
    return ""

# ---------------- UI ----------------

st.title("📁 Document Manager (Supabase)")

st.markdown("### Upload New Document")
uploaded_file = st.file_uploader("Choose a file")
note_text = st.text_input("Note (optional)")
if st.button("Upload File"):
    if uploaded_file:
        success, msg = upload_file_to_supabase(uploaded_file, note_text)
        if success:
            st.success(msg)
        else:
            st.error(msg)
    else:
        st.warning("Please select a file.")

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
            "Preview": image_preview,
            "Filename": filename,
            "Type": filetype,
            "Uploaded": uploaded_at.strftime("%Y-%m-%d %H:%M"),
            "Note": note,
            "Download": download_html,
            "Delete": f"🗑️ Delete {doc_id}",
            "id": doc_id
        })

    df = pd.DataFrame(records)

    # Display in editable table style (non-editable)
    st.data_editor(
        df[["Preview", "Filename", "Type", "Uploaded", "Note", "Download", "Delete"]],
        column_config={
            "Preview": st.column_config.ImageColumn("Preview", width="small", help="Image preview (if supported)"),
            "Download": st.column_config.LinkColumn("Download"),
        },
        hide_index=True,
        use_container_width=True,
        disabled=True
    )

    # Handle delete action
    for r in records:
        if st.button(r["Delete"]):
            deleted = delete_document(r["id"])
            if deleted:
                st.success(f"Deleted {r['Filename']}")
                st.experimental_rerun()
else:
    st.info("No documents uploaded yet.")
