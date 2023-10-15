from datetime import datetime

def log_to_file(message, filename=None):
    if filename is None:
        filename = datetime.now().strftime('lw_%Y%m%d_%H%M.log')
    with open(filename, 'a') as f:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        f.write(f"[{timestamp}] {message}\n")
