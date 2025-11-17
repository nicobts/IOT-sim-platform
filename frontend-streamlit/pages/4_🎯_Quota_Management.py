"""
Quota Management page - Monitor and manage quotas
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from utils.api import api_client
from utils.helpers import require_auth, show_error, show_success, format_bytes


st.set_page_config(
    page_title="Quota Management - IOT SIM Admin",
    page_icon="🎯",
    layout="wide",
)


@require_auth
def main():
    st.title("🎯 Quota Management")
    st.markdown("Monitor and manage data and SMS quotas")
    st.markdown("---")

    # Get SIMs
    try:
        sims = api_client.get_sims(limit=1000)

        if not sims:
            st.warning("No SIMs found. Add SIMs first.")
            return

        # SIM selection
        selected_iccid = st.selectbox(
            "Select SIM",
            options=[s.get("iccid") for s in sims],
            key="quota_sim_select"
        )

        st.markdown("---")

        if selected_iccid:
            # Load quotas
            try:
                quotas = api_client.get_quotas(selected_iccid)

                if quotas:
                    # Separate data and SMS quotas
                    data_quotas = [q for q in quotas if q.get("quota_type") == "data"]
                    sms_quotas = [q for q in quotas if q.get("quota_type") == "sms"]

                    # Data Quota Section
                    st.subheader("📊 Data Quota")

                    if data_quotas:
                        for quota in data_quotas:
                            col1, col2 = st.columns([2, 1])

                            with col1:
                                # Quota metrics
                                total = quota.get("volume_total", 0)
                                used = quota.get("volume_used", 0)
                                remaining = quota.get("volume_remaining", 0)
                                percentage = (used / total * 100) if total > 0 else 0

                                # Progress bar
                                st.progress(percentage / 100)

                                col_a, col_b, col_c = st.columns(3)
                                with col_a:
                                    st.metric("Total", format_bytes(total))
                                with col_b:
                                    st.metric("Used", format_bytes(used))
                                with col_c:
                                    st.metric("Remaining", format_bytes(remaining))

                                # Gauge chart
                                fig = go.Figure(go.Indicator(
                                    mode="gauge+number+delta",
                                    value=percentage,
                                    domain={'x': [0, 1], 'y': [0, 1]},
                                    title={'text': "Usage %"},
                                    delta={'reference': 100},
                                    gauge={
                                        'axis': {'range': [None, 100]},
                                        'bar': {'color': "#0ea5e9"},
                                        'steps': [
                                            {'range': [0, 50], 'color': "#d1fae5"},
                                            {'range': [50, 75], 'color': "#fef3c7"},
                                            {'range': [75, 100], 'color': "#fee2e2"}
                                        ],
                                        'threshold': {
                                            'line': {'color': "red", 'width': 4},
                                            'thickness': 0.75,
                                            'value': quota.get("threshold_percentage", 90)
                                        }
                                    }
                                ))

                                fig.update_layout(height=300)
                                st.plotly_chart(fig, use_container_width=True)

                            with col2:
                                st.markdown("**Quota Details**")
                                st.text(f"Status: {quota.get('status', 'N/A')}")
                                st.text(f"Auto Top-up: {'Yes' if quota.get('auto_topup') else 'No'}")

                                if quota.get('threshold_percentage'):
                                    st.text(f"Threshold: {quota.get('threshold_percentage')}%")

                                if quota.get('expires_at'):
                                    st.text(f"Expires: {quota.get('expires_at')[:10]}")

                                st.text(f"Last Updated: {quota.get('last_updated', 'N/A')[:10]}")

                                st.markdown("---")

                                # Sync button
                                if st.button("🔄 Sync Data Quota", key=f"sync_data_{quota.get('id')}"):
                                    with st.spinner("Syncing..."):
                                        try:
                                            result = api_client.sync_quota(selected_iccid, "data")
                                            show_success("Data quota synced successfully")
                                            st.rerun()
                                        except Exception as e:
                                            show_error(f"Sync failed: {str(e)}")
                    else:
                        st.info("No data quota found for this SIM")

                        if st.button("🔄 Sync Data Quota"):
                            with st.spinner("Syncing..."):
                                try:
                                    result = api_client.sync_quota(selected_iccid, "data")
                                    show_success("Data quota synced successfully")
                                    st.rerun()
                                except Exception as e:
                                    show_error(f"Sync failed: {str(e)}")

                    st.markdown("---")

                    # SMS Quota Section
                    st.subheader("💬 SMS Quota")

                    if sms_quotas:
                        for quota in sms_quotas:
                            col1, col2 = st.columns([2, 1])

                            with col1:
                                # Quota metrics
                                total = quota.get("volume_total", 0)
                                used = quota.get("volume_used", 0)
                                remaining = quota.get("volume_remaining", 0)
                                percentage = (used / total * 100) if total > 0 else 0

                                # Progress bar
                                st.progress(percentage / 100)

                                col_a, col_b, col_c = st.columns(3)
                                with col_a:
                                    st.metric("Total", f"{total:,} SMS")
                                with col_b:
                                    st.metric("Used", f"{used:,} SMS")
                                with col_c:
                                    st.metric("Remaining", f"{remaining:,} SMS")

                                # Gauge chart
                                fig = go.Figure(go.Indicator(
                                    mode="gauge+number+delta",
                                    value=percentage,
                                    domain={'x': [0, 1], 'y': [0, 1]},
                                    title={'text': "Usage %"},
                                    delta={'reference': 100},
                                    gauge={
                                        'axis': {'range': [None, 100]},
                                        'bar': {'color': "#10b981"},
                                        'steps': [
                                            {'range': [0, 50], 'color': "#d1fae5"},
                                            {'range': [50, 75], 'color': "#fef3c7"},
                                            {'range': [75, 100], 'color': "#fee2e2"}
                                        ],
                                        'threshold': {
                                            'line': {'color': "red", 'width': 4},
                                            'thickness': 0.75,
                                            'value': quota.get("threshold_percentage", 90)
                                        }
                                    }
                                ))

                                fig.update_layout(height=300)
                                st.plotly_chart(fig, use_container_width=True)

                            with col2:
                                st.markdown("**Quota Details**")
                                st.text(f"Status: {quota.get('status', 'N/A')}")
                                st.text(f"Auto Top-up: {'Yes' if quota.get('auto_topup') else 'No'}")

                                if quota.get('threshold_percentage'):
                                    st.text(f"Threshold: {quota.get('threshold_percentage')}%")

                                if quota.get('expires_at'):
                                    st.text(f"Expires: {quota.get('expires_at')[:10]}")

                                st.text(f"Last Updated: {quota.get('last_updated', 'N/A')[:10]}")

                                st.markdown("---")

                                # Sync button
                                if st.button("🔄 Sync SMS Quota", key=f"sync_sms_{quota.get('id')}"):
                                    with st.spinner("Syncing..."):
                                        try:
                                            result = api_client.sync_quota(selected_iccid, "sms")
                                            show_success("SMS quota synced successfully")
                                            st.rerun()
                                        except Exception as e:
                                            show_error(f"Sync failed: {str(e)}")
                    else:
                        st.info("No SMS quota found for this SIM")

                        if st.button("🔄 Sync SMS Quota"):
                            with st.spinner("Syncing..."):
                                try:
                                    result = api_client.sync_quota(selected_iccid, "sms")
                                    show_success("SMS quota synced successfully")
                                    st.rerun()
                                except Exception as e:
                                    show_error(f"Sync failed: {str(e)}")

                else:
                    st.info("No quotas found for this SIM")

                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("🔄 Sync Data Quota", use_container_width=True):
                            with st.spinner("Syncing..."):
                                try:
                                    result = api_client.sync_quota(selected_iccid, "data")
                                    show_success("Data quota synced successfully")
                                    st.rerun()
                                except Exception as e:
                                    show_error(f"Sync failed: {str(e)}")

                    with col2:
                        if st.button("🔄 Sync SMS Quota", use_container_width=True):
                            with st.spinner("Syncing..."):
                                try:
                                    result = api_client.sync_quota(selected_iccid, "sms")
                                    show_success("SMS quota synced successfully")
                                    st.rerun()
                                except Exception as e:
                                    show_error(f"Sync failed: {str(e)}")

            except Exception as e:
                show_error(f"Failed to load quotas: {str(e)}")

    except Exception as e:
        show_error(f"Failed to load SIMs: {str(e)}")


if __name__ == "__main__":
    main()
