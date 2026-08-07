"""
Thin async client for the pyHSS provisioning REST API.
"""

import logging
from os import makedirs
from typing import Any

import httpx

from .config import settings


class PyHSSError(Exception):
    """Raised for any non-2xx/404 response from the pyHSS API."""

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


class PyHSSClient:
    def __init__(
        self,
        base_url: str,
        provisioning_key: str | None = None,
        timeout: float = 10.0,
    ):
        self.base_url = base_url.rstrip("/")
        self.provisioning_key = provisioning_key
        self.timeout = timeout
        self._setup_logging()

    def _setup_logging(self, log_filename: str = "pyhss_client.log"):
        makedirs(f"{settings.logs_dir}/", exist_ok=True)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(logging.INFO)

        formatter = logging.Formatter(fmt="%(asctime)s [%(classname)s] %(levelname)s: %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
        handler = logging.FileHandler(f"{settings.logs_dir}/{log_filename}")
        handler.setFormatter(formatter)
        handler.setLevel(logging.INFO)

        self.logger.addHandler(handler)
        self.logger = logging.LoggerAdapter(self.logger, {"classname": self.__class__.__name__})

    def _headers(self) -> dict:
        headers = {"Content-Type": "application/json", "accept": "application/json"}
        if self.provisioning_key:
            headers["Provisioning-Key"] = self.provisioning_key
        return headers

    async def _request(self, method: str, path: str, **kwargs) -> Any | None:
        url = f"{self.base_url}{path}"
        self.logger.info(f"{method} {path}")
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.request(method, url, headers=self._headers(), **kwargs)
        except httpx.RequestError as e:
            raise PyHSSError(f"Could not reach pyHSS at {url}: {e}") from e
        self.logger.info(f"{resp.text}")

        if resp.status_code == 404:
            return None
        if resp.status_code >= 400:
            self.logger.error(f"HTTP {resp.status_code}: {resp.text}")
            raise PyHSSError(
                f"pyHSS API error {resp.status_code} on {method} {path}: {resp.text}",
                status_code=resp.status_code,
            )
        if resp.status_code == 204 or not resp.content:
            return None
        return resp.json()

    # ---- Subscriber -----------------------------------------------------

    async def get_subscribers(self) -> list | None:
        return await self._request("GET", "/subscriber/list?page=0&page_size=500")

    async def get_subscriber_by_imsi(self, imsi) -> dict | None:
        return await self._request("GET", f"/subscriber/imsi/{imsi}")

    async def get_subscriber_by_msisdn(self, msisdn) -> dict | None:
        return await self._request("GET", f"/subscriber/msisdn/{msisdn}")

    async def get_subscriber(self, subscriber_id) -> dict | None:
        return await self._request("GET", f"/subscriber/{subscriber_id}")

    async def create_subscriber(self, payload: dict) -> dict:
        return await self._request("PUT", "/subscriber/", json=payload)

    async def update_subscriber(self, subscriber_id, **fields) -> dict:
        """PATCH only the given fields on an existing subscriber."""
        return await self._request("PATCH", f"/subscriber/{subscriber_id}", json=fields)

    async def delete_subscriber(self, subscriber_id) -> dict | None:
        return await self._request("DELETE", f"/subscriber/{subscriber_id}")

    # ---- Subscriber Attributes -----------------------------------------

    async def get_subscriber_attributes(self, subscriber_id) -> dict | None:
        return await self._request("GET", f"/subscriber_attributes/{subscriber_id}")

    async def create_subscriber_attribute(self, payload: dict) -> dict:
        return await self._request("PUT", "/subscriber_attributes/", json=payload)

    async def update_subscriber_attribute(self, subscriber_attributes_id, **fields) -> dict | None:
        return await self._request("PATCH", f"/subscriber_attributes/{subscriber_attributes_id}", json=fields)

    async def delete_subscriber_attribute(self, subscriber_attributes_id) -> dict | None:
        return await self._request("DELETE", f"/subscriber_attributes/{subscriber_attributes_id}")

    # ---- AuC (SIM crypto material) --------------------------------------

    async def get_auc_by_iccid(self, iccid) -> dict | None:
        return await self._request("GET", f"/auc/iccid/{iccid}")

    async def get_auc_by_imsi(self, imsi) -> dict | None:
        return await self._request("GET", f"/auc/imsi/{imsi}")

    async def get_auc(self, auc_id) -> dict | None:
        return await self._request("GET", f"/auc/{auc_id}")

    async def create_auc(self, payload: dict) -> dict:
        return await self._request("PUT", "/auc/", json=payload)

    async def update_auc(self, auc_id, **fields) -> dict:
        return await self._request("PATCH", f"/auc/{auc_id}", json=fields)

    async def delete_auc(self, auc_id) -> dict | None:
        return await self._request("DELETE", f"/auc/{auc_id}")

    # ---- APN --------------------------------------------------------------

    async def list_apns(self, page: int = 0, page_size: int = 200) -> Any:
        return await self._request("GET", "/apn/list", params={"page": page, "page_size": page_size})

    async def create_apn(self, payload: dict) -> dict:
        return await self._request("PUT", "/apn/", json=payload)


pyhss_client = PyHSSClient(
    base_url=settings.pyhss_base_url,
    provisioning_key=getattr(settings, "pyhss_provisioning_key", None),
)
