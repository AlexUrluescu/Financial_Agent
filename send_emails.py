from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from financial_agent import financial_agent
import os
from dotenv import load_dotenv
from pathlib import Path
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path, override=True)

def send_email():
    api_key = os.getenv('SENDGRID_API_KEY')


    news_content = financial_agent()

    formatted_news = news_content.replace("\n", "<br>")
    html_content = f'<strong>Here is your financial news summary:</strong><br><br>{formatted_news}'

    message = Mail(
        from_email='alexandre.urluescu@mtdtechnology.net',
        to_emails='alexurluescu23@gmail.com',
        subject='Daily Financial News Summary',
        html_content=html_content
    )
    try:
        api_key = os.getenv('SENDGRID_API_KEY')
        sg = SendGridAPIClient(api_key)
        response = sg.send(message)
        print(response.status_code)
        print(response.body)
        print(response.headers)
    except Exception as e:
        print(e.message)

# schedule.every().day.at("16:52").do(send_email)

# while True:
#     schedule.run_pending()
#     time.sleep(60)  
