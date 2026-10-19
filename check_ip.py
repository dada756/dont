import os
import sys
import requests

PROXY_URL = os.getenv(
    "PROXY_URL",
    "http://yamaeroo:tdxs1ohaoh3w@38.154.185.97:6370"
)

proxies = {
    "http": PROXY_URL,
    "https": PROXY_URL,
}

def verify_proxy_ip():
    target_url = "https://api.ipify.org?format=json"
    
    try:
        response = requests.get(target_url, proxies=proxies, timeout=20)
        response.raise_for_status()
        
        data = response.json()
        external_ip = data.get("ip")
        
        print(f"Proxy connection successful.")
        print(f"Detected IP: {external_ip}")
        return external_ip

    except requests.exceptions.ProxyError as e:
        sys.stderr.write(f"Proxy Authentication/Connection Failed: {e}\n")
        sys.exit(1)
    except requests.exceptions.Timeout:
        sys.stderr.write("Connection timed out while reaching ipify through the proxy.\n")
        sys.exit(1)
    except requests.exceptions.RequestException as e:
        sys.stderr.write(f"HTTP request error: {e}\n")
        sys.exit(1)

if __name__ == "__main__":
    verify_proxy_ip()
