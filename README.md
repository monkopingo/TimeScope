# TimeScope

**TimeScope** is a Windows application that tracks the amount of time you spend in various applications. It records your usage in real time, stores historical data in a local SQLite database, and provides an easy-to-use interface built with Tkinter. You can also minimize it to the system tray for convenient, unobtrusive monitoring.

## Features

- **Real-time Tracking:** Monitors the currently active window every second, capturing application name and window title.  
- **Automatic Logging:** Stores usage data in a local SQLite database, so your history persists even if the app closes unexpectedly.  
- **Detailed Statistics:** View total time spent on each application for different intervals (e.g., All Time, 24 Hours, 48 Hours, Week, Month, Year).  
- **Modern Tkinter GUI:** A clean interface using `ttk` styles to display your usage in a sortable table.  
- **System Tray Integration:** Runs in the background with a tray icon (via [pystray](https://pypi.org/project/pystray/)), allowing you to show or hide the main window and exit gracefully.

## Screenshots

![image](https://github.com/user-attachments/assets/f261330f-1f55-4e04-8bad-457eeb375177)
![image](https://github.com/user-attachments/assets/95c33529-cfdd-406a-9a8d-1ae0298d1954)
![image](https://github.com/user-attachments/assets/03de0a22-48d8-413a-9854-c3448b0fbe89)


## Getting Started

### Prerequisites

- **Windows OS** (tracking code uses Windows-specific APIs)
- **Python 3.7+** (for best compatibility, 3.11 or below recommended if you plan to build with PyInstaller)
- The following Python packages:
  - `pywin32`
  - `psutil`
  - `pystray`
  - `Pillow` (for tray icon images)
  - `sqlite3` (usually comes with Python)
  - `tkinter` (usually comes with Python)

Install the required libraries:
```bash
pip install pywin32 psutil pystray pillow
```

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-username/timescope.git
   ```
2. **Navigate to the project folder**:
   ```bash
   cd timescope
   ```
3. **Install dependencies** (if you haven’t already):
   ```bash
   pip install -r requirements.txt
   ```
   *(Create or update a `requirements.txt` if desired.)*

### Usage

1. **Run the main script**:
   ```bash
   python main.py
   ```
2. **Interact with the GUI**:
   - The main window shows a dropdown to select the time interval for stats (e.g., “All time,” “24 hours,” etc.).
   - A table (Treeview) displays the total time spent in each application for the chosen interval.
3. **System Tray**:
   - When you close the main window, it actually just hides (minimizes to tray).  
   - To exit completely, use the tray icon menu (right-click → “Exit”) or press Ctrl+C in the terminal window running the script.

### Building an Executable (Optional)

If you want to distribute the program without requiring Python on the user’s machine, you can build an executable using [PyInstaller](https://www.pyinstaller.org/). For example:

```bash
pyinstaller --noconsole main.py
```

> **Note**:  
> - If you’re using Python 3.12 or newer, PyInstaller may not fully support it yet. Consider using Python 3.11 or lower, or try the development version of PyInstaller from GitHub.  
> - Make sure to run the final executable from the `dist/` folder that PyInstaller creates.

## How It Works

1. **Tracking Loop**  
   A background thread checks the currently active window every second using the Windows API (`win32gui`, `win32process`, etc.). It identifies the process ID and extracts a human-readable description (via `win32api.GetFileVersionInfo`) or falls back to the process name.

2. **Data Storage**  
   Each “usage event” is stored in an internal list and also written to a local SQLite database (`app_usage.db`). This means your data persists even if the program exits unexpectedly.

3. **Statistics**  
   To calculate total usage time for a given interval, the program sums the durations of events that intersect with that interval. The results are then sorted by total usage time and displayed in the GUI.

4. **Tkinter GUI**  
   - Built using `ttk` for a cleaner look.  
   - The main window shows a `Treeview` listing each application and the formatted time (HH:MM:SS).  
   - A dropdown menu (OptionMenu) lets you select different time intervals.

5. **System Tray**  
   - Uses [pystray](https://pypi.org/project/pystray/) and [Pillow](https://pypi.org/project/Pillow/) to create a simple tray icon.  
   - The tray icon has a context menu for showing the main window or exiting the program.  
   - When you click the window’s close button, the main window is hidden instead of exiting, so tracking continues.

## License
This project is licensed under the [MIT License](LICENSE). Feel free to use, modify, and distribute it as you wish.
