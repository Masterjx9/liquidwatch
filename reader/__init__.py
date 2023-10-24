import os
import json

def read_and_match_errors(log_folder_path, dataset_path='datasets/reasons.json'):
    # Step 1: Read the JSON file
    with open(dataset_path, 'r') as f:
        error_dataset = json.load(f)

    # Convert the list of dictionaries to a dictionary for faster lookup
    error_dict = {item['string']: item['reason'] for item in error_dataset}

    # Step 2: Read the log files
    summary = {}
    for filename in os.listdir(log_folder_path):
        if filename.endswith('.log'):
            with open(os.path.join(log_folder_path, filename), 'r') as log_file:
                log_contents = log_file.readlines()

            # Step 3: Search for errors
            for line in log_contents:
                for error_string, reason in error_dict.items():
                    if error_string in line:
                        if error_string not in summary:
                            summary[error_string] = {
                                'reason': reason,
                                'occurrences': []
                            }
                        summary[error_string]['occurrences'].append(line.strip())

    # Step 5: Return the summary
    return summary
