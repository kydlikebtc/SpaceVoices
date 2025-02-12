from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

def check_selenium():
    """Check Selenium installation and version."""
    print('Selenium version:', webdriver.__version__)
    print('Checking Chrome WebDriver...')
    try:
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.binary_location = '/usr/bin/chromium-browser'
        
        service = Service()
        service.path = '/usr/lib/chromium-browser/chromedriver'
        driver = webdriver.Chrome(service=service, options=options)
        print('Chrome WebDriver initialized successfully')
        driver.quit()
    except Exception as e:
        print('Error:', str(e))

if __name__ == '__main__':
    check_selenium()
