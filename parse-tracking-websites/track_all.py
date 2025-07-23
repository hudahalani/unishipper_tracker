import pandas as pd
from datetime import datetime, timedelta
import asyncio
import re
import io
import sys
import pyperclip
import webbrowser
import os

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
    email_lines = ["Hey Muhammad,", ""]
    for _, row in df.iterrows():
        if not should_track(row):
            continue
        bol = str(row['BOL #']).strip()
        tracking_number = str(row['PRO/Tracking#']).strip()
        carrier = str(row['Carrier']).lower()
        if not tracking_number or tracking_number.lower() == 'nan':
            status = "not picked up yet"
        else:
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
                if status.lower().startswith('eta is'):
                    # Capitalize 'ETA is' for consistency
                    status = 'ETA is' + status[6:]
            except Exception as e:
                sys.stdout = old_stdout
                status = f"Error: {str(e)}"
        email_lines.append(bol)
        email_lines.append(status)
        email_lines.append("")  # blank line between shipments

    email_body = "\n".join(email_lines).strip()

    # Write to file
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"tracking_results_{timestamp}.txt"
    with open(filename, 'w') as f:
        f.write(email_body)
    print(f"Tracking results saved to: {filename}")

    # Copy results to clipboard and open Outlook web compose page
    pyperclip.copy(email_body)
    print("Tracking results copied to clipboard!")
    to = os.getenv('UNISHIPPER_EMAILS', 'your@email.com;another@email.com')
    subject = 'Unishipper Tracking'
    url = f"https://outlook.office.com/mail/deeplink/compose?to={to}&subject={subject}"
    webbrowser.open_new_tab(url)
    print("Paste (Ctrl+V) the tracking results into the email body.")

if __name__ == "__main__":
    asyncio.run(main()) 