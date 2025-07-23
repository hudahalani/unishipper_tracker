import pandas as pd
from datetime import datetime, timedelta
import asyncio
import re
import io
import sys

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
    results = []
    for _, row in df.iterrows():
        if not should_track(row):
            continue
        carrier = str(row['Carrier']).lower()
        tracking_number = str(row['PRO/Tracking#']).strip()
        bol = str(row['BOL #']).strip()
        if not tracking_number or tracking_number.lower() == 'nan':
            result = f"BOL: {bol}\nCarrier: {carrier}\nPRO: {tracking_number}\nStatus: No tracking number available.\n{'-'*30}"
            results.append(result)
            continue
        try:
            old_stdout = sys.stdout
            new_stdout = io.StringIO()
            sys.stdout = new_stdout
            if 'r&l' in carrier or 'rl carriers' in carrier:
                await get_rl_eta(tracking_number)
            elif 'southeastern' in carrier or 'sefl' in carrier:
                await get_sefl_eta(tracking_number)
            elif 'saia' in carrier:
                await get_saia_eta(tracking_number)
            elif 'forward' in carrier:
                await get_forward_eta(tracking_number)
            else:
                print("Unknown carrier:", carrier)
            sys.stdout = old_stdout
            status = new_stdout.getvalue().strip()
        except Exception as e:
            sys.stdout = old_stdout
            status = f"Error: {str(e)}"
        result = f"BOL: {bol}\nCarrier: {carrier}\nPRO: {tracking_number}\nStatus: {status}\n{'-'*30}"
        results.append(result)
    # Write all results to a file
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"tracking_results_{timestamp}.txt"
    with open(filename, 'w') as f:
        f.write("Unishippers Tracking Results\n" + "="*50 + "\n\n")
        for r in results:
            f.write(r + "\n")
    print(f"Tracking results saved to: {filename}")

if __name__ == "__main__":
    asyncio.run(main()) 