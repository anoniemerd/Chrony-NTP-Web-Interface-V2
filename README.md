# Chrony-NTP-Web-Interface
A nice, simple, Web Interface for Chrony NTP


1️⃣ Install Required Packages
On your Linux server, install the necessary dependencies:

bash
Kopiëren
Bewerken
sudo apt update && sudo apt install -y python3 python3-pip python3-venv chrony nginx


2️⃣ Set Up the Project Directory
Create a dedicated project directory and set up a virtual environment:

mkdir -p ~/chrony_web && cd ~/chrony_web
python3 -m venv venv
source venv/bin/activate
pip install flask gunicorn


3️⃣ Run Flask with Gunicorn
Install Gunicorn, a production server for Flask:

pip install gunicorn

Test it by running:

gunicorn --bind 0.0.0.0:5000 chrony_web:app

If everything works, stop it with CTRL+C.

4️⃣ Create a Systemd Service
To keep the app running, create a systemd service:

sudo nano /etc/systemd/system/chronyweb.service
Paste the following configuration:

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

Your app is now running as a background service.



