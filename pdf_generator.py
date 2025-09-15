from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.colors import black, grey, HexColor, lightgrey
from reportlab.lib.pagesizes import letter
from datetime import datetime, timedelta, date

class PDFGenerator:
    def __init__(self):
        # Page dimensions for reMarkable Pro Move (1696 x 954 pixels at 264 PPI)
        # Convert pixels to points (72 points per inch)
        pixels_per_inch = 264
        points_per_inch = 72
        conversion_factor = points_per_inch / pixels_per_inch

        self.page_width = 954 * conversion_factor  # 462.5 points
        self.page_height = 1696 * conversion_factor   # 260.2 points
        self.margin = 18  # 0.25 inch in points

        # Content area
        self.content_width = self.page_width - (2 * self.margin)
        self.content_height = self.page_height - (2 * self.margin)

    def generate_pdf(self, start_date, end_date, events, output_path, start_hour=6, end_hour=17, show_todos=True):
        """Generate PDF with one page per day for the specified date range"""

        c = canvas.Canvas(output_path, pagesize=(self.page_width, self.page_height))
        # Ensure no page borders
        c.setStrokeColor(black)
        c.setLineWidth(0)

        # Calculate number of days
        total_days = (end_date - start_date).days + 1  # +1 to make it inclusive

        for day_offset in range(total_days):
            current_date = start_date + timedelta(days=day_offset)
            date_str = current_date.strftime('%Y-%m-%d')
            day_events = [e for e in events if e['date'] == date_str]


            self.draw_daily_page(c, current_date, day_events, start_hour, end_hour, show_todos)
            if day_offset < total_days - 1:  # Don't add page after last day
                c.showPage()

        c.save()

    def draw_daily_page(self, c, current_date, events, start_hour=6, end_hour=17, show_todos=True):
        """Draw single day page with time slots and events"""
        # Starting position (top of content area)
        y_pos = self.page_height - self.margin

        # Draw date header (right-aligned, smaller font)
        c.setFont("Helvetica-Bold", 12)
        date_text = current_date.strftime('%A, %B %d, %Y')
        text_width = c.stringWidth(date_text, "Helvetica-Bold", 12)
        c.drawString(self.page_width - self.margin - text_width, y_pos, date_text)
        y_pos -= 12

        # Draw faint horizontal line under header (very close to header)
        c.setStrokeColor(lightgrey)
        c.setLineWidth(0.5)
        c.line(self.margin, y_pos, self.page_width - self.margin, y_pos)
        c.setStrokeColor(black)  # Reset
        y_pos -= 8.5

        # Calculate dimensions with more space per hour
        hour_height = 26  # points per hour (increased for better spacing)
        half_hour_height = hour_height / 2
        time_column_width = 50  # Time column width
        event_column_start = self.margin + time_column_width - 10  # Add small padding after time
        event_column_width = (self.content_width - time_column_width - 6) * 0.5  # 50% for events, 50% for notes

        # Track the bottom of the schedule section
        schedule_bottom = y_pos

        # Check for all-day events (those with date objects, not datetime)
        all_day_events = [e for e in events if isinstance(e['start'], date) and not isinstance(e['start'], datetime)]

        # Draw all-day slot if there are all-day events
        if all_day_events:
            # Draw "ALL DAY" time label
            c.setFont("Helvetica-Bold", 9)
            c.setFillColor(black)
            c.drawString(self.margin, y_pos - 12, "All Day")

            # Draw all-day events in their row
            all_day_box_y = y_pos - hour_height  # Full hour height for all-day section
            self._draw_all_day_events(c, all_day_events, event_column_start, event_column_width, all_day_box_y, hour_height)

            # Draw hour line after all-day section
            c.setStrokeColor(grey)
            c.setLineWidth(0.5)
            y_pos -= hour_height
            c.line(self.margin, y_pos, self.page_width - self.margin, y_pos)

            # Update schedule bottom position
            schedule_bottom = y_pos

        # Draw hourly time slots (start_hour through end_hour)
        for hour in range(start_hour, end_hour):
            # Format time (without :00)
            if hour < 12:
                time_str = f"{hour} AM" if hour > 0 else "12 AM"
            elif hour == 12:
                time_str = "12 PM"
            else:
                time_str = f"{hour-12} PM"

            # Draw time label with bold font and more padding above
            c.setFont("Helvetica-Bold", 9)
            c.setFillColor(black)
            c.drawString(self.margin, y_pos - 12, time_str)  # More padding from divider line

            # Draw half-hour line (faint)
            c.setStrokeColor(lightgrey)
            c.setLineWidth(0.25)
            half_hour_y = y_pos - half_hour_height
            c.line(event_column_start, half_hour_y, self.page_width - self.margin, half_hour_y)

            # Draw hour line
            c.setStrokeColor(grey)
            c.setLineWidth(0.5)
            y_pos -= hour_height
            c.line(self.margin, y_pos, self.page_width - self.margin, y_pos)

            # Update schedule bottom position
            schedule_bottom = y_pos

            # Stop if we're getting close to bottom (leave room for to-do list)
            if y_pos < self.margin + 100:  # Reduced space to fit more hours
                break

        # Draw events (pass whether we have all-day events to adjust positioning)
        has_all_day = len(all_day_events) > 0
        self._draw_events(c, current_date, events, event_column_start, event_column_width, hour_height, start_hour, end_hour, has_all_day)

        # Draw to-do list section at the bottom (only if show_todos is True)
        if show_todos:
            self._draw_todo_section(c, schedule_bottom)

    def _draw_events(self, c, current_date, events, x_start, width, hour_height, start_hour=6, end_hour=17, has_all_day=False):
        """Draw events as rounded boxes positioned by time"""
        # Base position matches the grid - align with first time label position
        # Account for header (12pt) + line (8pt) = 20pt total
        grid_top = self.page_height - self.margin - 20

        # If there's an all-day section, shift everything down by one hour height
        if has_all_day:
            grid_top -= hour_height

        # Group events by time slot to handle overlaps
        time_slots = {}

        # First pass: group events by hour
        for event in events:
            # Skip all-day events (those with date objects, not datetime)
            if not isinstance(event['start'], datetime):
                continue  # Skip all-day events

            # Skip events outside our time range
            if event['start'].hour < start_hour or event['start'].hour >= end_hour:
                continue

            event_hour = event['start'].hour
            if event_hour not in time_slots:
                time_slots[event_hour] = []
            time_slots[event_hour].append(event)

        # Second pass: draw events, handling overlaps
        for hour, hour_events in time_slots.items():
            for i, event in enumerate(hour_events):
                # Calculate base position
                event_minute = event['start'].minute
                hours_from_start = hour - start_hour + (event_minute / 60.0)
                event_top = grid_top - (hours_from_start * hour_height) - 1

                # Calculate duration and height
                duration_minutes = 60  # Default 1 hour
                if event['end'] and isinstance(event['end'], datetime):
                    delta = event['end'] - event['start']
                    duration_minutes = delta.total_seconds() / 60

                # Round to 15-minute increments
                duration_minutes = max(15, round(duration_minutes / 15) * 15)
                box_height = (duration_minutes / 60.0) * hour_height

                # Add spacing between events for visual separation
                spacing = 1
                box_height = max(box_height - spacing, 8)  # Minimum 8 points height

                # Event box starts at event_top and goes down box_height
                box_y = event_top - box_height

                # Calculate position - first event in event section, others in notes section
                event_width = width
                event_x = x_start

                if i > 0:
                    # Additional events go in the notes section (right half of page)
                    notes_section_start = x_start + width + 10  # Small gap between event and notes sections
                    notes_section_width = (self.content_width - (notes_section_start - self.margin))

                    # If multiple events in notes section, divide the notes space
                    events_in_notes = len(hour_events) - 1
                    event_width = notes_section_width / events_in_notes
                    event_x = notes_section_start + ((i - 1) * event_width)

                # Draw rounded rectangle with dark grey background
                self._draw_rounded_rect(c, event_x, box_y, event_width, box_height, radius=2)

                # Draw event text in white with bold font
                c.setFillColor(HexColor('#FFFFFF'))
                c.setFont("Helvetica-Bold", 8)

                # Calculate how many lines we can fit
                line_height = 9  # Height per line of text (reduced for better fit)
                padding = 3  # Vertical padding (reduced)
                available_height = box_height - (2 * padding)
                max_lines = max(1, int(available_height / line_height))

                # For 1-hour blocks, ensure we can show at least 2 lines
                if duration_minutes >= 60 and max_lines < 2:
                    max_lines = 2
                    line_height = available_height / 2  # Adjust line height to fit

                # Calculate character width for wrapping (adjust for narrower width if multiple events)
                char_width = 4  # Approximate character width for font size 8
                max_chars_per_line = int((event_width - 10) / char_width)  # 10 = horizontal padding

                # Wrap text to fit
                event_text = event['title']
                lines = self._wrap_text(event_text, max_chars_per_line, max_lines)

                # Draw each line
                for j, line in enumerate(lines):
                    if j >= max_lines:
                        break

                    # Calculate y position for this line
                    if len(lines) == 1:
                        # Single line - center vertically
                        text_y = box_y + (box_height / 2) - 3
                    else:
                        # Multiple lines - distribute evenly
                        total_text_height = len(lines) * line_height
                        start_y = box_y + (box_height - total_text_height) / 2 + (len(lines) - 1) * line_height
                        text_y = start_y - (j * line_height)

                    c.drawString(event_x + 5, text_y, line)

                # Reset color
                c.setFillColor(black)

    def _draw_all_day_events(self, c, all_day_events, x_start, width, y_bottom, row_height):
        """Draw all-day events in the all-day section"""
        for i, event in enumerate(all_day_events):
            # Calculate position - first event in event section, others in notes section
            event_width = width
            event_x = x_start

            if i > 0:
                # Additional events go in the notes section (right half of page)
                notes_section_start = x_start + width + 10  # Small gap between event and notes sections
                notes_section_width = (self.content_width - (notes_section_start - self.margin))

                # If multiple events in notes section, divide the notes space
                events_in_notes = len(all_day_events) - 1
                event_width = notes_section_width / events_in_notes
                event_x = notes_section_start + ((i - 1) * event_width)

            # All-day events fill most of the row height
            box_height = row_height - 6  # Leave some spacing
            box_y = y_bottom + 3  # Small padding from bottom line

            # Draw rounded rectangle with dark grey background
            self._draw_rounded_rect(c, event_x, box_y, event_width, box_height, radius=2)

            # Draw event text in white with bold font
            c.setFillColor(HexColor('#FFFFFF'))
            c.setFont("Helvetica-Bold", 8)

            # Calculate character width for wrapping
            char_width = 4  # Approximate character width for font size 8
            max_chars_per_line = int((event_width - 10) / char_width)  # 10 = horizontal padding

            # For all-day events, try to fit in one line, but allow two if needed
            max_lines = 2
            line_height = 9

            # Wrap text to fit
            event_text = event['title']
            lines = self._wrap_text(event_text, max_chars_per_line, max_lines)

            # Draw each line
            for j, line in enumerate(lines):
                if j >= max_lines:
                    break

                # Calculate y position for this line
                if len(lines) == 1:
                    # Single line - center vertically
                    text_y = box_y + (box_height / 2) - 3
                else:
                    # Multiple lines - distribute evenly
                    total_text_height = len(lines) * line_height
                    start_y = box_y + (box_height - total_text_height) / 2 + (len(lines) - 1) * line_height
                    text_y = start_y - (j * line_height)

                c.drawString(event_x + 5, text_y, line)

            # Reset color
            c.setFillColor(black)

    def _draw_rounded_rect(self, c, x, y, width, height, radius=3):
        """Draw a rounded rectangle"""
        c.setFillColor(HexColor('#4A4A4A'))  # Dark grey
        c.setStrokeColor(HexColor('#4A4A4A'))

        # Draw the rounded rectangle path
        c.roundRect(x, y, width, height, radius, fill=1, stroke=1)

        # Reset colors
        c.setFillColor(black)
        c.setStrokeColor(black)

    def _draw_todo_section(self, c, y_start):
        """Draw to-do list section with checkboxes"""
        y_pos = y_start - 14

        # No divider line - we already have one from 9 PM hour

        # Draw checkbox lines with better spacing
        c.setFont("Helvetica", 9)
        checkbox_size = 10  # Slightly larger checkboxes

        # Calculate available space and distribute 4 to-dos evenly
        num_lines = 4
        available_space = y_pos - self.margin + 22  # Leave minimal bottom margin to use full space
        line_height = available_space / num_lines  # Divide space evenly among 4 items

        for i in range(num_lines):
            # Draw checkbox
            c.setLineWidth(0.5)
            c.setStrokeColor(black)
            c.rect(self.margin, y_pos - checkbox_size, checkbox_size, checkbox_size)

            # Draw line for text (aligned with bottom of checkbox)
            line_start = self.margin + checkbox_size + 6
            c.setLineWidth(0.3)
            c.setStrokeColor(black)
            line_y = y_pos - checkbox_size  # Bottom of checkbox
            c.line(line_start, line_y, self.page_width - self.margin, line_y)

            y_pos -= line_height

        # Reset colors
        c.setStrokeColor(black)

    def _wrap_text(self, text, max_chars_per_line, max_lines):
        """Wrap text to fit within specified constraints"""
        if not text:
            return [""]

        words = text.split()
        lines = []
        current_line = ""

        for word in words:
            # If adding this word would exceed the line length
            if len(current_line + " " + word) > max_chars_per_line:
                if current_line:
                    lines.append(current_line.strip())
                    current_line = word
                else:
                    # Single word is too long, truncate it
                    lines.append(word[:max_chars_per_line - 3] + "...")
                    current_line = ""

                # Stop if we've reached max lines
                if len(lines) >= max_lines:
                    break
            else:
                current_line += (" " + word) if current_line else word

        # Add the last line if there's content and we haven't exceeded max lines
        if current_line and len(lines) < max_lines:
            lines.append(current_line.strip())

        # If we had to truncate due to max lines, add ellipsis to last line
        if len(lines) == max_lines and len(words) > len(" ".join(lines).split()):
            if lines:
                last_line = lines[-1]
                if len(last_line) > 3:
                    lines[-1] = last_line[:-3] + "..."

        return lines if lines else [""]