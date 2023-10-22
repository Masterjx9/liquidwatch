import os
import psutil
import subprocess   
from datetime import datetime, timedelta
import time


def wait_for_loadwatch(loadwatch_dir='/var/log/loadwatch', buffer_minutes=4):
    """
    Waits for Loadwatch to finish its operation based on the modification time of the output files.

    :param loadwatch_dir: Directory where Loadwatch stores its output files.
    :param buffer_minutes: Buffer time in minutes to ensure Loadwatch has finished its operations.
    :return: None
    """
    now = datetime.now()
    buffer_time = timedelta(minutes=buffer_minutes)

    while True:
        latest_file = find_latest_loadwatch_file(loadwatch_dir)
        if latest_file:
            mod_time = datetime.fromtimestamp(os.path.getmtime(latest_file))
            if now - mod_time > buffer_time:
                break
        time.sleep(60)  # Wait for 1 minute before checking again
        
def log_server_stats(file_path, apache_port=80, apache_uri='/server-status'):
    # Gathering system statistics
    load_avg = os.getloadavg()[0]
    memory_info = psutil.virtual_memory()
    swap_info = psutil.swap_memory()
    uptime = subprocess.getoutput("uptime")
    top_output = subprocess.getoutput("top -bcn1")
    ps_output = subprocess.getoutput("ps auxf")
    netstat_output = subprocess.getoutput("/bin/netstat -nut")

    # MySQL statistics using mysqladmin
    mysqladmin_stat = subprocess.getoutput("mysqladmin stat")
    mysqladmin_processlist = subprocess.getoutput("mysql -e 'show processlist\G'")
    
    # Apache statistics
    httpd_stats = ""
    if apache_port != 0:
        httpd_stats = subprocess.getoutput(f"lynx -dump -width 400 http://localhost:{apache_port}/{apache_uri}")
    else:
        # Count connections if apache_port is 0
        # You can implement the connection counting here based on your needs
        httpd_stats = "Apache port is set to 0. Connections counting not implemented."

    # Writing to log file
    with open(file_path, 'a') as f:
        f.write("## server overview\n")
        f.write(f"{datetime.now()} load[{load_avg}] mem[{memory_info.percent}/{swap_info.percent}] mysql[-/-] httpd[{apache_port}]\n")
        f.write(f"{memory_info}\n{uptime}\n\n")
        
        f.write("## system overview\n")
        f.write(f"{top_output}\n{ps_output}\n\n")
        
        f.write("## mysql stats\n")
        f.write(f"{mysqladmin_stat}\n{mysqladmin_processlist}\n\n")
        
        f.write("## network stats\n")
        f.write(f"{netstat_output}\n\n")
        
        if apache_port != 0:
            f.write("## httpd stats\n")
            f.write(f"{httpd_stats}\n\n")
    
    
def find_latest_loadwatch_file(loadwatch_dir='/var/log/loadwatch', days_threshold=1):
    # Get the current time
    now = datetime.now()

    # List all files in the loadwatch directory
    all_files = os.listdir(loadwatch_dir)
    
    # Filter and sort files based on modification time and date threshold
    valid_files = []
    for file in all_files:
        # Construct full file path
        file_path = os.path.join(loadwatch_dir, file)
        
        # Get the file's modification time and convert it to datetime
        mod_time = datetime.fromtimestamp(os.path.getmtime(file_path))
        
        # Calculate the difference in days between now and the file's modification time
        days_diff = (now - mod_time).days
        
        # Check if the file is a text file and is within the date threshold
        if file.endswith('.txt') and days_diff <= days_threshold:
            valid_files.append((file_path, mod_time))
    
    # Sort files by modification time in descending order
    valid_files.sort(key=lambda x: x[1], reverse=True)

    # Return the path of the latest file, or None if no valid file was found
    return valid_files[0][0] if valid_files else None

def create_and_log_file():
    current_time = datetime.now()
    formatted_time = current_time.strftime("%Y-%m-%d.%H.%M")
    filename = f"loadwatch_stats_{formatted_time}.log"
    file_path = os.path.join("", filename)
    log_server_stats(file_path)