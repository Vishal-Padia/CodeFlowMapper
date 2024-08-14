def log_message(message):
    print(f"[LOG] {message}")


def validate_data(data):
    if not isinstance(data, list):
        raise ValueError("Data must be a list")
    if not all(isinstance(x, (int, float)) for x in data):
        raise ValueError("All elements must be numbers")
