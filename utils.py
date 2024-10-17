from pytz import timezone
from datetime import datetime


def timestamp():
    # Returns the time in correspondnce with West African Time
    wat_timezone = timezone('Africa/Lagos')
    return str(datetime.now(wat_timezone))


# def create_transaction_debt(amount: float | int, type: str, db):
#     if type not in ['increase_debt', 'reduce_debt']:
#         raise Exception('Invalid transaction type')
    
#     db.find_one