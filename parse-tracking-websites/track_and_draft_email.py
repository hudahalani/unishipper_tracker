import asyncio
from playwright.async_api import async_playwright
import pandas as pd
from datetime import datetime, timedelta
import os
import glob
import re
import io
import sys

# Import carrier tracking functions
from rnl import get_rl_eta
from sefl import get_sefl_eta
from saia import get_saia_eta
from forward import get_forward_eta

# --- CONFIG ---
CARRIER_TRACKING_URLS = {
    'FORWARD AIR': 'https://www.forwardair.com/tracking',
    'SOUTHEASTERN FREIGHT LINES': 'https://sefl.com/Tracing/index.jsp',
    'RL CARRIERS': 'https://www2.rlcarriers.com/freight/shipping/shipment-tracing',
    'SAIA': 'https://www.saia.com/track',
    'XPO LOGISTICS': 'https://www.xpo.com/track/',
}

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
        if 'voided' in status:
            continue  # Skip voided shipments
        shipment = {
            'carrier': carrier,
            'bol': bol,
            'pro': pro,
            'eta': None,
            'raw_eta': eta,
            'status': status,
        }
        # If tracking number is empty, mark as pending pickup
        if not pro or pro.lower() == 'nan':
            shipment['eta'] = 'Pending Pickup'
        shipments.append(shipment)

    # 3. Track shipments with tracking numbers using carrier-specific functions
    for shipment in shipments:
        if shipment['eta'] == 'Pending Pickup':
            continue
        carrier = shipment['carrier'].lower()
        pro = shipment['pro']
        
        try:
            if 'r&l' in carrier:
                # Capture the output from get_rl_eta
                old_stdout = sys.stdout
                new_stdout = io.StringIO()
                sys.stdout = new_stdout
                await get_rl_eta(pro)
                output = new_stdout.getvalue().strip()
                sys.stdout = old_stdout
                shipment['eta'] = output
            elif 'southeastern' in carrier or 'sefl' in carrier:
                old_stdout = sys.stdout
                new_stdout = io.StringIO()
                sys.stdout = new_stdout
                await get_sefl_eta(pro)
                output = new_stdout.getvalue().strip()
                sys.stdout = old_stdout
                shipment['eta'] = output
            elif 'saia' in carrier:
                old_stdout = sys.stdout
                new_stdout = io.StringIO()
                sys.stdout = new_stdout
                await get_saia_eta(pro)
                output = new_stdout.getvalue().strip()
                sys.stdout = old_stdout
                shipment['eta'] = output
            elif 'forward' in carrier:
                old_stdout = sys.stdout
                new_stdout = io.StringIO()
                sys.stdout = new_stdout
                await get_forward_eta(pro)
                output = new_stdout.getvalue().strip()
                sys.stdout = old_stdout
                shipment['eta'] = output
            else:
                shipment['eta'] = 'Unknown Carrier'
        except Exception as e:
            shipment['eta'] = f'Error: {str(e)}'

    # 4. Filter shipments: not delivered or delivered within last 3 days
    filtered_shipments = filter_shipments(shipments)

    # 5. Write results to file
    write_results_to_file(filtered_shipments)

def get_tracking_url(carrier):
    for key in CARRIER_TRACKING_URLS:
        if key in carrier:
            return CARRIER_TRACKING_URLS[key]
    return None

def is_today_or_prev_business_day(date_obj):
    today = datetime.now().date()
    weekday = today.weekday()
    if weekday == 0:  # Monday
        prev_business_day = today - timedelta(days=3)
    else:
        prev_business_day = today - timedelta(days=1)
    return date_obj == today or date_obj == prev_business_day

def filter_shipments(shipments):
    filtered = []
    for s in shipments:
        status = s.get('status', '').lower()
        eta = s.get('eta', '').lower()
        if 'void' in status:
            continue  # Skip void/voided
        if 'delivered' in status:
            # Try to parse the delivered date from eta
            match = re.search(r'(\d{2}/\d{2}/\d{4})', eta)
            if match:
                try:
                    delivered_date = datetime.strptime(match.group(1), '%m/%d/%Y').date()
                    if is_today_or_prev_business_day(delivered_date):
                        filtered.append(s)
                except Exception:
                    continue  # Skip if date can't be parsed
            # If can't parse, skip
        else:
            filtered.append(s)
    return filtered

def write_results_to_file(shipments):
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"tracking_results_{timestamp}.txt"
    
    with open(filename, 'w') as f:
        f.write("Unishippers Tracking Results\n")
        f.write("=" * 50 + "\n\n")
        
        for s in shipments:
            f.write(f"BOL: {s['bol']}\n")
            f.write(f"Carrier: {s['carrier']}\n")
            f.write(f"PRO: {s['pro']}\n")
            f.write(f"Status: {s.get('eta', 'N/A')}\n")
            f.write("-" * 30 + "\n")
    
    print(f"Tracking results saved to: {filename}")

if __name__ == '__main__':
    asyncio.run(main()) 