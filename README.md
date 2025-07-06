# Skylab Altitude Client

[![Work in Progress](https://img.shields.io/badge/status-wip-orange)](https://github.com/yourusername/SkylabAltitude)

**⚠️ Work in progress — nothing here is perfect.**

A desktop application that streams real-time aircraft data from Microsoft Flight Simulator (MSFS) to a remote tracking server. Built with Tkinter and SimConnect for a smooth, themed, low-latency experience.

---

## Need Help?
[Discord](https://discord.gg/V4BvVskxSG)

---

## 🚀 Features

- **SimConnect Integration**: Reads live sim data (latitude, longitude, altitude, heading, on-ground status)  
- **Delta-only Updates**: Sends data only when values change, minimizing network traffic  
- **Light/Dark Theme Toggle**: Matches your server’s UI with a single click  
- **Threaded, Non-blocking GUI**: Keeps the interface responsive during network calls  

---

## 🛠 Installation & Running

1. **Clone the client repo**  
   ```bash
   git clone https://github.com/yourusername/SkylabAltitude.git
2. **Install Dependencies**
    ```bash
    pip install requests SimConnect
3. **Running Client**
    ```bash
    python SkylabAltitudeClient.pyw
---

### Road Map
- [ ] Clean up lines for aircraft. Currently showing all lines regaurdless if clicked off of a specific aircraft.
- [ ] Add more data to flight details.
- [ ] Front end UI changes.
