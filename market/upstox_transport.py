"""
Jaguar Quant X Enterprise
Upstox HTTP Transport v1

Purpose:
Provide the isolated HTTP transport boundary for Upstox
market-data APIs.

Transport responsibilities:
- construct provider URLs
- percent-encode path identities
- attach provider authorization
- enforce request timeout
- validate HTTP status
- decode JSON responses

This module does not:
- resolve Jaguar symbols
- select futures contracts
- normalize candle records
- execute requests at import time
"""

from urllib.parse import quote

import requests

from config.provider_credentials import (
    ProviderCredentials,
)


class UpstoxTransportError(RuntimeError):
    """
    Raised when Upstox transport or response handling fails.
    """


class UpstoxTransport:
    """
    Isolated Upstox REST transport.
    """

    BASE_URL = "https://api.upstox.com"

    DEFAULT_TIMEOUT = 10

    def __init__(
        self,
        access_token=None,
        session=None,
        timeout=DEFAULT_TIMEOUT,
    ):
        if access_token is None:

            access_token = (
                ProviderCredentials
                .upstox_access_token()
            )

        access_token = str(
            access_token
        ).strip()

        if not access_token:

            raise UpstoxTransportError(
                "Upstox access token is unavailable"
            )

        try:
            timeout = float(timeout)

        except (TypeError, ValueError) as exc:

            raise UpstoxTransportError(
                "Invalid Upstox request timeout: "
                f"{timeout!r}"
            ) from exc

        if timeout <= 0:

            raise UpstoxTransportError(
                "Upstox request timeout must be positive"
            )

        self._access_token = access_token

        self._session = (
            session
            if session is not None
            else requests.Session()
        )

        self._timeout = timeout

    @staticmethod
    def _encode_path_value(value):
        """
        Percent-encode one provider path identity.
        """

        value = str(
            value
            if value is not None
            else ""
        ).strip()

        if not value:

            raise UpstoxTransportError(
                "Upstox path value is unavailable"
            )

        return quote(
            value,
            safe="",
        )

    def _headers(self):
        """
        Build provider headers without exposing credentials.
        """

        return {
            "Accept": "application/json",
            "Authorization": (
                f"Bearer {self._access_token}"
            ),
        }

    def _get_json(
        self,
        path,
        params=None,
    ):
        """
        Execute one Upstox GET request and decode JSON.
        """

        if not isinstance(path, str):

            raise UpstoxTransportError(
                "Upstox request path must be a string"
            )

        path = path.strip()

        if not path.startswith("/"):

            raise UpstoxTransportError(
                "Upstox request path must start with '/'"
            )

        url = (
            f"{self.BASE_URL}"
            f"{path}"
        )

        try:

            response = self._session.get(
                url,
                headers=self._headers(),
                params=params,
                timeout=self._timeout,
            )

            response.raise_for_status()

        except requests.RequestException as exc:

            raise UpstoxTransportError(
                "Upstox GET request failed"
            ) from exc

        try:

            payload = response.json()

        except (TypeError, ValueError) as exc:

            raise UpstoxTransportError(
                "Upstox response is not valid JSON"
            ) from exc

        if not isinstance(payload, dict):

            raise UpstoxTransportError(
                "Upstox JSON response must be an object"
            )

        return payload

    def search_instruments(
        self,
        query,
        exchange=None,
        segment=None,
        instrument_type=None,
    ):
        """
        Search Upstox instruments.

        Pagination is intentionally not abstracted yet.
        The raw provider response is returned.
        """

        query = str(
            query
            if query is not None
            else ""
        ).strip()

        if not query:

            raise UpstoxTransportError(
                "Instrument search query is unavailable"
            )

        params = {
            "query": query,
        }

        if exchange is not None:
            params["exchange"] = str(
                exchange
            ).strip()

        if segment is not None:
            params["segment"] = str(
                segment
            ).strip()

        if instrument_type is not None:
            params["instrument_type"] = str(
                instrument_type
            ).strip()

        return self._get_json(
            "/instruments/search",
            params=params,
        )

    def historical_candles(
        self,
        instrument_key,
        unit,
        interval,
        to_date,
        from_date,
    ):
        """
        Fetch Upstox Historical Candle Data V3.
        """

        encoded_key = self._encode_path_value(
            instrument_key
        )

        encoded_unit = self._encode_path_value(
            unit
        )

        encoded_interval = self._encode_path_value(
            interval
        )

        encoded_to_date = self._encode_path_value(
            to_date
        )

        encoded_from_date = self._encode_path_value(
            from_date
        )

        path = (
            "/v3/historical-candle/"
            f"{encoded_key}/"
            f"{encoded_unit}/"
            f"{encoded_interval}/"
            f"{encoded_to_date}/"
            f"{encoded_from_date}"
        )

        return self._get_json(path)

    def intraday_candles(
        self,
        instrument_key,
        unit,
        interval,
    ):
        """
        Fetch Upstox Intraday Candle Data V3.
        """

        encoded_key = self._encode_path_value(
            instrument_key
        )

        encoded_unit = self._encode_path_value(
            unit
        )

        encoded_interval = self._encode_path_value(
            interval
        )

        path = (
            "/v3/historical-candle/intraday/"
            f"{encoded_key}/"
            f"{encoded_unit}/"
            f"{encoded_interval}"
        )

        return self._get_json(path)
