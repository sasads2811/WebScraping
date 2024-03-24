import requests
from bs4 import BeautifulSoup
import sqlite3
import time
import datetime

def scrape_job(job):
    job_info = {}
    title = job.find('a', class_='long-title')
    if title:
        job_info['Position title'] = title.text.strip()

    location = job.find('li', class_='location')
    if location:
        job_info['Location'] = location.text.strip()

    added = job.find('li', class_='added')
    if added:
        job_info['When the vacancy has been added'] = added.text.strip()

    salary = job.find('li', class_='salary')
    if salary:
        job_info['Salary'] = salary.text.strip()

    company = job.find('li', class_='company')
    if company:
        job_info['Company name'] = company.text.strip()

    date = job.find('li', class_='duedate')
    if date:
        job_info['Due date'] = date.text.strip()

    source = job.find('li', class_='source')
    if source:
        job_info['Source'] = source.text.strip()

    job_info['Timestamp'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(job_info)
    return job_info

# Function to create or connect to the database
def create_or_connect_db():
    conn = sqlite3.connect('job_listings.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS job_listings (
                 id INTEGER PRIMARY KEY,
                 position_title TEXT,
                 location TEXT,
                 added TEXT,
                 salary TEXT,
                 company_name TEXT,
                 due_date TEXT,
                 source TEXT,
                 timestamp TEXT)''')
    return conn

# Function to insert data into the database
def insert_into_db(conn, job_info):
    c = conn.cursor()
    c.execute('''INSERT INTO job_listings (position_title, location, added, salary, company_name, due_date, source, timestamp)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
              (job_info.get('Position title'), job_info.get('Location'), job_info.get('When the vacancy has been added'),
               job_info.get('Salary'), job_info.get('Company name'), job_info.get('Due date'),
               job_info.get('Source'), job_info.get('Timestamp')))
    conn.commit()

# Function to log script execution
def log_execution(start_time, end_time, num_rows_retrieved, error=None):
    with open('log.txt', 'a') as f:
        f.write(f"Script started at: {start_time}\n")
        if error:
            f.write(f"Error occurred: {error}\n")
        else:
            f.write(f"Script ended at: {end_time}\n")
            f.write(f"Script took: {end_time - start_time} seconds\n")
            f.write(f"Number of data rows retrieved: {num_rows_retrieved}\n\n")

# Main function to run the script
def main():
    start_time = time.time()
    try:
        conn = create_or_connect_db()
        num_rows_retrieved = 0
        for page_num in range(1, 6):  # Assuming there are 5 pages to scrape
            url = f'https://www.visidarbi.lv/darba-sludinajumi?page={page_num}#results'
            response = requests.get(url)
            soup = BeautifulSoup(response.content, 'html.parser')
            job_boxes = soup.find_all('div', class_='item premium big-item')
            for job_box in job_boxes:
                job_info = scrape_job(job_box)
                insert_into_db(conn, job_info)
                num_rows_retrieved += 1

        end_time = time.time()
        log_execution(start_time, end_time, num_rows_retrieved)
    except Exception as e:
        end_time = time.time()
        log_execution(start_time, end_time, num_rows_retrieved, error=str(e))
        raise

if __name__ == "__main__":
    main()
