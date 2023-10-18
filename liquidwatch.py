import argparse
import psutil
import json
from outputs import email, logs
import subprocess
import time
import os 
from datetime import datetime, timedelta



# Argument parsing
parser = argparse.ArgumentParser(description="Monitor system load and notify based on specified output method.")
parser.add_argument('--output', type=str, choices=['email', 'logs'], help='Output method: email or logs')
parser.add_argument('--mode', type=str, choices=['once', 'service'], default='once', help='Run mode: once or service loop')
args = parser.parse_args()

TESTING = True  


class MockProcess:
    def __init__(self, name, cpu_percent, exe_path):
        self.info = {
            'pid': 12345,
            'name': name,
            'cpu_percent': cpu_percent,
            'exe': exe_path
        }
                
def get_date_range_in_format(date_format):
    current_date_str = datetime.now().strftime(date_format)
    one_minute_ago_str = (datetime.now() - timedelta(minutes=1)).strftime(date_format)
    current_minute = datetime.now().minute
    one_minute_ago = current_minute - 1 if current_minute != 0 else 59
    return current_date_str, one_minute_ago_str, current_minute, one_minute_ago

def extract_date_components(date_str, date_format):
    try:
        date_obj = datetime.strptime(date_str, date_format)
        return {
            'year': date_obj.year,
            'month': date_obj.strftime('%b'),
            'day': date_obj.day,
            'hour': date_obj.hour,
            'minute': date_obj.minute
        }
    except Exception as e:
        print(f"Error extracting date components from {date_str} with format {date_format}: {e}")
        return {}
    
def get_search_patterns(date_str, date_format):
    """Construct partial datetime strings for searching in logs."""
    try:
        date_obj = datetime.strptime(date_str, date_format)
        search_pattern = date_obj.strftime(date_format.split('%S')[0])  # Format up to minutes
        return search_pattern
    except Exception as e:
        print(f"Error constructing search pattern from {date_str} with format {date_format}: {e}")
        return ""
    
def detect_control_panel():
    # Check for WHM/cPanel
    if "cpsrvd" in [p.info['name'] for p in psutil.process_iter(attrs=['name'])] or os.path.exists("/usr/local/cpanel"):
        return "WHM/cPanel"
    
    # Check for Plesk
    if "sw-engine" in [p.info['name'] for p in psutil.process_iter(attrs=['name'])] or os.path.exists("/usr/local/psa"):
        return "Plesk"
    
    # Check for InterWorx
    if "iworx" in [p.info['name'] for p in psutil.process_iter(attrs=['name'])] or os.path.exists("/home/interworx"):
        return "InterWorx"
    
    return "direct-admin"

def monitor_system():
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

        # Insert the mock process for testing purposes
        if TESTING:
            mock_process = MockProcess("httpd", 99.9, "/usr/sbin/httpd")
            processes.insert(0, mock_process)
        # Sort processes by CPU usage percentage (descending)
        processes.sort(key=lambda x: x.info['cpu_percent'], reverse=True)

        with open("watchlist.json", "r") as file:
            watchlist = json.load(file)
        watchlist_detected = False  # Flag to check if any watchlist process is detected

        # print(mock_process)
        # Check the top processes
        control_panel = detect_control_panel()
        for process in processes[:3]:
            if TESTING:
                pid = process.info.get('pid')
                name = process.info.get('name')
                cpu_percent = process.info.get('cpu_percent')
                exe = process.info.get('exe')

            else:
                pid = process.pid
                name = process.name()
                cpu_percent = process.cpu_percent()
                exe = process.exe()



            matched_process = None
            for panel_data in watchlist:
                current_panel_name = list(panel_data.keys())[0]  # Extract the control panel name from the dictionary
                if control_panel == current_panel_name:
                    for proc_data in panel_data[control_panel]:
                        if name in proc_data:
                            print(name)
                            matched_process = proc_data[name]
                            
                            break
                    if matched_process:
                        break
            if matched_process:
                # print(matched_process)
                paths = matched_process["paths"]
                print(f"Watchlist process detected!")
                print(f"PID: {pid}, Name: {name}, CPU%: {cpu_percent}, Executable: {exe}")
                for path in matched_process["paths"]:
                    print(f"Fetching logs from {path['path']} for the past 1 minute:")
                    current_date, one_minute_ago, current_minute, prev_minute = get_date_range_in_format(path['date_format'])

                    
                    current_pattern = get_search_patterns(current_date, path['date_format'])
                    one_minute_ago_pattern = get_search_patterns(one_minute_ago, path['date_format'])


                    try:
                        with open(path['path'], 'r') as file:
                            lines = file.readlines()[-100:]  # Only read the last 100 lines
                        print(current_date)
                        print(one_minute_ago_pattern)
                        recentlogs = []
                        for line in lines:
                            if current_pattern in line or one_minute_ago_pattern in line:
                                recentlogs.append(line)
                            # Limit to 50 lines after first match
                            if len(recentlogs) >= 50:
                                break

                        #
                        # Combine the logs
                        recentlogs_combined = "".join(recentlogs)


                        if "-- No entries --" not in recentlogs:
                            if args.output == "email":
                                email.send_email("Alert: High load!", "High load detected on the server." + recentlogs, "admin@example.com", "alerts@example.com", "smtp.example.com", 465, "login", "password")
                            elif args.output == "logs":
                                logs.log_to_file("High load detected!" + recentlogs_combined, f"lw_{name}_{current_date}.log")
                    except Exception as e:
                        print(f"Error reading logs from {path['path']}: {e}")
                        continue

            else:
                print(f"Unwatched process causing high load detected!")
                print(f"PID: {pid}, Name: {name}, CPU%: {cpu_percent}, Executable: {exe}")
                print(f"Fetching logs for {name} using journalctl for the past 1 minute:")
                recentlogs = subprocess.check_output(f"journalctl -u {name} --since '1 minute ago'", shell=True).decode('utf-8')
                if "-- No entries --" not in recentlogs:
                    if args.output == "email":
                        email.send_email("Alert: High load!", "High load detected on the server." + recentlogs, "admin@example.com", "alerts@example.com", "smtp.example.com", 465, "login", "password")
                    elif args.output == "logs":
                        logs.log_to_file("High load detected!" + recentlogs)
                else:
                    print(f"No recent logs for {name} in journalctl.")


    else:
        print(f"Load is normal: {load1}")

if args.mode == 'once':
    monitor_system()
elif args.mode == 'service':
    counter = 0
    while True:
        monitor_system()
        counter += 1
        if counter == 3:
            time.sleep(3600)  # Sleep for an hour
            counter = 0  # Reset the counter
        else:
            time.sleep(60)