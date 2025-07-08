import requests
import time
import json
import os
from SimConnect import SimConnect, AircraftRequests
import tkinter as tk
from tkinter import messagebox, ttk
import threading
import logging
from datetime import datetime
import random

# Configuration
CLIENT_VERSION = "2.1.0"
DEFAULT_SERVER = "https://aviation.skylabco.cloud"
CONFIG_FILE = "client_config.json"
LOG_FILE = "client.log"

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

class PlaneTrackerApp:
    def __init__(self, master):
        self.master = master
        self.setup_window()
        self.load_config()
        self.init_variables()
        self.create_widgets()
        self.setup_session()
        
        # Start connection threads
        threading.Thread(target=self.connect_sim, daemon=True).start()
        threading.Thread(target=self.connect_server, daemon=True).start()
        
        logging.info(f"SkylabAltitude Client {CLIENT_VERSION} started")

    def setup_window(self):
        """Configure the main window"""
        self.master.title(f"SkylabAltitude Client {CLIENT_VERSION}")
        self.master.resizable(False, False)
        self.master.geometry("450x400")
        self.master.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Set window icon if available
        try:
            self.master.iconbitmap("icon.ico")
        except:
            pass

    def load_config(self):
        """Load configuration from file"""
        self.config = {
            "server_url": DEFAULT_SERVER,
            "update_interval": 1000,
            "auto_reconnect": True,
            "reconnect_delay": 5
        }
        
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r') as f:
                    saved_config = json.load(f)
                    self.config.update(saved_config)
                logging.info("Configuration loaded from file")
        except Exception as e:
            logging.warning(f"Failed to load config: {e}")

    def save_config(self):
        """Save configuration to file"""
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            logging.error(f"Failed to save config: {e}")

    def init_variables(self):
        """Initialize instance variables"""
        self.running = True
        self.sim_connected = False
        self.server_connected = False
        self.ident_public = None
        self.ident_private = None
        self.last_update_time = None
        self.update_count = 0
        self.error_count = 0
        self.aq = None
        self.last_rate_limit_time = 0  # Track when we last hit rate limit

    def create_widgets(self):
        """Create and arrange GUI widgets"""
        # Main frame
        main_frame = ttk.Frame(self.master, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title
        title_label = tk.Label(
            main_frame, 
            text="SkylabAltitude", 
            font=("Arial", 18, "bold"),
            fg="#4A90E2"
        )
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 10))
        
        # Status section
        status_frame = ttk.LabelFrame(main_frame, text="Connection Status", padding="10")
        status_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.sim_status = tk.Label(status_frame, text="● Not connected to simulator", fg="red")
        self.sim_status.grid(row=0, column=0, sticky=tk.W, pady=2)
        
        self.server_status = tk.Label(status_frame, text="● Not connected to server", fg="red")
        self.server_status.grid(row=1, column=0, sticky=tk.W, pady=2)
        
        # Flight code section
        code_frame = ttk.LabelFrame(main_frame, text="Flight Code", padding="10")
        code_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.ident_label = tk.Label(
            code_frame, 
            text="LOADING...", 
            font=("Courier New", 24, "bold"),
            fg="#4A90E2"
        )
        self.ident_label.grid(row=0, column=0, columnspan=2)
        
        # Statistics section
        stats_frame = ttk.LabelFrame(main_frame, text="Statistics", padding="10")
        stats_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.stats_label = tk.Label(stats_frame, text="Waiting for connection...", justify=tk.LEFT)
        self.stats_label.grid(row=0, column=0, sticky=tk.W)
        
        # Control section
        control_frame = ttk.LabelFrame(main_frame, text="Controls", padding="10")
        control_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Button(control_frame, text="Reconnect", command=self.manual_reconnect).grid(row=0, column=0, padx=(0, 5))
        ttk.Button(control_frame, text="Settings", command=self.show_settings).grid(row=0, column=1, padx=5)
        ttk.Button(control_frame, text="View Online", command=self.open_web_view).grid(row=0, column=2, padx=(5, 0))
        
        # Progress bar
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))

    def setup_session(self):
        """Configure HTTP session with retries and timeouts"""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': f'SkylabAltitude-Client/{CLIENT_VERSION}',
            'Content-Type': 'application/json'
        })

    def calculate_backoff_delay(self, attempt, base_delay=2, max_delay=60):
        """Calculate exponential backoff delay with jitter"""
        # Exponential backoff: base_delay * 2^(attempt-1)
        delay = min(base_delay * (2 ** (attempt - 1)), max_delay)
        # Add jitter (±25% random variance)
        jitter = delay * 0.25 * random.random()
        return delay + jitter

    def handle_rate_limit(self, attempt):
        """Handle rate limiting with smart backoff"""
        self.last_rate_limit_time = time.time()
        
        # For rate limits, use longer delays
        if attempt <= 3:
            delay = 30 + (attempt * 30)  # 30s, 60s, 90s
        else:
            delay = 120  # 2 minutes for subsequent attempts
        
        logging.warning(f"Rate limited. Waiting {delay} seconds before retry...")
        self.update_server_status(f"Rate limited - waiting {delay}s...", False)
        
        return delay

    def update_sim_status(self, message, connected=False):
        """Update simulator connection status"""
        self.sim_connected = connected
        color = "green" if connected else "red"
        symbol = "●" if connected else "●"
        self.sim_status.config(text=f"{symbol} {message}", fg=color)
        
    def update_server_status(self, message, connected=False):
        """Update server connection status"""
        self.server_connected = connected
        color = "green" if connected else "red"
        symbol = "●" if connected else "●"
        self.server_status.config(text=f"{symbol} {message}", fg=color)

    def update_stats(self):
        """Update statistics display"""
        if self.last_update_time:
            time_str = self.last_update_time.strftime("%H:%M:%S")
            stats_text = f"Updates sent: {self.update_count}\nLast update: {time_str}\nErrors: {self.error_count}"
        else:
            stats_text = "Waiting for first update..."
        
        self.stats_label.config(text=stats_text)

    def connect_sim(self):
        """Connect to Microsoft Flight Simulator"""
        attempts = 0
        self.progress.start()
        
        while self.running:
            try:
                attempts += 1
                self.update_sim_status(f"Connecting to simulator... (attempt {attempts})")
                
                sm = SimConnect()
                self.aq = AircraftRequests(sm, _time=10)
                
                # Test connection with a simple request
                test_title = self.aq.get("TITLE")
                
                self.update_sim_status("Connected to Microsoft Flight Simulator", True)
                logging.info("Successfully connected to Flight Simulator")
                break
                
            except Exception as e:
                logging.warning(f"Failed to connect to simulator (attempt {attempts}): {e}")
                if attempts >= 10:
                    self.update_sim_status("Failed to connect - Is MSFS running?")
                    if not self.config["auto_reconnect"]:
                        break
                    attempts = 0  # Reset counter for auto-reconnect
                
                # Use exponential backoff for sim connection too
                delay = self.calculate_backoff_delay(attempts, base_delay=1, max_delay=30)
                time.sleep(delay)
        
        self.progress.stop()

    def connect_server(self):
        """Connect to SkylabAltitude server with smart retry logic"""
        # Wait for sim connection
        while not self.sim_connected and self.running:
            time.sleep(0.1)
        
        if not self.running:
            return
            
        attempts = 0
        consecutive_rate_limits = 0
        
        while self.running:
            try:
                attempts += 1
                self.update_server_status(f"Connecting to server... (attempt {attempts})")
                
                # Get aircraft data
                title = self.aq.get("TITLE").decode('utf-8', errors='ignore')
                atc_id = self.aq.get("ATC_ID").decode('utf-8', errors='ignore')
                
                # Register with server
                response = self.session.post(
                    f"{self.config['server_url']}/api/create_new_plane",
                    json={
                        'title': title,
                        'atc_id': atc_id,
                        'client_version': CLIENT_VERSION
                    },
                    timeout=15  # Increased timeout
                )
                response.raise_for_status()
                
                data = response.json()
                self.ident_public = data['ident_public_key']
                self.ident_private = data['ident_private_key']
                
                self.ident_label.config(text=self.ident_public)
                self.update_server_status("Connected to SkylabAltitude server", True)
                
                logging.info(f"Successfully registered with server. Code: {self.ident_public}")
                consecutive_rate_limits = 0  # Reset rate limit counter
                break
                
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 429:  # Rate limited
                    consecutive_rate_limits += 1
                    delay = self.handle_rate_limit(consecutive_rate_limits)
                    time.sleep(delay)
                    continue
                else:
                    logging.warning(f"HTTP error {e.response.status_code}: {e}")
                    self.error_count += 1
                    
            except requests.exceptions.RequestException as e:
                logging.warning(f"Server connection failed (attempt {attempts}): {e}")
                self.error_count += 1
                
            except Exception as e:
                logging.error(f"Unexpected error connecting to server: {e}")
                self.error_count += 1
                
            # Handle max attempts
            if attempts >= 10:
                self.update_server_status("Failed to connect to server")
                if not self.config["auto_reconnect"]:
                    break
                attempts = 0
                consecutive_rate_limits = 0
            
            # Calculate delay based on error type
            if consecutive_rate_limits > 0:
                continue  # Rate limit delay already handled above
            else:
                delay = self.calculate_backoff_delay(attempts, base_delay=2, max_delay=30)
                time.sleep(delay)
        
        # Start periodic updates
        if self.server_connected:
            self.master.after(self.config["update_interval"], self.periodic_update)

    def periodic_update(self):
        """Schedule periodic location updates"""
        if not self.running:
            return
            
        if self.sim_connected and self.server_connected:
            threading.Thread(target=self.update_location, daemon=True).start()
        
        self.master.after(self.config["update_interval"], self.periodic_update)

    def update_location(self):
        """Send location update to server"""
        try:
            if not (self.sim_connected and self.server_connected and self.aq):
                return
            
            # Get current aircraft state
            p = self.aq
            title = p.get("TITLE").decode('utf-8', errors='ignore')
            atc_id = p.get("ATC_ID").decode('utf-8', errors='ignore')
            
            data = {
                'ident_public_key': self.ident_public,
                'ident_private_key': self.ident_private,
                'current_latitude': p.get("PLANE_LATITUDE"),
                'current_longitude': p.get("PLANE_LONGITUDE"), 
                'current_altitude': p.get("PLANE_ALTITUDE"),
                'current_compass': p.get("PLANE_HEADING_DEGREES_MAGNETIC"),
                'title': title,
                'atc_id': atc_id,
                'on_ground': bool(p.get("SIM_ON_GROUND")),
                'ground_speed': p.get("GROUND_VELOCITY"),
                'client_version': CLIENT_VERSION
            }
            
            response = self.session.post(
                f"{self.config['server_url']}/api/update_plane_location",
                json=data,
                timeout=8
            )
            
            if response.status_code == 429:
                # Rate limited on update - back off temporarily
                logging.warning("Rate limited on location update - backing off")
                self.update_server_status("Rate limited - reducing update frequency", True)
                # Double the update interval temporarily
                self.master.after(self.config["update_interval"] * 2, self.periodic_update)
                return
            
            response.raise_for_status()
            
            self.update_count += 1
            self.last_update_time = datetime.now()
            self.update_stats()
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                # Handled above
                pass
            elif e.response.status_code == 403:
                logging.error("Authentication failed - need to reconnect")
                self.server_connected = False
                threading.Thread(target=self.connect_server, daemon=True).start()
            else:
                logging.warning(f"HTTP error during update: {e}")
                self.error_count += 1
                
        except requests.exceptions.RequestException as e:
            logging.warning(f"Failed to update location: {e}")
            self.error_count += 1
            self.update_server_status("Connection error - retrying...", False)
            
            # Attempt to reconnect
            if self.config["auto_reconnect"]:
                threading.Thread(target=self.connect_server, daemon=True).start()
                
        except Exception as e:
            logging.error(f"Unexpected error in update_location: {e}")
            self.error_count += 1

    def manual_reconnect(self):
        """Manually trigger reconnection"""
        self.sim_connected = False
        self.server_connected = False
        self.ident_public = None
        self.ident_private = None
        self.last_rate_limit_time = 0  # Reset rate limit tracking
        
        self.ident_label.config(text="RECONNECTING...")
        
        threading.Thread(target=self.connect_sim, daemon=True).start()
        threading.Thread(target=self.connect_server, daemon=True).start()

    def show_settings(self):
        """Show settings dialog"""
        settings_window = tk.Toplevel(self.master)
        settings_window.title("Settings")
        settings_window.geometry("400x300")
        settings_window.resizable(False, False)
        settings_window.transient(self.master)
        settings_window.grab_set()
        
        # Server URL
        ttk.Label(settings_window, text="Server URL:").grid(row=0, column=0, sticky=tk.W, padx=10, pady=5)
        server_var = tk.StringVar(value=self.config["server_url"])
        ttk.Entry(settings_window, textvariable=server_var, width=40).grid(row=0, column=1, padx=10, pady=5)
        
        # Update interval
        ttk.Label(settings_window, text="Update Interval (ms):").grid(row=1, column=0, sticky=tk.W, padx=10, pady=5)
        interval_var = tk.IntVar(value=self.config["update_interval"])
        ttk.Entry(settings_window, textvariable=interval_var, width=10).grid(row=1, column=1, sticky=tk.W, padx=10, pady=5)
        
        # Auto-reconnect
        auto_reconnect_var = tk.BooleanVar(value=self.config["auto_reconnect"])
        ttk.Checkbutton(settings_window, text="Auto-reconnect on failure", variable=auto_reconnect_var).grid(row=2, column=0, columnspan=2, sticky=tk.W, padx=10, pady=5)
        
        def save_settings():
            self.config["server_url"] = server_var.get().rstrip('/')
            self.config["update_interval"] = max(1000, interval_var.get())  # Minimum 1000ms to respect rate limits
            self.config["auto_reconnect"] = auto_reconnect_var.get()
            self.save_config()
            settings_window.destroy()
            messagebox.showinfo("Settings", "Settings saved! Restart the application for changes to take effect.")
        
        ttk.Button(settings_window, text="Save", command=save_settings).grid(row=3, column=0, pady=20)
        ttk.Button(settings_window, text="Cancel", command=settings_window.destroy).grid(row=3, column=1, pady=20)

    def open_web_view(self):
        """Open web interface in browser"""
        if self.ident_public:
            import webbrowser
            url = f"{self.config['server_url']}/view/{self.ident_public}"
            webbrowser.open(url)
        else:
            messagebox.showwarning("Not Ready", "Flight code not available yet. Please wait for connection.")

    def on_closing(self):
        """Handle application closing"""
        if messagebox.askokcancel("Quit", "Do you want to quit SkylabAltitude?"):
            logging.info("Application shutting down")
            self.running = False
            self.save_config()
            self.master.destroy()

def main():
    """Main entry point"""
    try:
        root = tk.Tk()
        app = PlaneTrackerApp(root)
        root.mainloop()
    except KeyboardInterrupt:
        logging.info("Application interrupted by user")
    except Exception as e:
        logging.error(f"Fatal error: {e}")
        messagebox.showerror("Fatal Error", f"An unexpected error occurred:\n{e}")

if __name__ == "__main__":
    main()