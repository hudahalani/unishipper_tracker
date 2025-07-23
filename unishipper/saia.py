import asyncio
from playwright.async_api import async_playwright
import re

async def get_saia_eta(tracking_number):
    url = "https://www.saia.com/track"
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        await page.goto(url)
        # Wait for the textarea to be visible
        await page.wait_for_selector('textarea', state='visible', timeout=20000)

        # Fill the Pro Number textarea
        await page.fill('textarea', tracking_number)
        print("Filled the textarea with the tracking number.")

        print("Please solve the captcha manually, then click TRACK.")
        input("Press Enter after you have solved the captcha and clicked TRACK...")

        # Wait for results to load
        await page.wait_for_timeout(5000)

        # Get the full page text and extract the delivery or estimated delivery date
        full_text = await page.inner_text('body')

        delivered_match = re.search(r"Delivered\\s+(\\d{2}/\\d{2}/\\d{4})", full_text)
        if delivered_match:
            print("Delivered", delivered_match.group(1))
        else:
            eta_match = re.search(r"Estimated Delivery:?\\s*(\\d{2}/\\d{2}/\\d{4})", full_text)
            if eta_match:
                print("eta is", eta_match.group(1))
            else:
                print("Could not find delivery or estimated delivery date.")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(get_saia_eta("10776626490")) 