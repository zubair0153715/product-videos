"""Screenshot helper: renders pages with system Chromium through the VM's
egress proxy (auth read from env, never printed or logged)."""
import asyncio
import os
import sys
import urllib.parse

sys.path.insert(0, "/home/hatch/workspace/harvey-sales-agent/.venv/lib/python3.12/site-packages")


async def shoot(url: str, out_path: str, width: int = 390, height: int = 844,
                full_page: bool = False):
    from playwright.async_api import async_playwright

    proxy_url = os.environ.get("https_proxy") or os.environ.get("HTTPS_PROXY") or ""
    parsed = urllib.parse.urlparse(proxy_url)
    proxy = None
    if parsed.hostname:
        proxy = {"server": f"{parsed.scheme}://{parsed.hostname}:{parsed.port or 3128}"}
        if parsed.username:
            proxy["username"] = urllib.parse.unquote(parsed.username)
            proxy["password"] = urllib.parse.unquote(parsed.password or "")

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            executable_path="/opt/meta-chromium/chrome",
            args=["--no-sandbox", "--disable-gpu"],
            proxy=proxy,
        )
        page = await browser.new_page(viewport={"width": width, "height": height})
        await page.goto(url, wait_until="networkidle", timeout=45000)
        await page.wait_for_timeout(1500)
        await page.screenshot(path=out_path, full_page=full_page)
        await browser.close()
    print("saved", out_path)


if __name__ == "__main__":
    # usage: shoot.py <url> <out.png> [width] [height]
    url, out = sys.argv[1], sys.argv[2]
    w = int(sys.argv[3]) if len(sys.argv) > 3 else 390
    h = int(sys.argv[4]) if len(sys.argv) > 4 else 844
    asyncio.run(shoot(url, out, w, h))
