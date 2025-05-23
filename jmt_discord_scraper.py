import time
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

# ---------- Config ----------
DISCORD_WEBHOOK_URL = 'https://discord.com/api/webhooks/1375267006034743308/C7HYZ1HzgzJbKISqZq1ZHviBmtEhMB56VzRbydHMZexOLpbc5dL1P6FuoLwg6ayQm2ps'
LYELL_TRAILHEADS = [
    "Happy Isles->Past LYV (Donohue Pass Eligible)",
    "Cathedral Lakes",
    "Lyell Canyon (Donohue Pass Eligible)",
    "Rafferty Creek->Vogelsang",
    "Mono Meadow",
    "Sunrise (No Donohue Pass)"
]

# ---------- Setup Browser ----------
options = Options()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
chrome_path = "/usr/bin/chromium-browser"
chromedriver_path = "/usr/local/bin/chromedriver"
options.binary_location = chrome_path
service = Service(executable_path=chromedriver_path)
driver = webdriver.Chrome(service=service, options=options)

driver.get("https://www.recreation.gov/permits/445859/registration/detailed-availability")
time.sleep(5)

# ---------- Add 1 participant ----------
try:
    group_button = driver.find_element(By.ID, "guest-counter")
    group_button.click()
    time.sleep(1)
    add_button = driver.find_element(By.CSS_SELECTOR, "button[aria-label='Add Peoples']")
    add_button.click()
    print("👥 Opened group member selector")
    time.sleep(1)
    from selenium.webdriver.common.action_chains import ActionChains
    from selenium.webdriver.common.keys import Keys
    ActionChains(driver).send_keys(Keys.ESCAPE).perform()
    print("➕ Added 1 participant")
    print("❌ Closed group selector popup")
except Exception as e:
    print(f"⚠️ Group size setup failed: {e}")

time.sleep(3)
print("✅ Grid loaded")

# ---------- Scrape Function ----------
from datetime import datetime, timedelta

base_date = datetime(2025, 5, 22)  # first visible date in window 0
all_availability = []

for window_index in range(22):  # assuming 22 windows
    # 👇 advance to next window if not window 0
    if window_index > 0:
        try:
            next_button = driver.find_element(By.CSS_SELECTOR, "button.sarsa-button.sarsa-button-link.sarsa-button-xs.ml-1.mr-2")
            next_button.click()
            print(f"📆 Advanced to window {window_index}")
            time.sleep(2)
        except Exception as e:
            print(f"⚠️ Could not advance calendar at window {window_index}: {e}")
            break

    # 👇 grab trailhead rows
    trailhead_rows = driver.find_elements(By.CSS_SELECTOR, "div.rec-grid-row.is-small-grid")
    for row in trailhead_rows:
        cells = row.find_elements(By.CSS_SELECTOR, "div.rec-grid-grid-cell button[aria-label]")
        if not cells:
            continue

        trailhead_name = cells[0].get_attribute("aria-label").strip()
        if trailhead_name not in LYELL_TRAILHEADS:
            print(f"🔍 Skipping trailhead: {trailhead_name}")
            continue

        print(f"🛤️ Trailhead match: {trailhead_name}")
        for day_index, cell in enumerate(cells[1:]):  # skip first (trailhead name)
            label = cell.get_attribute("aria-label").strip()
            print(f"🔘 Cell label: {label}")

            if "People:" in label:
                parts = label.split("\n")
                if len(parts) == 2:
                    _, people_info = parts
                    people_count = people_info.strip().replace("People:", "").strip()
                    try:
                        used, total = [int(x) for x in people_count.split(" out of ")]
                        if used > 0:
                            real_date = base_date + timedelta(days=(window_index * 5 + day_index))
                            label_str = real_date.strftime("%a %b %d")  # e.g., "Mon May 27"
                            all_availability.append((trailhead_name, label_str, f"{used} of {total}"))
                    except ValueError:
                        continue

# ---------- Deduplicate and Sort ----------
# Step 1: Build dict to dedupe by (trailhead, date)
deduped = {}
for trailhead, date, status in all_availability:
    deduped[(trailhead, date)] = status  # latest status wins

# Step 2: Rebuild list
deduped_availability = [(th, dt, st) for (th, dt), st in deduped.items()]

# Step 3: Sort by actual calendar date
def parse_date_label(label):
    try:
        parts = label.split()
        if len(parts) != 2:
            return datetime.max  # junk to bottom
        fake_date_str = f"2025-06-{int(parts[1]):02d}"
        return datetime.strptime(fake_date_str, "%Y-%m-%d")
    except Exception:
        return datetime.max

from datetime import datetime
import requests

# ---------- Send to Discord ----------
def send_discord_alert(data):
    if not data:
        print("✅ No Donohue-eligible permits found.")
        return

    content = "**🎟️ Donohue-Eligible Permit Availability**\n"
    for trailhead, date, status in data:
        try:
            content += f"- `{trailhead}` on **{date}**: `{status}`\n"
        except Exception as e:
            print(f"⚠️ Error formatting row: {trailhead}, {date}, {status} — {e}")

    print("🧾 Final message payload:\n" + content)

    try:
        resp = requests.post(DISCORD_WEBHOOK_URL, json={"content": content})
        if resp.status_code != 204:
            print(f"⚠️ Discord rejected the post: {resp.status_code} {resp.text}")
        else:
            print("📡 Sent to Discord ✅")
    except Exception as e:
        print(f"❌ Discord webhook failed: {e}")


# ---------- Deduplicate and Sort ----------
# Step 1: Dedupe using dict
deduped = {}
for trailhead, date, status in all_availability:
    deduped[(trailhead, date)] = status  # latest status wins

deduped_availability = [(th, dt, st) for (th, dt), st in deduped.items()]

# Step 2: Sort chronologically
def parse_date_label(label):
    try:
        parts = label.split()
        if len(parts) != 2:
            return datetime.max
        fake_date_str = f"2025-06-{int(parts[1]):02d}"
        return datetime.strptime(fake_date_str, "%Y-%m-%d")
    except Exception:
        return datetime.max

deduped_availability.sort(key=lambda x: parse_date_label(x[1]))

# Step 3: Send once
send_discord_alert(deduped_availability)
driver.quit()

