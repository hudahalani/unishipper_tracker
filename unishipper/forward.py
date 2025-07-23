import asyncio
from playwright.async_api import async_playwright
import re

async def get_forward_eta(tracking_number):
    url = f"https://www.forwardair.com/tracking?numbers={tracking_number}"
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        await page.goto(url)
        await page.wait_for_timeout(4000)  # Wait for page to load

        # Try to click the rightmost clickable element in the shipment row
        buttons = await page.query_selector_all('button, a')
        if buttons:
            await buttons[-1].click()
            await page.wait_for_timeout(2000)  # Wait for modal to open
        else:
            await browser.close()
            return

        # Find the 'Current Location' label and get the next .copy element
        location_label = await page.query_selector('div.inputformassistive-text:text("Current Location")')
        if location_label:
            # The location is in the next sibling .copy
            location_value = await location_label.evaluate('el => el.nextElementSibling ? el.nextElementSibling.textContent.trim() : null')
            if location_value:
                if "Invoiced" in location_value:
                    print("Delivered")
                elif "Departed" in location_value:
                    print("On the way")
                else:
                    print(location_value)
            else:
                print("Could not find location value.")
        else:
            print("Could not find 'Current Location' label.")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(get_forward_eta("93573570")) 