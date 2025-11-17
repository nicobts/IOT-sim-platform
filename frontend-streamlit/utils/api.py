import os
from typing import Dict, List, Optional, Any
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class APIClient:
    """API Client for backend communication"""

    def __init__(self, base_url: str = None):
        self.base_url = base_url or os.getenv("API_URL", "http://backend:8000")
        self.session = requests.Session()

        # Setup retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        # Default headers
        self.session.headers.update({
            "Content-Type": "application/json",
        })

    def set_token(self, token: str):
        """Set authentication token"""
        self.session.headers.update({"Authorization": f"Bearer {token}"})

    def clear_token(self):
        """Clear authentication token"""
        if "Authorization" in self.session.headers:
            del self.session.headers["Authorization"]

    # Auth endpoints
    def login(self, username: str, password: str) -> Dict:
        """Login and get access token"""
        data = {
            "username": username,
            "password": password,
        }
        response = self.session.post(
            f"{self.base_url}/api/v1/auth/login",
            data=data,
        )
        response.raise_for_status()
        return response.json()

    def get_current_user(self) -> Dict:
        """Get current authenticated user"""
        response = self.session.get(f"{self.base_url}/api/v1/auth/me")
        response.raise_for_status()
        return response.json()

    # Health check
    def health_check(self) -> Dict:
        """Check API health"""
        response = self.session.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()

    # SIM endpoints
    def get_sims(self, skip: int = 0, limit: int = 1000) -> List[Dict]:
        """Get all SIMs"""
        response = self.session.get(
            f"{self.base_url}/api/v1/sims",
            params={"skip": skip, "limit": limit}
        )
        response.raise_for_status()
        return response.json()

    def get_sim(self, iccid: str) -> Dict:
        """Get SIM by ICCID"""
        response = self.session.get(f"{self.base_url}/api/v1/sims/{iccid}")
        response.raise_for_status()
        return response.json()

    def create_sim(self, iccid: str, imsi: str = None, msisdn: str = None) -> Dict:
        """Create new SIM"""
        data = {"iccid": iccid}
        if imsi:
            data["imsi"] = imsi
        if msisdn:
            data["msisdn"] = msisdn

        response = self.session.post(f"{self.base_url}/api/v1/sims", json=data)
        response.raise_for_status()
        return response.json()

    def delete_sim(self, iccid: str) -> None:
        """Delete SIM"""
        response = self.session.delete(f"{self.base_url}/api/v1/sims/{iccid}")
        response.raise_for_status()

    def sync_sims(self) -> Dict:
        """Sync SIMs from 1NCE API"""
        response = self.session.post(f"{self.base_url}/api/v1/sims/sync")
        response.raise_for_status()
        return response.json()

    # Usage endpoints
    def get_usage(
        self,
        iccid: str,
        start_date: str = None,
        end_date: str = None
    ) -> List[Dict]:
        """Get usage for SIM"""
        params = {}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date

        response = self.session.get(
            f"{self.base_url}/api/v1/usage/{iccid}",
            params=params
        )
        response.raise_for_status()
        return response.json()

    def sync_usage(self, iccid: str) -> Dict:
        """Sync usage for SIM"""
        response = self.session.post(f"{self.base_url}/api/v1/usage/{iccid}/sync")
        response.raise_for_status()
        return response.json()

    # Quota endpoints
    def get_quotas(self, iccid: str) -> List[Dict]:
        """Get quotas for SIM"""
        response = self.session.get(f"{self.base_url}/api/v1/quotas/{iccid}")
        response.raise_for_status()
        return response.json()

    def get_quota(self, iccid: str, quota_type: str) -> Dict:
        """Get specific quota for SIM"""
        response = self.session.get(
            f"{self.base_url}/api/v1/quotas/{iccid}/{quota_type}"
        )
        response.raise_for_status()
        return response.json()

    def sync_quota(self, iccid: str, quota_type: str) -> Dict:
        """Sync quota for SIM"""
        response = self.session.post(
            f"{self.base_url}/api/v1/quotas/{iccid}/{quota_type}/sync"
        )
        response.raise_for_status()
        return response.json()

    # Metrics
    def get_metrics(self) -> str:
        """Get Prometheus metrics"""
        response = self.session.get(f"{self.base_url}/api/v1/metrics")
        response.raise_for_status()
        return response.text


# Singleton instance
api_client = APIClient()
