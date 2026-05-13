from selenium import webdriver
from selenium.webdriver.common.by import By

driver = webdriver.Chrome()
driver.get("http://openinsider.com/")
print(driver.title)
print(driver.find_element(By.CSS_SELECTOR, "table.tinytable tbody tr").text)
driver.quit()
