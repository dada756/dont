import os
import sys
from curl_cffi import requests
from curl_cffi.requests.errors import RequestsError

PROXY_URL = os.getenv(
    "PROXY_URL",
    "http://yamaeroo:tdxs1ohaoh3w@38.154.185.97:6370"
)

def verify_proxy_ip():
    target_url = "https://api.ipify.org?format=json"

    try:
        response = requests.get(
            target_url,
            proxy=PROXY_URL,
            timeout=20,
            impersonate="chrome"
        )
        response.raise_for_status()

        data = response.json()
        external_ip = data.get("ip")

        print("Proxy connection successful.")
        print(f"Detected IP: {external_ip}")
        return external_ip

    except RequestsError as e:
        sys.stderr.write(f"Proxy request error via curl_cffi: {e}\n")
        sys.exit(1)
    except Exception as e:
        sys.stderr.write(f"Unexpected error: {e}\n")
        sys.exit(1)

if __name__ == "__main__":
    verify_proxy_ip()
