"""
Jaguar Quant X Enterprise
Provider Credential Contract v1

Purpose:
Prove environment-only credential access and fail-closed
provider credential behaviour.

No real credential is required.
No network request is executed.
"""

import os

from config.provider_credentials import (
    ProviderCredentialError,
    ProviderCredentials,
)


ENV_NAME = (
    ProviderCredentials.UPSTOX_ACCESS_TOKEN_ENV
)

TEST_TOKEN = "JAGUAR_TEST_TOKEN_DO_NOT_USE"


def main():

    original_present = ENV_NAME in os.environ
    original_value = os.environ.get(ENV_NAME)

    failures = []

    try:

        # ==================================================
        # MISSING OPTIONAL CREDENTIAL
        # ==================================================

        os.environ.pop(
            ENV_NAME,
            None,
        )

        actual = (
            ProviderCredentials.upstox_access_token(
                required=False
            )
        )

        if actual is not None:

            failures.append(
                {
                    "contract": "OPTIONAL_MISSING",
                    "actual": actual,
                }
            )

        # ==================================================
        # MISSING REQUIRED CREDENTIAL FAILS CLOSED
        # ==================================================

        try:

            ProviderCredentials.upstox_access_token(
                required=True
            )

        except ProviderCredentialError as exc:

            message = str(exc)

            if ENV_NAME not in message:

                failures.append(
                    {
                        "contract": "ERROR_MESSAGE",
                        "actual": message,
                    }
                )

        else:

            failures.append(
                {
                    "contract": "REQUIRED_FAIL_CLOSED",
                    "actual": "CREDENTIAL ACCESS ALLOWED",
                }
            )

        # ==================================================
        # BLANK CREDENTIAL NORMALIZES TO MISSING
        # ==================================================

        os.environ[ENV_NAME] = "   "

        actual = (
            ProviderCredentials.upstox_access_token(
                required=False
            )
        )

        if actual is not None:

            failures.append(
                {
                    "contract": "BLANK_NORMALIZATION",
                    "actual": actual,
                }
            )

        # ==================================================
        # ENVIRONMENT CREDENTIAL ACCESS
        # ==================================================

        os.environ[ENV_NAME] = (
            f"  {TEST_TOKEN}  "
        )

        actual = (
            ProviderCredentials.upstox_access_token()
        )

        if actual != TEST_TOKEN:

            failures.append(
                {
                    "contract": "ENVIRONMENT_ACCESS",
                    "expected": TEST_TOKEN,
                    "actual": actual,
                }
            )

        # ==================================================
        # CONFIGURED STATE
        # ==================================================

        if not ProviderCredentials.upstox_configured():

            failures.append(
                {
                    "contract": "CONFIGURED_STATE",
                    "actual": False,
                }
            )

    finally:

        if original_present:

            os.environ[ENV_NAME] = (
                original_value
                if original_value is not None
                else ""
            )

        else:

            os.environ.pop(
                ENV_NAME,
                None,
            )

    # ======================================================
    # RESULT
    # ======================================================

    if failures:

        print(
            "PROVIDER_CREDENTIAL_CONTRACT: FAIL"
        )

        for failure in failures:

            print(
                "FAIL:",
                failure,
            )

        raise AssertionError(
            "Provider credential contract violated"
        )

    print(
        "PROVIDER_CREDENTIAL_CONTRACT: PASS"
    )

    print(
        "Environment:",
        ENV_NAME,
    )

    print(
        "Credential source: ENVIRONMENT_ONLY"
    )

    print(
        "Network required: NO"
    )


if __name__ == "__main__":
    main()
