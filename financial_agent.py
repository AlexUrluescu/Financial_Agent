from langchain_google_genai import ChatGoogleGenerativeAI
from google.oauth2 import service_account
import json
from langchain.agents import initialize_agent, Tool
from datetime import datetime
import feedparser
import requests
from bs4 import BeautifulSoup
import os
from dotenv import load_dotenv
from pathlib import Path
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path, override=True)


type = os.getenv('GOOGLE_TYPE')
project_id = os.getenv('GOOGLE_PROJECT_ID')
private_key_id = os.getenv('PRIVATE_KEY_ID')
private_key = os.getenv('PRIVATE_KEY')
client_email = os.getenv('CLIENT_EMAIL')
client_id = os.getenv('CLIENT_ID')
auth_uri = os.getenv('AUTH_URI')
token_uri = os.getenv('TOKEN_URI')
auth_provider = os.getenv('AUTH_PROVIDER')
client_cert_url = os.getenv('CLIENT_CERT_URL')
universe_domain = os.getenv('UNIVERS_DOMAIN')

json_string = """
{{
  "type": "{type}",
  "project_id": "{project_id}",
  "private_key_id": "{private_key_id}",
  "private_key": "{private_key}",
  "client_email": "{client_email}",
  "client_id": "{client_id}",
  "auth_uri": "{auth_uri}",
  "token_uri": "{token_uri}",
  "auth_provider_x509_cert_url": "{auth_provider}",
  "client_x509_cert_url": "{client_cert_url}",
  "universe_domain": "{universe_domain}"
}}
""".format(
    type=type,
    project_id=project_id,
    private_key_id=private_key_id,
    private_key=private_key,
    client_email=client_email,
    client_id=client_id,
    auth_uri=auth_uri,
    token_uri=token_uri,
    auth_provider=auth_provider,
    client_cert_url=client_cert_url,
    universe_domain=universe_domain
)



credentials_info = json.loads(json_string)
credentials = service_account.Credentials.from_service_account_info(credentials_info)

def initialize_summarization_agent():
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", credentials=credentials)
    summarization_agent = initialize_agent(
        tools=[scrape_tool],
        llm=llm,
        agent="zero-shot-react-description",
        verbose=True,
        handle_parsing_errors=True
    )
    return summarization_agent


def format_pub_date(pub_date: str) -> str:
    # Parse the date string into a datetime object
    date_obj = datetime.strptime(pub_date, "%a, %d %b %Y %H:%M:%S GMT")
    
    # Reformat the date into the desired format: "Sun, 13 Apr 2025"
    formatted_date = date_obj.strftime("%a, %d %b %Y")
    return formatted_date


def summarize_article(agent, title, link, pub_date, article_text):
    # Summarization prompt
    prompt = f"""
    You are analyzing a CNBC article. Your task is twofold:

    1. Write a concise summary in 6–7 sentences focusing on key <strong>financial</strong>, <strong>political</strong>, or <strong>economic</strong> implications.
    2. After the summary, include a separate section titled <strong>Key Takeaways</strong> with 2-3 short bullet points, each using <strong> tags to highlight the most important concepts or statistics.

    IMPORTANT INSTRUCTIONS:
    - The output MUST be clean, valid HTML.
    - NEVER include markdown, code blocks, or triple backticks (e.g. ```html).
    - Do NOT wrap anything in quotation marks or escape characters.
    - Return only the final HTML content that can be rendered directly in a browser.

    <strong>Title:</strong> {title}<br>
    <strong>Link:</strong> <a href="{link}" target="_blank">{link}</a><br>
    <strong>Published:</strong> {format_pub_date(pub_date)}<br><br>

    Article:
    {article_text}
    """
    # Running the agent to generate a summary
    summary = agent.run(prompt)
    summary = summary.replace("```html", "").replace("```", "").strip()
    return summary.strip()

def format_article_to_html(title, pub_date, summary, link):
    # Convert the summary into a structured HTML format
    html_output = f"""
    <div style='margin-bottom: 30px;'>
        <div style="margin-bottom: 5px;">
            <h2 style="margin: 0; font-size: 18px;">{title}</h2>
            <p style="margin: 5px 0 0 0;"><strong>Published:</strong> {format_pub_date(pub_date)}</p>
        </div>

        {summary}

        <p><a href="{link}" target="_blank">Read full article</a></p>
    </div>
    <hr>
    """
    return html_output

import requests
from bs4 import BeautifulSoup

def scrape_cnbc_article(url: str) -> str:
    # Check if the URL is valid
    if not url or not url.startswith("http"):
        raise ValueError("Invalid URL: URL must be a non-empty string and start with 'http'.")
    
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # This will raise an HTTPError for bad responses (4xx or 5xx)
    except requests.exceptions.RequestException as e:
        print(f"Error while making request: {e}")
        return ""  # Return empty string in case of error (could also raise an exception)
    
    soup = BeautifulSoup(response.content, "html.parser")
    paragraphs = soup.select("div.ArticleBody-articleBody p")
    
    # Fallback if no paragraphs found
    if not paragraphs:
        paragraphs = soup.select("div.group p")
    
    text = "\n".join(p.get_text(strip=True) for p in paragraphs)
    
    return text[:4000]  # Optional length cap


# --- Create LangChain Tool ---
scrape_tool = Tool(
    name="CNBCArticleScraper",
    func=scrape_cnbc_article,
    description="Scrapes CNBC article text from a given URL."
)

def financial_agent():

    url = 'https://www.cnbc.com/id/100003114/device/rss/rss.html'
    feed = feedparser.parse(url)

    # Step 2: Init LangChain Agent with Gemini
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", credentials=credentials)
    agent = initialize_agent(
        tools=[scrape_tool],
        llm=llm,
        agent="zero-shot-react-description",
        verbose=True,
        handle_parsing_errors=True
    )

    html_output = "<html><body>"
    summarization_agent = initialize_summarization_agent()

    for entry in feed.entries[:5]:
        title = entry.title
        link = entry.link
        pub_date = entry.published

           # Scrape the article content
        article_text = scrape_cnbc_article(link)

        # 1. Summarize the article using the summarization agent
        summary = summarize_article(summarization_agent, title, link, pub_date, article_text)

        # 2. Format the summary into HTML using the formatting agent
        article_html = format_article_to_html(title, pub_date, summary, link)

        # Append the formatted HTML to the final output
        html_output += article_html


    html_output += "</body></html>"

    print(html_output)
    return html_output

# financial_agent()

