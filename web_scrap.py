import requests
from bs4 import BeautifulSoup
import sqlite3
import time
import random

# Create a database connection
conn = sqlite3.connect('job_listings_expanded.db')
c = conn.cursor()

# Create the jobs table
c.execute('''
CREATE TABLE IF NOT EXISTS jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT,
    title TEXT,
    company TEXT,
    location TEXT,
    tags TEXT,
    date_posted TEXT
)
''')

# Function to scrape job listings
def scrape_remoteok(max_pages=50):
    base_url = 'https://remoteok.io/remote-dev-jobs'
    headers = {'User-Agent': 'Mozilla/5.0'}
    total_scraped = 0

    for _ in range(max_pages):
        response = requests.get(base_url, headers=headers)
        if response.status_code != 200:
            print("Blocked or failed")
            break

        soup = BeautifulSoup(response.text, 'html.parser')
        job_rows = soup.find_all('tr', class_='job')

        for job in job_rows:
            try:
                title = job.find('h2').text.strip()
                company = job.find('h3').text.strip()
                tags = ', '.join(tag.text.strip() for tag in job.find_all('div', class_='tag'))
                date = job.find('time')['datetime']
                c.execute('''INSERT INTO jobs (source, title, company, location, tags, date_posted)
                             VALUES (?, ?, ?, ?, ?, ?)''', 
                          ('RemoteOK', title, company, 'Remote', tags, date))
                total_scraped += 1
            except:
                continue

        conn.commit()
        print(f"✅ Page done — total scraped so far: {total_scraped}")
        time.sleep(random.uniform(1, 2))

        if total_scraped >= 1000:
            break

    print(f"🎉 Done! Total jobs scraped: {total_scraped}")
    conn.close()

# Start scraping
scrape_remoteok()
