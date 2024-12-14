import pandas as pd
import json

def load_data(log_file):
    """
    Loads data from the log file and converts it into a pandas DataFrame.

    :param log_file: Path to the log file.
    :return: pandas.DataFrame containing the loaded data.
    """
    data = []  # Initialize an empty list to store log entries
    try:
        # Open the log file in read mode
        with open(log_file, 'r') as file:
            for line in file:
                # Check if the line contains a JSON entry (indicated by '{')
                if '{' in line:
                    try:
                        # Extract the JSON part of the line and parse it
                        log_entry = json.loads(line.split(' - ')[-1])
                        # Append the relevant data to the list
                        data.append({
                            'symbol': log_entry['symbol'],
                            'price': float(log_entry['price']),
                            'high': float(log_entry['high']),
                            'low': float(log_entry['low']),
                            'volume': float(log_entry['volume'])
                        })
                    except json.JSONDecodeError as e:
                        # Handle JSON parsing errors
                        print(f"Error parsing the line: {e}")
    except FileNotFoundError:
        # Handle the case where the log file is not found
        print(f"The log file {log_file} was not found.")
    except Exception as e:
        # Handle any other general exceptions
        print(f"General error while loading data: {e}")

    # Convert the list of log entries into a pandas DataFrame
    return pd.DataFrame(data)
