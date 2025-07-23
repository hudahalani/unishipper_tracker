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

        # ETA extraction: only the first date
        eta_elem = await page.query_selector('div.delivery-date .copy')
        eta_val = None
        if eta_elem:
            label_text = (await eta_elem.text_content()).strip()
            if label_text == "Expected Delivery":
                eta_full = await eta_elem.evaluate('el => el.nextElementSibling ? el.nextElementSibling.textContent.trim() : null')
                if eta_full:
                    # Extract only the first date (MM/DD/YYYY)
                    match = re.search(r"(\d{2}/\d{2}/\d{4})", eta_full)
                    if match:
                        eta_val = match.group(1)

        # Status extraction
        progress_blocks = await page.query_selector_all('div.shipment-progress')
        status_val = None
        for block in progress_blocks:
            label = await block.query_selector('div.copy')
            if label:
                label_text = (await label.text_content()).strip()
                if label_text == "Status:":
                    progress = await label.evaluate_handle('el => el.nextElementSibling')
                    if progress:
                        status_val = (await progress.text_content()).strip()
                        break

        # Print result based on status
        if status_val:
            if "Invoiced" in status_val:
                print("Delivered")
            elif eta_val:
                print(f"eta is {eta_val}")
            else:
                print(status_val)
        else:
            print("Could not find status in modal.")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(get_forward_eta("93588227")) 