import logging
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import yaml
from pathlib import Path
from emailer_bot.main import run_monitor

CONFIG_PATH = Path("config.yaml")
EXAMPLE_CONFIG_PATH = Path("config.example.yaml")

class TextHandler(logging.Handler):
    """Redirect logging output to a Tkinter ScrolledText widget."""
    def __init__(self, text_widget):
        super().__init__()
        self.text_widget = text_widget

    def emit(self, record):
        msg = self.format(record)
        def append():
            self.text_widget.configure(state='normal')
            self.text_widget.insert(tk.END, msg + '\n')
            self.text_widget.configure(state='disabled')
            self.text_widget.yview(tk.END)
        self.text_widget.after(0, append)

class EmailerBotGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Investment Emailer Bot")
        self.root.geometry("900x700")

        self.stop_event = threading.Event()
        self.monitor_thread = None
        self.config_data = {}
        self.fields = []  # List of (entry_widget, key_path)

        self.setup_ui()
        self.load_config()
        self.setup_logging()

    def setup_ui(self):
        # Main layout
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Config Notebook
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Tabs
        self.tabs = {}
        self.create_general_tab()
        self.create_imap_tab()
        self.create_smtp_tab()
        self.create_onedrive_tab()
        self.create_openai_tab()
        self.create_recipients_tab()

        # Controls
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=5)

        ttk.Button(control_frame, text="Save Config", command=self.save_config).pack(side=tk.LEFT, padx=5)
        self.start_btn = ttk.Button(control_frame, text="Start Bot", command=self.start_bot)
        self.start_btn.pack(side=tk.LEFT, padx=5)
        self.stop_btn = ttk.Button(control_frame, text="Stop Bot", command=self.stop_bot, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5)

        # Logs
        log_frame = ttk.LabelFrame(main_frame, text="Logs", padding="5")
        log_frame.pack(fill=tk.BOTH, expand=True)

        self.log_area = scrolledtext.ScrolledText(log_frame, state='disabled', height=10)
        self.log_area.pack(fill=tk.BOTH, expand=True)

    def create_tab(self, name):
        frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(frame, text=name)
        self.tabs[name] = frame
        return frame

    def add_field(self, parent, label_text, key_path):
        """Helper to create a label and entry linked to config_data."""
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.X, pady=2)

        ttk.Label(frame, text=label_text, width=20, anchor='w').pack(side=tk.LEFT)
        entry = ttk.Entry(frame)
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.fields.append((entry, key_path))
        return entry

    def create_general_tab(self):
        tab = self.create_tab("General")
        self.add_field(tab, "Investment Keyword", ["investment_keyword"])
        self.add_field(tab, "Poll Interval (sec)", ["poll_interval_seconds"])

    def create_imap_tab(self):
        tab = self.create_tab("IMAP")
        self.add_field(tab, "Host", ["imap", "host"])
        self.add_field(tab, "Port", ["imap", "port"])
        self.add_field(tab, "Username", ["imap", "username"])
        self.add_field(tab, "Password", ["imap", "password"])
        self.add_field(tab, "Folder", ["imap", "folder"])

    def create_smtp_tab(self):
        tab = self.create_tab("SMTP")
        self.add_field(tab, "Host", ["smtp", "host"])
        self.add_field(tab, "Port", ["smtp", "port"])
        self.add_field(tab, "Username", ["smtp", "username"])
        self.add_field(tab, "Password", ["smtp", "password"])
        self.add_field(tab, "From Email", ["smtp", "from_email"])
        self.add_field(tab, "Subject Prefix", ["smtp", "subject_prefix"])

    def create_onedrive_tab(self):
        tab = self.create_tab("OneDrive")
        self.add_field(tab, "Access Token", ["onedrive", "access_token"])
        self.add_field(tab, "Drive ID", ["onedrive", "drive_id"])
        self.add_field(tab, "Folder Path", ["onedrive", "folder_path"])
        self.add_field(tab, "Max Files", ["onedrive", "max_files"])

    def create_openai_tab(self):
        tab = self.create_tab("OpenAI")
        self.add_field(tab, "API Key", ["openai", "api_key"])
        self.add_field(tab, "Model", ["openai", "model"])

    def create_recipients_tab(self):
        tab = self.create_tab("Recipients")
        ttk.Label(tab, text="Recipients (YAML format list):").pack(anchor='w')
        self.recipients_text = scrolledtext.ScrolledText(tab, height=10)
        self.recipients_text.pack(fill=tk.BOTH, expand=True)

    def get_nested_value(self, data, path):
        current = data
        for key in path:
            if isinstance(current, dict):
                current = current.get(key, {})
            else:
                return ""
        return current if not isinstance(current, dict) else ""

    def set_nested_value(self, data, path, value):
        current = data
        for key in path[:-1]:
            current = current.setdefault(key, {})
        current[path[-1]] = value

    def load_config(self):
        path = CONFIG_PATH if CONFIG_PATH.exists() else EXAMPLE_CONFIG_PATH
        if not path.exists():
            messagebox.showerror("Error", "Config file not found!")
            return

        try:
            with open(path, 'r') as f:
                self.config_data = yaml.safe_load(f) or {}
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load config: {e}")
            return

        # Populate fields
        for entry, key_path in self.fields:
            val = self.get_nested_value(self.config_data, key_path)
            entry.delete(0, tk.END)
            entry.insert(0, str(val))

        # Populate recipients
        recipients = self.config_data.get("recipients", [])
        self.recipients_text.delete('1.0', tk.END)
        # Using safe_dump to ensure it's readable
        self.recipients_text.insert('1.0', yaml.safe_dump(recipients, default_flow_style=False))

    def save_config(self):
        # Update config_data from UI
        for entry, key_path in self.fields:
            val = entry.get()
            # Try to convert to int if possible for ports/intervals
            if val.isdigit():
                val = int(val)
            self.set_nested_value(self.config_data, key_path, val)

        try:
            recipients_yaml = self.recipients_text.get('1.0', tk.END)
            recipients_data = yaml.safe_load(recipients_yaml)
            if recipients_data is None:
                recipients_data = []
            if not isinstance(recipients_data, list):
                raise ValueError("Recipients must be a list")
            self.config_data["recipients"] = recipients_data
        except Exception as e:
            messagebox.showerror("Error", f"Invalid Recipients YAML: {e}")
            return

        try:
            with open(CONFIG_PATH, 'w') as f:
                yaml.dump(self.config_data, f, default_flow_style=False)
            messagebox.showinfo("Success", "Configuration saved!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save config: {e}")

    def setup_logging(self):
        # Add handler to root logger
        logger = logging.getLogger()
        if not any(isinstance(h, TextHandler) for h in logger.handlers):
            handler = TextHandler(self.log_area)
            handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)

    def start_bot(self):
        if not CONFIG_PATH.exists():
            messagebox.showwarning("Warning", "Please save configuration first!")
            return

        self.stop_event.clear()
        self.monitor_thread = threading.Thread(target=self.run_wrapper, daemon=True)
        self.monitor_thread.start()

        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        logging.info("Bot started.")

    def run_wrapper(self):
        try:
            run_monitor(str(CONFIG_PATH), self.stop_event)
        except Exception as e:
            logging.error(f"Bot crashed: {e}")
        finally:
            # Schedule UI update on main thread
            self.root.after(0, self.on_bot_stop)

    def stop_bot(self):
        if self.monitor_thread and self.monitor_thread.is_alive():
            logging.info("Stopping bot... (this may take up to poll interval)")
            self.stop_event.set()
            self.stop_btn.config(state=tk.DISABLED)

    def on_bot_stop(self):
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        logging.info("Bot stopped.")

if __name__ == "__main__":
    root = tk.Tk()
    app = EmailerBotGUI(root)
    root.mainloop()
