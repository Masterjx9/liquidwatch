import os
import psutil
import subprocess   
from datetime import datetime, timedelta
import time
import shutil


def wait_for_loadwatch(loadwatch_dir='/var/log/loadwatch', buffer_minutes=4, old_threshold_minutes=10):
    """
    Waits for Loadwatch to finish its operation based on the modification time of the output files.

    :param loadwatch_dir: Directory where Loadwatch stores its output files.
    :param buffer_minutes: Buffer time in minutes to ensure Loadwatch has finished its operations.
    :param old_threshold_minutes: Threshold time in minutes after which the file is considered old.
    :return: Status of the file, "good" if within threshold, "old" if past the old threshold, and None otherwise.
    """
    buffer_time = timedelta(minutes=buffer_minutes)
    old_threshold_time = timedelta(minutes=old_threshold_minutes)
    first_detected_file = None

    while True:
        now = datetime.now()
        
        if not first_detected_file:
            first_detected_file = find_latest_loadwatch_file(loadwatch_dir)
        
        if first_detected_file:
            mod_time = datetime.fromtimestamp(os.path.getmtime(first_detected_file))
            time_difference = now - mod_time
            
            print(f"First detected file: {first_detected_file}")
            print(f"File modification time: {mod_time}")
            print(f"Current time: {now}")
            print(f"Time difference: {time_difference}")
            print(f"Buffer time: {buffer_time}")
            print(f"Old threshold time: {old_threshold_time}")
            
            if time_difference > old_threshold_time:
                print("File is too old.")
                return "old"
            elif buffer_time <= time_difference <= old_threshold_time:
                print("File is within the acceptable time range.")
                return "good"
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

def copy_loadwatch_file(loadwatch_dir='/var/log/loadwatch'):
    latest_file = find_latest_loadwatch_file(loadwatch_dir)
    if latest_file:
        # Extract filename from the latest Loadwatch file path
        _, filename = os.path.split(latest_file)
        
        # Remove file extension from filename to create the folder name
        folder_name = os.path.splitext(filename)[0]
        
        # Create the directory with the same name as the Loadwatch file in /var/log/liquidwatch
        new_directory_path = os.path.join("/var/log/liquidwatch", folder_name)
        os.makedirs(new_directory_path, exist_ok=True)
        
        # Copy the Loadwatch file to the new directory
        new_file_path = os.path.join(new_directory_path, filename)
        shutil.copy(latest_file, new_file_path)
        return new_directory_path
    else:
        print("No recent Loadwatch file found. Please ensure Loadwatch is configured and running.")
        return None
        
def create_and_log_file():
    # Create a timestamped folder in the /var/log/liquidwatch directory
    current_time = datetime.now()
    formatted_time = current_time.strftime("%Y-%m-%d.%H.%M")
    folder_name = f"liquidwatch_stats_{formatted_time}"
    directory_path = os.path.join("/var/log/liquidwatch", folder_name)
    os.makedirs(directory_path, exist_ok=True)
    
    # Create the log file within the new directory
    log_file_path = os.path.join(directory_path, 'server_stats.log')
    log_server_stats(log_file_path)
    return directory_path
