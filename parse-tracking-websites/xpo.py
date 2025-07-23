import asyncio
from playwright.async_api import async_playwright

async def get_xpo_eta(tracking_number):
    url = f"https://ext-web.ltl-xpo.com/public-app/shipments?referenceNumber={tracking_number}"
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        await page.goto(url)
        await page.wait_for_timeout(5000)  # Wait for JS to load

        # Find the event in the shipment history that says "The shipment has been delivered to the recipient."
        delivered_event = page.locator("text=The shipment has been delivered to the recipient.")
        if await delivered_event.count() > 0:
            print("Delivered")
        else:
            print("No delivered event found.")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(get_xpo_eta("502156863"))