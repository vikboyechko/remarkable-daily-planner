# Daily Calendar Generator for reMarkable Paper Pro Move

Generate customizable PDF daily planners optimized for the reMarkable Paper Pro Move. Import events from Google Calendar, Outlook, or any iCal feed to create simple daily schedules.

## 🔒 Privacy First

**Your data stays private:**
- No calendar data is stored or logged
- No URLs are saved or tracked
- PDFs are automatically deleted immediately after download
- Zero data persistence - everything is processed in memory

## ✨ Features

- **Multiple Calendar Support**: Google Calendar, Outlook, Apple Calendar, or any iCal feed
- **Smart Layout**: Automatic event positioning with overflow handling
- **All-Day Events**: If an all day event exists, show it, otherwise hide
- **Customizable Time Range**: Choose your daily schedule hours (8-12 hour range)
- **Optional To-Do Section**: Add checkboxes and lines for daily tasks
- **Optimized for reMarkable**: Perfect dimensions (954 x 1696 pixels, 264 PPI)

## 🚀 Quick Start

### Option 1: Use the Hosted Version
Visit the hosted app at [https://remarkable-daily-planner.onrender.com/](https://remarkable-daily-planner.onrender.com/) - no setup required!

### Option 2: Run Locally

1. **Clone the repository:**
   ```bash
   git clone https://github.com/vikboyechko/remarkable-daily-planner.git
   cd remarkable-daily-planner
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the app:**
   ```bash
   python app.py
   ```

4. **Open your browser:**
   Navigate to `http://localhost:5000`

## 📅 Getting Your Calendar Links

### Google Calendar

1. Open [Google Calendar](https://calendar.google.com)
2. On the left sidebar, find your calendar and click the three dots (⋮)
3. Select **"Settings and sharing"**
4. Scroll down to **"Integrate calendar"**
5. Copy the **"Secret address in iCal format"** link
6. ⚠️ **Important**: Use the **secret** link, not the public one, for private events

### Outlook Calendar

1. Open [Outlook Calendar](https://outlook.live.com/calendar)
2. Click **"Settings"** (gear icon) → **"View all Outlook settings"**
3. Go to **"Calendar"** → **"Shared calendars"**
4. Under **"Publish a calendar"**, select your calendar
5. Choose **"Can view all details"** for private events
6. Click **"Publish"** and copy the **ICS link**

### Apple Calendar (iCloud)

1. Open [iCloud Calendar](https://www.icloud.com/calendar)
2. Click the share icon next to your calendar name
3. Check **"Public Calendar"**
4. Copy the provided link and change `webcal://` to `https://`

### Other Calendar Apps

Most calendar applications support iCal export. Look for:
- "Export calendar" or "Share calendar"
- "iCal feed" or "ICS link"
- "Calendar URL" or "Subscription link"

## 🎯 Usage Tips

- **Multiple Calendars**: Separate multiple iCal URLs with commas
- **Time Range**: Choose 8-12 hour ranges (e.g., 6 AM - 5 PM)
- **Date Range**: Generate single days or multi-day planners
- **To-Do Section**: Toggle on/off based on your preference

## 🛠️ Technical Details

- **Frontend**: HTML, CSS, vanilla JavaScript
- **Backend**: Python Flask
- **PDF Generation**: ReportLab
- **Calendar Parsing**: icalendar library with full RRULE support
- **Deployment**: Ready for Render, Heroku, or any Python hosting

## 📱 Device Compatibility

Optimized for reMarkable Paper Pro Move, but it can easily be adapted for other Remarkable devices or eink tablets by adjusting the PDF dimensions in `app.py`.
