"""
Jaguar Quant X
Upstox Order Transport

Isolated authenticated transport for Upstox order APIs.

This module is intentionally separate from market/upstox_transport.py.

LIVE order writes are possible only through an explicitly constructed
transport. No requests are performed at import time.
"""


import requests

from config.provider_credentials import ProviderCredentials


class UpstoxOrderTransportError(RuntimeError):
    """Raised when Upstox order transport or response handling fails."""


class UpstoxOrderTransport:
    """
    Low-level Upstox order transport.

    Write APIs:
        POST   /v3/order/place
        DELETE /v3/order/cancel

    Read APIs:
        GET /v2/order/details
        GET /v2/order/history
        GET /v2/portfolio/short-term-positions
    """

    ORDER_BASE_URL = "https://api-hft.upstox.com"
    READ_BASE_URL = "https://api.upstox.com"

    DEFAULT_TIMEOUT = 10.0

    def __init__(
        self,
        access_token=None,
        session=None,
        timeout=DEFAULT_TIMEOUT,
    ):
        if access_token is None:
            access_token = ProviderCredentials.upstox_access_token()

        access_token = str(access_token).strip()

        if not access_token:
            raise UpstoxOrderTransportError(
                "Upstox access token is unavailable"
            )

        try:
            timeout = float(timeout)
        except (TypeError, ValueError) as exc:
            raise UpstoxOrderTransportError(
                f"Invalid Upstox request timeout: {timeout!r}"
            ) from exc

        if timeout <= 0:
            raise UpstoxOrderTransportError(
                "Upstox request timeout must be positive"
            )

        self._access_token = access_token
        self._session = (
            session
            if session is not None
            else requests.Session()
        )
        self._timeout = timeout

    def _headers(self):
        return {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._access_token}",
        }

    @staticmethod
    def _validate_path(path):
        if not isinstance(path, str):
            raise UpstoxOrderTransportError(
                "Upstox request path must be a string"
            )

        path = path.strip()

        if not path.startswith("/"):
            raise UpstoxOrderTransportError(
                "Upstox request path must start with '/'"
            )

        return path

    @staticmethod
    def _validate_payload(payload):
        if not isinstance(payload, dict):
            raise UpstoxOrderTransportError(
                "Upstox request payload must be an object"
            )

    @staticmethod
    def _decode(response):
        try:
            payload = response.json()
        except (TypeError, ValueError) as exc:
            raise UpstoxOrderTransportError(
                "Upstox response is not valid JSON"
            ) from exc

        if not isinstance(payload, dict):
            raise UpstoxOrderTransportError(
                "Upstox JSON response must be an object"
            )

        return payload

    def _post_json(self, path, payload):
        path = self._validate_path(path)
        self._validate_payload(payload)

        url = f"{self.ORDER_BASE_URL}{path}"

        try:
            response = self._session.post(
                url,
                headers=self._headers(),
                json=payload,
                timeout=self._timeout,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            raise UpstoxOrderTransportError(
                "Upstox POST request failed"
            ) from exc

        return self._decode(response)

    def _delete_json(self, path, params=None):
        path = self._validate_path(path)

        if params is not None and not isinstance(params, dict):
            raise UpstoxOrderTransportError(
                "Upstox DELETE parameters must be an object"
            )

        url = f"{self.ORDER_BASE_URL}{path}"

        try:
            response = self._session.delete(
                url,
                headers=self._headers(),
                params=params,
                timeout=self._timeout,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            raise UpstoxOrderTransportError(
                "Upstox DELETE request failed"
            ) from exc

        return self._decode(response)

    def _get_json(self, path, params=None):
        path = self._validate_path(path)

        if params is not None and not isinstance(params, dict):
            raise UpstoxOrderTransportError(
                "Upstox GET parameters must be an object"
            )

        url = f"{self.READ_BASE_URL}{path}"

        try:
            response = self._session.get(
                url,
                headers=self._headers(),
                params=params,
                timeout=self._timeout,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            raise UpstoxOrderTransportError(
                "Upstox GET request failed"
            ) from exc

        return self._decode(response)

    def place_order(self, payload):
        return self._post_json(
            "/v3/order/place",
            payload,
        )

    def cancel_order(self, order_id):
        order_id = str(order_id).strip()

        if not order_id:
            raise UpstoxOrderTransportError(
                "Upstox order_id is unavailable"
            )

        return self._delete_json(
            "/v3/order/cancel",
            params={"order_id": order_id},
        )

    def get_order_details(self, order_id):
        order_id = str(order_id).strip()

        if not order_id:
            raise UpstoxOrderTransportError(
                "Upstox order_id is unavailable"
            )

        return self._get_json(
            "/v2/order/details",
            params={"order_id": order_id},
        )

    def get_order_history(
        self,
        order_id=None,
        tag=None,
    ):
        params = {}

        if order_id is not None:
            order_id = str(order_id).strip()
            if not order_id:
                raise UpstoxOrderTransportError(
                    "Upstox order_id is unavailable"
                )
            params["order_id"] = order_id

        if tag is not None:
            tag = str(tag).strip()
            if not tag:
                raise UpstoxOrderTransportError(
                    "Upstox tag is unavailable"
                )
            params["tag"] = tag

        if not params:
            raise UpstoxOrderTransportError(
                "Either order_id or tag is required"
            )

        return self._get_json(
            "/v2/order/history",
            params=params,
        )

    def get_positions(self):
        return self._get_json(
            "/v2/portfolio/short-term-positions"
        )
