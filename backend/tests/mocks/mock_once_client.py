"""
Mock 1NCE API client for testing.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional


class MockOnceClient:
    """Mock implementation of OnceClient for testing."""

    def __init__(self):
        """Initialize mock client with test data."""
        self.mock_sims: Dict[str, Dict[str, Any]] = {
            "8991101200003204514": {
                "iccid": "8991101200003204514",
                "imsi": "310150123456789",
                "msisdn": "+1234567890",
                "status": "active",
                "ip_address": "10.0.0.1",
                "imei": "490154203237518",
            },
            "89148000000060671234": {
                "iccid": "89148000000060671234",
                "imsi": "262011234567890",
                "msisdn": "+9876543210",
                "status": "enabled",
                "ip_address": "10.0.0.2",
                "imei": "352099001761481",
            },
        }

        self.mock_usage: Dict[str, List[Dict[str, Any]]] = {
            "8991101200003204514": [
                {
                    "timestamp": "2024-11-17T10:00:00Z",
                    "volume_rx": 1024000,
                    "volume_tx": 512000,
                    "total_volume": 1536000,
                    "sms_mo": 5,
                    "sms_mt": 3,
                }
            ]
        }

        self.mock_quotas: Dict[str, Dict[str, Any]] = {
            "8991101200003204514": {
                "data": {
                    "volume": 50000000,
                    "total_volume": 100000000,
                    "expiry_date": "2025-01-01T00:00:00Z",
                },
                "sms": {
                    "volume": 80,
                    "total_volume": 100,
                    "expiry_date": "2025-01-01T00:00:00Z",
                },
            }
        }

        self.sent_sms: List[Dict[str, Any]] = []
        self.topup_history: List[Dict[str, Any]] = []

    async def authenticate(self) -> bool:
        """Mock authentication."""
        return True

    async def get_sims(
        self,
        page: int = 1,
        page_size: int = 100,
        iccid: Optional[str] = None,
        imsi: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Mock get SIMs."""
        sims = list(self.mock_sims.values())

        # Apply filters
        if iccid:
            sims = [s for s in sims if s["iccid"] == iccid]
        if imsi:
            sims = [s for s in sims if s["imsi"] == imsi]

        # Pagination
        start = (page - 1) * page_size
        end = start + page_size

        return {
            "sims": sims[start:end],
            "total": len(sims),
            "page": page,
            "page_size": page_size,
        }

    async def get_sim(self, iccid: str) -> Dict[str, Any]:
        """Mock get single SIM."""
        if iccid not in self.mock_sims:
            raise ValueError(f"SIM with ICCID {iccid} not found")

        return self.mock_sims[iccid]

    async def get_sim_usage(
        self,
        iccid: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Mock get SIM usage."""
        if iccid not in self.mock_usage:
            return {"usage": []}

        return {"usage": self.mock_usage[iccid]}

    async def get_data_quota(self, iccid: str) -> Dict[str, Any]:
        """Mock get data quota."""
        if iccid not in self.mock_quotas:
            return {
                "volume": 0,
                "total_volume": 0,
                "expiry_date": None,
            }

        return self.mock_quotas[iccid]["data"]

    async def get_sms_quota(self, iccid: str) -> Dict[str, Any]:
        """Mock get SMS quota."""
        if iccid not in self.mock_quotas:
            return {
                "volume": 0,
                "total_volume": 0,
                "expiry_date": None,
            }

        return self.mock_quotas[iccid]["sms"]

    async def topup_sim(
        self, iccid: str, quota_type: str, volume: int
    ) -> Dict[str, Any]:
        """Mock top-up SIM quota."""
        self.topup_history.append(
            {
                "iccid": iccid,
                "quota_type": quota_type,
                "volume": volume,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

        # Update mock quota
        if iccid in self.mock_quotas:
            if quota_type == "data":
                self.mock_quotas[iccid]["data"]["volume"] += volume
            elif quota_type == "sms":
                self.mock_quotas[iccid]["sms"]["volume"] += volume

        return {
            "success": True,
            "iccid": iccid,
            "quota_type": quota_type,
            "volume_added": volume,
        }

    async def send_sms(
        self, iccid: str, message: str, destination: Optional[str] = None
    ) -> Dict[str, Any]:
        """Mock send SMS."""
        sms_record = {
            "iccid": iccid,
            "message": message,
            "destination": destination,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "sent",
        }

        self.sent_sms.append(sms_record)

        return {
            "success": True,
            "message_id": f"msg_{len(self.sent_sms)}",
            "status": "sent",
        }

    async def get_connectivity_status(self, iccid: str) -> Dict[str, Any]:
        """Mock get connectivity status."""
        if iccid not in self.mock_sims:
            raise ValueError(f"SIM with ICCID {iccid} not found")

        return {
            "iccid": iccid,
            "status": "connected",
            "ip_address": self.mock_sims[iccid].get("ip_address"),
            "session_start": "2024-11-17T08:00:00Z",
            "data_transmitted": 1536000,
        }

    async def reset_connectivity(self, iccid: str) -> Dict[str, Any]:
        """Mock reset connectivity."""
        if iccid not in self.mock_sims:
            raise ValueError(f"SIM with ICCID {iccid} not found")

        return {
            "success": True,
            "iccid": iccid,
            "status": "reset_initiated",
        }

    async def get_sim_events(
        self, iccid: str, event_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Mock get SIM events."""
        events = [
            {
                "event_id": 1,
                "iccid": iccid,
                "event_type": "status_change",
                "description": "SIM activated",
                "timestamp": "2024-11-17T08:00:00Z",
            },
            {
                "event_id": 2,
                "iccid": iccid,
                "event_type": "data_usage",
                "description": "Data threshold exceeded",
                "timestamp": "2024-11-17T10:00:00Z",
            },
        ]

        if event_type:
            events = [e for e in events if e["event_type"] == event_type]

        return {"events": events}

    async def close(self):
        """Mock close connection."""
        pass


def get_mock_once_client() -> MockOnceClient:
    """Get mock 1NCE client instance."""
    return MockOnceClient()
