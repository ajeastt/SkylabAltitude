import requests
import time
from SimConnect import SimConnect, AircraftRequests
import tkinter as tk
import webbrowser
from tkinter import messagebox
import threading

client_version = 2000
website_address = "https://aviation.skylabco.cloud"

class PlaneTrackerApp:
    def __init__(self, master):
        self.master = master
        master.title("SkylabAltitude")
        master.resizable(False, False)
        master.geometry("400x300")
        master.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Status labels
        self.sim_status = tk.Label(master, text="Not connected to sim", fg="red")
        self.server_status = tk.Label(master, text="Not connected to server", fg="red")
        self.ident_label = tk.Label(master, text="LOADING", font=("Courier", 36))
        self.link_label = tk.Label(master, text="", fg="blue", cursor="hand2")
        self.stats_label = tk.Label(master, text="")

        for w in (self.sim_status, self.server_status, self.ident_label, self.link_label, self.stats_label):
            w.pack(pady=2)

        self.session = requests.Session()
        self.delay_ms = 1000  # update interval (ms)
        self.running = True
        self.last_state = None  # track last sent sim data

        # Start connections in threads
        threading.Thread(target=self.connect_sim, daemon=True).start()
        threading.Thread(target=self.connect_server, daemon=True).start()

    def on_closing(self):
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            self.running = False
            self.master.destroy()

    def connect_sim(self):
        attempts = 0
        while self.running:
            try:
                sm = SimConnect()
                self.aq = AircraftRequests(sm, _time=10)
                self.sim_status.config(text="Connected to sim", fg="green")
                break
            except Exception:
                attempts += 1
                self.sim_status.config(text=f"Connecting to sim... ({attempts})", fg="red")
                time.sleep(1)

    def connect_server(self):
        while not hasattr(self, 'aq') and self.running:
            time.sleep(0.1)
        while self.running:
            try:
                title = self.aq.get("TITLE").decode('utf-8')
                atc_id = self.aq.get("ATC_ID").decode('utf-8')
                resp = self.session.post(
                    f"{website_address}/api/create_new_plane",
                    json={'title': title, 'atc_id': atc_id, 'client_version': client_version},
                    timeout=5
                )
                resp.raise_for_status()
                data = resp.json()
                self.ident_public = data['ident_public_key']
                self.ident_private = data['ident_private_key']
                self.server_status.config(text="Connected to server", fg="green")
                self.ident_label.config(text=self.ident_public)
                url = f"{website_address}"
                self.link_label.config(text=url)
                self.link_label.bind("<Button-1>", lambda e: webbrowser.open_new(url))
                break
            except Exception:
                self.server_status.config(text="Retrying server...", fg="red")
                time.sleep(2)
        self.master.after(self.delay_ms, self.periodic_update)

    def periodic_update(self):
        if not self.running:
            return
        threading.Thread(target=self.update_location, daemon=True).start()
        self.master.after(self.delay_ms, self.periodic_update)

    def update_location(self):
        try:
            p = self.aq
            # Gather sim data
            state = (
                p.get("PLANE_LATITUDE"),
                p.get("PLANE_LONGITUDE"),
                p.get("PLANE_ALTITUDE"),
                p.get("MAGNETIC_COMPASS"),
                p.get("SIM_ON_GROUND")
            )
            # REMOVE this if/else, always send update
            data = {
                'ident_public_key': self.ident_public,
                'ident_private_key': self.ident_private,
                'current_latitude': state[0],
                'current_longitude': state[1],
                'current_altitude': state[2],
                'current_compass': state[3],
                'title': p.get("TITLE").decode('utf-8'),
                'atc_id': p.get("ATC_ID").decode('utf-8'),
                'on_ground': state[4],
                'client_version': client_version
            }
            self.session.post(f"{website_address}/api/update_plane_location", json=data, timeout=5)
            self.stats_label.config(text=f"Updated at {time.strftime('%H:%M:%S')}")
        except Exception as e:
            self.stats_label.config(text=f"Error: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = PlaneTrackerApp(root)
    root.mainloop()
