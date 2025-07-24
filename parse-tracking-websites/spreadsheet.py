import asyncio
from xpo import get_xpo_eta
from forward import get_forward_eta
from sefl import get_sefl_eta
import io
import sys

# Your provided data as a string
DATA = """
XPO	BLL18314110	528338333
SEFL	BLL18465336	444592458
XPO	BLL18506469	528338366
XPO	BLL18571270	528338370
FORWARD AIR	BLL18833539	93596015
XPO	BLL18833544	528338403
FORWARD AIR	BLL18833551	93596021
FORWARD AIR	BLL18833553	93596026
FORWARD AIR	BLL18833557	93596030
FORWARD AIR	BLL18833559	93596033
FORWARD AIR	BLL18833569	93596037
FORWARD AIR	BLL18833576	93596038
FORWARD AIR	BLL18833590	93596040
FORWARD AIR	BLL18833629	93596050
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
    # Special handling for SEFL: check for 'delivered to customer'
    if carrier == "sefl" and "delivered to customer" in output:
        # Try to extract the delivered date
        import re
        match = re.search(r'delivered\s*(\d{2}/\d{2}/\d{4})', output)
        if match:
            return "DELIVERED", match.group(1)
        else:
            return "DELIVERED", ""
    # Parse output: expect "Delivered MM/DD/YYYY" or "eta is MM/DD/YYYY"
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