from datetime import datetime, timedelta



def get_next_year_events(data):
    """
    This function takes a list of dictionaries (data) representing events
    and returns a list of events happening in the next calendar year.
    """
    today = datetime.today()
    next_year_start = datetime(today.year + 1, 1, 1)  # January 1st of next year
    next_year_end = datetime(today.year + 1, 12, 31)  # December 31st of next year

    print(f"Next year starts on: {next_year_start}")
    print(f"Next year ends on: {next_year_end}")

    events = []
    for event in data:
        try:
            # Check and parse "Current Tenure"
            if isinstance(event.get("Current Tenure"), str):
                start_date_str, end_date_str = event["Current Tenure"].split(" - ")
            else:
                print(f"Skipping event due to invalid 'Current Tenure': {event}")
                continue

            # Parse the start and end dates
            start_date = datetime.strptime(start_date_str.strip(), "%d %b, %Y")
            end_date = datetime.strptime(end_date_str.strip(), "%d %b, %Y")

            # Debugging: Print parsed dates
            print(f"Event: {event.get('State Name')} | Start Date: {start_date} | End Date: {end_date}")

            # Check if the event's start date falls in the next year's range
            if next_year_start <= start_date <= next_year_end:
                print(f"Adding event: {event.get('State Name')}")
                events.append(event)

        except Exception as e:
            # Log an error message and continue
            print(f"Error processing event: {event}, Error: {e}")
            continue

    return events


def get_next_week_events(data):
    """
    This function takes a list of dictionaries (data) representing events
    and returns a list of events happening in the next week.
    """
    today = datetime.today()
    next_week_start = today + timedelta(days=7 - today.weekday())  # Monday of next week
    next_week_end = next_week_start + timedelta(days=6)  # Sunday of next week

    print(f"Today's date: {today}")
    print(f"Next week starts on: {next_week_start}")
    print(f"Next week ends on: {next_week_end}")

    events = []
    for event in data:
        try:
            # Check and parse "Current Tenure"
            if isinstance(event.get("Current Tenure"), str):
                start_date_str, end_date_str = event["Current Tenure"].split(" - ")
            else:
                print(f"Skipping event due to invalid 'Current Tenure': {event}")
                continue

            # Parse the start and end dates
            start_date = datetime.strptime(start_date_str.strip(), "%d %b, %Y")
            end_date = datetime.strptime(end_date_str.strip(), "%d %b, %Y")

            # Debugging: Print parsed dates
            print(f"Event: {event.get('State Name')} | Start Date: {start_date} | End Date: {end_date}")

            # Check if the event's start date falls in the next week range
            if next_week_start <= start_date <= next_week_end:
                print(f"Adding event: {event.get('State Name')}")
                events.append(event)

        except Exception as e:
            # Log an error message and continue
            print(f"Error processing event: {event}, Error: {e}")
            continue

    return events
