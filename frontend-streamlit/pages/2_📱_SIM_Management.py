"""
SIM Management page - Manage SIM cards
"""

import streamlit as st
import pandas as pd
from utils.api import api_client
from utils.helpers import (
    require_auth,
    show_success,
    show_error,
    show_warning,
    format_status_badge
)


st.set_page_config(
    page_title="SIM Management - IOT SIM Admin",
    page_icon="📱",
    layout="wide",
)


@require_auth
def main():
    st.title("📱 SIM Management")
    st.markdown("Manage SIM cards, sync with 1NCE API, and view details")
    st.markdown("---")

    # Action buttons
    col1, col2, col3, col4 = st.columns([1, 1, 1, 3])

    with col1:
        if st.button("🔄 Sync SIMs", use_container_width=True, help="Sync all SIMs from 1NCE API"):
            with st.spinner("Syncing SIMs..."):
                try:
                    result = api_client.sync_sims()
                    show_success(f"Synced {result.get('synced', 0)} SIMs")
                    st.rerun()
                except Exception as e:
                    show_error(f"Sync failed: {str(e)}")

    with col2:
        if st.button("➕ Add SIM", use_container_width=True):
            st.session_state.show_add_form = True

    with col3:
        if st.button("🔍 Refresh", use_container_width=True):
            st.rerun()

    st.markdown("---")

    # Add SIM form (if triggered)
    if st.session_state.get("show_add_form", False):
        with st.expander("Add New SIM", expanded=True):
            with st.form("add_sim_form"):
                iccid = st.text_input("ICCID *", placeholder="89490200001234567890")
                imsi = st.text_input("IMSI (optional)", placeholder="901700000012345")
                msisdn = st.text_input("MSISDN (optional)", placeholder="+1234567890")

                col1, col2 = st.columns(2)
                with col1:
                    submit = st.form_submit_button("Add SIM", use_container_width=True)
                with col2:
                    cancel = st.form_submit_button("Cancel", use_container_width=True)

                if cancel:
                    st.session_state.show_add_form = False
                    st.rerun()

                if submit:
                    if not iccid:
                        show_error("ICCID is required")
                    else:
                        try:
                            api_client.create_sim(
                                iccid=iccid,
                                imsi=imsi if imsi else None,
                                msisdn=msisdn if msisdn else None
                            )
                            show_success(f"SIM {iccid} added successfully")
                            st.session_state.show_add_form = False
                            st.rerun()
                        except Exception as e:
                            show_error(f"Failed to add SIM: {str(e)}")

    # Filters
    st.subheader("Filters")
    col1, col2, col3 = st.columns(3)

    with col1:
        status_filter = st.selectbox(
            "Status",
            ["All", "ACTIVATED", "ENABLED", "DISABLED", "SUSPENDED", "TERMINATED"],
            key="status_filter"
        )

    with col2:
        search_iccid = st.text_input("Search ICCID", placeholder="Enter ICCID", key="search_iccid")

    with col3:
        operator_filter = st.selectbox("Operator", ["All"], key="operator_filter")

    st.markdown("---")

    # Load and display SIMs
    try:
        sims = api_client.get_sims(limit=1000)

        # Apply filters
        filtered_sims = sims

        if status_filter != "All":
            filtered_sims = [s for s in filtered_sims if s.get("status", "").upper() == status_filter]

        if search_iccid:
            filtered_sims = [s for s in filtered_sims if search_iccid.lower() in s.get("iccid", "").lower()]

        # Display count
        st.subheader(f"SIM Cards ({len(filtered_sims)} found)")

        if filtered_sims:
            # Create DataFrame
            df = pd.DataFrame([
                {
                    "ICCID": s.get("iccid", ""),
                    "Status": s.get("status", ""),
                    "IMSI": s.get("imsi", "N/A"),
                    "MSISDN": s.get("msisdn", "N/A"),
                    "Operator": s.get("operator", "N/A"),
                    "Country": s.get("country", "N/A"),
                    "IP Address": s.get("ip_address", "N/A"),
                    "Last Updated": s.get("last_status_update", "N/A").split("T")[0] if s.get("last_status_update") else "N/A",
                }
                for s in filtered_sims
            ])

            # Display table
            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Status": st.column_config.TextColumn("Status", width="small"),
                }
            )

            st.markdown("---")

            # SIM Details Section
            st.subheader("SIM Details")

            selected_iccid = st.selectbox(
                "Select SIM to view details",
                options=[s.get("iccid") for s in filtered_sims],
                key="selected_iccid"
            )

            if selected_iccid:
                sim = next((s for s in filtered_sims if s.get("iccid") == selected_iccid), None)

                if sim:
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.markdown("**Basic Information**")
                        st.text(f"ICCID: {sim.get('iccid', 'N/A')}")
                        st.text(f"Status: {sim.get('status', 'N/A')}")
                        st.text(f"IMSI: {sim.get('imsi', 'N/A')}")
                        st.text(f"MSISDN: {sim.get('msisdn', 'N/A')}")

                    with col2:
                        st.markdown("**Network Information**")
                        st.text(f"Operator: {sim.get('operator', 'N/A')}")
                        st.text(f"Country: {sim.get('country', 'N/A')}")
                        st.text(f"IP Address: {sim.get('ip_address', 'N/A')}")
                        st.text(f"IMEI: {sim.get('imei', 'N/A')}")

                    with col3:
                        st.markdown("**Timestamps**")
                        st.text(f"Created: {sim.get('created_at', 'N/A')[:10]}")
                        st.text(f"Updated: {sim.get('updated_at', 'N/A')[:10]}")
                        st.text(f"Last Status Update: {sim.get('last_status_update', 'N/A')[:10] if sim.get('last_status_update') else 'N/A'}")

                    st.markdown("---")

                    # Actions
                    col1, col2, col3 = st.columns([1, 1, 4])

                    with col1:
                        if st.button("🗑️ Delete SIM", use_container_width=True):
                            if st.session_state.get("confirm_delete") != selected_iccid:
                                st.session_state.confirm_delete = selected_iccid
                                show_warning("Click again to confirm deletion")
                            else:
                                try:
                                    api_client.delete_sim(selected_iccid)
                                    show_success(f"SIM {selected_iccid} deleted")
                                    st.session_state.confirm_delete = None
                                    st.rerun()
                                except Exception as e:
                                    show_error(f"Delete failed: {str(e)}")

        else:
            st.info("No SIMs found matching the filters")

    except Exception as e:
        show_error(f"Failed to load SIMs: {str(e)}")


if __name__ == "__main__":
    main()
