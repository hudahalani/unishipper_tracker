import asyncio
from playwright.async_api import async_playwright
import pandas as pd
from datetime import datetime, timedelta
import win32com.client as win32
from dateutil import parser as date_parser
import os
import glob

# --- CONFIG ---
CARRIER_TRACKING_URLS = {
    'FORWARD AIR': 'https://www.forwardair.com/tracking',
    'SOUTHEASTERN FREIGHT LINES': 'https://sefl.com/Tracing/index.jsp',
    'RL CARRIERS': 'https://www2.rlcarriers.com/freight/shipping/shipment-tracing',
    'SAIA': 'https://www.saia.com/track',
    'XPO LOGISTICS': 'https://www.xpo.com/track/',
}

EMAIL_SUBJECT = 'Unishippers Tracking'
EMAIL_GREETING = 'Hey Muhammad,'
CSV_FILENAME = None
for file in glob.glob("*.csv"):
    CSV_FILENAME = file
    break

if not CSV_FILENAME:
    print("No CSV file found in the current directory!")
    exit(1)
else:
    print(f"Using CSV file: {CSV_FILENAME}")

# --- MAIN SCRIPT ---
async def main():
    # 1. Read the CSV file
    if not os.path.exists(CSV_FILENAME):
        print(f'CSV file {CSV_FILENAME} not found!')
        return
    df = pd.read_csv(CSV_FILENAME)

    # 2. Prepare shipment list
    shipments = []
    for _, row in df.iterrows():
        carrier = str(row['Carrier']).strip().upper()
        bol = str(row['BOL #']).strip()
        pro = str(row['PRO/Tracking#']).strip()
        eta = str(row.get('Estimated Delivery Date', '')).strip()
        status = str(row.get('Status', '')).strip().lower()
        if 'void' in status:
            continue  # Skip voided shipments
        shipment = {
            'carrier': carrier,
            'bol': bol,
            'pro': pro,
            'eta': None,
            'raw_eta': eta,
            'status': status,  # include status for email formatting
        }
        # If tracking number is empty, mark as pending pickup
        if not pro or pro.lower() == 'nan':
            shipment['eta'] = 'Pending Pickup'
        shipments.append(shipment)

    # 3. Track shipments with tracking numbers
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        for shipment in shipments:
            if shipment['eta'] == 'Pending Pickup':
                continue
            carrier = shipment['carrier']
            pro = shipment['pro']
            tracking_url = get_tracking_url(carrier)
            if not tracking_url:
                shipment['eta'] = 'Unknown Carrier'
                continue
            # TODO: Implement carrier-specific tracking and ETA parsing
            # shipment['eta'] = await track_and_parse_eta(page, tracking_url, carrier, pro)
            shipment['eta'] = shipment['raw_eta'] if shipment['raw_eta'] else 'TBD (tracking not yet implemented)'
        await browser.close()

    # 4. Filter shipments: not delivered or delivered within last 3 days
    filtered_shipments = filter_shipments(shipments)

    # 5. Draft Outlook email
    draft_outlook_email(filtered_shipments)

def get_tracking_url(carrier):
    for key in CARRIER_TRACKING_URLS:
        if key in carrier:
            return CARRIER_TRACKING_URLS[key]
    return None

def filter_shipments(shipments):
    filtered = []
    now = datetime.now()
    for s in shipments:
        eta = s.get('eta', '').lower()
        if eta == 'pending pickup' or eta == 'unknown carrier' or eta == 'tbd (tracking not yet implemented)':
            filtered.append(s)
        else:
            try:
                eta_date = date_parser.parse(eta, fuzzy=True)
                if eta_date >= now - timedelta(days=3):
                    filtered.append(s)
            except Exception:
                filtered.append(s)  # If can't parse, include just in case
    return filtered

def draft_outlook_email(shipments):
    outlook = win32.Dispatch('outlook.application')
    mail = outlook.CreateItem(0)
    mail.Subject = EMAIL_SUBJECT
    body = f"<p>{EMAIL_GREETING}</p>"
    for s in shipments:
        bol_line = f"<div>{s['bol']}</div>"
        eta_val = s.get('eta', 'N/A')
        status = str(s.get('status', '')).lower()
        if s.get('eta', '').lower() == 'pending pickup':
            eta_line = '<div><span style="background-color: yellow">not picked up</span></div>'
        elif 'delivered' in status:
            try:
                eta_date = date_parser.parse(eta_val, fuzzy=True)
                eta_str = eta_date.strftime('%m/%d')
            except Exception:
                eta_str = eta_val
            eta_line = f'<div><span style="background-color: yellow">delivered on {eta_str}</span></div>'
        elif 'in transit' in status:
            try:
                eta_date = date_parser.parse(eta_val, fuzzy=True)
                eta_str = eta_date.strftime('%m/%d')
            except Exception:
                eta_str = eta_val
            eta_line = f'<div><span style="background-color: yellow">eta is {eta_str}</span></div>'
        else:
            try:
                eta_date = date_parser.parse(eta_val, fuzzy=True)
                eta_str = eta_date.strftime('%m/%d')
            except Exception:
                eta_str = eta_val
            eta_line = f'<div><span style="background-color: yellow">ETA is {eta_str}</span></div>'
        body += bol_line + eta_line + "<br>"
    mail.HTMLBody = body.strip()
    mail.Display()  # Opens the draft for review

if __name__ == '__main__':
    asyncio.run(main()) 