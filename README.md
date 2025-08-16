# ⏱️ Chrony NTP Web Dashboard

A simple but powerful **web interface** for monitoring Chrony NTP clients.  
Built with **Flask + Bootstrap + jQuery**, it provides a clean, responsive UI with live updates.

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
<img width="3825" height="1375" alt="afbeelding" src="https://github.com/user-attachments/assets/32df1d96-d5ab-41c1-bcb0-94ba41498297" />





## ⚙️ Installation Steps :

### 1️⃣ Install required packages
On your Linux server, with chrony already installed and running, install the other necessary dependencies:
```bash
sudo apt update && sudo apt install -y python3 python3-pip python3-venv chrony nginx
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
