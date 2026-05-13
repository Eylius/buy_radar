import json
from pathlib import Path

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait


BASE_URL = "http://openinsider.com"
PAGES = [
    "/latest-insider-sales-100k",
    "/latest-officer-sales-100k",
    "/latest-ceo-cfo-sales-100k",
    "/latest-insider-purchases-25k",
    "/latest-officer-purchases-25k",
    "/latest-ceo-cfo-purchases-25k",
    "/latest-cluster-buys",
]


def load_table_rows(driver, path):
    for _ in range(3):
        driver.get(f"{BASE_URL}{path}")
        try:
            WebDriverWait(driver, 20).until(
                lambda current_driver: current_driver.find_elements(By.CSS_SELECTOR, "table.tinytable")
            )
            break
        except TimeoutException:
            continue
    else:
        raise TimeoutException(f"Could not load table for {path}")

    tables = driver.find_elements(By.CSS_SELECTOR, "table.tinytable")
    table = max(
        tables,
        key=lambda current_table: len(current_table.find_elements(By.CSS_SELECTOR, "tbody tr")),
    )
    headers = [read_text(cell) for cell in table.find_elements(By.CSS_SELECTOR, "thead th")]

    rows = []
    for row in table.find_elements(By.CSS_SELECTOR, "tbody tr"):
        values = [read_text(cell) for cell in row.find_elements(By.TAG_NAME, "td")]
        if values and any(values):
            rows.append(dict(zip(headers, values)))

    return rows


def read_text(cell):
    return cell.get_attribute("textContent").strip()


def write_output(path, data):
    filename = f"output_{path.removeprefix('/').replace('-', '_')}.json"
    Path(filename).write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def main():
    driver = webdriver.Chrome()

    try:
        for path in PAGES:
            rows = load_table_rows(driver, path)
            write_output(path, rows)
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
