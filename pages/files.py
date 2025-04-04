import streamlit as st
import psycopg2
from psycopg2 import Binary
import pandas as pd
import base64
import datetime

# Use Streamlit Secrets for database connection
DATABASE_URL = st.secrets["DATABASE_URL"]

def get_connection():
    return psycopg2.connect(DATABASE_URL)

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

def binary_to_image_data(filedata, filetype):
    if filetype.startswith("image/"):
        b64 = base64.b64encode(filedata).decode()
        return f"data:{filetype};base64,{b64}"
    return ""

def generate_download_link(filedata, filename, filetype):
    b64 = base64.b64encode(filedata).decode()
    return f'<a href="data:{filetype};base64,{b64}" download="{filename}">📥 Download</a>'

# ---------------- UI ----------------

st.title("📁 Document Manager (Supabase)")

# --- Documents Table ---
st.markdown("---")
st.markdown("### 📑 Uploaded Documents")

documents = fetch_documents()
if documents:
    records = []
    for row in documents:
        doc_id, filename, filetype, uploaded_at, note, filedata = row
        image_preview = binary_to_image_data(filedata, filetype)
        download_link = generate_download_link(filedata, filename, filetype)
        records.append({
            "Preview": image_preview,
            "Filename": filename,
            "Type": filetype,
            "Uploaded": uploaded_at.strftime("%Y-%m-%d %H:%M"),
            "Note": note,
            "Download": download_link
        })

    df = pd.DataFrame(records)

    st.data_editor(
        df[["Preview", "Filename", "Type", "Uploaded", "Note", "Download"]],
        column_config={
            "Preview": st.column_config.ImageColumn("Preview", width="small"),
            "Download": st.column_config.LinkColumn("Download")
        },
        hide_index=True,
        use_container_width=True,
        disabled=True
    )
else:
    st.info("No documents uploaded yet.")

# --- Button trigger ---
if st.button("Upload Document"):
    st.session_state.show_upload_dialog = True

# --- Upload Dialog ---
@st.dialog("Upload New Document")
def upload_dialog():
    uploaded_file = st.file_uploader("Choose a file")
    note_text = st.text_input("Note (optional)")
    if st.button("Upload"):
        if uploaded_file:
            success, msg = upload_file_to_supabase(uploaded_file, note_text)
            if success:
                st.success(msg)
                st.session_state.show_upload_dialog = False
                st.rerun()
            else:
                st.error(msg)
        else:
            st.warning("Please select a file.")
    if st.button("Cancel"):
        st.session_state.show_upload_dialog = False
        st.rerun()

# --- Trigger dialogs ---
if st.session_state.get("show_upload_dialog", False):
    upload_dialog()
