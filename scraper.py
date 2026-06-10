import json
from pathlib import Path

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait


BASE_URL = "http://openinsider.com"
DATA_DIR = Path("data")
SKIP_COLUMNS = {"1d", "1w", "1m", "6m"}
CATEGORIES = {
    "Insider Sales 100k": "/latest-insider-sales-100k",
    "Officer Sales 100k": "/latest-officer-sales-100k",
    "CEO/CFO Sales 100k": "/latest-ceo-cfo-sales-100k",
    "Insider Purchases 25k": "/latest-insider-purchases-25k",
    "Officer Purchases 25k": "/latest-officer-purchases-25k",
    "CEO/CFO Purchases 25k": "/latest-ceo-cfo-purchases-25k",
    "Cluster Buys": "/latest-cluster-buys",
}


def scrape_category(category_name):
    path = CATEGORIES[category_name]
    driver = webdriver.Chrome()

    try:
        rows = load_table_rows(driver, path)
    finally:
        driver.quit()

    save_category_data(category_name, rows)
    return rows


def load_category_data(category_name):
    file_path = get_data_file_path(category_name)
    if not file_path.exists():
        return []
    return json.loads(file_path.read_text(encoding="utf-8"))


def save_category_data(category_name, rows):
    DATA_DIR.mkdir(exist_ok=True)
    file_path = get_data_file_path(category_name)
    file_path.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")


def get_data_file_path(category_name):
    slug = category_name.lower().replace("/", "_").replace(" ", "_")
    return DATA_DIR / f"{slug}.json"


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
    keep_indexes = [index for index, header in enumerate(headers) if header not in SKIP_COLUMNS]
    kept_headers = [headers[index] for index in keep_indexes]

    rows = []
    for row in table.find_elements(By.CSS_SELECTOR, "tbody tr"):
        values = [read_text(cell) for cell in row.find_elements(By.TAG_NAME, "td")]
        if values and any(values):
            kept_values = [values[index] for index in keep_indexes]
            rows.append(dict(zip(kept_headers, kept_values)))

    return rows


def read_text(cell):
    return cell.get_attribute("textContent").strip()
