import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import os
import json
import time

def scrape_all_pages(base_url="https://pakexcel.com/events-upcoming"):
    """Scrape all pages of events"""
    all_events = []
    page = 0

    while True:
        url = f"{base_url}?page={page}" if page > 0 else base_url
        print(f"\n🌐 Scraping page {page + 1}: {url}")

        try:
            # Add headers to mimic a real browser
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }

            # Retry logic for 503 errors
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    response = requests.get(url, headers=headers, timeout=10)
                    response.raise_for_status()
                    break  # Success, exit retry loop
                except requests.exceptions.HTTPError as e:
                    if e.response.status_code == 503 and attempt < max_retries - 1:
                        wait_time = (attempt + 1) * 2  # 2, 4, 6 seconds
                        print(f"   ⏳ 503 error, retrying in {wait_time}s... (attempt {attempt + 1}/{max_retries})")
                        time.sleep(wait_time)
                    else:
                        raise  # Re-raise if not 503 or last attempt

            soup = BeautifulSoup(response.content, 'html.parser')

            # Find all event items
            event_items = soup.find_all('div', class_='event-item')

            if not event_items:
                print(f"   ⚠️  No events found with selector 'div.event-item' on page {page + 1}")
                # Try alternative selectors for debugging
                alternatives = soup.find_all('div', class_='event-pitem')
                if alternatives:
                    print(f"   💡 Found {len(alternatives)} elements with class 'event-pitem' instead")
                    event_items = alternatives
                else:
                    print(f"   Stopping pagination.")
                    break

            print(f"   ✅ Found {len(event_items)} event containers on page {page + 1}")

            for item in event_items:
                event = extract_event_data(item)
                if event:
                    all_events.append(event)
                    print(f"      ✓ Extracted: {event['title'][:50]}...")
                else:
                    print(f"      ✗ Failed to extract event data from container")

            # Check if there's a next page
            pagination = soup.find('nav', class_='pagination') or soup.find('ul', class_='pagination')
            if pagination:
                next_link = pagination.find('a', string=lambda s: 'Next' in s if s else False)
                if not next_link:
                    print(f"   No 'Next' link found - last page reached")
                    break  # No more pages
            else:
                print(f"   No pagination found - single page or last page")
                break  # No pagination means single page

            page += 1

        except Exception as e:
            print(f"   ❌ Error scraping page {page + 1}: {e}")
            import traceback
            traceback.print_exc()
            break

    return all_events


def extract_event_data(event_item):
    """Extract data from a single event item"""
    try:
        # Event title (required)
        title_elem = event_item.find('h3', class_='event-title')
        if not title_elem:
            return None

        title = title_elem.get_text(strip=True)

        # Dates with datetime attributes (most reliable)
        date_elements = event_item.find_all('time', attrs={'datetime': True})

        if len(date_elements) >= 2:
            start_date_text = date_elements[0].get_text(strip=True)
            end_date_text = date_elements[1].get_text(strip=True)
            start_datetime = date_elements[0].get('datetime')
            end_datetime = date_elements[1].get('datetime')
        elif len(date_elements) == 1:
            # Single date event
            start_date_text = date_elements[0].get_text(strip=True)
            end_date_text = start_date_text
            start_datetime = date_elements[0].get('datetime')
            end_datetime = start_datetime
        else:
            # Fallback: try to find dates without datetime attribute
            start_date_text = "Date not found"
            end_date_text = "Date not found"
            start_datetime = None
            end_datetime = None

        # Details URL (required)
        details_link = event_item.find('a', href=lambda h: h and '/node/' in h)
        details_url = None
        if details_link:
            href = details_link.get('href', '')
            if href.startswith('/'):
                details_url = f"https://pakexcel.com{href}"
            else:
                details_url = href

        # Organizer URL (optional)
        organizer_link = event_item.find('a', target='_blank')
        organizer_url = organizer_link.get('href') if organizer_link else None

        # Event image (optional)
        image_elem = event_item.find('img')
        image_url = None
        if image_elem:
            src = image_elem.get('src', '')
            if src.startswith('/'):
                image_url = f"https://pakexcel.com{src}"
            else:
                image_url = src

        return {
            'title': title,
            'start_date': start_date_text,
            'end_date': end_date_text,
            'start_datetime_iso': start_datetime,
            'end_datetime_iso': end_datetime,
            'details_url': details_url,
            'organizer_url': organizer_url,
            'image_url': image_url
        }

    except Exception as e:
        print(f"Error extracting event data: {e}")
        return None


def filter_events_by_date_range(events, days_ahead=3):
    """Filter events happening within the next X days"""
    today = datetime.utcnow()
    target_date = today + timedelta(days=days_ahead)

    filtered_events = []
    skipped_no_date = []
    skipped_out_of_range = []

    print(f"\n📊 Date Filter Debug:")
    print(f"   Today (UTC): {today.strftime('%b %d, %Y %H:%M')}")
    print(f"   Target date: {target_date.strftime('%b %d, %Y %H:%M')}")
    print(f"   Looking for events between these dates...\n")

    for event in events:
        if not event.get('start_datetime_iso'):
            # Include events without datetime with a warning
            print(f"⚠️  '{event['title']}' - No datetime attribute found, including anyway")
            filtered_events.append(event)
            skipped_no_date.append(event['title'])
            continue

        try:
            # Parse ISO datetime
            event_start = datetime.fromisoformat(event['start_datetime_iso'].replace('Z', '+00:00'))

            # Check if event starts within the date range
            if today <= event_start <= target_date:
                print(f"✅ '{event['title']}' - {event_start.strftime('%b %d, %Y')} - MATCH")
                filtered_events.append(event)
            else:
                print(f"❌ '{event['title']}' - {event_start.strftime('%b %d, %Y')} - OUT OF RANGE")
                skipped_out_of_range.append(f"{event['title']} ({event_start.strftime('%b %d, %Y')})")
        except Exception as e:
            print(f"⚠️  Error parsing date for '{event['title']}': {e}")
            # Include events with parsing errors
            filtered_events.append(event)

    # Summary
    print(f"\n📈 Filter Summary:")
    print(f"   ✅ Matched: {len(filtered_events)}")
    print(f"   ⚠️  No datetime: {len(skipped_no_date)}")
    print(f"   ❌ Out of range: {len(skipped_out_of_range)}")

    return filtered_events


def send_to_slack(events, webhook_url):
    """Send formatted event list to Slack"""
    if not webhook_url:
        print("ERROR: Slack webhook URL not provided")
        return False

    # Build message
    if not events:
        message = "📅 *Upcoming Events - Next 3 Days*\n\n_No events found in the next 3 days._"
    else:
        message = "📅 *Upcoming Events - Next 3 Days*\n\n"

        for i, event in enumerate(events, 1):
            message += f"*{i}. {event['title']}*\n"

            # Date formatting
            if event['start_date'] == event['end_date']:
                message += f"🗓️ {event['start_date']}\n"
            else:
                message += f"🗓️ {event['start_date']} - {event['end_date']}\n"

            # Organizer link
            if event.get('organizer_url'):
                message += f"🔗 {event['organizer_url']}\n"

            # Details link
            if event.get('details_url'):
                message += f"📄 <{event['details_url']}|View Details>\n"

            message += "\n"

    # Add timestamp
    message += f"_Last checked: {datetime.utcnow().strftime('%b %d, %Y at %H:%M UTC')}_"

    # Send to Slack
    try:
        payload = {"text": message}
        response = requests.post(webhook_url, json=payload, timeout=10)

        if response.status_code == 200:
            print("✅ Successfully sent to Slack!")
            return True
        else:
            print(f"❌ Slack API returned status {response.status_code}")
            print(f"Response: {response.text}")
            return False

    except Exception as e:
        print(f"❌ Error sending to Slack: {e}")
        return False


def main():
    """Main execution function"""
    print("=" * 60)
    print("PAKISTAN EXPO EVENTS SCRAPER")
    print("=" * 60)

    # Step 1: Scrape all events from all pages
    print("\n🔍 Step 1: Scraping all events...")
    all_events = scrape_all_pages()
    print(f"\n✅ Found {len(all_events)} total events across all pages")

    # Show all events found (for debugging)
    if all_events:
        print("\n📋 All Events Found:")
        for i, event in enumerate(all_events, 1):
            date_info = f"{event['start_date']} - {event['end_date']}" if event['start_date'] != event['end_date'] else event['start_date']
            has_datetime = "✓" if event.get('start_datetime_iso') else "✗"
            print(f"   {i}. {event['title']}")
            print(f"      Dates: {date_info}")
            print(f"      Has datetime attribute: {has_datetime}")
            if event.get('start_datetime_iso'):
                print(f"      ISO datetime: {event['start_datetime_iso']}")
    else:
        print("\n⚠️ WARNING: No events found! This might indicate:")
        print("   - CSS selector '.event-item' doesn't match the HTML")
        print("   - Website structure has changed")
        print("   - Network/connection issue")

    # Step 2: Filter events happening in next 3 days
    print("\n📅 Step 2: Filtering events for next 3 days...")
    upcoming_events = filter_events_by_date_range(all_events, days_ahead=3)
    print(f"\n✅ Found {len(upcoming_events)} events in the next 3 days")

    # Print filtered events
    if upcoming_events:
        print("\n🎯 Events to be sent to Slack:")
        for event in upcoming_events:
            print(f"  - {event['title']} ({event['start_date']})")
    else:
        print("\n⚠️ No events match the filter criteria")

    # Step 3: Send to Slack
    # Check both WEBHOOK_URL and SLACK_WEBHOOK_URL for flexibility
    webhook_url = os.environ.get('WEBHOOK_URL') or os.environ.get('SLACK_WEBHOOK_URL')

    if not webhook_url:
        print("\n⚠️ WARNING: WEBHOOK_URL or SLACK_WEBHOOK_URL environment variable not set")
        print("Set it with: export WEBHOOK_URL='your_webhook_url'")
        return False

    print("\n📤 Step 3: Sending to Slack...")
    success = send_to_slack(upcoming_events, webhook_url)

    if success:
        print("\n✅ DONE! Check your Slack channel.")
        return True
    else:
        print("\n❌ FAILED to send to Slack")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
