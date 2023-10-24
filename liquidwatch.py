import argparse
import psutil
import json
from outputs import email, logs
import subprocess
import time
import os 
from datetime import datetime, timedelta
from collections import namedtuple
import re
from integrations import loadwatch_functions
import reader

# Argument parsing
parser = argparse.ArgumentParser(description="Monitor system load and notify based on specified output method.")
parser.add_argument('--output', type=str, choices=['email', 'logs'], help='Output method: email or logs')
parser.add_argument('--mode', type=str, choices=['once', 'service'], default='once', help='Run mode: once or service loop')
parser.add_argument('--loadwatchmode', type=str, choices=['true', 'false'], default='True', help='Run loadwatch or not')
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
    print(current_date_str)
    one_minute_ago_str = (datetime.now() - timedelta(minutes=1)).strftime(date_format)
    current_minute = datetime.now().minute
    one_minute_ago = current_minute - 1 if current_minute != 0 else 59
    return current_date_str, one_minute_ago_str, current_minute, one_minute_ago

def get_search_patterns(date_str, date_format):
    # Remove timezone information from date format
    simplified_date_format = date_format.replace('%z', '')
    date_obj = datetime.strptime(date_str, simplified_date_format)
    search_pattern = date_obj.strftime(simplified_date_format.split('%S')[0])  # Format up to minutes
    return search_pattern
    
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

        
def get_top_swap_processes(limit=3):
    ProcessSwapInfo = namedtuple('ProcessSwapInfo', ['swap', 'process'])
    swap_data = []
    
    # Compile the regular expression once
    swap_regex = re.compile(r'VmSwap:\s+(\d+)')
    
    for proc in psutil.process_iter(attrs=['pid', 'name']):
        try:
            with open(f"/proc/{proc.info['pid']}/status", "r") as f:
                for line in f:
                    match = swap_regex.search(line)
                    if match:
                        vm_swap = int(match.group(1))
                        if vm_swap > 0:
                            swap_data.append(ProcessSwapInfo(vm_swap, proc))
                            break  # No need to read the rest of the file
        except Exception as e:
            pass  # Some processes might deny access or terminate before we can read them

    # Sort and return the top processes
    top_swap_processes = sorted(swap_data, key=lambda x: x.swap, reverse=True)[:limit]
    return top_swap_processes


def diagnose_issue():
    # 1. Check CPU-bound issues
    top_cpu_processes = sorted(psutil.process_iter(['pid', 'name', 'cpu_percent']),
                               key=lambda p: p.info['cpu_percent'],
                               reverse=True)[:5]

    total_cpu_percent = sum(p.info['cpu_percent'] for p in top_cpu_processes)
    if total_cpu_percent >= 50:
        print("CPU-bound issue detected")
        print(top_cpu_processes)
        processes_causing_cpu_usage = [p for p in psutil.process_iter(['pid', 'name', 'cpu_percent']) if p.info['name'] in top_cpu_processes]
        
        return processes_causing_cpu_usage

    # 2. Check Memory-bound issues
    top_memory_processes = sorted(psutil.process_iter(['pid', 'name', 'memory_percent']),
                                  key=lambda p: p.info['memory_percent'],
                                  reverse=True)[:5]

    mem_info = psutil.virtual_memory()
    if mem_info.percent >= 80:
        print("Memory-bound issue detected")
        print(top_memory_processes)
        processes_causing_memory_usage = [p for p in psutil.process_iter(['pid', 'name', 'cpu_percent']) if p.info['name'] in top_memory_processes]
        
        return processes_causing_memory_usage

    # 3. Check swap issues
    swap_info = psutil.swap_memory()
    if swap_info.percent >= 50:
        print("Swap-bound issue detected")
        top_swap_processes_names = get_top_swap_processes()

        # Convert the process names to process objects for consistency
        processes_causing_swap_usage = [p for p in psutil.process_iter(['pid', 'name', 'cpu_percent']) if p.info['name'] in top_swap_processes_names]
        return processes_causing_swap_usage

    # 4. Check I/O-bound issues (this is a bit more heuristic)
    old_io = psutil.disk_io_counters()
    time.sleep(1)  # Sleep for 1 second to measure IO
    new_io = psutil.disk_io_counters()
    
    if (new_io.read_count - old_io.read_count) > 1000 or (new_io.write_count - old_io.write_count) > 1000:
        # This is more heuristic, not directly tied to a specific process
        # We can return the processes with the most IO activity in the past 1 second
        print("I/O-bound issue detected")
        top_io_processes = sorted(psutil.process_iter(['pid', 'name', 'io_counters']),
                                  key=lambda p: (p.info['io_counters'].read_bytes + p.info['io_counters'].write_bytes),
                                  reverse=True)[:5]
        print(top_io_processes)
        return top_io_processes

    return []
    
 
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
        
        if args.loadwatchmode.lower() == 'true':
            time_result = loadwatch_functions.wait_for_loadwatch()  # Wait for Loadwatch to finish if it's running
            if time_result == "old":
                print("Loadwatch file is too old. Creating a log file.")
                log_path = loadwatch_functions.create_and_log_file()
            elif time_result == "good":
                print("Loadwatch file is within the acceptable time range.")
                log_path = loadwatch_functions.copy_loadwatch_file()
                if log_path == None:
                    print("No recent Loadwatch file found. Creating a log file.")
                    log_path = loadwatch_functions.create_and_log_file()
        elif args.loadwatchmode.lower() == 'false':
            latest_file = loadwatch_functions.find_latest_loadwatch_file()
            if latest_file:
                print(f"Found latest Loadwatch file: {latest_file}")
                # Here you can move the file to the desired directory or perform other actions
            else:
                print("No recent Loadwatch file found. Creating a log file.")
                log_path = loadwatch_functions.create_and_log_file()  # Log the server stats as fallback

            
        # Get a list of all running processes
        # processes = [p for p in psutil.process_iter(attrs=['pid', 'name', 'cpu_percent', 'exe'])]
        processes = diagnose_issue()
        # Insert the mock process for testing purposes
        if TESTING:
            mock_process = MockProcess("httpd", 99.9, "/usr/sbin/httpd")
            processes.insert(0, mock_process)
        # Sort processes by CPU usage percentage (descending)
        processes.sort(key=lambda x: x.info['cpu_percent'], reverse=True)

        with open("watchlist.json", "r") as file:
            watchlist = json.load(file)
        # watchlist_detected = False  # Flag to check if any watchlist process is detected

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

            if " child" in name:
                name = name.replace(" child", "")

            if " worker" in name:
                name = name.replace(" worker", "")
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
                        # print(current_date)
                        # print(one_minute_ago_pattern)
                        recentlogs = []
                        for line in lines:
                            if current_pattern in line or one_minute_ago_pattern in line:
                                recentlogs.append(line)
                            # Limit to 50 lines after first match
                            if len(recentlogs) >= 50:
                                break

                        #
                        # Combine the logs
                        print(len(recentlogs))
                        if len(recentlogs) > 0:
                            
                            recentlogs_combined = "".join(recentlogs)


                            if "-- No entries --" not in recentlogs:
                                if args.output == "email":
                                    email.send_email("Alert: High load!", "High load detected on the server." + recentlogs, "admin@example.com", "alerts@example.com", "smtp.example.com", 465, "login", "password")
                                elif args.output == "logs":
                                    current_time = datetime.now()
                                    formatted_time = current_time.strftime("%Y-%m-%d.%H.%M")
                                    print(recentlogs_combined)
                                    logs.log_to_file("High load detected!" + recentlogs_combined, f"lw_{name}_{formatted_time}.log", log_path=log_path)
                        else:
                            print(f"No recent logs for {name} in {path['path']}.")
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
                        logs.log_to_file("High load detected!" + recentlogs, log_path=log_path)
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