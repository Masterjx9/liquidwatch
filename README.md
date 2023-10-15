# LiquidWatch 🚀

_LiquidWatch is a lightweight Python-based monitoring tool designed especially for LiquidWeb servers. It efficiently tracks the server's load and zeroes in on specific processes that might be the culprits behind potential hiccups._

## 🌟 Features

- **🔍 Monitors Server Load**: Sends alerts if the load goes beyond a specified threshold.
- **📊 Scans Top Processes**: Pinpoints the top CPU-intensive processes at work.
- **📋 Watchlist**: Keeps an eye on specific processes like `httpd2`, `apache`, `mysql`, `whm`, `cpanel`, `plesk`, `interworx`, and `php-fpm`.
- **🛠 Customizable Actions**: Execute specific actions when watchlisted processes are detected.

## 📦 Prerequisites

- Python 3.6 or above
- `psutil` library

## 🔧 Installation

**Clone the Repository**:
   ```bash
   git clone https://github.com/yourusername/liquidwatch.git
   cd liquidwatch
   ```

### Manual Installation 
1. **Setup Virtual Environment**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. **Install Dependencies**:
   ```bash
   pip install psutil
   ```

3. 🚀 **Run the script**:
```bash
python liquidwatch.py
```

### Automatic Installation

1. **Move the service file to the systemd directory**
   ```bash
   sudo cp liquidwatch.service /etc/systemd/system/
   ```

2. **Reload systemd to recognize the new service**
   ```bash
   sudo systemctl daemon-reload
   ```

3. **Enable the service to start on boot**
   ```bash
   sudo systemctl enable liquidwatch
   ```

4. **Start the service**
   ```bash
   sudo systemctl start liquidwatch
   ```

5. **Check the status of the service**
   ```bash
   sudo systemctl status liquidwatch
   ```

## 🤝 Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## 📜 License

[MIT](https://choosealicense.com/licenses/mit/)
