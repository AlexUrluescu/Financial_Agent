import os
from flask import Flask
from threading import Thread
import schedule
import time
from send_emails import send_email

app = Flask(__name__)

schedule.every().day.at("22:31").do(send_email)

def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(60)

@app.route('/')
def home():
    return 'Email Scheduler Running with Flask!'

if __name__ == '__main__':
    scheduler_thread = Thread(target=run_scheduler)
    scheduler_thread.daemon = True
    scheduler_thread.start()

    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)

