import asyncio
from playwright.async_api import async_playwright
import re

async def get_sefl_eta(tracking_number):
    url = "https://sefl.com/Tracing/index.jsp"
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        await page.goto(url)
        await page.wait_for_timeout(3000)  # Wait for page to load

        # Fill the Reference Numbers textarea
        textareas = await page.query_selector_all('textarea')
        if textareas:
            await textareas[0].fill(tracking_number)
        else:
            await browser.close()
            return

        # Click the 'Submit Trace' button
        await page.get_by_role("button", name="Submit Trace").click()

        # Wait for results to load
        await page.wait_for_timeout(5000)

        # Get the full page text and extract the delivery or estimated delivery date
        full_text = await page.inner_text('body')

        # Try to find "Delivered MM/DD/YYYY"
        delivered_match = re.search(r"Delivered\s+(\d{2}/\d{2}/\d{4})", full_text)
        if delivered_match:
            print("Delivered", delivered_match.group(1))
        else:
            # If not delivered, try to find "Estimated Delivery: MM/DD/YYYY"
            eta_match = re.search(r"Estimated Delivery:\s*(\d{2}/\d{2}/\d{4})", full_text)
            if eta_match:
                print("eta is", eta_match.group(1))
            else:
                print("Could not find delivery or estimated delivery date.")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(get_sefl_eta("413238172")) 