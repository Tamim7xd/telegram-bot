import time

def get_timestamp():
    return int(time.time())

def format_time(timestamp):
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp))

def is_expired(until_timestamp):
    return get_timestamp() > until_timestamp 