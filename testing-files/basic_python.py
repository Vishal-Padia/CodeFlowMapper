def main():
    print("Starting the program...")
    data = get_data()
    processed_data = process_data(data)
    result = analyze_results(processed_data)
    display_results(result)
    print("Program completed.")


def get_data():
    print("Fetching data...")
    data = [1, 2, 3, 4, 5]
    validate_data(data)
    return data


def validate_data(data):
    print("Validating data...")
    if not data:
        raise ValueError("Data is empty")
    return True


def process_data(data):
    print("Processing data...")
    return [x * 2 for x in data]


def analyze_results(data):
    print("Analyzing results...")
    total = calculate_total(data)
    average = calculate_average(data)
    return {"total": total, "average": average}


def calculate_total(data):
    return sum(data)


def calculate_average(data):
    total = calculate_total(data)
    return total / len(data)


def display_results(results):
    print("Displaying results...")
    print(f"Total: {results['total']}")
    print(f"Average: {results['average']}")


if __name__ == "__main__":
    main()
