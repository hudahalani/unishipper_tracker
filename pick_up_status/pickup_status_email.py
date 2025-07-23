import pandas as pd
import pyperclip
import webbrowser
import glob
import os

# Find the CSV file in the pick_up_status folder
csv_file = None
for file in glob.glob('*.csv'):
    csv_file = file
    break

if not csv_file:
    print("No CSV file found in pick_up_status folder!")
    exit(1)

# Read the CSV
df = pd.read_csv(csv_file)

# Filter for rows where status is 'not picked up' (case-insensitive)
not_picked_up = df[df['Status'].str.strip().str.lower().str.replace(' ', '_') == 'pending_pickup']

if not not_picked_up.empty:
    bol_numbers = not_picked_up['BOL #'].astype(str).tolist()
    email_lines = [
        "Hi team,",
        "",
        "Can you please confirm the following are on board for pickup today.",
        "",
    ]
    email_lines.extend(bol_numbers)
    email_lines.append("")
    email_lines.append("Regards,")
    email_body = "\n".join(email_lines).strip()
else:
    email_body = "Hi team,\n\nNo shipments are pending pickup today.\n\nRegards,"

# Copy to clipboard
pyperclip.copy(email_body)
print("Pickup status email copied to clipboard!")

# Draft Outlook web email
to = 'customerservice.bll@unishippers.com'
subject = 'Orbit / PUs'
url = f"https://outlook.office.com/mail/deeplink/compose?to={to}&subject={subject}"
webbrowser.open_new_tab(url)
print("Paste (Ctrl+V) the pickup status email into the message body.") 