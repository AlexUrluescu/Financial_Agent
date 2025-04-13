# worker.py

import schedule
import time
from send_emails import send_email

# Schedule your task
schedule.every().day.at("23:10").do(send_email)

# Continuous loop to keep checking schedule
while True:
    schedule.run_pending()
    time.sleep(60)
