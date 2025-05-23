from dateutil.parser import isoparse  # Add this at the top
import requests
import csv
from datetime import datetime
import time

# Configuration
CAMPGROUNDS = {
    'Upper Pines': '232447',
    'Lower Pines': '232446',
    'North Pines': '232445',
    'Hodgdon Meadow': '232450',
    'Wawona': '232449',
    'Bridalveil Creek': '232448'
}
DISCORD_WEBHOOK_URL = 'https://discord.com/api/webhooks/1375267006034743308/C7HYZ1HzgzJbKISqZq1ZHviBmtEhMB56VzRbydHMZexOLpbc5dL1P6FuoLwg6ayQm2ps'
CHECK_MONTHS = ['2025-06', '2025-07', '2025-08', '2025-09']
MIN_CONSECUTIVE_DAYS = 2
LOG_FILE = 'campground_availability_log.csv'

def fetch_availability(facility_id, month):
    url = f'https://www.recreation.gov/api/camps/availability/campground/{facility_id}/month'
    params = {
        'start_date': f'{month}-01T00:00:00.000Z'
    }
    headers = {
        'User-Agent': 'Mozilla/5.0'
    }
    response = requests.get(url, params=params, headers=headers)
    return response.json() if response.status_code == 200 else None

def find_consecutive_availability(data, min_days):
    openings = []
    for site_id, site_data in data.get('campsites', {}).items():
        dates = sorted(site_data['availabilities'].items())
        consecutive = []
        for date_str, status in dates:
            if status == 'Available':
                consecutive.append(date_str)
                if len(consecutive) >= min_days:
                    openings.append((site_id, consecutive[:min_days]))
                    consecutive.pop(0)
            else:
                consecutive = []
    return openings

def send_discord_alert(campground_name, openings):
    if not openings:
        return
    content = f"**Availability Alert: {campground_name}**\n"
    for site_id, dates in openings:
        readable_dates = [isoparse(d).strftime("%b %d") for d in dates]
        content += f"- Site `{site_id}`: {', '.join(readable_dates)}\n"
    payload = {'content': content}
    requests.post(DISCORD_WEBHOOK_URL, json=payload)

def log_to_csv(campground_name, openings):
    with open(LOG_FILE, 'a', newline='') as f:
        writer = csv.writer(f)
        for site_id, dates in openings:
            for d in dates:
                writer.writerow([datetime.utcnow().isoformat(), campground_name, site_id, d])

# Main script logic
for campground_name, facility_id in CAMPGROUNDS.items():
    for month in CHECK_MONTHS:
        data = fetch_availability(facility_id, month)  # ← use loop variable here
        if data:
            openings = find_consecutive_availability(data, MIN_CONSECUTIVE_DAYS)
            send_discord_alert(campground_name, openings)
            log_to_csv(campground_name, openings)
    time.sleep(1)  # Rate limit to be polite

