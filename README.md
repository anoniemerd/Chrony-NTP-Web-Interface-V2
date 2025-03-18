# Chrony-NTP-Web-Interface
A nice, simple, Web Interface for Chrony NTP

![image](https://github.com/user-attachments/assets/24f37619-fbaa-46ec-a60f-0f837e967697)

## By Anoniemerd

## Step-by-Step Guide: Deploying Chrony NTP Web Monitor
This guide will help you set up, run, and deploy the Chrony NTP Web Monitor using Flask, Gunicorn, and systemd.

The web interface uses AJAX to update data dynamically every second, instead of HTML, improving stability and preventing crashes. Additionally, hostnames are sorted alphabetically, first displaying hostnames with letters, followed by IP addresses.

### 1️⃣ Install Required Packages
On your Linux server, install the necessary dependencies:

```bash
sudo apt update && sudo apt install -y python3 python3-pip python3-venv chrony nginx

2️⃣ Set Up the Project Directory

Create a dedicated project directory and set up a virtual environment:

mkdir -p ~/chrony_web && cd ~/chrony_web
python3 -m venv venv
source venv/bin/activate
pip install flask gunicorn pytz

3️⃣ Create the Flask App (chrony_web.py)

Create the chrony_web.py file inside ~/chrony_web/:

nano chrony_web.py

Copy and paste the Flask application code (see attachments).

Save and exit the file (CTRL+X, Y, Enter).
4️⃣ Run Flask with Gunicorn

Test the setup by running:

gunicorn --bind 0.0.0.0:5000 chrony_web:app

If everything works, stop it with CTRL+C.
🔧 5️⃣ Fix Sudo Permissions for Chrony

To allow chronyc to run without requiring a password (fixing sudo: a password is required errors), follow these steps:

    Open the sudo configuration:

sudo visudo

Scroll to the bottom and add this line:

<USERNAME> ALL=(ALL) NOPASSWD: /usr/bin/chronyc

Replace <USERNAME> with the user running the Flask service.

Save and exit (CTRL+X, Y, Enter).

Restart the service:

    sudo systemctl daemon-reload
    sudo systemctl restart chronyweb.service
    sudo systemctl status chronyweb.service

6️⃣ Create a Systemd Service

To keep the app running, create a systemd service:

sudo nano /etc/systemd/system/chronyweb.service

Edit and paste the following configuration:

[Unit]
Description=Flask Chrony Web Interface
After=network.target

[Service]
User=<USERNAME>
Group=<USERNAME>
WorkingDirectory=/home/<USERNAME>/chrony_web
Environment="PATH=/home/<USERNAME>/chrony_web/venv/bin"
ExecStart=/home/<USERNAME>/chrony_web/venv/bin/gunicorn --bind 0.0.0.0:5000 chrony_web:app
Restart=always

[Install]
WantedBy=multi-user.target

Save and exit (CTRL+X, Y, Enter).

Reload and start the service:

sudo systemctl daemon-reload
sudo systemctl enable chronyweb.service
sudo systemctl start chronyweb.service
sudo systemctl status chronyweb.service

7️⃣ Finished 🎉

Your app is now running as a background service. Test it in your browser by typing:

http://<IP-ADDRESS>:5000/
