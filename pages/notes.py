import streamlit as st
import sqlite3
from auth import login_popup  # Import your authentication function

# Set page configuration
st.set_page_config(
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Define a CSS snippet to hide Streamlit's default menu, footer, and header
hide_st_style = """
<style>
#MainMenu {visibility: hidden;}     /* Hide the hamburger menu */
footer {visibility: hidden;}        /* Hide the “Made with Streamlit” footer */
header {visibility: hidden;}        /* Hide the header */
</style>
"""
st.markdown(hide_st_style, unsafe_allow_html=True)

# Ensure authentication before rendering any UI
login_popup()

# Initialize the database
def init_db():
    conn = sqlite3.connect("notes.db")
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# Function to load the latest note from the database
def load_latest_note():
    conn = sqlite3.connect("notes.db")
    c = conn.cursor()
    c.execute("SELECT content FROM notes ORDER BY id DESC LIMIT 1")
    note = c.fetchone()
    conn.close()
    return note[0] if note else ""

# Function to save a new note to the database
def save_note(content):
    conn = sqlite3.connect("notes.db")
    c = conn.cursor()
    c.execute("INSERT INTO notes (content) VALUES (?)", (content,))
    conn.commit()
    conn.close()

# Initialize the database
init_db()

# Load the latest note
latest_note = load_latest_note()

# Title of the app
st.title("📝 Notes App")

# Text area for user input
note_content = st.text_area(
    "Write your notes here:",
    value=latest_note,
    height=300,
    placeholder="Start typing your notes here..."
)

# Save button
if st.button("Save Note"):
    save_note(note_content)
    st.success("Note saved successfully!")
