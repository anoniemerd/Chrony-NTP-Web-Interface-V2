# Chrony-NTP-Web-Interface
A nice, simple, Web Interface for Chrony NTP

#By Anoniemerd

# Step-by-Step Guide: Deploying Chrony NTP Web Monitor
This guide will help you set up, run, and deploy the Chrony NTP Web Monitor using Flask, Gunicorn, and systemd.

1️⃣ Install Required Packages
On your Linux server, install the necessary dependencies:

sudo apt update && sudo apt install -y python3 python3-pip python3-venv chrony nginx

2️⃣ Set Up the Project Directory
Create a dedicated project directory and set up a virtual environment:

mkdir -p ~/chrony_web && cd ~/chrony_web
python3 -m venv venv
source venv/bin/activate
pip install flask gunicorn

3️⃣ Create the Flask App (chrony_web.py)
Create the chrony_web.py file inside ~/chrony_web/:

nano chrony_web.py
Copy and paste the following Flask application code:

from flask import Flask, jsonify, render_template_string
import subprocess

app = Flask(__name__)

def get_chrony_clients():
    try:
        output = subprocess.check_output(["sudo", "chronyc", "clients"], universal_newlines=True)
        lines = output.strip().split("\n")
        if len(lines) > 1:
            separator = lines[-1] if "=" in lines[-1] else None
            data = lines[1:-1] if separator else lines[1:]
            text_hosts = [line for line in data if not line.split()[0][0].isdigit()]
            ip_hosts = [line for line in data if line.split()[0][0].isdigit()]
            sorted_data = sorted(text_hosts, key=lambda x: x.split()[0]) + sorted(ip_hosts, key=lambda x: x.split()[0])
            return "\n".join([separator] + [lines[0]] + sorted_data) if separator else "\n".join([lines[0]] + sorted_data)
        return output
    except Exception as e:
        return f"Error: {e}"

@app.route("/")
def home():
    html_template = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Chrony NTP Clients</title>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
        <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
        <script>
            function refreshData() {
                $.getJSON("/data", function(data) {
                    $("#clients").text(data.clients);
                });
            }
            setInterval(refreshData, 1000);
            $(document).ready(refreshData);
        </script>
    </head>
    <body class="bg-light">
        <div class="container mt-5">
            <h1 class="text-center">Chrony NTP Clients</h1>
            <div class="card shadow-sm mx-auto border-0" style="max-width: 75%; border-radius: 12px;">
                <div class="card-body">
                    <pre id="clients" class="bg-dark text-white p-3 rounded text-center mx-auto"
                        style="overflow-x: auto; max-height: 400px; max-width: 70%;">{{ clients }}</pre>
                </div>
            </div>
            <div class="mt-4 text-center">
                <h5>Column Descriptions:</h5>
                <table class="table table-bordered table-striped mx-auto" style="max-width: 75%;">
                    <thead>
                        <tr>
                            <th>Column</th>
                            <th>Description</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td><strong>Hostname</strong></td>
                            <td>The name or IP address of the client.</td>
                        </tr>
                        <tr>
                            <td><strong>NTP</strong></td>
                            <td>Number of NTP packets received from the server.</td>
                        </tr>
                        <tr>
                            <td><strong>Drop</strong></td>
                            <td>Number of received packets that were ignored.</td>
                        </tr>
                        <tr>
                            <td><strong>Int</strong></td>
                            <td>Interval of the received packet in seconds.</td>
                        </tr>
                        <tr>
                            <td><strong>IntL</strong></td>
                            <td>Last received interval in seconds.</td>
                        </tr>
                        <tr>
                            <td><strong>Last</strong></td>
                            <td>Time since the last received packet.</td>
                        </tr>
                        <tr>
                            <td><strong>Cmd</strong></td>
                            <td>Number of command packets sent to the client.</td>
                        </tr>
                        <tr>
                            <td><strong>Drop Int</strong></td>
                            <td>Intervals of ignored packets.</td>
                        </tr>
                        <tr>
                            <td><strong>Last</strong></td>
                            <td>Time since the last ignored packet.</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
    </body>
    </html>
    """
    return render_template_string(html_template, clients=get_chrony_clients())

@app.route("/data")
def data():
    return jsonify({"clients": get_chrony_clients()})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

    
Save and exit the file (CTRL+X, Y, Enter).

4️⃣ Run Flask with Gunicorn
Install Gunicorn, a production server for Flask:

pip install gunicorn

Test it by running:

gunicorn --bind 0.0.0.0:5000 chrony_web:app

If everything works, stop it with CTRL+C.

5️⃣ Create a Systemd Service
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

6️⃣ Finished
Your app is now running as a background service. Test it in your browser by typing in : http://<IP-ADDRESS>:5000/

