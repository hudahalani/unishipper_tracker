import asyncio
from playwright.async_api import async_playwright
import re

async def get_rl_eta(pro_number):
    url = f"https://www2.rlcarriers.com/freight/shipping/shipment-tracing?pro={pro_number}&docType=PRO&source=web"
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        await page.goto(url)
        await page.wait_for_timeout(4000)  # Wait for page to load

        # Try to extract the delivery status line
        delivered_locator = page.locator("text=delivered on time on")
        if await delivered_locator.count() > 0:
            delivered_text = await delivered_locator.first.text_content()
            # Extract the date from the status line
            match = re.search(r"delivered on time on (\d{2}/\d{2}/\d{4})", delivered_text, re.IGNORECASE)
            if match:
                print(f"delivered on {match.group(1)}")
            else:
                print(delivered_text.strip())
        else:
            # Try to find "Est. Delivery Date" if not delivered
            eta_locator = page.locator("text=Est. Delivery Date")
            if await eta_locator.count() > 0:
                eta_row = eta_locator.first
                parent = await eta_row.evaluate_handle("el => el.parentElement")
                parent_text = await parent.evaluate("el => el.textContent")
                print("ETA row:", parent_text.strip())
            else:
                print("Could not find delivery status or ETA.")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(get_rl_eta("I313183413"))