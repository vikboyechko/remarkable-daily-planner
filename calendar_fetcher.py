import requests
from icalendar import Calendar
from datetime import datetime, timedelta, date
import pytz
from dateutil import rrule
from dateutil.rrule import rrulestr

class CalendarFetcher:
    def __init__(self, urls, timezone='America/Chicago'):
        self.urls = [url.strip() for url in urls.split(',') if url.strip()]
        try:
            self.local_tz = pytz.timezone(timezone)
        except:
            self.local_tz = pytz.timezone('America/Chicago')

    def fetch_events(self, start_date, end_date):
        """
        Returns list of events in format:
        [
            {
                'start': datetime_object,
                'end': datetime_object,
                'title': 'Event Title',
                'date': 'YYYY-MM-DD'
            }
        ]
        """
        all_events = []

        for url in self.urls:
            try:
                # try to force fresh data from ICS
                import time
                cache_buster = int(time.time())
                url_with_cache_buster = f"{url}&_cb={cache_buster}" if '?' in url else f"{url}?_cb={cache_buster}"

                response = requests.get(url_with_cache_buster, timeout=30, headers={
                    'Cache-Control': 'no-cache',
                    'Pragma': 'no-cache'
                })
                response.raise_for_status()

                cal = Calendar.from_ical(response.content)

                for component in cal.walk():
                    if component.name == "VEVENT":
                        # check for recurring events
                        if component.get('RRULE'):
                            recurring_events = self._parse_recurring_event(component, start_date, end_date)
                            all_events.extend(recurring_events)
                        else:
                            # single event
                            event = self._parse_event(component, start_date, end_date)
                            if event:
                                all_events.append(event)

            except Exception as e:
                continue

        # sort events, handling both date and datetime objects
        def sort_key(event):
            start = event['start']
            if isinstance(start, datetime):
                # ensure datetime is timezone-aware
                if start.tzinfo is None:
                    return self.local_tz.localize(start)
                return start
            else:
                # convert date to timezone-aware datetime for sorting purposes only
                dt = datetime.combine(start, datetime.min.time())
                return self.local_tz.localize(dt)

        return sorted(all_events, key=sort_key)

    def _parse_event(self, event, start_date, end_date):
        """Parse individual event and return formatted dict if in date range"""
        try:
            dtstart = event.get('dtstart')
            dtend = event.get('dtend')
            summary = event.get('summary')


            if not dtstart or not summary:
                return None

            # handle different datetime formats
            start_dt = dtstart.dt

            if isinstance(start_dt, datetime):
                # convert to local timezone if needed
                if start_dt.tzinfo is None:
                    start_dt = start_dt.replace(tzinfo=pytz.UTC)
                start_dt = start_dt.astimezone(self.local_tz)
            else:
                # all-day event - keep as date object
                pass

            # check if event is in our date range
            event_date = start_dt.date() if isinstance(start_dt, datetime) else start_dt
            if not (start_date <= event_date <= end_date):
                return None

            end_dt = None
            if dtend:
                end_dt = dtend.dt
                if isinstance(end_dt, datetime):
                    if end_dt.tzinfo is None:
                        end_dt = end_dt.replace(tzinfo=pytz.UTC)
                    end_dt = end_dt.astimezone(self.local_tz)
                else:
                    # for all-day events, keep end as date object too
                    pass  # keep as date

            result = {
                'start': start_dt,
                'end': end_dt,
                'title': str(summary),
                'date': event_date.strftime('%Y-%m-%d')
            }
            return result

        except Exception as e:
            return None

    def _parse_recurring_event(self, event, start_date, end_date):
        """Parse recurring event and expand occurrences within date range"""
        recurring_events = []

        try:
            dtstart = event.get('dtstart')
            dtend = event.get('dtend')
            summary = event.get('summary')
            rrule_data = event.get('RRULE')


            if not dtstart or not summary or not rrule_data:
                return []

            # get the start datetime
            start_dt = dtstart.dt

            # calculate duration if end time exists
            duration = None
            if dtend:
                end_dt = dtend.dt
                if isinstance(start_dt, datetime) and isinstance(end_dt, datetime):
                    duration = end_dt - start_dt
                elif isinstance(start_dt, date) and isinstance(end_dt, date):
                    duration = end_dt - start_dt

            # convert vRecur to string format
            rrule_str = rrule_data.to_ical().decode('utf-8')

            # handle timezone
            is_all_day = not isinstance(start_dt, datetime)
            original_start_dt = start_dt  # keep original for later

            if isinstance(start_dt, datetime):
                if start_dt.tzinfo is None:
                    start_dt = start_dt.replace(tzinfo=pytz.UTC)
                start_dt = start_dt.astimezone(self.local_tz)
            else:
                # for all-day events, we need to temporarily convert to datetime for rrule
                # but keep the original date
                start_dt_for_rrule = datetime.combine(start_dt, datetime.min.time())
                start_dt_for_rrule = start_dt_for_rrule.replace(tzinfo=self.local_tz)

            # create rrule object
            try:
                # parse the RRULE
                if is_all_day:
                    rule = rrulestr(rrule_str, dtstart=start_dt_for_rrule)
                else:
                    rule = rrulestr(rrule_str, dtstart=start_dt)

                # generate occurrences within our date range
                # always use datetime for search range with rrule
                search_start = datetime.combine(start_date, datetime.min.time())
                search_end = datetime.combine(end_date, datetime.max.time())

                # make search dates timezone-aware with local timezone
                search_start = self.local_tz.localize(search_start)
                search_end = self.local_tz.localize(search_end)


                # get occurrences
                occurrences = list(rule.between(search_start, search_end, inc=True))

                # for all-day events, convert occurrences back to dates
                if is_all_day:
                    occurrences = [occ.date() if isinstance(occ, datetime) else occ for occ in occurrences]


                for occurrence in occurrences:
                    # create event for this occurrence
                    if isinstance(occurrence, datetime):
                        event_date = occurrence.date()
                    else:
                        event_date = occurrence


                    # skip if outside our actual date range
                    if not (start_date <= event_date <= end_date):
                        continue

                    end_time = None
                    if duration:
                        if isinstance(occurrence, datetime):
                            end_time = occurrence + duration
                        else:
                            # for date objects, duration should be in days
                            end_time = occurrence + duration if isinstance(duration, timedelta) else None

                    recurring_events.append({
                        'start': occurrence,
                        'end': end_time,
                        'title': str(summary),
                        'date': event_date.strftime('%Y-%m-%d')
                    })


            except Exception as e:
                pass
                # fall back to single event
                single_event = self._parse_event(event, start_date, end_date)
                if single_event:
                    return [single_event]

        except Exception as e:
            pass

        return recurring_events