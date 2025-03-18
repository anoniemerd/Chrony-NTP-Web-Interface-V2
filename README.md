# Chrony-NTP-Web-Interface
A nice, simple, Web Interface for Chrony NTP

![image](https://github.com/user-attachments/assets/24f37619-fbaa-46ec-a60f-0f837e967697)


## By Anoniemerd

### 1️⃣ Install Required Packages

On your Linux server, install the necessary dependencies:

```bash
sudo apt update && sudo apt install -y python3 python3-pip python3-venv chrony nginx
```

### 2️⃣ Set Up the Project Directory

Create a dedicated project directory and set up a virtual environment:
```bash
mkdir -p ~/chrony_web && cd ~/chrony_web
python3 -m venv venv
source venv/bin/activate
pip install flask gunicorn pytz
```

### 3️⃣ Create the Flask App (chrony_web.py)

Create the chrony_web.py file inside ~/chrony_web/:
```bash
nano chrony_web.py
```
Copy and paste the application code (see attachments, chrony_web.py).

Save and exit (CTRL+X, Y, Enter).

### 4️⃣ Run Flask with Gunicorn

Test the setup by running:
```bash
gunicorn --bind 0.0.0.0:5000 chrony_web:app
```
If everything works, stop it with CTRL+C.

### 5️⃣ Fix Sudo Permissions for Chrony

By default, the chronyc command requires sudo, which systemd cannot provide interactively. To allow chronyc to run without requiring a password, follow these steps:

➤ Step 5.1: Open the sudo configuration
```bash
sudo visudo
```
➤ Step 5.2: Grant permission to run chronyc without a password

Scroll to the bottom and add this line: (change the <USER> to the current user yourself)
```bash
<USER> ALL=(ALL) NOPASSWD: /usr/bin/chronyc
```
➤ Step 5.3: Save and exit

Press CTRL+X, then Y, then Enter.

➤ Step 5.4: Restart the service
```bash
sudo systemctl daemon-reload
sudo systemctl restart chronyweb.service
sudo systemctl status chronyweb.service
```

### 6️⃣ Create a Systemd Service

To keep the app running, create a systemd service:
```bash
sudo nano /etc/systemd/system/chronyweb.service
```
Paste the following configuration:
```bash
[Unit]
Description=Flask Chrony Web Interface
After=network.target

[Service]
User=thijmen
Group=thijmen
WorkingDirectory=/home/thijmen/chrony_web
Environment="PATH=/home/thijmen/chrony_web/venv/bin"
ExecStart=/home/thijmen/chrony_web/venv/bin/gunicorn --bind 0.0.0.0:5000 chrony_web:app
Restart=always

[Install]
WantedBy=multi-user.target
```
Save and exit (CTRL+X, Y, Enter).

➤ Step 6.1: Enable and start the service
```bash
sudo systemctl daemon-reload
sudo systemctl enable chronyweb.service
sudo systemctl start chronyweb.service
sudo systemctl status chronyweb.service
```
7️⃣ Finished 🎉

Your app is now running as a background service. Test it in your browser by typing:
```bash
http://<IP-ADDRESS>:5000/
```
