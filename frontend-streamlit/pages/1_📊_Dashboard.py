"""
Dashboard page - System overview and statistics
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from utils.api import api_client
from utils.helpers import require_auth, show_error, format_bytes


st.set_page_config(
    page_title="Dashboard - IOT SIM Admin",
    page_icon="📊",
    layout="wide",
)


@require_auth
def main():
    st.title("📊 Dashboard")
    st.markdown("System overview and real-time statistics")
    st.markdown("---")

    # Metrics row
    try:
        sims = api_client.get_sims(limit=1000)

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "Total SIMs",
                len(sims),
                help="Total number of SIM cards in the system"
            )

        with col2:
            active_sims = len([s for s in sims if s.get("status", "").upper() in ["ACTIVATED", "ENABLED", "ACTIVE"]])
            st.metric(
                "Active SIMs",
                active_sims,
                help="SIMs currently active"
            )

        with col3:
            inactive_sims = len(sims) - active_sims
            st.metric(
                "Inactive SIMs",
                inactive_sims,
                help="SIMs not currently active"
            )

        with col4:
            if sims:
                activation_rate = (active_sims / len(sims)) * 100
                st.metric(
                    "Activation Rate",
                    f"{activation_rate:.1f}%",
                    help="Percentage of active SIMs"
                )

        st.markdown("---")

        # Status Distribution Chart
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("SIM Status Distribution")

            # Count SIMs by status
            status_counts = {}
            for sim in sims:
                status = sim.get("status", "UNKNOWN")
                status_counts[status] = status_counts.get(status, 0) + 1

            if status_counts:
                fig = px.pie(
                    values=list(status_counts.values()),
                    names=list(status_counts.keys()),
                    title="SIM Status Breakdown",
                    hole=0.4,
                )
                fig.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No SIM data available")

        with col2:
            st.subheader("SIMs by Operator")

            # Count SIMs by operator
            operator_counts = {}
            for sim in sims:
                operator = sim.get("operator", "Unknown")
                if operator:
                    operator_counts[operator] = operator_counts.get(operator, 0) + 1

            if operator_counts:
                fig = px.bar(
                    x=list(operator_counts.keys()),
                    y=list(operator_counts.values()),
                    title="SIM Distribution by Operator",
                    labels={'x': 'Operator', 'y': 'Count'},
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No operator data available")

        st.markdown("---")

        # Recent SIMs Table
        st.subheader("Recent SIMs")

        if sims:
            # Sort by created_at (most recent first)
            sorted_sims = sorted(
                sims,
                key=lambda x: x.get("created_at", ""),
                reverse=True
            )[:10]

            df = pd.DataFrame([
                {
                    "ICCID": s.get("iccid", ""),
                    "Status": s.get("status", ""),
                    "Operator": s.get("operator", "N/A"),
                    "Country": s.get("country", "N/A"),
                    "Created": s.get("created_at", "").split("T")[0] if s.get("created_at") else "N/A",
                }
                for s in sorted_sims
            ])

            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No SIMs found")

    except Exception as e:
        show_error(f"Failed to load dashboard data: {str(e)}")

    st.markdown("---")

    # System Health
    st.subheader("System Health")

    col1, col2, col3 = st.columns(3)

    try:
        health = api_client.health_check()

        with col1:
            status = health.get("status", "unknown")
            if status.upper() == "OK":
                st.success(f"API: {status.upper()}")
            else:
                st.error(f"API: {status.upper()}")

        with col2:
            db_status = health.get("database", "unknown")
            if db_status.upper() == "OK":
                st.success(f"Database: {db_status.upper()}")
            else:
                st.error(f"Database: {db_status.upper()}")

        with col3:
            redis_status = health.get("redis", "unknown")
            if redis_status.upper() == "OK":
                st.success(f"Redis: {redis_status.upper()}")
            else:
                st.error(f"Redis: {redis_status.upper()}")

        if "timestamp" in health:
            st.caption(f"Last checked: {health['timestamp']}")

    except Exception as e:
        st.error(f"Failed to check system health: {str(e)}")


if __name__ == "__main__":
    main()
