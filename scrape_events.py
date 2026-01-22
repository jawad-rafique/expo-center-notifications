import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import os
import json

def get_upcoming_events():
    """Scrape events from Pakistan Expo website"""
    url = "https://pakexcel.com/events-upcoming"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        # Calculate date range (next 3 days)
        today = datetime.now()
        three_days_later = today + timedelta(days=3)

        events = []

        # Find all event containers
        event_sections = soup.find_all('div', class_='views-row')

        if not event_sections:
            # Fallback: try to find event titles and dates
            titles = soup.find_all(['h2', 'h3'])
            for title in titles:
                event_name = title.get_text(strip=True)
                if event_name and len(event_name) > 5:
                    # Try to find dates near this title
                    parent = title.find_parent()
                    dates = parent.find_all('time') if parent else []

                    if dates and len(dates) >= 2:
                        start_date = dates[0].get_text(strip=True)
                        end_date = dates[1].get_text(strip=True) if len(dates) > 1 else start_date

                        # Try to find organizer link
                        organizer_link = parent.find('a', href=True, string=lambda s: 'Organizer' in s if s else False)
                        organizer = organizer_link['href'] if organizer_link else None

                        # Parse date to check if within 3 days
                        try:
                            event_start = datetime.strptime(start_date, "%b %d, %Y")
                            if today <= event_start <= three_days_later:
                                events.append({
                                    'name': event_name,
                                    'start_date': start_date,
                                    'end_date': end_date,
                                    'organizer': organizer
                                })
                        except:
                            # If date parsing fails, include all events found
                            events.append({
                                'name': event_name,
                                'start_date': start_date,
                                'end_date': end_date,
                                'organizer': organizer
                            })

        return events

    except Exception as e:
        print(f"Error scraping events: {e}")
        return []

def send_to_slack(events):
    """Send events to Slack webhook"""
    webhook_url = os.environ.get('SLACK_WEBHOOK_URL')

    if not webhook_url:
        print("ERROR: SLACK_WEBHOOK_URL not set in environment variables")
        return False

    # Build message
    if not events:
        message = "📅 *Upcoming Events - Next 3 Days*\n\nNo events found in the next 3 days."
    else:
        message = "📅 *Upcoming Events - Next 3 Days*\n\n"

        for i, event in enumerate(events, 1):
            message += f"*{i}. {event['name']}*\n"
            message += f"🗓️ {event['start_date']}"
            if event['end_date'] != event['start_date']:
                message += f" - {event['end_date']}"
            message += "\n"

            if event.get('organizer'):
                message += f"🔗 {event['organizer']}\n"

            message += "\n"

    message += f"_Last checked: {datetime.now().strftime('%b %d, %Y at %I:%M %p')}_"

    # Send to Slack
    try:
        payload = {"text": message}
        response = requests.post(webhook_url, json=payload, timeout=10)

        if response.status_code == 200:
            print("✅ Successfully sent to Slack!")
            print(f"Message: {message}")
            return True
        else:
            print(f"❌ Failed to send to Slack. Status: {response.status_code}")
            print(f"Response: {response.text}")
            return False

    except Exception as e:
        print(f"❌ Error sending to Slack: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Scraping upcoming events...")
    events = get_upcoming_events()

    print(f"📋 Found {len(events)} event(s) in the next 3 days")
    for event in events:
        print(f"  - {event['name']}")

    print("\n📤 Sending to Slack...")
    success = send_to_slack(events)

    if success:
        print("✅ Done!")
    else:
        print("❌ Failed to send notification")
        exit(1)
