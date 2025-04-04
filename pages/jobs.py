import streamlit as st
import psycopg2
from io import BytesIO
from datetime import datetime

# ======================================================================
# SUPABASE and DATABASE configuration (DO NOT hardcode secrets in prod!)
# ======================================================================
SUPABASE_URL = "https://pckftxhpmfebxlnfhepq.supabase.co"
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBja2Z0eGhwbWZlYnhsbmZoZXBxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDMzNjQxNjMsImV4cCI6MjA1ODk0MDE2M30.5QhW4hOEpDg1CVHZuC_4-pgQ8LiX4f2EFFBq1R2gBJA"
# For a direct connection (replace [YOUR-PASSWORD] with your actual password)
DATABASE_URL = "postgresql://postgres:[YOUR-PASSWORD]@db.pckftxhpmfebxlnfhepq.supabase.co:5432/postgres"

# ====================================================
# Database helper functions
# ====================================================
def get_connection():
    conn = psycopg2.connect(DATABASE_URL)
    return conn

def init_db():
    conn = get_connection()
    cur = conn.cursor()
    # Create a table for storing documents if it does not already exist
    cur.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id SERIAL PRIMARY KEY,
            filename TEXT,
            filetype TEXT,
            filedata BYTEA,
            uploaded_at TIMESTAMP
        )
    """)
    conn.commit()
    cur.close()
    conn.close()

def upload_document(file, filename, filetype):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO documents (filename, filetype, filedata, uploaded_at) VALUES (%s, %s, %s, %s)",
        (filename, filetype, file.getvalue(), datetime.now())
    )
    conn.commit()
    cur.close()
    conn.close()

def delete_document(doc_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM documents WHERE id = %s", (doc_id,))
    conn.commit()
    cur.close()
    conn.close()

def edit_document(doc_id, filename, filetype, file):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE documents SET filename = %s, filetype = %s, filedata = %s, uploaded_at = %s WHERE id = %s",
        (filename, filetype, file.getvalue(), datetime.now(), doc_id)
    )
    conn.commit()
    cur.close()
    conn.close()

def get_documents():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, filename, filetype, filedata, uploaded_at FROM documents ORDER BY uploaded_at DESC")
    docs = cur.fetchall()
    cur.close()
    conn.close()
    return docs

# Initialize the database table if it doesn't exist
init_db()

# ====================================================
# Streamlit UI
# ====================================================
st.set_page_config(page_title="Supabase Document Manager", layout="wide")
st.markdown(
    """
    <style>
    .title {
        font-size:40px;
        font-weight: bold;
        text-align: center;
        margin-bottom: 20px;
    }
    .section {
        margin: 20px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="title">Supabase Document Manager</div>', unsafe_allow_html=True)

# Sidebar menu for operations
menu = st.sidebar.radio("Select an operation", 
                         ["Upload Document", "View Documents", "Edit Document", "Delete Document"])

# -----------------------
# Upload Document
# -----------------------
if menu == "Upload Document":
    st.header("Upload a New Document")
    uploaded_file = st.file_uploader("Choose a file", type=["pdf", "jpeg", "png", "docx"])
    if uploaded_file is not None:
        st.write("**File details:**", {"filename": uploaded_file.name, "type": uploaded_file.type})
        if st.button("Upload"):
            try:
                upload_document(uploaded_file, uploaded_file.name, uploaded_file.type)
                st.success("Document uploaded successfully!")
            except Exception as e:
                st.error(f"Error uploading document: {e}")

# -----------------------
# View Documents
# -----------------------
elif menu == "View Documents":
    st.header("View Uploaded Documents")
    documents = get_documents()
    if documents:
        for doc in documents:
            doc_id, filename, filetype, filedata, uploaded_at = doc
            st.subheader(f"{filename} (ID: {doc_id})")
            st.write("Uploaded at:", uploaded_at)
            # Show image preview if the file is an image
            if filetype.startswith("image"):
                st.image(filedata)
            else:
                # For other file types, offer a download button
                st.download_button("Download File", data=filedata, file_name=filename)
            st.markdown("---")
    else:
        st.info("No documents found.")

# -----------------------
# Edit Document
# -----------------------
elif menu == "Edit Document":
    st.header("Edit an Existing Document")
    documents = get_documents()
    if documents:
        # Create a dictionary for selection options
        doc_options = {f"{doc[1]} (ID: {doc[0]})": doc for doc in documents}
        selected_doc_label = st.selectbox("Select a document to edit", list(doc_options.keys()))
        selected_doc = doc_options[selected_doc_label]
        new_filename = st.text_input("New filename", value=selected_doc[1])
        st.write("If you wish to update the file, please upload a new one below. Otherwise the current file will remain.")
        new_file = st.file_uploader("Upload new file (optional)", key="edit")
        if st.button("Update Document"):
            try:
                if new_file is not None:
                    file_to_save = new_file
                    new_filetype = new_file.type
                else:
                    file_to_save = BytesIO(selected_doc[3])
                    new_filetype = selected_doc[2]
                edit_document(selected_doc[0], new_filename, new_filetype, file_to_save)
                st.success("Document updated successfully!")
            except Exception as e:
                st.error(f"Error updating document: {e}")
    else:
        st.info("No documents found.")

# -----------------------
# Delete Document
# -----------------------
elif menu == "Delete Document":
    st.header("Delete a Document")
    documents = get_documents()
    if documents:
        doc_options = {f"{doc[1]} (ID: {doc[0]})": doc for doc in documents}
        selected_doc_label = st.selectbox("Select a document to delete", list(doc_options.keys()))
        selected_doc = doc_options[selected_doc_label]
        if st.button("Delete Document"):
            try:
                delete_document(selected_doc[0])
                st.success("Document deleted successfully!")
            except Exception as e:
                st.error(f"Error deleting document: {e}")
    else:
        st.info("No documents found.")
