import argparse
import psutil
import os 
import json
from outputs import email, logs
import subprocess

# Argument parsing
parser = argparse.ArgumentParser(description="Monitor system load and notify based on specified output method.")
parser.add_argument('--output', type=str, choices=['email', 'logs'], help='Output method: email or logs')
args = parser.parse_args()

# Get the 1-minute load average
load1, _, _ = psutil.getloadavg()

print(f"Load Average: {load1}, {load1}, {load1}")

# Check if the load exceeds the threshold
# Use this for actual script
# if load1 > 5:
# Use this for testing
if True:
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


        matched_process = next((item for item in watchlist if name in item), None)
        if matched_process:
            paths = matched_process[name]["paths"]
            
            print(f"Watchlist process detected!")
            print(f"PID: {pid}, Name: {name}, CPU%: {cpu_percent}, Executable: {exe}")
            for path in matched_process["paths"]:
                print(f"Fetching logs from {path} for the past 1 minute:")
                recentlogs = subprocess.check_output(f"tail -n 100 {path} | grep '$(date +'%b %d %H:%M')'", shell=True).decode('utf-8')
                if "-- No entries --" not in recentlogs:
                    if args.output == "email":
                        email.send_email("Alert: High load!", "High load detected on the server." + recentlogs, "admin@example.com", "alerts@example.com", "smtp.example.com", 465, "login", "password")
                    elif args.output == "logs":
                        logs.log_to_file("High load detected!" + recentlogs)
                        
        else:
            print(f"Unwatched process causing high load detected!")
            print(f"PID: {pid}, Name: {name}, CPU%: {cpu_percent}, Executable: {exe}")
            print("Fetching logs using journalctl for the past 1 minute:")
            recentlogs = subprocess.check_output(f"journalctl -u {name} --since '1 minute ago'", shell=True).decode('utf-8')
            if "-- No entries --" not in recentlogs:
                if args.output == "email":
                    email.send_email("Alert: High load!", "High load detected on the server." + recentlogs, "admin@example.com", "alerts@example.com", "smtp.example.com", 465, "login", "password")
                elif args.output == "logs":
                    logs.log_to_file("High load detected!" + recentlogs)



else:
    print(f"Load is normal: {load1}")
