import psutil
import os 
import json
# Get the 1-minute load average
load1, _, _ = psutil.getloadavg()

print(f"Load Average: {load1}, {load1}, {load1}")

# Check if the load exceeds the threshold
# Use this for actual script
if load1 > 5:
# Use this for testing
# if True:
    print(f"High load detected: {load1}")

    # Get a list of all running processes
    processes = [p for p in psutil.process_iter(attrs=['pid', 'name', 'cpu_percent', 'exe'])]

    # Sort processes by CPU usage percentage (descending)
    processes.sort(key=lambda x: x.info['cpu_percent'], reverse=True)

    with open("watchlist.json", "r") as file:
        watchlist = json.load(file)
    watchlist_detected = False  # Flag to check if any watchlist process is detected

    # Check the top processes
    for process in processes[:3]:
        pid = process.info['pid']
        name = process.info['name']
        cpu_percent = process.info['cpu_percent']
        exe = process.info['exe']

        # Check if the process name matches any in our watchlist
        if any(watch_item in name for watch_item in watchlist):
            print(f"Watchlist process detected!")
            print(f"PID: {pid}, Name: {name}, CPU%: {cpu_percent}, Executable: {exe}")
            watchlist_detected = True

    if not watchlist_detected:
        print("No processes from the watchlist detected. Top 3 CPU-consuming processes are:")
        for process in processes[:3]:
            pid = process.info['pid']
            name = process.info['name']
            cpu_percent = process.info['cpu_percent']
            exe = process.info['exe']
            print(f"PID: {pid}, Name: {name}, CPU%: {cpu_percent}, Executable: {exe}")
            print("Fetching logs using journalctl for the past 1 minute:")
            os.system(f"journalctl -u {name} --since '1 minute ago'")

else:
    print(f"Load is normal: {load1}")
