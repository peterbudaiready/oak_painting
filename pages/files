import streamlit as st
import psycopg2
from psycopg2 import sql
from psycopg2.extensions import AsIs
from dotenv import load_dotenv
import os
import datetime
import pandas as pd

# Load environment variables from .env
load_dotenv()

# Fetch connection variables
USER = os.getenv("user")
PASSWORD = os.getenv("password")
HOST = os.getenv("host")
PORT = os.getenv("port")
DBNAME = os.getenv("dbname")

def get_connection():
    """Create and return a new database connection."""
    try:
        connection = psycopg2.connect(
            user=USER,
            password=PASSWORD,
            host=HOST,
            port=PORT,
            dbname=DBNAME
        )
        return connection
    except Exception as e:
        st.error("Failed to connect to the database.")
        st.error(e)
        return None

st.title("Document Manager")

st.markdown("### Upload a Document")
# File uploader widget: adjust allowed types as needed.
uploaded_file = st.file_uploader("Choose a document to upload", type=[
    "pdf", "docx", "txt", "png", "jpg", "jpeg", "gif", "csv", "xlsx", "zip", "mp3", "mp4"
])
note_text = st.text_input("Enter a note for this document (optional)")

if st.button("Upload Document"):
    if uploaded_file is not None:
        file_bytes = uploaded_file.read()
        file_name = uploaded_file.name
        file_type = uploaded_file.type
        uploaded_at = datetime.datetime.now()  # Current timestamp

        conn = get_connection()
        if conn:
            cursor = conn.cursor()
            try:
                insert_query = """
                    INSERT INTO documents (filename, filetype, filedata, uploaded_at, note)
                    VALUES (%s, %s, %s, %s, %s)
                """
                cursor.execute(insert_query, (
                    file_name,
                    file_type,
                    psycopg2.Binary(file_bytes),
                    uploaded_at,
                    note_text
                ))
                conn.commit()
                st.success("Document uploaded successfully!")
            except Exception as e:
                st.error("Error uploading document:")
                st.error(e)
            finally:
                cursor.close()
                conn.close()
    else:
        st.warning("Please select a file to upload.")

st.markdown("---")
st.markdown("### Uploaded Documents")

def fetch_documents():
    conn = get_connection()
    if conn:
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT id, filename, filetype, uploaded_at, note
                FROM documents
                ORDER BY uploaded_at DESC
            """)
            rows = cursor.fetchall()
            return rows
        except Exception as e:
            st.error("Error fetching documents:")
            st.error(e)
            return []
        finally:
            cursor.close()
            conn.close()
    return []

rows = fetch_documents()
if rows:
    df = pd.DataFrame(rows, columns=["ID", "Filename", "Filetype", "Uploaded At", "Note"])
    st.dataframe(df)
else:
    st.info("No documents found.")

st.markdown("---")
st.markdown("### Delete a Document")

# Fetch documents for deletion options.
def fetch_document_options():
    conn = get_connection()
    options = {}
    if conn:
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT id, filename FROM documents ORDER BY uploaded_at DESC")
            rows = cursor.fetchall()
            for row in rows:
                # Create a label like "123 - myfile.pdf" mapping to id 123.
                options[f"{row[0]} - {row[1]}"] = row[0]
        except Exception as e:
            st.error("Error fetching documents for deletion:")
            st.error(e)
        finally:
            cursor.close()
            conn.close()
    return options

doc_options = fetch_document_options()

if doc_options:
    selected_doc = st.selectbox("Select a document to delete", options=list(doc_options.keys()))
    if st.button("Delete Document"):
        doc_id = doc_options[selected_doc]
        conn = get_connection()
        if conn:
            cursor = conn.cursor()
            try:
                cursor.execute("DELETE FROM documents WHERE id = %s", (doc_id,))
                conn.commit()
                st.success("Document deleted successfully!")
            except Exception as e:
                st.error("Error deleting document:")
                st.error(e)
            finally:
                cursor.close()
                conn.close()
else:
    st.info("No documents available for deletion.")
