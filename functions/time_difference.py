import datetime

def is_greater_than_24_hours(timestamp):
    current_time = datetime.datetime.now()
    new_time = datetime.datetime.fromtimestamp(timestamp)
    difference_in_seconds = abs(current_time - new_time).total_seconds()
    difference_in_hours = (difference_in_seconds / 60) / 60
    return True if difference_in_hours > 24 else False

def is_greater_than_1_hour(timestamp):
    current_time = datetime.datetime.now()
    new_time = datetime.datetime.fromtimestamp(timestamp)
    difference_in_seconds = abs(current_time - new_time).total_seconds()
    difference_in_hours = (difference_in_seconds / 60) / 60
    return True if difference_in_hours > 1 else False

def is_greater_than_12_hours(timestamp):
    current_time = datetime.datetime.now()
    new_time = datetime.datetime.fromtimestamp(timestamp)
    difference_in_seconds = abs(current_time - new_time).total_seconds()
    difference_in_hours = (difference_in_seconds / 60) / 60
    print(difference_in_hours)
    return True if difference_in_hours > 12 else False