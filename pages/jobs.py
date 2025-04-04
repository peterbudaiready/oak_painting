import streamlit as st
import psycopg2
from io import BytesIO
from datetime import datetime
import pandas as pd

# ======================================================================
# SUPABASE and DATABASE configuration (DO NOT hardcode secrets in prod!)
# ======================================================================
SUPABASE_URL = "https://pckftxhpmfebxlnfhepq.supabase.co"
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBja2Z0eGhwbWZlYnhsbmZoZXBxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDMzNjQxNjMsImV4cCI6MjA1ODk0MDE2M30.5QhW4hOEpDg1CVHZuC_4-pgQ8LiX4f2EFFBq1R2gBJA"

# Using the session pooler connection (IPv4) as recommended
DATABASE_URL = "postgresql://postgres:pckftxhpmfebxlnfhepq:Aaabacadae1.@aws-0-us-east-1.pooler.supabase.com:5432/postgres?sslmode=require"

# ====================================================
# Database helper functions
# ====================================================
def get_connection():
    conn = psycopg2.connect(DATABASE_URL)
    return conn

# Update the table creation to include a "note" field
def init_db():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id SERIAL PRIMARY KEY,
            filename TEXT,
            filetype TEXT,
            filedata BYTEA,
            uploaded_at TIMESTAMP,
            note TEXT
        )
    """)
    conn.commit()
    cur.close()
    conn.close()

def upload_document(file, filename, filetype, note):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO documents (filename, filetype, filedata, uploaded_at, note) VALUES (%s, %s, %s, %s, %s)",
        (filename, filetype, file.getvalue(), datetime.now(), note)
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

def edit_document(doc_id, filename, filetype, note):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE documents SET filename = %s, filetype = %s, note = %s, uploaded_at = %s WHERE id = %s",
        (filename, filetype, note, datetime.now(), doc_id)
    )
    conn.commit()
    cur.close()
    conn.close()

def get_documents():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, filename, filetype, filedata, uploaded_at, note FROM documents ORDER BY uploaded_at DESC")
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
# Upload Document with st.data_editor
# -----------------------
if menu == "Upload Document":
    st.header("Upload a New Document")
    uploaded_file = st.file_uploader("Choose a file", type=["pdf", "jpeg", "png", "docx"])
    if uploaded_file is not None:
        st.write("**File details:**", {"filename": uploaded_file.name, "type": uploaded_file.type})
        # Prepare a one-row DataFrame for editing metadata
        new_doc_df = pd.DataFrame({
            "filename": [uploaded_file.name],
            "filetype": [uploaded_file.type],
            "note": [""]
        })
        # Allow the user to edit the metadata using st.data_editor
        edited_new_doc = st.data_editor(new_doc_df, num_rows="fixed", hide_index=True, key="upload_editor")
        if st.button("Upload Document"):
            # Retrieve edited values
            filename = edited_new_doc.loc[0, "filename"]
            filetype = edited_new_doc.loc[0, "filetype"]
            note = edited_new_doc.loc[0, "note"]
            try:
                upload_document(uploaded_file, filename, filetype, note)
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
            doc_id, filename, filetype, filedata, uploaded_at, note = doc
            st.subheader(f"{filename} (ID: {doc_id})")
            st.write("Uploaded at:", uploaded_at)
            st.write("Note:", note)
            if filetype.startswith("image"):
                st.image(filedata)
            else:
                st.download_button("Download File", data=filedata, file_name=filename)
            st.markdown("---")
    else:
        st.info("No documents found.")

# -----------------------
# Edit Document with st.data_editor
# -----------------------
elif menu == "Edit Document":
    st.header("Edit Existing Documents")
    documents = get_documents()
    if documents:
        # Create a DataFrame from documents. Convert filedata to hex string for display.
        df_docs = pd.DataFrame(documents, columns=["id", "filename", "filetype", "filedata", "uploaded_at", "note"])
        df_docs["filedata"] = df_docs["filedata"].apply(lambda x: x.hex() if x is not None else "")
        # Display the data editor widget.
        edited_df = st.data_editor(
            df_docs,
            column_config={
                "id": {"disabled": True},
                "filedata": {"disabled": True, "label": "File Data (hex)"},
                "uploaded_at": {"disabled": True, "label": "Uploaded At"}
            },
            num_rows="fixed",
            hide_index=True,
            key="edit_editor"
        )
        if st.button("Save Changes"):
            # Loop over the rows and update changes
            for idx, row in edited_df.iterrows():
                doc_id = row["id"]
                filename = row["filename"]
                filetype = row["filetype"]
                note = row["note"]
                try:
                    edit_document(doc_id, filename, filetype, note)
                except Exception as e:
                    st.error(f"Error updating document ID {doc_id}: {e}")
            st.success("Changes saved successfully!")
    else:
        st.info("No documents found.")

# -----------------------
# Delete Document (unchanged)
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
