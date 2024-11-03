from flask import Flask, render_template, jsonify
import threading
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import imaplib
import email
import RPi.GPIO as GPIO
import Freenove_DHT as DHT

app = Flask(__name__)

# GPIO and DHT setup
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)
DHTPin = 11
Motor1 = 15
Motor2 = 13
Motor3 = 29

GPIO.setup(Motor1, GPIO.OUT)
GPIO.setup(Motor2, GPIO.OUT)
GPIO.setup(Motor3, GPIO.OUT)

# Email credentials (replace with your credentials)
sender_email = "stromika78@gmail.com"
app_password = "uekhmtqwuotoghbx"
receiver_email = "nsumanyim@gmail.com"

# Initialize flag and lock
alert_sent = False
alert_lock = threading.Lock()

# Method for sending an email
def send_email(sender_email, sender_password, receiver_email, subject, body):
    message = MIMEMultipart()
    message['From'] = sender_email
    message['To'] = receiver_email
    message['Subject'] = subject
    message.attach(MIMEText(body, 'plain'))
    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(message)

# Method for receiving email and checking response
def receive_email(email_address, app_password, num_emails=5):
    imap_server = "imap.gmail.com"
    imap = imaplib.IMAP4_SSL(imap_server)
    imap.login(email_address, app_password)
    imap.select('INBOX')
    _, message_numbers = imap.search(None, 'ALL')
    email_ids = message_numbers[0].split()[-num_emails:]
    for email_id in reversed(email_ids):
        _, msg_data = imap.fetch(email_id, '(RFC822 FLAGS)')
        for response_part in msg_data:
            if isinstance(response_part, tuple):
                email_body = response_part[1]
                email_message = email.message_from_bytes(email_body)
                flags = response_part[0].decode().split(' ')
                if '\\Seen' not in flags and email_message.is_multipart():
                    for part in email_message.walk():
                        if part.get_content_type() == "text/plain":
                            try:
                                content = part.get_payload(decode=True).decode('utf-8')
                                if "YES" in content.strip().upper():
                                    return True
                            except UnicodeDecodeError:
                                return False
    imap.close()
    imap.logout()
    return False

# Background function to handle temperature alerts
def monitor_temperature():
    global alert_sent
    dht = DHT.DHT(DHTPin)

    while True:
        readValue = dht.readDHT11()
        if readValue == dht.DHTLIB_OK:
            current_temp = dht.temperature
            with alert_lock:
                if current_temp > 24 and not alert_sent:
                    # Send email if the temperature is too high and no alert has been sent
                    send_email(
                        sender_email,
                        app_password,
                        receiver_email,
                        "Temperature Alert",
                        f"The current temperature is {current_temp}°C. Reply with 'YES' to turn on the fan."
                    )
                    alert_sent = True
                    print('Email sent for temperature alert.')

                    # Wait and check for the user’s response
                    time.sleep(40)
                    if receive_email(sender_email, app_password, num_emails=1):
                        print('Turning fan on.')
                        GPIO.output(Motor1, GPIO.HIGH)
                        GPIO.output(Motor2, GPIO.LOW)
                        GPIO.output(Motor3, GPIO.HIGH)
                        time.sleep(10)
                        GPIO.output(Motor1, GPIO.LOW)
                    else:
                        print('No response or fan off.')

                elif current_temp <= 24:
                    # Reset alert if temperature drops below threshold
                    alert_sent = False
        time.sleep(10)  # Interval to check temperature

# Start the background thread
threading.Thread(target=monitor_temperature, daemon=True).start()

@app.route('/')
def home():
    dht = DHT.DHT(DHTPin)
    readValue = dht.readDHT11()
    current_temp = None
    current_humidity = None

    if readValue == dht.DHTLIB_OK:
        current_temp = dht.temperature
        current_humidity = dht.humidity

    if current_temp is None or current_humidity is None:
        current_temp = "Error reading temperature"
        current_humidity = "Error reading humidity"

    return render_template('main.html', temperature=current_temp, humidity=current_humidity)

@app.route('/sensor_data')
def sensor_data():
    dht = DHT.DHT(DHTPin)
    readValue = dht.readDHT11()
    current_temp = None
    current_humidity = None

    if readValue == dht.DHTLIB_OK:
        current_temp = dht.temperature
        current_humidity = dht.humidity

    return jsonify({'temperature': current_temp, 'humidity': current_humidity})

@app.route('/fan_status')
def fan_status():
    fan_is_on = GPIO.input(Motor1) == GPIO.HIGH
    return jsonify({'status': 'ON' if fan_is_on else 'OFF'})

if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', port=5500, debug=True)
    except KeyboardInterrupt:
        GPIO.cleanup()
