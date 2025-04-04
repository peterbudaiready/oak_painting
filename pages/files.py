import streamlit as st
import psycopg2
from psycopg2 import Binary
from dotenv import load_dotenv
import os
import datetime

# Load environment variables from .env
load_dotenv()

# Retrieve the connection string from the environment
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    st.error("DATABASE_URL not found in environment.")
    st.stop()

def upload_file_to_supabase(file, note):
    """
    Connects to the Supabase database and uploads the file.
    """
    try:
        # Establish a connection using the connection string
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        # Prepare the insert query (assumes the documents table exists)
        insert_query = """
            INSERT INTO documents (filename, filetype, filedata, uploaded_at, note)
            VALUES (%s, %s, %s, %s, %s)
        """
        # Read file attributes and content
        filename = file.name
        filetype = file.type
        file_content = file.read()
        uploaded_at = datetime.datetime.now()

        # Execute the insert query
        cur.execute(insert_query, (filename, filetype, Binary(file_content), uploaded_at, note))
        conn.commit()
        cur.close()
        conn.close()
        return True, "File uploaded successfully!"
    except Exception as e:
        return False, f"Error: {e}"

# --- Streamlit UI ---
st.title("Upload a File to Supabase")

# File uploader widget
uploaded_file = st.file_uploader("Choose a file to upload")
note_text = st.text_input("Enter a note (optional)")

if st.button("Upload File"):
    if uploaded_file is None:
        st.warning("Please select a file.")
    else:
        success, message = upload_file_to_supabase(uploaded_file, note_text)
        if success:
            st.success(message)
        else:
            st.error(message)
