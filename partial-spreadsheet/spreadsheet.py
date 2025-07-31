import asyncio
from xpo import get_xpo_eta
from forward import get_forward_eta
from sefl import get_sefl_eta
import io
import sys
import re

# Your provided data as a string
DATA = """
SEFL	BLL18465336	444592458
XPO	BLL18506469	528338366
XPO	BLL18571270	528338370
FORWARD AIR	BLL18833539	93596015
FORWARD AIR	BLL18833551	93596021
"""

async def get_status(carrier, tracking):
    old_stdout = sys.stdout
    sys.stdout = mystdout = io.StringIO()
    try:
        if carrier == "xpo":
            await get_xpo_eta(tracking)
        elif "forward" in carrier:
            await get_forward_eta(tracking)
        elif "sefl" in carrier:
            await get_sefl_eta(tracking)
        else:
            print("Unknown carrier:", carrier)
    finally:
        sys.stdout = old_stdout
    output = mystdout.getvalue().strip().lower()
    print(f"DEBUG OUTPUT for {carrier} {tracking}:", repr(output))  # Debug line
    # --- SEFL: Delivered to Customer ---
    if carrier == "sefl" and "delivered to customer" in output:
        idx = output.find('delivered to customer')
        after = output[idx:]
        # Look for a line starting with 'delivered' and extract the date
        for line in after.splitlines():
            if line.strip().startswith('delivered'):
                date_match = re.search(r'(\d{2}/\d{2}/\d{2,4})', line)
                if date_match:
                    date_str = date_match.group(1)
                    if re.match(r'\d{2}/\d{2}/\d{2}$', date_str):
                        mm, dd, yy = date_str.split('/')
                        year = int(yy)
                        yyyy = 2000 + year if year < 50 else 1900 + year
                        date_str = f"{mm}/{dd}/{yyyy}"
                    return "DELIVERED", date_str
        # fallback: any date in output
        dates = re.findall(r'(\d{2}/\d{2}/\d{2,4})', after)
        if dates:
            return "DELIVERED", dates[-1]
        else:
            return "DELIVERED", ""
    # --- XPO: Delivery Date ---
    if carrier == "xpo" and "delivery date" in output:
        for line in output.splitlines():
            if 'delivery date' in line:
                date_match = re.search(r'(\d{2}/\d{2}/\d{2,4})', line)
                if date_match:
                    date_str = date_match.group(1)
                    if re.match(r'\d{2}/\d{2}/\d{2}$', date_str):
                        mm, dd, yy = date_str.split('/')
                        year = int(yy)
                        yyyy = 2000 + year if year < 50 else 1900 + year
                        date_str = f"{mm}/{dd}/{yyyy}"
                    return "DELIVERED", date_str
        # fallback: any date in output
        dates = re.findall(r'(\d{2}/\d{2}/\d{2,4})', output)
        if dates:
            date_str = dates[-1]
            if re.match(r'\d{2}/\d{2}/\d{2}$', date_str):
                mm, dd, yy = date_str.split('/')
                year = int(yy)
                yyyy = 2000 + year if year < 50 else 1900 + year
                date_str = f"{mm}/{dd}/{yyyy}"
            return "DELIVERED", date_str
        else:
            return "DELIVERED", ""
    # Fallback: eta/delivered
    if output.startswith("delivered"):
        return "DELIVERED", output.split()[-1]
    elif output.startswith("eta is"):
        return "IN TRANSIT", output.split()[-1]
    else:
        return output, ""

async def main():
    lines = [line.strip() for line in DATA.strip().split('\n') if line.strip()]
    for line in lines:
        parts = line.split('\t')
        if len(parts) != 3:
            continue
        carrier, bol, tracking = parts
        carrier_lower = carrier.strip().lower()
        status, date = await get_status(carrier_lower, tracking.strip())
        print(f"{bol}\t{status}\t{date}")

if __name__ == "__main__":
    asyncio.run(main()) 