# Daily Events Slack Notifier

Automatically checks Pakistan Expo Centre website for upcoming events and sends daily updates to Slack.

## How it works
- Runs every day at 8:00 AM Pakistan Time
- Scrapes https://pakexcel.com/events-upcoming
- Sends events happening in the next 3 days to Slack

## Setup
1. Add SLACK_WEBHOOK_URL to GitHub Secrets
2. GitHub Actions will run automatically

## Manual trigger
Go to Actions tab → Daily Events Notification → Run workflow

---

## 🎯 What You'll Receive

Every morning at 8 AM, you'll receive a Slack message like this:

```
📅 Upcoming Events - Next 3 Days

1. 11TH PAKISTAN MEGA LEATHER SHOW 2026
🗓️ Jan 24, 2026 - Jan 26, 2026
🔗 https://pmls.pk/

2. SME Cluster Showcase Expo
🗓️ Jan 24, 2026 - Jan 26, 2026

Last checked: Jan 22, 2026 at 08:00 AM
```

---

## 💰 Cost Breakdown

- **GitHub Actions**: FREE (2,000 minutes/month for private repos, unlimited for public)
- **This script uses**: ~1 minute per day = 30 minutes/month
- **Slack Incoming Webhooks**: FREE forever
- **Total cost**: $0.00 ✅

---

## 🔧 Customization Options

### Change notification time:
Edit the cron schedule in `.github/workflows/daily-events.yml`:
```yaml
- cron: '0 3 * * *'  # 8 AM Pakistan Time
# Change to:
- cron: '0 2 * * *'  # 7 AM Pakistan Time
- cron: '30 3 * * *' # 8:30 AM Pakistan Time
```

### Change to weekly instead of daily:
```yaml
- cron: '0 3 * * 1'  # Every Monday at 8 AM
```

### Add more details to messages:
Edit the `send_to_slack()` function in `scrape_events.py`

### Change Slack channel:
In `scrape_events.py`, modify the payload:
```python
payload = {
    "text": message,
    "channel": "#events"  # Add this line
}
```

---

## 🐛 Troubleshooting

### Workflow not running?
- Check Actions tab → enable workflows if disabled
- Verify the cron syntax

### No Slack message?
- Check GitHub Actions logs for errors
- Verify SLACK_WEBHOOK_URL secret is set correctly
- Test webhook manually with:
  ```bash
  curl -X POST -d '{"text":"test"}' YOUR_WEBHOOK_URL
  ```

### Website structure changed?
- Update the scraping logic in `scrape_events.py`
- Check the GitHub Actions logs to see what went wrong

---

## 📋 Files Structure

```
.
├── .github/
│   └── workflows/
│       └── daily-events.yml    # GitHub Actions workflow
├── scrape_events.py            # Python scraper script
└── README.md                   # This file
```

---

## 🚀 Quick Start

1. **Add Slack Webhook to GitHub Secrets**:
   - Go to repository Settings → Secrets and variables → Actions
   - Click "New repository secret"
   - Name: `SLACK_WEBHOOK_URL`
   - Value: Your Slack webhook URL
   - Click "Add secret"

2. **Test immediately**:
   - Go to Actions tab
   - Click "Daily Events Notification"
   - Click "Run workflow"
   - Check your Slack channel!

3. **Sit back and relax** - notifications will arrive every morning at 8 AM PKT 🎉