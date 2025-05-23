# yosemite_campgrounds

# 🏕️ Yosemite Permit & Campground Availability Notifier

This repo provides two Python scripts designed to **monitor** and **alert** on wilderness permit and campground availability in Yosemite National Park. Ideal for tracking **John Muir Trail (JMT)** entry points and **high-demand campsites**.

---

## 📂 Scripts

### `jmt_discord_scraper.py`
A Selenium-powered headless browser that:
- Navigates [Recreation.gov](https://www.recreation.gov/permits/445859) permit portal
- Adds a single group member to enable permit visibility
- Iterates through 75+ days of permit availability
- Extracts quota information for these trailheads:
  - **Happy Isles → Past LYV (Donohue Pass Eligible)**
  - **Cathedral Lakes**
  - **Lyell Canyon (Donohue Pass Eligible)**
  - **Rafferty Creek → Vogelsang**
  - **Mono Meadow**
  - **Sunrise (No Donohue Pass)**
- Sends updates via Discord webhook if permits are available

🔧 **Debug Logging:**  
Console prints track each trailhead, button interaction, window advancement, and availability payloads.

---

### `yosemite_availability_checker.py`
A lightweight, API-based script that:
- Queries campground availability via `https://www.recreation.gov/api/camps/availability/...`
- Scans popular Yosemite campgrounds (e.g., North Pines, Lower Pines, Upper Pines)
- Searches for **2+ consecutive nights** of availability in the configured month
- Posts Discord alerts when matches are found

🧪 **Purpose:** Ideal for casual Yosemite campers who want alerts about hard-to-book spots.

---

## 🔌 Dependencies

- Python 3.9+ recommended
- `selenium`
- `requests`
- `python-dateutil`
- A headless-compatible Chromium browser & chromedriver

---

## ⚙️ Install

Clone the repo and run:

```bash
./setup.sh

python3 -m venv myenv
source myenv/bin/activate
pip install -r requirements.txt

0  * * * * /home/YOUR_USER/myenv/bin/python /path/to/jmt_discord_scraper.py >> /path/to/log.txt 2>&1
10 * * * * /home/YOUR_USER/myenv/bin/python /path/to/yosemite_availability_checker.py >> /path/to/campground_log.txt 2>&1

DISCORD_WEBHOOK_URL = 'https://discord.com/api/webhooks/...'

🚧 Known Limitations
Recreation.gov occasionally changes DOM structure

Permit pages load slowly or timeout — handled with retries

Discord webhooks should not be spammed — consider using caching or state diffing

🧠 Author's Note
This project was built to enable stress-free wilderness planning. Don’t let permit systems ruin your shot at the high Sierra. 🌄

Pull requests welcome!


---

## 🔧 `setup.sh`

```bash
#!/bin/bash

echo "🔧 Creating Python virtual environment..."
python3 -m venv myenv
source myenv/bin/activate

echo "📦 Installing dependencies..."
pip install -U pip
pip install selenium requests python-dateutil

echo "🎉 Setup complete."
echo "✅ Run scripts with: source myenv/bin/activate && python your_script.py"
