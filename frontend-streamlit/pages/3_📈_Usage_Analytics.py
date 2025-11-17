"""
Usage Analytics page - Analyze data usage patterns
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from utils.api import api_client
from utils.helpers import require_auth, show_error, format_bytes


st.set_page_config(
    page_title="Usage Analytics - IOT SIM Admin",
    page_icon="📈",
    layout="wide",
)


@require_auth
def main():
    st.title("📈 Usage Analytics")
    st.markdown("Analyze data usage patterns and trends")
    st.markdown("---")

    # Get SIMs
    try:
        sims = api_client.get_sims(limit=1000)

        if not sims:
            st.warning("No SIMs found. Add SIMs first.")
            return

        # SIM selection
        col1, col2 = st.columns([2, 3])

        with col1:
            selected_iccid = st.selectbox(
                "Select SIM",
                options=[s.get("iccid") for s in sims],
                key="usage_sim_select"
            )

        with col2:
            # Date range
            date_range = st.selectbox(
                "Time Period",
                ["Last 7 Days", "Last 30 Days", "Last 90 Days", "Custom"],
                key="date_range"
            )

        # Calculate date range
        end_date = datetime.now()
        if date_range == "Last 7 Days":
            start_date = end_date - timedelta(days=7)
        elif date_range == "Last 30 Days":
            start_date = end_date - timedelta(days=30)
        elif date_range == "Last 90 Days":
            start_date = end_date - timedelta(days=90)
        else:  # Custom
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input("Start Date", value=end_date - timedelta(days=30))
            with col2:
                end_date = st.date_input("End Date", value=end_date)

        st.markdown("---")

        # Load usage data
        if selected_iccid:
            with st.spinner("Loading usage data..."):
                try:
                    usage_data = api_client.get_usage(
                        iccid=selected_iccid,
                        start_date=start_date.strftime("%Y-%m-%d") if hasattr(start_date, 'strftime') else str(start_date),
                        end_date=end_date.strftime("%Y-%m-%d") if hasattr(end_date, 'strftime') else str(end_date)
                    )

                    if usage_data:
                        # Convert to DataFrame
                        df = pd.DataFrame(usage_data)
                        df['timestamp'] = pd.to_datetime(df['timestamp'])
                        df = df.sort_values('timestamp')

                        # Summary metrics
                        col1, col2, col3, col4 = st.columns(4)

                        total_bytes = df['total_bytes'].sum()
                        total_rx = df['volume_rx_bytes'].sum()
                        total_tx = df['volume_tx_bytes'].sum()
                        avg_daily = total_bytes / len(df) if len(df) > 0 else 0

                        with col1:
                            st.metric("Total Data", format_bytes(total_bytes))

                        with col2:
                            st.metric("Downloaded", format_bytes(total_rx))

                        with col3:
                            st.metric("Uploaded", format_bytes(total_tx))

                        with col4:
                            st.metric("Avg Daily", format_bytes(avg_daily))

                        st.markdown("---")

                        # Usage over time chart
                        st.subheader("Usage Over Time")

                        fig = go.Figure()

                        fig.add_trace(go.Scatter(
                            x=df['timestamp'],
                            y=df['total_mb'],
                            mode='lines+markers',
                            name='Total Usage (MB)',
                            line=dict(color='#0ea5e9', width=2),
                            marker=dict(size=6)
                        ))

                        fig.update_layout(
                            xaxis_title="Date",
                            yaxis_title="Usage (MB)",
                            hovermode='x unified',
                            height=400
                        )

                        st.plotly_chart(fig, use_container_width=True)

                        # RX vs TX chart
                        st.subheader("Download vs Upload")

                        fig = go.Figure()

                        fig.add_trace(go.Bar(
                            x=df['timestamp'],
                            y=df['volume_rx_bytes'] / (1024 * 1024),  # Convert to MB
                            name='Downloaded',
                            marker_color='#10b981'
                        ))

                        fig.add_trace(go.Bar(
                            x=df['timestamp'],
                            y=df['volume_tx_bytes'] / (1024 * 1024),  # Convert to MB
                            name='Uploaded',
                            marker_color='#f59e0b'
                        ))

                        fig.update_layout(
                            barmode='stack',
                            xaxis_title="Date",
                            yaxis_title="Usage (MB)",
                            hovermode='x unified',
                            height=400
                        )

                        st.plotly_chart(fig, use_container_width=True)

                        st.markdown("---")

                        # Usage table
                        st.subheader("Detailed Usage Data")

                        display_df = df[['timestamp', 'total_mb', 'volume_rx_bytes', 'volume_tx_bytes']].copy()
                        display_df['timestamp'] = display_df['timestamp'].dt.strftime('%Y-%m-%d %H:%M')
                        display_df['Downloaded'] = display_df['volume_rx_bytes'].apply(format_bytes)
                        display_df['Uploaded'] = display_df['volume_tx_bytes'].apply(format_bytes)
                        display_df = display_df[['timestamp', 'total_mb', 'Downloaded', 'Uploaded']]
                        display_df.columns = ['Timestamp', 'Total (MB)', 'Downloaded', 'Uploaded']

                        st.dataframe(
                            display_df,
                            use_container_width=True,
                            hide_index=True
                        )

                        # Sync button
                        st.markdown("---")
                        if st.button("🔄 Sync Usage Data", use_container_width=False):
                            with st.spinner("Syncing..."):
                                try:
                                    result = api_client.sync_usage(selected_iccid)
                                    st.success(f"✅ {result.get('message', 'Synced successfully')}")
                                    st.rerun()
                                except Exception as e:
                                    show_error(f"Sync failed: {str(e)}")

                    else:
                        st.info("No usage data found for the selected period")

                        if st.button("🔄 Sync Usage Data"):
                            with st.spinner("Syncing..."):
                                try:
                                    result = api_client.sync_usage(selected_iccid)
                                    st.success(f"✅ {result.get('message', 'Synced successfully')}")
                                    st.rerun()
                                except Exception as e:
                                    show_error(f"Sync failed: {str(e)}")

                except Exception as e:
                    show_error(f"Failed to load usage data: {str(e)}")

    except Exception as e:
        show_error(f"Failed to load SIMs: {str(e)}")


if __name__ == "__main__":
    main()
