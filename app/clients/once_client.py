"""
1NCE API Client with OAuth 2.0 authentication.
Provides complete integration with 1NCE IoT platform APIs.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class OnceAPIError(Exception):
    """Base exception for 1NCE API errors"""

    pass


class OnceAuthError(OnceAPIError):
    """Authentication failed"""

    pass


class OnceRateLimitError(OnceAPIError):
    """Rate limit exceeded"""

    pass


class OnceTimeoutError(OnceAPIError):
    """Request timeout"""

    pass


class OnceClient:
    """
    Async HTTP client for 1NCE API with automatic OAuth 2.0 token management.

    Features:
    - Automatic bearer token acquisition
    - Token caching (in-memory, can be extended to Redis)
    - Automatic token refresh
    - Retry logic with exponential backoff
    - Request/response logging
    - Rate limiting protection
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        timeout: Optional[int] = None,
        max_retries: Optional[int] = None,
    ):
        """
        Initialize 1NCE API client.

        Args:
            base_url: 1NCE API base URL (defaults to settings)
            client_id: OAuth client ID (defaults to settings)
            client_secret: OAuth client secret (defaults to settings)
            timeout: Request timeout in seconds (defaults to settings)
            max_retries: Maximum number of retries (defaults to settings)
        """
        self.base_url = base_url or settings.once_api_base_url_str
        self.client_id = client_id or settings.ONCE_CLIENT_ID
        self.client_secret = client_secret or settings.ONCE_CLIENT_SECRET
        self.timeout = timeout or settings.ONCE_API_TIMEOUT
        self.max_retries = max_retries or settings.ONCE_MAX_RETRIES

        self._token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None
        self._http_client: Optional[httpx.AsyncClient] = None
        self._token_lock = asyncio.Lock()

    async def __aenter__(self):
        """Async context manager entry"""
        await self._get_http_client()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()

    async def _get_http_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client"""
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=httpx.Timeout(self.timeout),
                follow_redirects=True,
            )
        return self._http_client

    async def close(self):
        """Close HTTP client"""
        if self._http_client and not self._http_client.is_closed:
            await self._http_client.aclose()
            logger.info("once_client_closed")

    async def _get_access_token(self) -> str:
        """
        Get OAuth 2.0 access token (cached if valid).

        Returns:
            Valid access token

        Raises:
            OnceAuthError: If authentication fails
        """
        async with self._token_lock:
            # Return cached token if still valid
            if (
                self._token
                and self._token_expires_at
                and datetime.utcnow() < self._token_expires_at
            ):
                logger.debug("using_cached_token")
                return self._token

            # Request new token
            logger.info("requesting_new_access_token")
            client = await self._get_http_client()

            try:
                response = await client.post(
                    "/oauth/token",
                    data={
                        "grant_type": "client_credentials",
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                    },
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )
                response.raise_for_status()

                data = response.json()
                self._token = data["access_token"]
                expires_in = data.get("expires_in", 3600)

                # Set expiry with 5-minute buffer
                self._token_expires_at = datetime.utcnow() + timedelta(
                    seconds=expires_in - 300
                )

                logger.info(
                    "access_token_acquired",
                    expires_in=expires_in,
                    expires_at=self._token_expires_at.isoformat(),
                )

                return self._token

            except httpx.HTTPStatusError as e:
                logger.error(
                    "auth_failed",
                    status_code=e.response.status_code,
                    response=e.response.text,
                )
                raise OnceAuthError(f"Authentication failed: {e.response.text}")
            except Exception as e:
                logger.error("auth_error", error=str(e))
                raise OnceAuthError(f"Authentication error: {str(e)}")

    @retry(
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError)),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        stop=stop_after_attempt(3),
    )
    async def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Make authenticated HTTP request to 1NCE API.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint path
            params: Query parameters
            json: JSON body
            data: Form data

        Returns:
            Response JSON

        Raises:
            OnceAPIError: For API errors
            OnceRateLimitError: For rate limit errors
            OnceTimeoutError: For timeout errors
        """
        token = await self._get_access_token()
        client = await self._get_http_client()

        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        }

        try:
            logger.debug(
                "api_request",
                method=method,
                endpoint=endpoint,
                params=params,
            )

            response = await client.request(
                method=method,
                url=endpoint,
                params=params,
                json=json,
                data=data,
                headers=headers,
            )

            # Handle rate limiting
            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", 60))
                logger.warning("rate_limit_exceeded", retry_after=retry_after)
                raise OnceRateLimitError(f"Rate limit exceeded. Retry after {retry_after}s")

            response.raise_for_status()

            logger.debug(
                "api_response",
                method=method,
                endpoint=endpoint,
                status_code=response.status_code,
            )

            # Some endpoints return 204 No Content
            if response.status_code == 204:
                return {}

            return response.json()

        except httpx.TimeoutException as e:
            logger.error("api_timeout", endpoint=endpoint, timeout=self.timeout)
            raise OnceTimeoutError(f"Request timeout: {endpoint}")

        except httpx.HTTPStatusError as e:
            logger.error(
                "api_error",
                endpoint=endpoint,
                status_code=e.response.status_code,
                response=e.response.text,
            )
            raise OnceAPIError(
                f"API error {e.response.status_code}: {e.response.text}"
            )

        except Exception as e:
            logger.error("unexpected_error", endpoint=endpoint, error=str(e))
            raise OnceAPIError(f"Unexpected error: {str(e)}")

    # ==================== SIM Management Methods ====================

    async def get_sims(
        self,
        page: int = 1,
        page_size: int = 100,
        iccid: Optional[str] = None,
        imsi: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get list of SIM cards.

        Args:
            page: Page number
            page_size: Results per page
            iccid: Filter by ICCID
            imsi: Filter by IMSI

        Returns:
            List of SIMs with pagination info
        """
        params = {"page": page, "pageSize": page_size}
        if iccid:
            params["iccid"] = iccid
        if imsi:
            params["imsi"] = imsi

        return await self._request("GET", "/management-api/v1/sims", params=params)

    async def get_sim(self, iccid: str) -> Dict[str, Any]:
        """
        Get single SIM card details.

        Args:
            iccid: SIM card ICCID

        Returns:
            SIM details
        """
        return await self._request("GET", f"/management-api/v1/sims/{iccid}")

    async def get_sim_status(self, iccid: str) -> Dict[str, Any]:
        """Get SIM status"""
        return await self._request("GET", f"/management-api/v1/sims/{iccid}/status")

    async def get_sim_connectivity(self, iccid: str) -> Dict[str, Any]:
        """Get SIM connectivity information"""
        return await self._request(
            "GET", f"/management-api/v1/sims/{iccid}/connectivity"
        )

    async def get_sim_usage(
        self,
        iccid: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get SIM usage data.

        Args:
            iccid: SIM card ICCID
            start_date: Start date (ISO format)
            end_date: End date (ISO format)

        Returns:
            Usage data
        """
        params = {}
        if start_date:
            params["startDate"] = start_date
        if end_date:
            params["endDate"] = end_date

        return await self._request(
            "GET", f"/management-api/v1/sims/{iccid}/usage", params=params
        )

    async def get_sim_events(
        self, iccid: str, event_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get SIM events"""
        params = {}
        if event_type:
            params["eventType"] = event_type

        return await self._request(
            "GET", f"/management-api/v1/sims/{iccid}/events", params=params
        )

    async def reset_sim_connectivity(self, iccid: str) -> Dict[str, Any]:
        """Reset SIM connectivity"""
        return await self._request(
            "POST", f"/management-api/v1/sims/{iccid}/connectivity/reset"
        )

    # ==================== Quota Management ====================

    async def get_data_quota(self, iccid: str) -> Dict[str, Any]:
        """Get SIM data quota"""
        return await self._request("GET", f"/management-api/v1/sims/{iccid}/quota/data")

    async def get_sms_quota(self, iccid: str) -> Dict[str, Any]:
        """Get SIM SMS quota"""
        return await self._request("GET", f"/management-api/v1/sims/{iccid}/quota/sms")

    async def topup_sim(
        self, iccid: str, quota_type: str, volume: int
    ) -> Dict[str, Any]:
        """
        Top-up SIM quota.

        Args:
            iccid: SIM card ICCID
            quota_type: 'data' or 'sms'
            volume: Volume to add

        Returns:
            Top-up result
        """
        return await self._request(
            "POST",
            f"/management-api/v1/sims/{iccid}/quota/{quota_type}/topup",
            json={"volume": volume},
        )

    # ==================== SMS Management ====================

    async def send_sms(
        self, iccid: str, message: str, destination: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send SMS to SIM.

        Args:
            iccid: SIM card ICCID
            message: SMS message text
            destination: Optional destination number

        Returns:
            SMS send result
        """
        payload = {"message": message}
        if destination:
            payload["destination"] = destination

        return await self._request(
            "POST", f"/management-api/v1/sims/{iccid}/sms", json=payload
        )

    async def get_sms_messages(self, iccid: str) -> Dict[str, Any]:
        """Get SMS messages for SIM"""
        return await self._request("GET", f"/management-api/v1/sims/{iccid}/sms")

    # ==================== Order Management ====================

    async def get_orders(self) -> Dict[str, Any]:
        """Get all orders"""
        return await self._request("GET", "/management-api/v1/orders")

    async def get_order(self, order_id: str) -> Dict[str, Any]:
        """Get single order"""
        return await self._request("GET", f"/management-api/v1/orders/{order_id}")

    async def create_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new order"""
        return await self._request("POST", "/management-api/v1/orders", json=order_data)

    # ==================== Product Management ====================

    async def get_products(self) -> Dict[str, Any]:
        """Get product catalog"""
        return await self._request("GET", "/management-api/v1/products")

    async def get_product(self, product_id: str) -> Dict[str, Any]:
        """Get single product"""
        return await self._request("GET", f"/management-api/v1/products/{product_id}")


# Singleton instance
_once_client: Optional[OnceClient] = None


async def get_once_client() -> OnceClient:
    """
    Get singleton OnceClient instance.

    Returns:
        Configured OnceClient instance
    """
    global _once_client

    if _once_client is None:
        _once_client = OnceClient()
        await _once_client._get_http_client()
        logger.info("once_client_initialized")

    return _once_client


async def close_once_client():
    """Close the singleton OnceClient"""
    global _once_client

    if _once_client:
        await _once_client.close()
        _once_client = None
