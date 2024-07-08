from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import random
import time
import os
from datetime import datetime

logging.basicConfig(filename="scrapingnaukari.log", level=logging.INFO)


def scrape_naukri_jobs(job_title: str, location: str, pages: int = None, max_jobs: int = None) -> list:
    pages = pages or 1
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--ignore-certificate-errors")
    driver = webdriver.Chrome(options=options)
    driver.get(f"https://www.naukri.com/hr-jobs-in-india?k={job_title}&l={location}")    
    job_count = 0
    jobs = []
    
    for i in range(pages):
        if max_jobs is not None and job_count >= max_jobs:
            break
        logging.info(f"Scrolling to bottom of page {i+1}...")
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        
        time.sleep(random.choice(list(range(3, 7))))
        soup = BeautifulSoup(driver.page_source, "html.parser")
        job_listings = soup.find_all("div", class_="cust-job-tuple")
        
        for job in job_listings:
            if max_jobs is not None and job_count >= max_jobs:
                break
            job_title = job.find("a", class_="title").text.strip()
            job_company = job.find("a", class_="comp-name").text.strip()
            job_location = job.find("span", class_="loc").text.strip()
            apply_link = job.find("a", class_="title")["href"]
            
            driver.execute_script(f"window.open('{apply_link}', '_blank');")  # Open job link in a new tab
            
            # Switch to the new tab
            driver.switch_to.window(driver.window_handles[1])
            time.sleep(random.choice(list(range(5, 11))))
            
            try:
                description_soup = BeautifulSoup(driver.page_source, "html.parser")
                job_description = description_soup.find("div", class_="job-desc").text.strip()
                
                # Optional: Remove "Show more" and "Show less" if present
                job_description = job_description.replace("Show more", "").replace("Show less", "")
                
            except AttributeError:
                job_description = None
                logging.warning("AttributeError occurred while retrieving job description.")
            
            # Close the current tab and switch back to the main tab with job listings
            driver.close()
            driver.switch_to.window(driver.window_handles[0])
            
            jobs.append({
                "title": job_title,
                "company": job_company,
                "location": job_location,
                "link": apply_link,
                "description": job_description,
            })
            
            logging.info(f'Scraped "{job_title}" at {job_company} in {job_location}...')
            job_count += 1

    driver.quit()
    return jobs


def html_to_formatted_text(html_text):
    soup = BeautifulSoup(html_text, "html.parser")
    formatted_text = []
    
    for element in soup.recursiveChildGenerator():
        if isinstance(element, str):
            formatted_text.append(element.strip())
        elif element.name == 'b':
            formatted_text.append(f"<b>{element.text.strip()}</b>")
        elif element.name == 'br':
            formatted_text.append("<br/>")
        elif element.name == 'ul':
            for li in element.find_all('li'):
                formatted_text.append(f"• {li.text.strip()}")
            formatted_text.append("\n")  # Add newline after each list item
    
    return "\n\n".join(formatted_text)


def save_job_data(data: list) -> None:
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    folder_name = f"jobs_naukri_{timestamp}"
    os.makedirs(folder_name, exist_ok=True)
    
    styles = getSampleStyleSheet()
    normal_style = styles['Normal']
    
    for idx, job in enumerate(data, start=1):
        job_title = job["title"]
        job_description = html_to_formatted_text(job["description"])
        job_link = job["link"]
        
        doc = SimpleDocTemplate(os.path.join(folder_name, f"{job_title}_{idx}.pdf"), pagesize=letter)
        flowables = [
            Paragraph(f"<b>Job Title:</b> {job_title}", normal_style),
            Paragraph(f"<b>Job Description:</b><br/>{job_description}", normal_style),
            Paragraph(f"<b>Job Link:</b> <link href='{job_link}'>{job_link}</link>", normal_style),
            Spacer(1, 20)  # Add spacer with 20 units of space
        ]
        
        doc.build(flowables)
        logging.info(f"Successfully saved job '{job_title}' to PDF file '{os.path.join(folder_name, f'{job_title}_{idx}.pdf')}'")


if __name__ == "__main__":
    c
    save_job_data(data)
