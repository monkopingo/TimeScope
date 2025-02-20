import tkinter as tk
from tkinter import ttk
import threading
import time
import datetime
import sqlite3
import sys
import os

import win32gui
import win32process
import psutil
import win32api

import pystray
from PIL import Image, ImageDraw

def get_file_description(exe_path: str) -> str:
    try:
        info = win32api.GetFileVersionInfo(exe_path, "\\VarFileInfo\\Translation")
        if not info:
            return None

        lang, codepage = info[0]
        str_info_path = u"\\StringFileInfo\\%04X%04X\\FileDescription" % (lang, codepage)
        description = win32api.GetFileVersionInfo(exe_path, str_info_path)
        if description:
            return description
        return None
    except:
        return None

def get_process_description(pid: int) -> str:
    try:
        proc = psutil.Process(pid)
        exe_path = proc.exe() 
        file_desc = get_file_description(exe_path)
        if file_desc:
            return file_desc
        else:
            return proc.name()
    except:
        return "Unknown"

class AppUsageTracker:
    def __init__(self):
        self.events = []
        self.current_event = None
        self.lock = threading.Lock()
        self.running = True

        self.conn = sqlite3.connect("app_usage.db", check_same_thread=False)
        self.cursor = self.conn.cursor()
        self._init_db()
        self._load_events_from_db()

    def _init_db(self):
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS events (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                app TEXT,
                                title TEXT,
                                start TEXT,
                                end TEXT
                              )''')
        self.conn.commit()

    def _load_events_from_db(self):
        self.cursor.execute("SELECT app, title, start, end FROM events")
        rows = self.cursor.fetchall()
        for app, title, start_str, end_str in rows:
            try:
                start_dt = datetime.datetime.fromisoformat(start_str)
                end_dt = datetime.datetime.fromisoformat(end_str)
            except Exception:
                continue
            self.events.append({
                "app": app,
                "title": title,
                "start": start_dt,
                "end": end_dt
            })

    def get_active_window(self):
        """
        thanks gpt for fix
        """
        try:
            hwnd = win32gui.GetForegroundWindow()
            if hwnd == 0:
                return "Idle", ""
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            app_description = get_process_description(pid)
            title = win32gui.GetWindowText(hwnd)
            if not app_description:
                app_description = "Unknown"
            return app_description, title
        except Exception:
            return "Idle", ""

    def track(self):
        while self.running:
            app, title = self.get_active_window()
            now = datetime.datetime.now()
            with self.lock:
                if self.current_event is None:
                    self.current_event = {"app": app, "title": title, "start": now, "end": now}
                else:
                    if app == self.current_event["app"] and title == self.current_event["title"]:
                        self.current_event["end"] = now
                    else:
                        self.events.append(self.current_event)
                        self._insert_event_to_db(self.current_event)
                        self.current_event = {"app": app, "title": title, "start": now, "end": now}
            time.sleep(1)

    def _insert_event_to_db(self, event):
        self.cursor.execute("INSERT INTO events (app, title, start, end) VALUES (?, ?, ?, ?)",
                            (event["app"],
                             event["title"],
                             event["start"].isoformat(),
                             event["end"].isoformat()))
        self.conn.commit()

    def compute_stats(self, delta):
        now = datetime.datetime.now()
        start_interval = None if delta is None else now - delta

        stats = {}
        with self.lock:
            all_events = self.events.copy()
            if self.current_event:
                all_events.append(self.current_event)

        for event in all_events:
            event_start = event["start"]
            event_end = event["end"]
            if start_interval is None:
                duration = (event_end - event_start).total_seconds()
            else:
                if event_end < start_interval:
                    continue
                effective_start = max(event_start, start_interval)
                duration = (event_end - effective_start).total_seconds()
            if duration < 0:
                continue
            app = event["app"] if event["app"] else "Unknown"
            stats[app] = stats.get(app, 0) + duration
        return stats

    def stop(self):
        self.running = False
        with self.lock:
            if self.current_event:
                self.events.append(self.current_event)
                self._insert_event_to_db(self.current_event)
        self.conn.close()

class AppTrackerGUI:
    def __init__(self, tracker):
        self.tracker = tracker
        self.root = tk.Tk()
        self.root.title("Check apps time!")
        self.root.geometry("600x400")
        self.root.resizable(False, False)

        self.style = ttk.Style(self.root)
        self.style.theme_use('clam')

        self.interval_var = tk.StringVar(value="All time")
        intervals = ["All time", "24 hours", "48 hours", "Week", "Month", "Year"]
        self.intervals = intervals

        top_frame = ttk.Frame(self.root)
        top_frame.pack(pady=10, padx=10, anchor="w")
        ttk.Label(top_frame, text="Choose Interval: ").pack(side=tk.LEFT, padx=(0,5))
        interval_menu = ttk.OptionMenu(top_frame, self.interval_var, intervals[0], *intervals, command=self.update_stats)
        interval_menu.pack(side=tk.LEFT)

        self.tree = ttk.Treeview(self.root, columns=("app", "time"), show="headings", height=15)
        self.tree.heading("app", text="App")
        self.tree.column("app", width=400, anchor="w")
        self.tree.heading("time", text="time (h:m:s)")
        self.tree.column("time", width=120, anchor="center")

        self.tree.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        self.update_stats()
        self.root.protocol("WM_DELETE_WINDOW", self.hide_window)

    def get_interval_delta(self, interval_name):
        if interval_name == "All time":
            return None
        elif interval_name == "24 hours":
            return datetime.timedelta(hours=24)
        elif interval_name == "48 hours":
            return datetime.timedelta(hours=48)
        elif interval_name == "Week":
            return datetime.timedelta(weeks=1)
        elif interval_name == "Month":
            return datetime.timedelta(days=30)
        elif interval_name == "Year":
            return datetime.timedelta(days=365)
        return None

    def update_stats(self, *args):
        for item in self.tree.get_children():
            self.tree.delete(item)

        interval_name = self.interval_var.get()
        delta = self.get_interval_delta(interval_name)
        stats = self.tracker.compute_stats(delta)
        sorted_stats = sorted(stats.items(), key=lambda x: x[1], reverse=True)

        for app, seconds in sorted_stats:
            h = int(seconds // 3600)
            m = int((seconds % 3600) // 60)
            s = int(seconds % 60)
            time_str = f"{h:02d}:{m:02d}:{s:02d}"
            self.tree.insert("", tk.END, values=(app, time_str))

        self.root.after(1000, self.update_stats)

    def hide_window(self):
        self.root.withdraw()

    def show_window(self):
        self.root.deiconify()
        self.root.lift()

    def run(self):
        self.root.mainloop()

def create_tray_image():
    image = Image.new('RGB', (64, 64), color=(0, 0, 0))
    dc = ImageDraw.Draw(image)
    dc.ellipse((8, 8, 56, 56), fill=(0, 128, 255))
    dc.text((22, 24), "A", fill=(255, 255, 255))
    return image

def setup_tray(gui):
    def on_show(icon, item):
        gui.root.after(0, gui.show_window)
    def on_exit(icon, item):
        icon.stop()
        gui.root.after(0, gui.root.quit)
    image = create_tray_image()
    menu = pystray.Menu(
        pystray.MenuItem("Info", on_show),
        pystray.MenuItem("Exit", on_exit)
    )
    tray_icon = pystray.Icon("AppTracker", image, "App time", menu)
    threading.Thread(target=tray_icon.run, daemon=True).start()

def main():
    tracker = AppUsageTracker()
    tracking_thread = threading.Thread(target=tracker.track, daemon=True)
    tracking_thread.start()

    gui = AppTrackerGUI(tracker)
    setup_tray(gui)
    try:
        gui.run()
    except KeyboardInterrupt:
        pass
    finally:
        tracker.stop()
        sys.exit()

if __name__ == "__main__":
    main()
