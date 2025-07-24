import pandas as pd
import asyncio
from xpo import get_xpo_eta
from forward import get_forward_eta
from sefl import get_sefl_eta
import io
import sys

# Load the spreadsheet
df = pd.read_excel('testing_report.xlsx')

# The columns you want to update
status_col = 'Status'
date_col = 'Est/Actual Delv Date'
carrier_col = 'Carrier'
bol_col = 'Unishippers BOL#'
pro_col = 'Pro#'

# Helper to capture print output from async tracking functions
async def get_tracking_status(carrier, tracking):
    old_stdout = sys.stdout
    sys.stdout = mystdout = io.StringIO()
    try:
        if carrier.lower() == "xpo":
            await get_xpo_eta(str(tracking))
        elif "forward" in carrier.lower():
            await get_forward_eta(str(tracking))
        elif "sefl" in carrier.lower():
            await get_sefl_eta(str(tracking))
        else:
            print("Unknown carrier")
    finally:
        sys.stdout = old_stdout
    output = mystdout.getvalue().strip()
    # Parse output: expect "Delivered MM/DD/YYYY" or "eta is MM/DD/YYYY"
    if output.lower().startswith("delivered"):
        return "DELIVERED", output.split()[-1]
    elif output.lower().startswith("eta is"):
        return "IN TRANSIT", output.split()[-1]
    else:
        return output, ""

async def main():
    print("Number of rows in spreadsheet:", len(df))
    # Find rows where Status is blank or NaN
    blank_status = df[df[status_col].isna() | (df[status_col].astype(str).str.strip() == '')]
    print(f"Updating {len(blank_status)} rows with blank Status.")
    for idx, row in blank_status.iterrows():
        carrier = str(row[carrier_col]).strip()
        tracking = str(row[pro_col]).strip()
        if not carrier or not tracking or carrier.lower() == 'nan' or tracking.lower() == 'nan':
            print(f"Skipping row {idx+1}: missing carrier or tracking number")
            continue
        status, date = await get_tracking_status(carrier, tracking)
        df.at[idx, status_col] = status
        df.at[idx, date_col] = date
        print(f"Row {idx+1}: {carrier} {tracking} -> {status}, {date}")

    # Save the updated file
    df.to_excel('testing report updated.xlsx', index=False)
    print("Updated file saved as 'testing report updated.xlsx'.")

if __name__ == "__main__":
    asyncio.run(main())