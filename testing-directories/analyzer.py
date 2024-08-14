from .utils import log_message
from .data_processor import preprocess_data


def analyze_results(data):
    log_message("Analyzing results")
    preprocessed = preprocess_data(data)
    total = sum(preprocessed)
    average = total / len(preprocessed)
    return {"total": total, "average": average}


def generate_report(results):
    log_message("Generating report")
    return f"Report: Total = {results['total']}, Average = {results['average']}"
