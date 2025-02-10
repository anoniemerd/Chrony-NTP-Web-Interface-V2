<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Chrony NTP Web Interface - Setup Guide</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            margin: 40px auto;
            max-width: 900px;
            padding: 20px;
        }
        h1, h2 {
            color: #333;
        }
        code {
            background: #f4f4f4;
            padding: 4px;
            border-radius: 5px;
        }
        pre {
            background: #333;
            color: #fff;
            padding: 10px;
            border-radius: 5px;
            overflow-x: auto;
        }
        .step {
            font-size: 1.2em;
            font-weight: bold;
            margin-top: 20px;
        }
        ul {
            list-style: none;
            padding: 0;
        }
        ul li {
            margin-bottom: 10px;
        }
    </style>
</head>
<body>

    <h1>Chrony NTP Web Interface</h1>
    <p>A nice, simple, Web Interface for Chrony NTP.</p>

    <h2>By Anoniemerd</h2>

    <h2>📌 Step-by-Step Guide: Deploying Chrony NTP Web Monitor</h2>
    <p>This guide will help you set up, run, and deploy the Chrony NTP Web Monitor using Flask, Gunicorn, and systemd.</p>

    <div class="step">1️⃣ Install Required Packages</div>
    <p>On your Linux server, install the necessary dependencies:</p>
    <pre>sudo apt update && sudo apt install -y python3 python3-pip python3-venv chrony nginx</pre>

    <div class="step">2️⃣ Set Up the Project Directory</div>
    <p>Create a dedicated project directory and set up a virtual environment:</p>
    <pre>
mkdir -p ~/chrony_web && cd ~/chrony_web
python3 -m venv venv
source venv/bin/activate
pip install flask gunicorn
    </pre>

    <div class="step">3️⃣ Create the Flask App (<code>chrony_web.py</code>)</div>
    <p>Create the <code>chrony_web.py</code> file inside <code>~/chrony_web/</code>:</p>
    <pre>nano chrony_web.py</pre>
    <p>Copy and paste the Flask application code (<code>chrony_web.py</code>). See attachments.</p>
    <p>Save and exit the file (<code>CTRL+X</code>, <code>Y</code>, <code>Enter</code>).</p>

    <div class="step">4️⃣ Run Flask with Gunicorn</div>
    <p>Install Gunicorn, a production server for Flask:</p>
    <pre>pip install gunicorn</pre>
    <p>Test it by running:</p>
    <pre>gunicorn --bind 0.0.0.0:5000 chrony_web:app</pre>
    <p>If everything works, stop it with <code>CTRL+C</code>.</p>

    <div class="step">5️⃣ Create a Systemd Service</div>
    <p>To keep the app running, create a systemd service:</p>
    <pre>sudo nano /etc/systemd/system/chronyweb.service</pre>

    <p>Edit and paste the following configuration:</p>
    <pre>
[Unit]
Description=Flask Chrony Web Interface
After=network.target

[Service]
User=&lt;USERNAME&gt;
Group=&lt;USERNAME&gt;
WorkingDirectory=/home/&lt;USERNAME&gt;/chrony_web
Environment="PATH=/home/&lt;USERNAME&gt;/chrony_web/venv/bin"
ExecStart=/home/&lt;USERNAME&gt;/chrony_web/venv/bin/gunicorn --bind 0.0.0.0:5000 chrony_web:app
Restart=always

[Install]
WantedBy=multi-user.target
    </pre>

    <p>Save and exit (<code>CTRL+X</code>, <code>Y</code>, <code>Enter</code>).</p>

    <p>Reload and start the service:</p>
    <pre>
sudo systemctl daemon-reload
sudo systemctl enable chronyweb.service
sudo systemctl start chronyweb.service
sudo systemctl status chronyweb.service
    </pre>

    <div class="step">6️⃣ Finished 🎉</div>
    <p>Your app is now running as a background service. Test it in your browser by visiting:</p>
    <pre>http://&lt;IP-ADDRESS&gt;:5000/</pre>

</body>
</html>
