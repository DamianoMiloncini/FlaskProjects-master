from flask import Flask, render_template
#for DHT11
import Freenove_DHT as DHT
import time
#for email
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import imaplib
import email
import RPi.GPIO as GPIO

app = Flask(__name__)
#define the dht pin, i will set it to 11 like in the lab
GPIO.setwarnings(False)
DHTPin = 11
#need to define the fan GPIO pin here as well
Motor3 = 29
Motor2 = 13
Motor1 = 15



GPIO.setmode(GPIO.BOARD)


GPIO.setup(Motor1,GPIO.OUT)
GPIO.setup(Motor2,GPIO.OUT)
GPIO.setup(Motor3,GPIO.OUT)

# GPIO.setmode(GPIO.BCM)
# GPIO.setup(FanPin, GPIO.OUT)

#email credentials (add your own credentials when you test it at home. if you have issues, text me -m )
sender_email = "stromika78@gmail.com"
app_password = "uekhmtqwuotoghbx" #i needed to have an app password to make it work personally
receiver_email = "nsumanyim@gmail.com"

#method for sending the email
def send_email(sender_email, sender_password, receiver_email, subject, body):
    message = MIMEMultipart()
    message['From'] = sender_email
    message['To'] = receiver_email
    message['Subject'] = subject #tbh this could be hardcoded
    message.attach(MIMEText(body, 'plain')) #tbh this could be hardcoded (the body i mean)

    with smtplib.SMTP('smtp.gmail.com', 587) as server: #!!dont change the smtp.gmail.com its required!!
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(message)

#method for receiving email
def receive_email(email_address,app_password,num_emails=5): #take the first 5 emails
    imap_server = "imap.gmail.com"
    imap = imaplib.IMAP4_SSL(imap_server)
    imap.login(email_address,app_password)
    imap.select('INBOX')

    #look for emails from a specific sender AKA the sender email you set on top
    _, message_numbers = imap.search(None,'ALL') #my email for ex
    email_ids = message_numbers[0].split()[-num_emails:] #retrieve the first string of email ids found
    #imma stop the commenting here cause im getting tired but ill continue tomorrow or so cause this shit is giving me a headache yall
    for email_id in reversed(email_ids):
        _, msg_data = imap.fetch(email_id,'(RFC822 FLAGS)')
        for response_part in msg_data:
            if isinstance(response_part, tuple):
                email_body = response_part[1]
                email_message = email.message_from_bytes(email_body)
                # Check the flags
                flags = response_part[0].decode().split(' ')
                # Check if the email is NOT seen
                if '\\Seen' not in flags:
                    # If the email is not seen, process it
                    #print(f"Email ID: {email_id}, Flags: {flags}")  # Debug: show flags

                    if email_message.is_multipart():
                        for part in email_message.walk():
                            if part.get_content_type() == "text/plain":
                                try:
                                    content = part.get_payload(decode=True).decode('utf-8')
                                except UnicodeDecodeError:
                                    # Return False if decoding fails
                                    return False
                                if "YES" in content.strip().upper() :  # Check if user replied with YES
                                    return True

    imap.close()
    imap.logout()
    return False 

@app.route('/')
def home():
    dht = DHT.DHT(DHTPin)  # creating the object 
    readValue = dht.readDHT11()  # read the DHT sensor
    
    # Initialize variables
    current_temp = None
    current_humidity = None

    # If the current temperature is greater than 24, send an email to the user
    if readValue is dht.DHTLIB_OK:  # if the value is normal
        current_temp = dht.temperature
        current_humidity = dht.humidity  # idk if we need it tbh
        
        # Check if the current temperature is greater than 24
        if current_temp > 24: #i think the issue is
            send_email(
                sender_email, 
                app_password, 
                receiver_email, 
                "Temperature Alert", 
                f"The current temperature is {current_temp}°C. Do you want to turn on the fan? Reply with 'YES' to turn it on."
            )
            print('works')
            # Wait a bit to give the user time to reply
            time.sleep(20)  # they got 60 sec, they better speed up esti

            # Check for user's response
            if receive_email(sender_email, app_password, num_emails=1):
                print('motor on')
                GPIO.output(Motor1,GPIO.HIGH)
                GPIO.output(Motor2,GPIO.LOW)
                GPIO.output(Motor3,GPIO.HIGH) 
                time.sleep(10)
                GPIO.output(Motor1, GPIO.LOW) # Turn on the fan
            else:
                GPIO.output(Motor1, GPIO.LOW)
                print('motor off')  # Turn off the fan

    # If the DHT reading fails, set a message or use default values
    if current_temp is None or current_humidity is None:
        current_temp = "Error reading temperature"
        current_humidity = "Error reading humidity"

    return render_template('main.html', temperature=current_temp, humidity=current_humidity)  # send this to the html so that we can display the data

@app.route('/fan_status')
def fan_status():
    fan_is_on = GPIO.input(Motor1) == GPIO.HIGH
    return {'status': 'ON' if fan_is_on else 'OFF'}


if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', port=5500, debug=True)
    except KeyboardInterrupt:
        GPIO.cleanup()

