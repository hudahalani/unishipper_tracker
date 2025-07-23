import pandas as pd
from datetime import datetime, timedelta
import asyncio
import re

from rnl import get_rl_eta
from sefl import get_sefl_eta
from saia import get_saia_eta
from forward import get_forward_eta

CSV_FILENAME = None
import glob
for file in glob.glob("*.csv"):
    CSV_FILENAME = file
    break

if not CSV_FILENAME:
    print("No CSV file found in the current directory!")
    exit(1)
else:
    print(f"Using CSV file: {CSV_FILENAME}")

def is_today_or_prev_business_day(date_obj):
    today = datetime.now().date()
    weekday = today.weekday()
    if weekday == 0:  # Monday
        prev_business_day = today - timedelta(days=3)
    else:
        prev_business_day = today - timedelta(days=1)
    return date_obj == today or date_obj == prev_business_day

def should_track(row):
    status = str(row.get('Status', '')).lower()
    eta = str(row.get('Estimated Delivery Date', '')).strip()
    if 'void' in status:
        return False
    if 'delivered' in status:
        # Try to parse delivered date from status or eta
        match = re.search(r'(\d{2}/\d{2}/\d{4})', eta)
        if match:
            try:
                delivered_date = datetime.strptime(match.group(1), '%m/%d/%Y').date()
                return is_today_or_prev_business_day(delivered_date)
            except Exception:
                return False
        return False
    return True

async def main():
    df = pd.read_csv(CSV_FILENAME)
    for _, row in df.iterrows():
        if not should_track(row):
            continue
        carrier = str(row['Carrier']).lower()
        tracking_number = str(row['PRO/Tracking#']).strip()
        print(f"\nTracking {tracking_number} with {carrier}...")
        if not tracking_number or tracking_number.lower() == 'nan':
            print("No tracking number available.")
            continue
        if 'r&l' in carrier:
            await get_rl_eta(tracking_number)
        elif 'southeastern' in carrier or 'sefl' in carrier:
            await get_sefl_eta(tracking_number)
        elif 'saia' in carrier:
            await get_saia_eta(tracking_number)
        elif 'forward' in carrier:
            await get_forward_eta(tracking_number)
        else:
            print("Unknown carrier:", carrier)

if __name__ == "__main__":
    asyncio.run(main()) 