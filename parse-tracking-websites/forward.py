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

        # Directly target the SVG path with the exact d attribute
        arrow_svg_selector = 'svg > path[d="M10 6 8.59 7.41 13.17 12l-4.58 4.59L10 18l6-6z"]'
        arrow_path = await page.query_selector(arrow_svg_selector)
        if arrow_path:
            parent = await arrow_path.evaluate_handle('el => el.closest("button,a")')
            await parent.click()
            await page.wait_for_timeout(2000)  # Wait for modal to open
        else:
            print("Could not find the right arrow SVG path.")
            await browser.close()
            return

        # Extract ETA from the correct div after clicking the arrow
        eta_div = await page.query_selector('div.header.--small.headline')
        if eta_div:
            eta_text = (await eta_div.text_content()).strip()
            # Try to extract only the date (MM/DD/YYYY) from the text
            match = re.search(r'(\d{2}/\d{2}/\d{4})', eta_text)
            if match:
                print(f"eta is {match.group(1)}")
                await browser.close()
                return
            else:
                print(f"Found ETA div but could not extract date: {eta_text}")
                await browser.close()
                return
        else:
            print("Could not find ETA div after clicking arrow.")
            await browser.close()
            return

if __name__ == "__main__":
    asyncio.run(get_forward_eta("93588227")) 