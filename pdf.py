from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, PageBreak
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import random
import time

logging.basicConfig(filename="scraping.log", level=logging.INFO)


def scrape_linkedin_jobs(job_title: str, location: str, pages: int = None, max_jobs: int = None) -> list:
    pages = pages or 1
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--ignore-certificate-errors")
    driver = webdriver.Chrome(options=options)
    driver.get(f"https://www.linkedin.com/jobs/search/?keywords={job_title}&location={location}")
    job_count = 0
    jobs = []
    
    for i in range(pages):
        if max_jobs is not None and job_count >= max_jobs:
            break
        logging.info(f"Scrolling to bottom of page {i+1}...")
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        
        try:
            element = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.XPATH, "/html/body/div[1]/div/main/section[2]/button"))
            )
            element.click()
        except Exception as e:
            logging.info(f"Error clicking on 'Show more' button: {str(e)}")
        
        time.sleep(random.choice(list(range(3, 7))))  # Fixed the syntax error here
        soup = BeautifulSoup(driver.page_source, "html.parser")
        job_listings = soup.find_all("div", class_="base-card relative w-full hover:no-underline focus:no-underline base-card--link base-search-card base-search-card--link job-search-card")
        
        for job in job_listings:
            if max_jobs is not None and job_count >= max_jobs:
                break
            job_title = job.find("h3", class_="base-search-card__title").text.strip()
            job_company = job.find("h4", class_="base-search-card__subtitle").text.strip()
            job_location = job.find("span", class_="job-search-card__location").text.strip()
            apply_link = job.find("a", class_="base-card__full-link")["href"]
            
            driver.get(apply_link)
            time.sleep(random.choice(list(range(5, 11))))  # Fixed the syntax error here
            
            try:
                description_soup = BeautifulSoup(driver.page_source, "html.parser")
                job_description = description_soup.find("div", class_="description__text description__text--rich").decode_contents()
            except AttributeError:
                job_description = None
                logging.warning("AttributeError occurred while retrieving job description.")
            
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
    
    return "\n".join(formatted_text)


def save_job_data(data: list) -> None:
    doc = SimpleDocTemplate("jobs.pdf", pagesize=letter)
    flowables = []
    styles = getSampleStyleSheet()
    normal_style = styles['Normal']
    
    for idx, job in enumerate(data, start=1):
        job_title = job["title"]
        job_description = html_to_formatted_text(job["description"])
        job_link = job["link"]
        
        title_para = Paragraph(f"<b>Job Title:</b> {job_title}", normal_style)
        flowables.append(title_para)
        
        description_para = Paragraph(f"<b>Job Description:</b><br/>{job_description}", normal_style)
        flowables.append(description_para)
        
        link_para = Paragraph(f"<b>Job Link:</b> <link href='{job_link}'>{job_link}</link>", normal_style)
        flowables.append(link_para)
        
        if idx < len(data):
            flowables.append(PageBreak())
    
    doc.build(flowables)
    logging.info(f"Successfully saved {len(data)} jobs to PDF file 'jobs.pdf'")


if __name__ == "__main__":
    data = scrape_linkedin_jobs("HR", "IND", pages=2, max_jobs=5)
    save_job_data(data)
