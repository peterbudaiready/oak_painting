import streamlit as st

# Define a CSS snippet to hide Streamlit's default menu, footer, and header
hide_st_style = """
<style>
#MainMenu {visibility: hidden;}     /* Hide the hamburger menu */
footer {visibility: hidden;}        /* Hide the “Made with Streamlit” footer */
header {visibility: hidden;}        /* Hide the header */
</style>
"""

def login_popup():
    """Ensures authentication is checked globally across all pages."""
    correct_password = "Betega50?"

    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    if not st.session_state["authenticated"]:
        st.title("🔒 Secure Login")
        with st.form("login_form"):
            password = st.text_input("password", type="password")
            submit = st.form_submit_button("Login")

            if submit:
                if password == correct_password:
                    st.session_state["authenticated"] = True
                    st.rerun()  # Corrected from st.experimental_rerun()
                else:
                    st.error("Incorrect password. Try again.")
        st.stop()  # Stop rendering anything else if not authenticated
