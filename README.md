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

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/yourusername/liquidwatch.git
   cd liquidwatch
   ```

2. **Setup Virtual Environment**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install psutil
   ```

## 🚀 Usage

Run the script:
```bash
python liquidwatch.py
```

## 🤝 Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## 📜 License

[MIT](https://choosealicense.com/licenses/mit/)
