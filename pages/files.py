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

def binary_to_image_data(filedata, filetype):
    if filetype.startswith("image/"):
        b64 = base64.b64encode(filedata).decode()
        return f"data:{filetype};base64,{b64}"
    return ""

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
        records.append({
            "Preview": image_preview,
            "Filename": filename,
            "Type": filetype,
            "Uploaded": uploaded_at.strftime("%Y-%m-%d %H:%M"),
            "Note": note,
        })

    df = pd.DataFrame(records)

    st.data_editor(
        df[["Preview", "Filename", "Type", "Uploaded", "Note"]],
        column_config={
            "Preview": st.column_config.ImageColumn("Preview", width="small"),
        },
        hide_index=True,
        use_container_width=True,
        disabled=True
    )

    st.markdown("### 📥 Download Links")
    for row in documents:
        doc_id, filename, filetype, uploaded_at, note, filedata = row
        b64 = base64.b64encode(filedata).decode()
        href = f'<a href="data:{filetype};base64,{b64}" download="{filename}">📥 Download {filename}</a>'
        st.markdown(href, unsafe_allow_html=True)
else:
    st.info("No documents uploaded yet.")

# --- Button triggers ---
if st.button("Upload Document"):
    st.session_state.show_upload_dialog = True

if st.button("Delete Document"):
    st.session_state.show_delete_dialog = True

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

# --- Delete Dialog ---
@st.dialog("Delete Document")
def delete_dialog():
    documents = fetch_documents()
    if not documents:
        st.warning("No documents to delete.")
        return

    doc_id_map = {
        f"{filename} ({uploaded_at.strftime('%Y-%m-%d')})": doc_id
        for doc_id, filename, _, uploaded_at, _, _ in documents
    }

    selected = st.selectbox("Select document to delete", list(doc_id_map.keys()))
    if st.button("Delete"):
        deleted = delete_document(doc_id_map[selected])
        if deleted:
            st.success(f"Deleted '{selected}'")
            st.session_state.show_delete_dialog = False
            st.rerun()
        else:
            st.error("Delete failed.")
    if st.button("Cancel"):
        st.session_state.show_delete_dialog = False
        st.rerun()

# --- Trigger dialogs ---
if st.session_state.get("show_upload_dialog", False):
    upload_dialog()

if st.session_state.get("show_delete_dialog", False):
    delete_dialog()
