import streamlit as st
import psycopg2
from psycopg2 import Binary
import datetime

# 🔐 Use Streamlit Cloud's secret manager
DATABASE_URL = st.secrets["DATABASE_URL"]

def upload_file_to_supabase(file):
    """
    Connects to the Supabase database and uploads the file.
    """
    try:
        # Connect using the DATABASE_URL
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()

        insert_query = """
            INSERT INTO documents (filename, filetype, filedata, uploaded_at)
            VALUES (%s, %s, %s, %s)
        """

        filename = file.name
        filetype = file.type
        file_content = file.read()
        uploaded_at = datetime.datetime.now()

        cur.execute(insert_query, (filename, filetype, Binary(file_content), uploaded_at))
        conn.commit()

        cur.close()
        conn.close()
        return True, "✅ File uploaded successfully!"
    except Exception as e:
        return False, f"❌ Error uploading file: {e}"

# ---------- Streamlit UI ----------
st.title("📁 Upload a File to Supabase")

uploaded_file = st.file_uploader("Choose a file to upload")

if st.button("Upload File"):
    if uploaded_file is None:
        st.warning("Please select a file first.")
    else:
        success, message = upload_file_to_supabase(uploaded_file)
        if success:
            st.success(message)
        else:
            st.error(message)
