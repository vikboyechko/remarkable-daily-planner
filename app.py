from flask import Flask, render_template, request, jsonify, send_file
from datetime import datetime, timedelta
import os
from calendar_fetcher import CalendarFetcher
from pdf_generator import PDFGenerator

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/generate', methods=['POST'])
def generate_calendar():
    try:
        # get form data
        ical_urls = request.form.get('ical_urls', '').strip()
        start_date_str = request.form.get('start_date', '')
        end_date_str = request.form.get('end_date', '')
        start_hour = int(request.form.get('start_hour', 6))
        end_hour = int(request.form.get('end_hour', 17))
        show_todos = request.form.get('show_todos') == 'on'  # Checkbox sends 'on' when checked

        # auto-detect computer timezone
        from datetime import datetime as dt
        # get the local timezone name in a more reliable way
        local_tz = dt.now().astimezone().tzinfo.tzname(None)
        # convert common abbreviations to full timezone names
        timezone_map = {
            'EST': 'America/New_York', 'EDT': 'America/New_York',
            'CST': 'America/Chicago', 'CDT': 'America/Chicago',
            'MST': 'America/Denver', 'MDT': 'America/Denver',
            'PST': 'America/Los_Angeles', 'PDT': 'America/Los_Angeles'
        }
        timezone = timezone_map.get(local_tz, 'America/Chicago')  # Default to Chicago if unknown

        # validate inputs
        if not ical_urls:
            return jsonify({'error': 'Please provide at least one iCal URL'}), 400

        # validate time range (8-12 hours)
        duration = end_hour - start_hour
        if duration < 8:
            return jsonify({'error': 'Time range must be at least 8 hours'}), 400
        if duration > 12:
            return jsonify({'error': 'Time range cannot exceed 12 hours'}), 400

        # parse start date or default to next Monday
        if start_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        else:
            today = datetime.now().date()
            days_ahead = 0 - today.weekday()  # Monday is 0
            if days_ahead <= 0:
                days_ahead += 7
            start_date = today + timedelta(days=days_ahead)

        # parse end date or default to 7 days from start (minus 1 to make it inclusive)
        if end_date_str:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        else:
            end_date = start_date + timedelta(days=6)  # 7 days total (inclusive)

        # validate date range
        if end_date < start_date:
            return jsonify({'error': 'End date must be on or after start date'}), 400

        # fetch calendar events with timezone
        fetcher = CalendarFetcher(ical_urls, timezone)
        events = fetcher.fetch_events(start_date, end_date)


        # generate filename based on date range
        if start_date == end_date:
            # single day: just month-day
            filename = f"{start_date.month}-{start_date.day}.pdf"
        else:
            # date range: month-day to month-day
            filename = f"{start_date.month}-{start_date.day}-to-{end_date.month}-{end_date.day}.pdf"
        output_path = os.path.join('output', filename)
        os.makedirs('output', exist_ok=True)

        generator = PDFGenerator()
        generator.generate_pdf(start_date, end_date, events, output_path, start_hour, end_hour, show_todos)

        # return the PDF file directly for download and remove from server
        try:
            response = send_file(output_path, as_attachment=True, download_name=filename)
            # delete the file after sending
            if os.path.exists(output_path):
                os.remove(output_path)
            return response
        except Exception as e:
            # clean up file if send fails
            if os.path.exists(output_path):
                os.remove(output_path)
            raise e

    except Exception as e:
        return jsonify({'error': 'An error occurred generating the calendar'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)