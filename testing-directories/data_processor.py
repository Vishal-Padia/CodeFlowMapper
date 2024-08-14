from .utils import log_message, validate_data

def process_data(data):
    log_message("Processing data")
    validate_data(data)
    return [x * 2 for x in data]

def preprocess_data(data):
    log_message("Preprocessing data")
    return [x + 1 for x in data]