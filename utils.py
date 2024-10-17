from pytz import timezone
from datetime import datetime


def timestamp():
    # Returns the time in correspondnce with West African Time
    wat_timezone = timezone('Africa/Lagos')
    return str(datetime.now(wat_timezone))