# ⏱️ Chrony NTP Web Interface V2

A simple but powerful **web interface** for monitoring Chrony NTP clients.  
Built with **Flask + Bootstrap + jQuery**, it provides a clean, responsive UI with live updates.

## 👨‍💻 Author

Created by **anoniemerd** 🇳🇱  
[GitHub Profile](https://github.com/anoniemerd)

## ✨ Features

- 🔎 **Live overview** of all Chrony clients (auto-refresh every second)
- 📊 **Summary dashboard** (OK / Warning / Critical clients)
- 🎨 **Light/Dark mode toggle**
- 🗂️ **Sorting & search** (by IP, drop count, last seen)
- ⬇️ **Expandable client cards** with detailed info
- 💾 **State persistence**: open/closed cards & theme saved in localStorage
- 🖥️ **Responsive layout** with CSS Grid masonry effect


## 📸 Screenshots
<img width="3822" height="1941" alt="afbeelding" src="https://github.com/user-attachments/assets/625d6986-eddf-43ad-98fc-5bc8574b5fbf" />
<img width="3830" height="1261" alt="afbeelding" src="https://github.com/user-attachments/assets/d15a82d0-43bc-40e5-af2a-1ec3c0e7f176" />



## ⚙️ Installation Steps :

### 1️⃣ Install required packages
On your Linux server, with chrony already installed and running, install the other necessary dependencies:
```bash
sudo apt update && sudo apt install -y python3 python3-pip python3.12-venv chrony nginx
```

### 2️⃣ Fix Sudo Permissions for Chrony

By default, the chronyc command requires sudo, which systemd cannot provide interactively. To allow chronyc to run without requiring a password, follow these steps:

➤ Step 2.1: Open the sudo configuration
```bash
sudo  visudo
```
➤ Step 2.2: Grant permission to run chronyc without a password
Scroll to the bottom and add this line: (change the USER to the current user yourself)
```bash
<USERNAME> ALL=(ALL) NOPASSWD: /usr/bin/chronyc
```
➤ Step 2.3: Save and exit

Press CTRL+X, then Y, then Enter.


###  3️⃣ Set Up the Project Directory
Create a dedicated project directory and set up a virtual environment:
```bash
mkdir -p ~/chrony_web && cd ~/chrony_web
python3 -m venv venv
source venv/bin/activate
pip install flask gunicorn
```

### 4️⃣ Create the Flask App (chrony_web.py)
Create the chrony_web.py file inside ~/chrony_web/:
```bash
nano  chrony_web.py
```
Copy and paste the application code (see attachments, chrony_web.py).

Save and exit (CTRL+X, Y, Enter).


### 5️⃣ Test the Flask App with Gunicorn
Test the setup by running:
```bash
gunicorn  --bind  0.0.0.0:5000  chrony_web:app
```
If everything works, stop it with CTRL+C.

### 6️⃣ Create a Systemd Service
To keep the app running, create a systemd service:
```bash
sudo  nano  /etc/systemd/system/chronyweb.service
```

Paste the following configuration: (change <USERNAME> to your username)

```bash
[Unit]

Description=Flask  Chrony  Web  Interface

After=network.target

  

[Service]

User=<USERNAME>

Group=<USERNAME>

WorkingDirectory=/home/<USERNAME>/chrony_web

Environment="PATH=/home/<USERNAME>/chrony_web/venv/bin"

ExecStart=/home/<USERNAME>/chrony_web/venv/bin/gunicorn  --bind  0.0.0.0:5000  chrony_web:app

Restart=always

  

[Install]

WantedBy=multi-user.target
```
Save and exit (CTRL+X, Y, Enter).

➤ Step 6.1: Enable and start the service

```bash
sudo  systemctl  daemon-reload
sudo  systemctl  enable  chronyweb.service
sudo  systemctl  start  chronyweb.service
sudo  systemctl  status  chronyweb.service
```


### 7️⃣ Finished 🎉

Your app is now running as a background service. Test it in your browser by typing:
```bash
http://<IP-ADDRESS>:5000/
```

## 🔄 Upgrading from V1 to V2

If you want to switch from **V1** to **V2**, follow these steps:

1. Go to your project directory:
   ```bash
   cd ~/chrony_web/
   rm chrony_web.py
   nano chrony_web.py
   ```
2.  Copy and paste the application code (see attachments, chrony_web.py).
Save and exit (CTRL+X, Y, Enter).   
3. Restart the chronyweb.service
	  ```bash
	  sudo systemctl restart chronyweb.service
	  ```
✅ Enjoy the V2 version!

## 🛠️ Technical Summary

This project provides a lightweight **web dashboard** for Chrony NTP clients.  
Here’s what happens under the hood:

1. **Chrony data collection**  
   - The Flask backend executes `chronyc clients` (via `subprocess`) to retrieve the current list of NTP clients.  
   - Output lines are parsed and classified (hostnames, IPv4, IPv6), then sorted for consistent display.  

2. **REST API endpoint**  
   - The backend exposes a `/data` JSON endpoint returning:  
     - Parsed clients with statistics (packets, drops, last seen, etc.)  
     - A timestamp of the local server time  
     - Error messages (if any)  

3. **Live frontend**  
   - The `/` route serves a self-contained HTML+JS dashboard built with **Bootstrap 5** and **jQuery**.  
   - The UI automatically fetches `/data` every second (`setInterval` + AJAX).  
   - Clients are rendered into **responsive cards** using CSS Grid.

4. **Interactive features**  
   - Client cards can expand/collapse individually, or all at once.  
   - Sorting modes: by IP, drop count, or last-seen timestamp.  
   - Search bar filters results in real-time.  
   - Theme toggle (light/dark) with preference stored in `localStorage`.  
   - Open/closed card state is also persisted locally per user.  

5. **Deployment**  
   - The app is served via **Gunicorn** behind **systemd**, ensuring it runs as a managed background service.  
   - Optionally, Nginx can be used as a reverse proxy for HTTPS termination.

👉 In short: the Flask app continuously polls Chrony, transforms raw CLI output into structured JSON, and feeds it into a dynamic, user-friendly web UI that refreshes live in your browser.


