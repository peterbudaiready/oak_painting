import streamlit as st
import psycopg2
from psycopg2 import Binary
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
    table_html = """
    <table>
        <thead>
            <tr>
                <th style="text-align: left;">Filename</th>
                <th style="text-align: left;">Type</th>
                <th style="text-align: left;">Uploaded</th>
                <th style="text-align: left;">Note</th>
                <th style="text-align: left;">Download</th>
            </tr>
        </thead>
        <tbody>
    """

    for row in documents:
        doc_id, filename, filetype, uploaded_at, note, filedata = row
        download_link = generate_download_link(filedata, filename, filetype)

        table_html += f"""
        <tr>
            <td>{filename}</td>
            <td>{filetype}</td>
            <td>{uploaded_at.strftime('%Y-%m-%d %H:%M')}</td>
            <td>{note or ""}</td>
            <td>{download_link}</td>
        </tr>
        """

    table_html += "</tbody></table>"

    st.markdown(table_html, unsafe_allow_html=True)
else:
    st.info("No documents uploaded yet.")

# --- Upload Button ---
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
