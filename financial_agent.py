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
        tools=[rss_feed_tool, scrape_tool],
        llm=llm,
        agent="zero-shot-react-description",
        verbose=True,
        handle_parsing_errors=True
    )
    return summarization_agent


def scrape_cnbc_article(url: str) -> str:
    if not url or not url.startswith("http"):
        raise ValueError("Invalid URL: URL must be a non-empty string and start with 'http'.")
    
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error while making request: {e}")
        return "" 
    
    soup = BeautifulSoup(response.content, "html.parser")
    paragraphs = soup.select("div.ArticleBody-articleBody p")
    
    if not paragraphs:
        paragraphs = soup.select("div.group p")
    
    text = "\n".join(p.get_text(strip=True) for p in paragraphs)
    
    return text[:4000] 
 

def fetch_cnbc_rss(_: str = ""):
    url = 'https://www.cnbc.com/id/100003114/device/rss/rss.html'
    feed = feedparser.parse(url)
    return [
        {
            "title": entry.title,
            "link": entry.link,
            "published": entry.published
        }
        for entry in feed.entries[:5]
    ]


# Agent's tools
rss_feed_tool = Tool(
    name="CNBCRSSFetcher",
    func=fetch_cnbc_rss,
    description="Fetches latest 5 articles from CNBC's RSS feed. Returns a list of title, link, and published date.",
)

scrape_tool = Tool(
    name="CNBCArticleScraper",
    func=scrape_cnbc_article,
    description="Scrapes CNBC article text from a given URL."
)

def financial_agent():

    html_output = "<html><body>"
    summarization_agent = initialize_summarization_agent()

    prompt = """
        Use the CNBCRSSFetcher tool to retrieve the latest 5 CNBC articles.

        Then, for each article:
        1. Use CNBCArticleScraper to extract its full content.
        2. Write a summary in 6–7 sentences focusing on financial, political, or economic implications.
        3. Include a <strong>Key Takeaways</strong> section with 2–3 bullet points.
        4. Format each article into clean, valid HTML ready for browser rendering.

        Include:
        - <strong>Title</strong>
        - <strong>Published</strong> date with this format: Sun, 13 Apr 2025 (i.e., abbreviated weekday, day, abbreviated month, full year).
        - A link to the full article

        Ensure everything is in proper HTML. Do not include markdown, code blocks, or escaped characters.
    """
    summary_html = summarization_agent.run(prompt)

    html_output += summary_html
    html_output += "</body></html>"

    print(html_output)
    return html_output


