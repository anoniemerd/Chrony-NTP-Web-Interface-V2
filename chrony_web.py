from flask import Flask, jsonify, render_template_string
import subprocess
from datetime import datetime, timedelta
import pytz

app = Flask(__name__)

# Function to retrieve and format the list of clients connected to Chrony
# It executes the 'chronyc clients' command and processes the output.
def get_chrony_clients():
    try:
        output = subprocess.check_output(["sudo", "chronyc", "clients"], universal_newlines=True)
        lines = output.strip().split("\n")
        
        if len(lines) > 1:
            separator = lines[-1] if "=" in lines[-1] else None  # Identify separator line
            data = lines[1:-1] if separator else lines[1:]  # Extract relevant lines
            
            # Separate text-based and IP-based hosts for sorting
            text_hosts = [line for line in data if not line.split()[0][0].isdigit()]
            ip_hosts = [line for line in data if line.split()[0][0].isdigit()]
            
            # Sort both groups separately and combine them
            sorted_data = sorted(text_hosts, key=lambda x: x.split()[0]) + sorted(ip_hosts, key=lambda x: x.split()[0])
            
            return "\n".join([separator] + [lines[0]] + sorted_data) if separator else "\n".join([lines[0]] + sorted_data)
        
        return output  # Return raw output if only one line
    except Exception as e:
        return f"Error: {e}"  # Handle exceptions and return an error message

# Function to get the current time in UTC+1 format
# It calculates the time based on UTC and adds one hour.
def get_ntp_time():
    try:
        utc_now = datetime.utcnow()
        cet_now = utc_now + timedelta(hours=1)  # Convert to UTC+1
        formatted_time = cet_now.strftime("%d-%m-%Y, %H:%M:%S")
        return formatted_time
    except Exception as e:
        return f"Error: {e}"  # Handle exceptions and return an error message

# Route for the homepage, renders an HTML template showing NTP clients and server time
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
                    $("#ntp-time").text("NTP Server Time (UTC+1): " + data.ntp_time);
                });
            }
            setInterval(refreshData, 1000);  // Refresh every second
            $(document).ready(refreshData);
        </script>
        <style>
            body {
                background-color: #f8f9fa;
                font-family: Arial, sans-serif;
            }
            .card {
                border-radius: 12px;
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
                width: fit-content;
                margin: auto;
                padding: 15px;
            }
            pre {
                background-color: #212529;
                color: #f8f9fa;
                padding: 10px;
                border-radius: 8px;
                overflow-x: auto;
                max-height: 400px;
                white-space: pre-wrap;
                word-wrap: break-word;
                margin: 0 auto;
                width: fit-content;
                min-width: 50%;
            }
            .table th, .table td {
                text-align: center;
            }
        </style>
    </head>
    <body>
        <div class="container mt-5">
            <div class="text-center mb-4">
                <h1 class="fw-bold">Chrony NTP Clients</h1>
                <h5 id="ntp-time" class="text-muted">NTP Server Time (UTC+1): Loading...</h5>
            </div>
            <div class="card">
                <div class="card-body text-center">
                    <pre id="clients" class="text-center">{{ clients }}</pre>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    return render_template_string(html_template, clients=get_chrony_clients(), ntp_time=get_ntp_time())

# API route that returns JSON data containing NTP clients and server time
@app.route("/data")
def data():
    return jsonify({"clients": get_chrony_clients(), "ntp_time": get_ntp_time()})

# Main entry point to run the Flask web server
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)  # Runs on port 5000, accessible on all interfaces
