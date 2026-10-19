import os
import sys
import random
from curl_cffi import requests
from curl_cffi.requests.errors import RequestsError

PROXY_URL = os.getenv(
    "PROXY_URL",
    "http://yamaeroo:tdxs1ohaoh3w@38.154.185.97:6370"
)

def verify_proxy_ip():
    # ipify will reflect the IP. If you want to see the headers sent, 
    # you could switch this to "https://httpbin.org/headers" for debugging.
    target_url = "https://api.ipify.org?format=json"

    # Generating some dummy values for the dynamic fields
    dynamic_phone = f"9198{random.randint(10000000, 99999999)}"
    dynamic_email = f"testuser{random.randint(100, 999)}@example.com"
    dynamic_ua = "Mozilla/5.0 (Linux; Android 13; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Mobile Safari/537.36"

    headers = {
        "X-Latitude": "17.385044",
        "X-Subregion-Code": "HYD",
        "X-App-Code": "MOBAND2",
        "X-Phone": dynamic_phone,
        "User-Agent": dynamic_ua,
        "X-Longitude": "78.48667",
        "X-Platform": "AND",
        "X-Region-Code": "HYD",
        "X-Platform-Code": "ANDROID",
        "X-Email": dynamic_email,
        "Content-Type": "text/plain; charset=utf-8",
        "Accept-Encoding": "gzip, deflate, br"
    }

    try:
        response = requests.get(
            target_url,
            headers=headers,
            proxy=PROXY_URL,
            timeout=20,
            impersonate="chrome110_android" # Changed to Android to match your X-Platform headers
        )
        response.raise_for_status()

        data = response.json()
        external_ip = data.get("ip")

        print("Proxy connection successful.")
        print(f"Detected IP: {external_ip}")
        print(f"Using Phone: {dynamic_phone}")
        print(f"Using Email: {dynamic_email}")
        
        return external_ip

    except RequestsError as e:
        sys.stderr.write(f"Proxy request error via curl_cffi: {e}\n")
        sys.exit(1)
    except Exception as e:
        sys.stderr.write(f"Unexpected error: {e}\n")
        sys.exit(1)

if __name__ == "__main__":
    verify_proxy_ip()
