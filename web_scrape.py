import requests
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType
from selenium.webdriver.common.keys import Keys


# API Keys (Replace with your actual keys)
# TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
# OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# for github
import os
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
TAVILY_API_KEY = os.environ["TAVILY_API_KEY"]



def get_driver():
    """Initialize a headless Selenium WebDriver."""
    options = Options()
    options.add_argument("--disable-gpu")
    options.add_argument("--headless=new")  # Runs without opening a browser window
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    return webdriver.Chrome(
        service=Service(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install()),
        options=options,
    )



    




def scrape_website(url):
    """Scrapes website data using Selenium in headless mode and saves it to a file."""
    # chrome_options = Options()
    # chrome_options.add_argument("--headless")  # Run in headless mode (no GUI)
    # chrome_options.add_argument("--disable-gpu")  # Disable GPU acceleration
    # chrome_options.add_argument("--no-sandbox")  # Required for some environments
    # chrome_options.add_argument("--disable-dev-shm-usage")  # Overcome limited resources in containers

    # service = Service(ChromeDriverManager().install())
    # driver = webdriver.Chrome(service=service, options=chrome_options)
    #driver = get_driver()
    #driver.get(url)
    driver = get_driver()
    driver.get("https://www.google.com")
    time.sleep(2)

    # Locate search bar and enter URL
    search_box = driver.find_element(By.NAME, "q")
    search_box.send_keys(url)
    search_box.send_keys(Keys.RETURN)
    time.sleep(3)

    # Click the first search result
    try:
        first_result = driver.find_element(By.XPATH, "//div[@class='tF2Cxc']/div/a")
        first_result.click()
        time.sleep(3)

        # Get the opened website URL
        driver = driver.current_url
        
          # Keep browser open for scraping

    except Exception as e:
        print(f"⚠️ No search results found: {str(e)}")
        driver.quit()
        return None
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
    print("scraped_content",scraped_content)
    return scraped_content
    # with open("raw_scraped_data.txt", "w", encoding="utf-8") as file:
    #     file.write(f"Scraped Data from {url}:\n\n{scraped_content}\n")

    # return "raw_scraped_data.txt"

def search_with_tavily(query):
    """Fetches additional web data using Tavily API and appends it to the file."""
    url = "https://api.tavily.com/search"
    headers = {"Authorization": f"Bearer {TAVILY_API_KEY}", "Content-Type": "application/json"}
    data = {"query": query, "num_results": 5}

    response = requests.post(url, json=data, headers=headers)

    if response.status_code == 200:
        results = response.json().get("results", [])
        tavily_content = "\n".join([f"{r['title']} - {r['url']}" for r in results])
        return tavily_content
    else:
        print(f"Tavily API Error: {response.status_code}, Message: {response.text}")

def analyze_with_openai(website_data, website_url):
    """Reads the scraped file and sends it to OpenAI API for structured analysis."""
    

    prompt = f"""Analyze the website {website_url} and its Website Data:
    {website_data}. If you do not know, leave the section blank and provide accurate results.
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
    tavily_search=search_with_tavily(url)
    raw_data=raw_data_file+tavily_search
    print(raw_data)
    analyze_with_openai(raw_data, url)


if __name__ == "__main__":
    url="https://appedology.pk/"
    main_scrape(url)

    
