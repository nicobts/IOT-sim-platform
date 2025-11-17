# IOT SIM Platform - Streamlit Admin Panel

Internal management interface for advanced administrative tasks.

**Note**: This is part of a monorepo. See the [main README](../README.md) for full platform documentation.

## Features

- 📊 **Dashboard**: System overview with real-time statistics
- 📱 **SIM Management**: Full CRUD operations, sync with 1NCE API
- 📈 **Usage Analytics**: Data usage charts and trends
- 🎯 **Quota Management**: Monitor and manage data/SMS quotas with visual gauges
- 🔐 **Authentication**: Secure login with JWT tokens
- 📊 **Interactive Charts**: Plotly-powered visualizations
- 🎨 **Modern UI**: Clean, intuitive interface

## Tech Stack

- **Framework**: Streamlit 1.29+
- **Language**: Python 3.11+
- **HTTP Client**: Requests + HTTPx
- **Charts**: Plotly
- **Data**: Pandas
- **Styling**: Streamlit theming

## Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run development server
streamlit run app.py

# Access at http://localhost:8501
```

## Environment Variables

Copy `.env.example` to `.env` and update:

```bash
API_URL=http://backend:8000
```

## Project Structure

```
frontend-streamlit/
├── app.py                    # Main application
├── pages/                    # Multi-page app pages
│   ├── 1_📊_Dashboard.py
│   ├── 2_📱_SIM_Management.py
│   ├── 3_📈_Usage_Analytics.py
│   └── 4_🎯_Quota_Management.py
├── utils/
│   ├── api.py               # API client
│   └── helpers.py           # Helper functions
├── .streamlit/
│   └── config.toml          # Streamlit configuration
└── requirements.txt
```

## Pages

### Dashboard
- System overview and statistics
- SIM status distribution
- Recent SIMs table
- Health checks

### SIM Management
- List all SIMs with filtering
- Add new SIMs
- View detailed SIM information
- Delete SIMs
- Sync with 1NCE API

### Usage Analytics
- Usage over time charts
- Download vs Upload analysis
- Date range filtering
- Detailed usage data table
- Sync usage data

### Quota Management
- Visual quota gauges
- Data and SMS quotas
- Progress bars and metrics
- Auto top-up status
- Sync quotas

## Docker

### Monorepo (Recommended)

```bash
# From repository root - Start all services
docker-compose up -d

# Streamlit admin will be available at http://localhost:8501
```

### Standalone

```bash
# Build image
docker build -t iot-streamlit:latest .

# Run container
docker run -p 8501:8501 \
  -e API_URL=http://backend:8000 \
  iot-streamlit:latest
```

## Authentication

Default credentials (for development):
- Username: `admin`
- Password: `admin123`

Change these in production!

## Integration

Connects to the FastAPI backend at `/api/v1/*` endpoints. Requires backend to be running.

See [Backend API Documentation](../backend/README.md) for API details.
