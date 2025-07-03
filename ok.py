from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
import time

# Setup driver
driver = webdriver.Chrome()
driver.get("https://bfsi.economictimes.indiatimes.com/articles/upi-achieves-613-million-daily-transactions-with-1840-billion-in-june-2025/122174857")
info = driver.find_element(By.CLASS_NAME, "article-section__body__news")
print("Page Title:", info.text)
time.sleep(10)