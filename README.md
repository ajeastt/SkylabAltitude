# SkylabAltitude Client

[![Version](https://img.shields.io/badge/version-2.1.0-blue)](https://github.com/yourusername/SkylabAltitude)
[![Status](https://img.shields.io/badge/status-production--ready-green)](https://github.com/yourusername/SkylabAltitude)

A professional desktop application that streams real-time aircraft data from Microsoft Flight Simulator to the SkylabAltitude tracking network. Built with modern Python and featuring a sleek aviation-inspired interface.

---

## 🌐 Live Tracking
Track flights in real-time at: **[aviation.skylabco.cloud](https://aviation.skylabco.cloud)**

## Need Help?
[Discord](https://discord.gg/V4BvVskxSG)

---

## ✈️ Features

### **Flight Tracking**
- **SimConnect Integration**: Real-time data from Microsoft Flight Simulator
- **Live Position Updates**: Latitude, longitude, altitude, heading, ground speed
- **Aircraft Details**: Type, ATC call sign, ground/flight status
- **Smart Rate Limiting**: Intelligent retry logic with exponential backoff

### **Professional Interface**
- **Aviation-Themed UI**: Clean, professional design inspired by flight software
- **Connection Status**: Real-time indicators for simulator and server connections
- **Statistics Dashboard**: Update counts, error tracking, last update times
- **Progress Indicators**: Visual feedback during connection attempts

### **Advanced Features**
- **Auto-Reconnection**: Automatically handles connection failures
- **Configurable Settings**: Server URL, update intervals, retry behavior
- **Logging System**: Comprehensive logging for troubleshooting
- **Web Integration**: One-click access to view your flight online

---

## 🚀 Running with Python

```bash
# Install dependencies
pip install requests SimConnect tkinter

# Run the client
python client.py

---

## 🛠️ Requirements

### **Python Requirements**
- **Python 3.8+**
- `requests`
- `SimConnect`
- `tkinter` (usually included with Python)

---

## 📖 Usage

1. **Start Microsoft Flight Simulator** and load into any aircraft
2. **Launch SkylabAltitude Client**
3. **Wait for connections**: 
  - Green dots indicate successful connections
  - Your unique flight code will appear when ready
4. **View online**: Click "View Online" to see your flight on the web map
5. **Share your code**: Others can track your flight using your 6-character code

### **Configuration**
Click "Settings" to configure:
- **Server URL**: Default points to official server
- **Update Interval**: How often to send position (minimum 1000ms)
- **Auto-reconnect**: Automatically retry failed connections

---

## 🐛 Troubleshooting

### **Connection Issues**
- **Simulator**: Ensure MSFS is running and SimConnect is enabled
- **Server**: Check internet connection and server status
- **Rate Limits**: Client automatically handles server rate limiting

### **Performance**
- Default update interval is 1000ms (1 second)
- Increase interval in settings if experiencing issues
- Check logs in `client.log` for detailed troubleshooting

---

## 🗺️ Roadmap

### **Completed ✅**
- [x] Professional desktop client with modern UI
- [x] Real-time flight tracking with web interface
- [x] Smart connection management and error handling
- [x] Production-ready server infrastructure

### **Planned 🚧**
- [ ] **Enhanced Web Features**: Flight trails, multiple aircraft view
- [ ] **Flight Planning**: Route planning and sharing
- [ ] **Community Features**: Public flights, events, leaderboards

---

## 🤝 Contributing

We welcome contributions! This project is **open source**.

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

## 🙏 Acknowledgments

- **Microsoft Flight Simulator** for SimConnect API
- **Flight simulation community** for inspiration and feedback
- **Contributors** who help improve the project

---

**Ready for takeoff? Download now and join the SkylabAltitude network!** ✈️