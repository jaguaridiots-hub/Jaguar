"""
Jaguar Quant X Enterprise
Provider Credential Boundary v1

Purpose:
Provide a single runtime boundary for external market-data
provider credentials.

Security contract:
- Credentials are read from environment variables only.
- Credentials are never embedded in source code.
- Credentials are never loaded from settings.json.
- Credential values are never printed or logged.
- Importing this module performs no network request.
"""

import os


class ProviderCredentialError(RuntimeError):
    """
    Raised when a required provider credential is unavailable.
    """


class ProviderCredentials:
    """
    Environment-backed provider credential facade.
    """

    UPSTOX_ACCESS_TOKEN_ENV = "UPSTOX_ACCESS_TOKEN"

    @staticmethod
    def _read_environment(name):
        """
        Read and normalize an environment variable.
        """

        value = os.getenv(name)

        if value is None:
            return None

        value = value.strip()

        if not value:
            return None

        return value

    @classmethod
    def upstox_access_token(
        cls,
        required=True,
    ):
        """
        Return the Upstox access token.

        When required=True, missing credentials fail closed.
        """

        token = cls._read_environment(
            cls.UPSTOX_ACCESS_TOKEN_ENV
        )

        if token is None and required:

            raise ProviderCredentialError(
                "Required provider credential is unavailable: "
                f"{cls.UPSTOX_ACCESS_TOKEN_ENV}"
            )

        return token

    @classmethod
    def upstox_configured(cls):
        """
        Return whether an Upstox access token is configured.
        """

        return (
            cls.upstox_access_token(
                required=False
            )
            is not None
        )
