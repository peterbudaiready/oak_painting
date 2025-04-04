import streamlit as st
import pandas as pd
import sqlite3
import os

# Name of the local database file and table name.
DB_FILE = "data.db"
TABLE_NAME = "tasks"

def init_db():
    """Initialize the SQLite database and create the table if it does not exist."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute(f"""
        CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
            Note TEXT,
            Web TEXT,
            Done BOOLEAN,
            Priority TEXT
        )
    """)
    conn.commit()
    conn.close()

def load_data():
    """Load data from the local SQLite database into a pandas DataFrame."""
    if os.path.exists(DB_FILE):
        conn = sqlite3.connect(DB_FILE)
        try:
            df = pd.read_sql_query(f"SELECT * FROM {TABLE_NAME}", conn)
        except Exception as e:
            st.error(f"Error loading data: {e}")
            df = pd.DataFrame(columns=["Note", "Web", "Done", "Priority"])
        conn.close()
        return df
    else:
        return pd.DataFrame(columns=["Note", "Web", "Done", "Priority"])

def save_data(df):
    """Save the DataFrame to the SQLite database."""
    conn = sqlite3.connect(DB_FILE)
    # Overwrite the table with the new DataFrame data.
    df.to_sql(TABLE_NAME, conn, if_exists="replace", index=False)
    conn.commit()
    conn.close()

# Initialize DB (creates it if necessary) and load the current data.
init_db()
df = load_data()

# If there is no data yet, start with one blank row.
if df.empty:
    df = pd.DataFrame({
        "Note": [""],
        "Web": [""],
        "Done": [False],
        "Priority": ["Low"]
    })

# Configure the columns for the data editor.
column_config = {
    "Note": "Note",  # Text column – no special config needed.
    "Web": st.column_config.LinkColumn("Web", help="Enter a valid URL"),
    # The "Done" column is a boolean; Streamlit automatically renders booleans as checkboxes.
    "Done": "Done",
    # Use a selectbox for Priority with specific options.
    "Priority": st.column_config.SelectboxColumn("Priority", options=["Low", "Mid", "High"]),
}

# Display the data editor. Allow users to add or delete rows with num_rows="dynamic".
edited_df = st.data_editor(
    df,
    column_config=column_config,
    num_rows="dynamic",
    use_container_width=True
)

# A simple button to save changes back to the database.
if st.button("Save Changes"):
    save_data(edited_df)
    st.success("Data saved to the database!")
