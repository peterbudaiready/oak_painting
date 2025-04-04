import streamlit as st
import pandas as pd
import sqlite3
import os
import datetime

# Database file and table names.
DB_FILE = "data.db"
TASKS_TABLE = "tasks"
EXPENSES_TABLE = "expenses"

def init_db():
    """Initialize the SQLite database with tasks and expenses tables if they do not exist."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # Create tasks table with expected columns.
    c.execute(f"""
        CREATE TABLE IF NOT EXISTS {TASKS_TABLE} (
            Note TEXT,
            Web TEXT,
            Done BOOLEAN,
            Priority TEXT,
            Date_Created DATE,
            Deadline DATE,
            Progress INTEGER
        )
    """)
    c.execute(f"""
        CREATE TABLE IF NOT EXISTS {EXPENSES_TABLE} (
            Name TEXT,
            Web TEXT,
            Date DATE,
            Type TEXT,
            Price INTEGER
        )
    """)
    conn.commit()
    conn.close()

def load_tasks():
    """Load tasks from the database into a DataFrame."""
    if os.path.exists(DB_FILE):
        conn = sqlite3.connect(DB_FILE)
        try:
            df = pd.read_sql_query(f"SELECT * FROM {TASKS_TABLE}", conn)
        except Exception as e:
            st.error(f"Error loading tasks: {e}")
            df = pd.DataFrame(columns=["Note", "Web", "Done", "Priority", "Date_Created", "Deadline", "Progress"])
        conn.close()
        return df
    else:
        return pd.DataFrame(columns=["Note", "Web", "Done", "Priority", "Date_Created", "Deadline", "Progress"])

def load_expenses():
    """Load expenses from the database into a DataFrame."""
    if os.path.exists(DB_FILE):
        conn = sqlite3.connect(DB_FILE)
        try:
            df = pd.read_sql_query(f"SELECT * FROM {EXPENSES_TABLE}", conn)
        except Exception as e:
            st.error(f"Error loading expenses: {e}")
            df = pd.DataFrame(columns=["Name", "Web", "Date", "Type", "Price"])
        conn.close()
        return df
    else:
        return pd.DataFrame(columns=["Name", "Web", "Date", "Type", "Price"])

def save_tasks(df):
    """Save the tasks DataFrame to the database."""
    conn = sqlite3.connect(DB_FILE)
    df.to_sql(TASKS_TABLE, conn, if_exists="replace", index=False)
    conn.commit()
    conn.close()

def save_expenses(df):
    """Save the expenses DataFrame to the database."""
    conn = sqlite3.connect(DB_FILE)
    df.to_sql(EXPENSES_TABLE, conn, if_exists="replace", index=False)
    conn.commit()
    conn.close()

def compute_progress(row, current_date):
    """
    Compute progress as a percentage based on the task's creation date, deadline,
    and the current system date.
    - Returns 0% if current_date is on or before the creation date.
    - Returns 100% if current_date is on or after the deadline.
    - Otherwise, computes the elapsed percentage between the two dates.
    """
    try:
        date_created = pd.to_datetime(row["Date_Created"])
        deadline = pd.to_datetime(row["Deadline"])
        current_date = pd.to_datetime(current_date)
        if pd.isnull(date_created) or pd.isnull(deadline):
            return 0
        if current_date <= date_created:
            return 0
        elif current_date >= deadline:
            return 100
        else:
            progress = ((current_date - date_created) / (deadline - date_created)) * 100
            return round(max(0, min(100, progress)))
    except Exception:
        return 0

# Initialize the database and load existing data.
init_db()
tasks_df = load_tasks()
expenses_df = load_expenses()

# --- Ensure tasks_df has all expected columns ---
expected_task_columns = {
    "Note": "",
    "Web": "",
    "Done": False,
    "Priority": "Low",
    "Date_Created": pd.Timestamp.today().date(),  # Automatically set on creation.
    "Deadline": (pd.Timestamp.today().date() + datetime.timedelta(days=7)),
    "Progress": 0
}
for col, default_val in expected_task_columns.items():
    if col not in tasks_df.columns:
        tasks_df[col] = default_val

# --- Ensure expenses_df has all expected columns ---
expected_expense_columns = {
    "Name": "",
    "Web": "",
    "Date": pd.Timestamp.today().date(),
    "Type": "one",
    "Price": 0
}
for col, default_val in expected_expense_columns.items():
    if col not in expenses_df.columns:
        expenses_df[col] = default_val

# Convert date columns in tasks to proper date objects.
tasks_df["Date_Created"] = pd.to_datetime(tasks_df["Date_Created"], errors="coerce").dt.date
tasks_df["Deadline"] = pd.to_datetime(tasks_df["Deadline"], errors="coerce").dt.date

# Convert the date column in expenses to proper date objects.
expenses_df["Date"] = pd.to_datetime(expenses_df["Date"], errors="coerce").dt.date

# --- Tasks Section ---

# Use system current date.
system_current_date = pd.Timestamp.today().date()

# If tasks_df is empty, initialize it with one default row.
if tasks_df.empty:
    today_date = system_current_date
    default_deadline = today_date + datetime.timedelta(days=7)
    tasks_df = pd.DataFrame({
        "Note": [""],
        "Web": [""],
        "Done": [False],
        "Priority": ["Low"],
        "Date_Created": [today_date],
        "Deadline": [default_deadline],
        "Progress": [0]
    })

# For any rows missing a creation date, set it to the system current date.
tasks_df["Date_Created"] = tasks_df["Date_Created"].apply(lambda d: d if pd.notnull(d) else system_current_date)

# Compute progress for each task using the system current date.
tasks_df["Progress"] = tasks_df.apply(lambda row: compute_progress(row, system_current_date), axis=1)

# Title for the tasks section.
st.title("Task Manager")

# Configure columns for the tasks editor.
# The "Date_Created" field is hidden from the user.
tasks_column_config = {
    "Note": "Note",
    "Web": st.column_config.LinkColumn("Web", help="Enter a valid URL"),
    "Done": "Done",
    "Priority": st.column_config.SelectboxColumn("Priority", options=["Low", "Mid", "High"]),
    "Deadline": st.column_config.DateColumn("Deadline", help="Task deadline"),
    "Progress": st.column_config.ProgressColumn(
        "Progress",
        help="Progress from creation to deadline (calculated automatically)",
        min_value=0,
        max_value=100,
        format="plain"
    ),
}
# Specify column order to hide "Date_Created".
tasks_column_order = ["Note", "Web", "Done", "Priority", "Deadline", "Progress"]

# Display the tasks data editor (allowing dynamic row additions).
edited_tasks_df = st.data_editor(
    tasks_df,
    column_config=tasks_column_config,
    column_order=tasks_column_order,
    num_rows="dynamic",
    use_container_width=True,
    key="tasks_editor"
)

# For any new rows missing a creation date, fill in with the current system date.
edited_tasks_df["Date_Created"] = edited_tasks_df["Date_Created"].apply(lambda d: d if pd.notnull(d) else system_current_date)

# Recompute the progress column after any edits using the system current date.
edited_tasks_df["Progress"] = edited_tasks_df.apply(lambda row: compute_progress(row, system_current_date), axis=1)

if st.button("Save Task Changes"):
    save_tasks(edited_tasks_df)
    st.success("Tasks saved successfully!")

st.markdown("---")

# --- Expenses Section ---
st.header("Expenses")

# If expenses_df is empty, initialize it with one blank row.
if expenses_df.empty:
    expenses_df = pd.DataFrame({
        "Name": [""],
        "Web": [""],
        "Date": [system_current_date],
        "Type": ["one"],
        "Price": [0]
    })

# Configure columns for the expenses editor.
expenses_column_config = {
    "Name": "Name",
    "Web": st.column_config.LinkColumn("Web", help="Enter a valid URL"),
    "Date": st.column_config.DateColumn("Date", help="Expense date"),
    "Type": st.column_config.SelectboxColumn("Type", options=["one", "monthly"]),
    "Price": st.column_config.NumberColumn("Price", help="Price in USD", format="$%d"),
}

# Display the expenses data editor (allowing dynamic row additions).
edited_expenses_df = st.data_editor(
    expenses_df,
    column_config=expenses_column_config,
    num_rows="dynamic",
    use_container_width=True,
    key="expenses_editor"
)

if st.button("Save Expenses Changes"):
    save_expenses(edited_expenses_df)
    st.success("Expenses saved successfully!")

st.markdown("---")

# --- Expenses Chart (Last 30 Days) ---
st.header("Expenses Over Last 30 Days")

# Convert the "Date" column in the edited expenses DataFrame to datetime for filtering.
edited_expenses_df["Date"] = pd.to_datetime(edited_expenses_df["Date"], errors="coerce")
system_current_ts = pd.Timestamp(system_current_date)
thirty_days_ago = system_current_ts - pd.Timedelta(days=30)
filtered_expenses = edited_expenses_df[edited_expenses_df["Date"] >= thirty_days_ago]

if not filtered_expenses.empty:
    chart_data = (
        filtered_expenses
        .sort_values("Date")
        .set_index("Date")["Price"]
    )
    st.line_chart(chart_data)
else:
    st.info("No expenses data in the last 30 days to display in the chart.")
