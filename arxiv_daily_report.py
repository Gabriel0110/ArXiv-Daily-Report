from datetime import timedelta, date
from typing import Dict, List
import requests
import xml.etree.ElementTree as ET
import pandas as pd
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import urllib.request as libreq


AUTHORS = [
    "Sergey Levine",
    "Pieter Abbeel",
    "John Schulman",
    "Doina Precup",
    "David Silver",
    "Yoshua Bengio",
    "Yann LeCun",
    "Richard Sutton",
    "David Ha",
    "David Sussillo",
    "Joelle Pineau",
    "Shakir Mohamed",
    "Ilya Sutskever",
    "Blake Richards",
    "Konrad Koerding",
    "Jeff Hawkins",
    "Geoffrey Hinton",
    "Emtiyaz Khan",
    "Andrej Karpathy",
    "Lucas Beyer",
    "Friedemann Zenke",
    "Rishabh Agarwal",
    "Pablo Samuel Castro",
    "Demis Hassabis",
    "Julian Schrittwieser",
    "Shane Gu",
    "Shane Legg",
    "Patrick Mineault",
    "Mark Humphries",
    "Subutai Ahmad",
    "Luiz Pessoa",
    "Dileep George",
    "Danilo Jimenez Rezende",
    "Jeff Clune",
    "Dustin Tran",
    "Nando de Freitas",
    "Max Jaderberg",
    "Beren Millidge",
    "Maxwell J D Ramstead",
    "Dalton A R Sakthivadivel",
    "Conor Heins",
    "Magnus Koudahl",
    "Karl J Friston",
    "Lancelot Da Costa"
]

TOPICS = [
    "Artificial Intelligence",
    "AI",
    "Reinforcement Learning",
    "RL",
    "Spiking Neural Network",
    "Energy-Based Model",
    "Predictive Coding",
    "Bayesian",
    "Biologically Inspired",
    "Biologically-Inspired",
    "Neuro-Inspired",
    "Free Energy Principle",
    "GFlowNet",
    "Generative Model",
    "Consciousness"
]

CATEGORIES = [
    "cs.AI",
    "cs.CL",
    "cs.CV",
    "cs.LG",
    "cs.NE",
    "stat.ML",
    "q-bio.NC"
]

AUTHOR_QUERY = "au:" + " OR ".join(AUTHORS)
TOPIC_QUERY = "ti:" + " OR ".join(TOPICS)
CATEGORY_QUERY = "cat:" + " OR ".join(CATEGORIES)
MAX_RESULTS = 1000

class EmailClient:
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.server = smtplib.SMTP('smtp.gmail.com', 587)
        self.server.starttls()
        self.server.login(username, password)

    def send_email(self, from_addr, to_addr, subject, body):
        msg = MIMEMultipart()
        msg['From'] = from_addr
        msg['To'] = to_addr
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'html'))
        text = msg.as_string()
        self.server.sendmail(from_addr, to_addr, text)

    def close(self):
        self.server.quit()

def get_papers(urls: Dict) -> List:
    all_papers_by_author_df = pd.DataFrame()
    all_papers_by_topic_df = pd.DataFrame()
    all_papers_by_category_df = pd.DataFrame()

    for key, url in urls.items():
        #resp = requests.get(url)
        with libreq.urlopen(url.replace(' ', '%20')) as link:
            r = link.read()
        root = ET.fromstring(r)

        all_papers = []
        entries = root.findall('r:entry', namespaces={'r': 'http://www.w3.org/2005/Atom'})
        for entry in entries:
            authors = ', '.join([author.find('r:name', namespaces={'r': 'http://www.w3.org/2005/Atom'}).text for author in entry.findall('r:author', namespaces={'r': 'http://www.w3.org/2005/Atom'})])
            categories = ', '.join([category.attrib['term'] for category in entry.findall('r:category', namespaces={'r': 'http://www.w3.org/2005/Atom'})])

            all_papers.append({
                'title': entry.find('r:title', namespaces={'r': 'http://www.w3.org/2005/Atom'}).text,
                'author': authors,
                'summary': entry.find('r:summary', namespaces={'r': 'http://www.w3.org/2005/Atom'}).text,
                'url': entry.find('r:id', namespaces={'r': 'http://www.w3.org/2005/Atom'}).text,
                'category': categories,
                'published': entry.find('r:published', namespaces={'r': 'http://www.w3.org/2005/Atom'}).text
            })

        df = pd.DataFrame(all_papers)

        if not df.empty:
            # Split the published date at 'T' and take the first element
            df['published'] = df['published'].str.split('T').str[0]

            # Only keep papers where 'published' was two days ago (ArXiv API seems to be a day behind, so we can't get yesterday's papers)
            yesterday = (date.today() - timedelta(days=2)).strftime("%Y-%m-%d")
            df = df[df['published'] == yesterday]

            # Replace '\n' with ' ' in 'summary'
            df['summary'] = df['summary'].str.replace('\n', ' ')

            # Trim down the summary to just 300 characters
            df['summary'] = df['summary'].str[:300] + '...'

            # Clean up columns to only relevant ones and ensure the columns actually contain our specified terms
            if key == 'author':                
                all_papers_by_author_df = pd.concat([all_papers_by_author_df, df[['author', 'title', 'summary', 'category', 'url']]])
                all_papers_by_author_df = all_papers_by_author_df[all_papers_by_author_df['author'].str.contains('|'.join(AUTHORS))]
                all_papers_by_author_df = all_papers_by_author_df.reset_index()
                all_papers_by_author_df = all_papers_by_author_df.drop(columns=['index'])
            elif key == 'topic':
                all_papers_by_topic_df = pd.concat([all_papers_by_topic_df, df[['title', 'author', 'summary', 'category', 'url']]])
                all_papers_by_topic_df = all_papers_by_topic_df[all_papers_by_topic_df['title'].str.contains('|'.join(TOPICS))]
                all_papers_by_topic_df = all_papers_by_topic_df.reset_index()
                all_papers_by_topic_df = all_papers_by_topic_df.drop(columns=['index'])
            elif key == 'category':
                all_papers_by_category_df = pd.concat([all_papers_by_category_df, df[['category', 'title', 'author', 'summary', 'url']]])
                all_papers_by_category_df = all_papers_by_category_df[all_papers_by_category_df['category'].str.contains('|'.join(CATEGORIES))]
                all_papers_by_category_df = all_papers_by_category_df.reset_index()
                all_papers_by_category_df = all_papers_by_category_df.drop(columns=['index'])

    return [all_papers_by_author_df, all_papers_by_topic_df, all_papers_by_category_df]

def main():
    author_url = f'https://export.arxiv.org/api/query?search_query={AUTHOR_QUERY}&sortBy=submittedDate&sortOrder=descending&max_results={MAX_RESULTS}'
    topic_url = f'https://export.arxiv.org/api/query?search_query={TOPIC_QUERY}&sortBy=submittedDate&sortOrder=descending&max_results={MAX_RESULTS}'
    category_url = f'https://export.arxiv.org/api/query?search_query={CATEGORY_QUERY}&sortBy=submittedDate&sortOrder=descending&max_results={MAX_RESULTS}'

    urls = {
        'author': author_url,
        'topic': topic_url,
        'category': category_url
    }

    all_papers_by_author_df, all_papers_by_topic_df, all_papers_by_category_df = get_papers(urls)

    # Get email client (Gmail in my case)
    try:
        email_client = EmailClient('gabrieltomberlin14@gmail.com', '{REDACTED}')
    except Exception as e:
        print(f"Error connecting to email server: {e}")
        return

    # Create the HTML body
    if not all_papers_by_author_df.empty or not all_papers_by_topic_df.empty or not all_papers_by_category_df.empty:
        body = f"""
        <html>
            <body>
                <h1>Arxiv Daily Digest for {(date.today() - timedelta(days=2)).strftime("%Y-%m-%d")}</h1>
                <h2>Papers by Author Search</h2>
                {all_papers_by_author_df.to_html()}
                </br>
                <h2>Papers by Topic Search</h2>
                {all_papers_by_topic_df.to_html()}
                </br>
                <h2>Papers by Category Search</h2>
                {all_papers_by_category_df.to_html()}
            </body>
        </html>
        """
    elif all_papers_by_author_df.empty and all_papers_by_topic_df.empty and all_papers_by_category_df.empty:
        body = f"""
        <html>
            <body>
                <h1>Arxiv Daily Digest for {(date.today() - timedelta(days=2)).strftime("%Y-%m-%d")}</h1>
                <h2>No new papers found.</h2>
            </body>
        </html>
        """

    # Send email
    try:
        email_client.send_email('gabrieltomberlin14@gmail.com', 'gabrieltomberlin14@gmail.com', 'Arxiv Daily Digest', body)
    except Exception as e:
        print(f"Error sending email: {e}")
        return

    email_client.close()

if __name__ == '__main__':
    main()