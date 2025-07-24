import asyncio
from playwright.async_api import async_playwright
import re
from datetime import datetime

async def get_xpo_eta(tracking_number):
    url = f"https://ext-web.ltl-xpo.com/public-app/shipments?referenceNumber={tracking_number}"
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        try:
            await page.goto(url, timeout=90000)
            # Wait for the 'Shipment Details' tab to be visible and click it
            try:
                await page.wait_for_selector('div.mat-tab-label-content:has-text("Shipment Details")', state='visible', timeout=10000)
                shipment_details_btn = await page.query_selector('div.mat-tab-label-content:has-text("Shipment Details")')
                if shipment_details_btn:
                    await shipment_details_btn.click(force=True)
                    await page.wait_for_timeout(1000)
                else:
                    print("Shipment Details tab not found or not visible. Printing all tab texts for debugging:")
                    tab_labels = await page.query_selector_all('div.mat-tab-label-content')
                    for tab in tab_labels:
                        print(await tab.text_content())
            except Exception as e:
                print(f"Could not click 'Shipment Details' tab: {e}")
                tab_labels = await page.query_selector_all('div.mat-tab-label-content')
                for tab in tab_labels:
                    print(await tab.text_content())
                pass  # If not found, continue
            # Wait for the Estimated Delivery Date label to appear
            await page.wait_for_selector(':text("Estimated Delivery Date")', timeout=30000)
            # Find the label and extract the date value next to it
            all_text = await page.inner_text('body')
            # Use regex to find 'ESTIMATED DELIVERY DATE' (case-insensitive) followed by a date
            match = re.search(r'ESTIMATED DELIVERY DATE\s*([0-9]{2}/[0-9]{2}/[0-9]{2,4})', all_text, re.IGNORECASE)
            if match:
                # Convert MM/DD/YY to MM/DD/YYYY if needed
                date_str = match.group(1)
                if re.match(r'\d{2}/\d{2}/\d{2}$', date_str):
                    # Expand 2-digit year
                    mm, dd, yy = date_str.split('/')
                    year = int(yy)
                    if year < 50:
                        yyyy = 2000 + year
                    else:
                        yyyy = 1900 + year
                    date_str = f"{mm}/{dd}/{yyyy}"
                print(f"eta is {date_str}")
            else:
                print("Could not find Estimated Delivery Date in page text.")
                print(all_text)
        except Exception as e:
            print(f"Error: {str(e)}")
        finally:
            await browser.close()

# For manual testing
if __name__ == "__main__":
    import sys
    tracking = sys.argv[1] if len(sys.argv) > 1 else ""
    if tracking:
        asyncio.run(get_xpo_eta(tracking))
    else:
        print("Usage: python xpo.py <tracking_number>")