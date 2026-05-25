import asyncio
import httpx
import time
import re
from typing import Set, Dict, Any
import os

# ==========================================
# ⚙️ CONFIGURATION & CREDENTIALS
# ==========================================

# Define pagination boundaries
START_PAGE = 1
END_PAGE = 5  # Change this to whatever page you want to stop at

# Paste your cookies and tokens here before execution
COOKIES = {
    "auth_token": "0ebc62618ca6ee0009bfd15dc79cf3c3882fe7c6",
    "_ga": "GA1.1.416671207.1779705207",
    "cf_clearance": "EtFqi7eB_sTqw92rygkwnJqNQxSDz0hrViVJ5kvMZNI-1779705206-1.2.1.1-ghUrwmy4NWa1X.9Xh06EA9ZGTto9FYfLs9i2mzYF8yxEC990QrIJTmwEUGfG2GfsU3VCN.yv0VscBq96UEKdU1K_4v7QgtNOqsUEMrCqVAgfOmTqKv2mTqrLTrmuyaY1pH2DzoiHYSsivH_VyNfuIMm2lG9FnYcz7856X4WBSDnT6OmspkI_fl9PsrhhUp.RpCZDWoYH3ffEe2a00q0Qj_tQvQiNdEPReooRVBl3g168FetBHswjah..IKQzP4G.V6tAR6a8EP3ew6pgMCAMhVMNRtN7MmDJoWevyj9Cc.tX6ATvoPJPmug2OA9lFa3pItN10On8DQMJLDsO8sVlHrv8QlqVbrK2P7Kkp0lpLQcjNdfzJFORfEmldHYLkuDmkhCweF8QjcEZrbnIJk8j5CuTgWAKzj7637AET68TCTw",
    "_ga_707F2E8WDS": "GS2.1.s1779705206$o1$g1$t1779705546$j22$l0$h0"
}

API_HEADERS = {
    "Accept-Language": "en-US,en;q=0.9",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
    "Accept": "*/*",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Dest": "empty",
    "Accept-Encoding": "gzip, deflate, br",
    "Priority": "u=1, i"
}

IMAGE_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
    "Accept": "image/avif,*/*;q=1.0",
    "Sec-Fetch-Site": "same-site",
    "Sec-Fetch-Mode": "no-cors",
    "Sec-Fetch-Dest": "image",
    "Priority": "0",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache"
}

BASE_URL = "https://mysite.in"

# ==========================================
# 🛠️ HELPER FUNCTIONS
# ==========================================

def extract_image_urls_recursively(data: Any, urls_set: Set[str]):
    if isinstance(data, dict):
        for key, value in data.items():
            if key in ["image", "full_image"] and isinstance(value, str) and value.startswith("http"):
                urls_set.add(value)
            else:
                extract_image_urls_recursively(value, urls_set)
    elif isinstance(data, list):
        for item in data:
            extract_image_urls_recursively(item, urls_set)

def format_size(size_in_bytes: int) -> str:
    if size_in_bytes >= 1024 * 1024:
        return f"{size_in_bytes / (1024 * 1024):.2f} MB"
    return f"{size_in_bytes / 1024:.2f} KB"

# ==========================================
# 🚀 ASYNC WORKERS
# ==========================================

async def fetch_image_size(client: httpx.AsyncClient, url: str, semaphore: asyncio.Semaphore) -> Dict[str, Any]:
    async with semaphore:
        try:
            headers = IMAGE_HEADERS.copy()
            headers["Referer"] = BASE_URL + "/"
            
            response = await client.head(url, headers=headers, follow_redirects=True, timeout=15.0)
            
            if "Content-Length" in response.headers:
                return {"url": url, "size_bytes": int(response.headers["Content-Length"])}
            
            size = 0
            async with client.stream("GET", url, headers=headers, follow_redirects=True, timeout=15.0) as stream_response:
                async for chunk in stream_response.aiter_bytes():
                    size += len(chunk)
            return {"url": url, "size_bytes": size}

        except Exception as e:
            print(f"[Warning] Failed to fetch size for {url} - {str(e)}")
            return {"url": url, "size_bytes": 0}

async def main():
    print(f"🚀 Starting Media Size Profiling Script (Pages {START_PAGE} to {END_PAGE})...")
    
    all_slugs = []
    all_image_urls = set()
    
    async with httpx.AsyncClient(http2=True, cookies=COOKIES, headers=API_HEADERS, timeout=30.0) as client:
        
        # ---------------------------------------------------------
        # PHASE 1: Fetch Schedule Pages & Extract Slugs
        # ---------------------------------------------------------
        print(f"\n⏳ [Phase 1] Fetching Schedule pages from {START_PAGE} to {END_PAGE}...")
        current_page = START_PAGE
        resolved_end_page = END_PAGE 
        
        while current_page <= resolved_end_page:
            schedule_url = f"{BASE_URL}/api/schedule?timeFilter=released&page={current_page}"
            headers = API_HEADERS.copy()
            headers["Referer"] = f"{BASE_URL}/schedule?timeFilter=today"
            
            try:
                resp = await client.get(schedule_url, headers=headers)
                resp.raise_for_status()
                data = resp.json()
                
                if current_page == START_PAGE:
                    api_total_pages = data.get("total_pages", END_PAGE)
                    resolved_end_page = min(END_PAGE, api_total_pages)
                    print(f"   -> API indicates {api_total_pages} total pages available. Will process up to page {resolved_end_page}.")
                
                items = data.get("data", [])
                for item in items:
                    content = item.get("content", {})
                    slug = content.get("slug")
                    if slug:
                        all_slugs.append(slug)
                
                print(f"   -> Fetched page {current_page}/{resolved_end_page}...")
            except Exception as e:
                print(f"[Error] Failed to fetch schedule page {current_page}: {e}")
            
            current_page += 1
            await asyncio.sleep(0.5) 
            
        print(f"✅ Extracted {len(all_slugs)} slugs successfully.")
        
        # ---------------------------------------------------------
        # PHASE 2: Fetch Content Details & Extract Images
        # ---------------------------------------------------------
        print(f"\n⏳ [Phase 2] Fetching content details for {len(all_slugs)} slugs...")
        for i, slug in enumerate(all_slugs, 1):
            details_url = f"{BASE_URL}/api/library/content/{slug}"
            headers = API_HEADERS.copy()
            headers["Referer"] = f"{BASE_URL}/content/{slug}"
            
            try:
                resp = await client.get(details_url, headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    extract_image_urls_recursively(data, all_image_urls)
            except Exception as e:
                pass # Silently continue on individual slug failures
            
            if i % 100 == 0:
                print(f"   -> Processed {i}/{len(all_slugs)} slugs...")
                
            await asyncio.sleep(0.5)
            
        print(f"✅ Found {len(all_image_urls)} unique image URLs to evaluate.")

        # ---------------------------------------------------------
        # PHASE 3: Fetch Exact Image Sizes (Concurrent)
        # ---------------------------------------------------------
        print("\n⏳ [Phase 3] Resolving exact image sizes from CDN...")
        semaphore = asyncio.Semaphore(50)
        tasks = [fetch_image_size(client, url, semaphore) for url in all_image_urls]
        results = await asyncio.gather(*tasks)

    # ---------------------------------------------------------
    # PHASE 4: Sort, Print, and Save Top 50 Heaviest Images
    # ---------------------------------------------------------
    print("\n✅ Processing Complete. Sorting and saving data...")
    
    valid_results = [r for r in results if r["size_bytes"] > 0]
    sorted_images = sorted(valid_results, key=lambda x: x["size_bytes"], reverse=True)
    top_50 = sorted_images[:50]

    # Print to logs
    print("\n" + "="*80)
    print(f"🔥 TOP 50 HEAVIEST IMAGES (Pages {START_PAGE}-{resolved_end_page}) 🔥")
    print("="*80 + "\n")
    
    for idx, item in enumerate(top_50, 1):
        size_str = format_size(item["size_bytes"])
        print(f"{idx:02d}. [{size_str}]")
        print(f"    URL: {item['url']}\n")

    # Save to file
    filename = f"top_50_{START_PAGE}_to_{resolved_end_page}.txt"
    filepath = os.path.join(os.getcwd(), filename)
    
    with open(filepath, "w", encoding="utf-8") as f:
        for item in top_50:
            size_str = format_size(item["size_bytes"])
            f.write(f"{size_str} | {item['url']}\n")
            
    print(f"💾 Results successfully saved to: {filename}")

if __name__ == "__main__":
    asyncio.run(main())
