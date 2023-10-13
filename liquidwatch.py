import psutil

# Get the 1-minute load average
load1, _, _ = psutil.getloadavg()

print(load1, _, _)
# Check if the load exceeds the threshold
if load1 > 5:
    print(f"High load detected: {load1}")

    # Get a list of all running processes
    processes = [p for p in psutil.process_iter(attrs=['pid', 'name', 'cpu_percent', 'exe'])]

    # Sort processes by CPU usage percentage (descending)
    processes.sort(key=lambda x: x.info['cpu_percent'], reverse=True)

    watchlist = [
    "httpd2", 
    "apache", 
    "mysql", 
    "whm", 
    "cpanel", 
    "plesk", 
    "interworx", 
    "php-fpm"
]

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
        
else:
    print(f"Load is normal: {load1}")


