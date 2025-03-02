import requests
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import subprocess
import os

# API Keys (Replace with your actual keys)
# TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
# OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# for github
import os
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
TAVILY_API_KEY = os.environ["TAVILY_API_KEY"]




def get_chromium_version():
    """Fetches the installed Chromium version."""
    try:
        version_output = subprocess.check_output(["chromium", "--version"]).decode("utf-8").strip()
        return version_output.split()[-1]  # Extracts version number
    except Exception as e:
        print(f"❌ Chromium not found: {e}")
        return None


def install_correct_chromedriver():
    """Downloads the ChromeDriver matching the installed Chromium version."""
    chromium_version = get_chromium_version()
    if not chromium_version:
        print("🚨 Chromium is not installed. Please install it first.")
        return None

    major_version = chromium_version.split('.')[0]
    driver_url = f"https://storage.googleapis.com/chrome-for-testing-public/{major_version}/linux64/chromedriver-linux64.zip"
    
    try:
        print(f"⬇️ Downloading ChromeDriver for Chromium v{major_version}...")
        subprocess.run(["wget", driver_url, "-O", "chromedriver.zip"], check=True)
        subprocess.run(["unzip", "-o", "chromedriver.zip"], check=True)
        subprocess.run(["chmod", "+x", "chromedriver-linux64/chromedriver"], check=True)
        
        chromedriver_path = os.path.abspath("chromedriver-linux64/chromedriver")
        if not os.path.exists(chromedriver_path):
            print("❌ ChromeDriver installation failed.")
            return None
        
        print(f"✅ ChromeDriver installed: {chromedriver_path}")
        return chromedriver_path

    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to download ChromeDriver: {e}")
        return None







def scrape_website(url):
    """Scrapes website data using Selenium in headless mode and saves it to a file."""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    chromedriver_path = install_correct_chromedriver()
    if not chromedriver_path:
        print("🚨 Could not install ChromeDriver. Exiting...")
        return None

    service = Service(chromedriver_path)
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.get(url)
    time.sleep(3)

    # Extract website text (paragraphs, spans, headers, footers, h1-h5)
    paragraphs = [p.text for p in driver.find_elements(By.TAG_NAME, "p") if p.text]
    spans = [span.text for span in driver.find_elements(By.TAG_NAME, "span") if span.text]
    headers = [header.text for header in driver.find_elements(By.TAG_NAME, "header") if header.text]
    footers = [footer.text for footer in driver.find_elements(By.TAG_NAME, "footer") if footer.text]

    headings = []
    for i in range(1, 6):
        headings.extend([h.text for h in driver.find_elements(By.TAG_NAME, f"h{i}") if h.text])

    driver.quit()

    # Save scraped data to a file
    scraped_content = "\n".join(paragraphs + spans + headers + footers + headings)
    with open("raw_scraped_data.txt", "w", encoding="utf-8") as file:
        file.write(f"Scraped Data from {url}:\n\n{scraped_content}\n")

    return "raw_scraped_data.txt"

def search_with_tavily(query):
    """Fetches additional web data using Tavily API and appends it to the file."""
    url = "https://api.tavily.com/search"
    headers = {"Authorization": f"Bearer {TAVILY_API_KEY}", "Content-Type": "application/json"}
    data = {"query": query, "num_results": 5}

    response = requests.post(url, json=data, headers=headers)

    if response.status_code == 200:
        results = response.json().get("results", [])
        tavily_content = "\n".join([f"{r['title']} - {r['url']}" for r in results])

        # Append Tavily data to the same file
        with open("raw_scraped_data.txt", "a", encoding="utf-8") as file:
            file.write(" Detail of Website:\n\n")
            file.write(tavily_content + "\n")

    else:
        print(f"Tavily API Error: {response.status_code}, Message: {response.text}")

def analyze_with_openai(filename, website_url):
    """Reads the scraped file and sends it to OpenAI API for structured analysis."""
    with open(filename, "r", encoding="utf-8") as file:
        scraped_data = file.read()

    prompt = f"""Analyze the website {website_url} and its Website Data:
    {scraped_data}. If you do not know, leave the section blank and provide accurate results.
    Provide a comprehensive report, including:

    Company Overview
    - Name, history, and background
    - Mission, vision, and core values
    - Locations (headquarters, global offices)

    Services & Solutions
    - Detailed list of services and solutions offered
    - Technologies used (AI, blockchain, cloud, etc.)
    - Industry-specific solutions
    - Links to social media and other resource pages

    Industries Served
    - List of industries the company caters to
    - Case studies and notable clients

    Contact Information
    - Phone numbers, emails, and office addresses
    - Social media profiles (LinkedIn, Twitter, etc.)
    - Contact forms or chatbot details

    Key Personnel
    - Leadership team (CEO, CTO, etc.)
    - Founders and management

    Client Testimonials & Reviews
    - Customer feedback from the website
    - External reviews (Clutch, Glassdoor, Trustpilot)

    News & Updates
    - Recent blog posts, press releases, or news mentions

    Competitor Comparison
    - How does this company compare to competitors in the same industry?
    """

    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"}
    data = {
        "model": "gpt-4o",
        "messages": [{"role": "user", "content": prompt}]
    }

    response = requests.post("https://api.openai.com/v1/chat/completions", json=data, headers=headers)

    if response.status_code == 200:
        analysis_result = response.json().get("choices", [{}])[0].get("message", {}).get("content", "No response content")
        with open("final_analysis.txt", "w", encoding="utf-8") as file:
            file.write("" + analysis_result + "\n")
        return 
    else:
        print(f"OpenAI API Error: {response.status_code}, Message: {response.text}")





def main_scrape(url):
    raw_data_file = scrape_website(url)
    search_with_tavily(url)
    analyze_with_openai(raw_data_file, url)


if __name__ == "__main__":
    main_scrape(url)

    
