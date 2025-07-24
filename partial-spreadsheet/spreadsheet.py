import asyncio
from xpo import get_xpo_eta
from forward import get_forward_eta
from sefl import get_sefl_eta

# Your provided data as a string
DATA = """
FORWARD AIR	BLL18570731	93557504
SEFL	BLL18571017	444592784
SEFL	BLL18571643	444592792
SEFL	BLL18571949	444592806
SEFL	BLL18620213	444592822
SEFL	BLL18620348	444592814
"""

async def main():
    lines = [line.strip() for line in DATA.strip().split('\n') if line.strip()]
    for line in lines:
        parts = line.split('\t')
        if len(parts) != 3:
            continue
        carrier, bol, tracking = parts
        print(bol)
        carrier_lower = carrier.strip().lower()
        if carrier_lower == "xpo":
            await get_xpo_eta(tracking.strip())
        elif "forward" in carrier_lower:
            await get_forward_eta(tracking.strip())
        elif "sefl" in carrier_lower:
            await get_sefl_eta(tracking.strip())
        else:
            print("Unknown carrier:", carrier)
        print()  # Blank line between shipments

if __name__ == "__main__":
    asyncio.run(main()) 