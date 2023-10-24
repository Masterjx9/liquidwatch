from datetime import datetime
import os

def log_to_file(message, filename=None, log_path=None):
    print("Logging to file...")
    if log_path is None:
        log_path = ""
    if filename is None:
        filename = datetime.now().strftime('lw_%Y%m%d_%H%M.log')
    file_path = os.path.join(log_path, filename)
    with open(file_path, 'a') as f:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        f.write(f"[{timestamp}] {message}\n")