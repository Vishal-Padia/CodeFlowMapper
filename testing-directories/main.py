from .data_processor import process_data
from .analyzer import analyze_results
from .utils import log_message
from .analyzer import generate_report


def main():
    log_message("Starting main process")
    data = [1, 2, 3, 4, 5]
    processed_data = process_data(data)
    results = analyze_results(processed_data)
    log_message(f"Analysis results: {results}")
    report = generate_report(results)
    log_message(f"Report: {report}")


if __name__ == "__main__":
    main()
