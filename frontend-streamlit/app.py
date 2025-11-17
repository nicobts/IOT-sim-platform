"""
IOT SIM Platform - Streamlit Admin Panel
Main application entry point
"""

import streamlit as st
from utils.api import api_client
from utils.helpers import show_success, show_error


# Page configuration
st.set_page_config(
    page_title="IOT SIM Admin",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="expanded",
)


def init_session_state():
    """Initialize session state variables"""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "user" not in st.session_state:
        st.session_state.user = None
    if "token" not in st.session_state:
        st.session_state.token = None


def login_page():
    """Display login page"""
    st.title("🔧 IOT SIM Admin Panel")
    st.markdown("---")

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.subheader("Login")

        with st.form("login_form"):
            username = st.text_input("Username", placeholder="Enter username")
            password = st.text_input("Password", type="password", placeholder="Enter password")
            submit = st.form_submit_button("Login", use_container_width=True)

            if submit:
                if not username or not password:
                    show_error("Please enter both username and password")
                else:
                    try:
                        # Attempt login
                        response = api_client.login(username, password)

                        # Set token
                        token = response.get("access_token")
                        api_client.set_token(token)

                        # Get user info
                        user = api_client.get_current_user()

                        # Update session state
                        st.session_state.authenticated = True
                        st.session_state.user = user
                        st.session_state.token = token

                        show_success(f"Welcome, {user.get('username')}!")
                        st.rerun()

                    except Exception as e:
                        show_error(f"Login failed: {str(e)}")

        st.markdown("---")
        st.caption("IOT SIM Platform Admin Panel v1.0")


def main_page():
    """Display main page after login"""
    # Sidebar
    with st.sidebar:
        st.title("🔧 IOT SIM Admin")

        st.markdown("---")

        # User info
        if st.session_state.user:
            user = st.session_state.user
            st.markdown(f"**User:** {user.get('username')}")
            st.markdown(f"**Email:** {user.get('email', 'N/A')}")

            if user.get('is_superuser'):
                st.markdown("**Role:** :red[Superuser]")
            else:
                st.markdown("**Role:** User")

        st.markdown("---")

        # Logout button
        if st.button("Logout", use_container_width=True):
            api_client.clear_token()
            st.session_state.authenticated = False
            st.session_state.user = None
            st.session_state.token = None
            st.rerun()

    # Main content
    st.title("Welcome to IOT SIM Admin Panel")

    st.markdown("""
    This is the administrative interface for managing IoT SIM cards and monitoring the platform.

    Use the sidebar to navigate to different sections:
    """)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📊 Dashboard")
        st.write("View system overview, statistics, and real-time metrics")

        st.subheader("📱 SIM Management")
        st.write("Manage SIM cards, sync with 1NCE API, and view details")

    with col2:
        st.subheader("📈 Usage Analytics")
        st.write("Analyze data usage patterns and trends")

        st.subheader("🎯 Quota Management")
        st.write("Monitor and manage data and SMS quotas")

    st.markdown("---")

    # API Health Check
    st.subheader("System Status")
    try:
        health = api_client.health_check()
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("API Status", health.get("status", "unknown").upper())

        with col2:
            if "database" in health:
                st.metric("Database", health["database"].upper())

        with col3:
            if "redis" in health:
                st.metric("Redis", health["redis"].upper())

    except Exception as e:
        st.error(f"Failed to connect to API: {str(e)}")

    st.markdown("---")

    # Quick Stats
    st.subheader("Quick Stats")
    try:
        sims = api_client.get_sims(limit=1000)

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total SIMs", len(sims))

        with col2:
            active_sims = len([s for s in sims if s.get("status", "").upper() in ["ACTIVATED", "ENABLED", "ACTIVE"]])
            st.metric("Active SIMs", active_sims)

        with col3:
            inactive_sims = len(sims) - active_sims
            st.metric("Inactive SIMs", inactive_sims)

        with col4:
            if sims:
                activation_rate = (active_sims / len(sims)) * 100
                st.metric("Activation Rate", f"{activation_rate:.1f}%")

    except Exception as e:
        st.warning("Could not load statistics")


def main():
    """Main application logic"""
    init_session_state()

    if not st.session_state.authenticated:
        login_page()
    else:
        main_page()


if __name__ == "__main__":
    main()
