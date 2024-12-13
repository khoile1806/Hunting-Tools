from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time

options = Options()
options.headless = True
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

url = "https://chongluadao.vn/thong-ke"

driver.get(url)
driver.implicitly_wait(10)
page_number = 1
while True:
    print(f"Đang lấy dữ liệu từ trang {page_number}...")

    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')
    tables = soup.find_all('table')

    if len(tables) > 1:
        print(f"Table 2 từ trang {page_number}:")
        table = tables[1]

        rows = table.find_all('tr')
        for row in rows:
            cols = row.find_all('td')
            cols = [col.text.strip() for col in cols]
            print(cols)
    else:
        print(f"Không tìm thấy bảng thứ 2 trên trang {page_number}.")
    try:
        next_page = driver.find_element(By.ID, 'table_next')
        if "disabled" not in next_page.get_attribute("class"):
            driver.execute_script("arguments[0].scrollIntoView();", next_page)
            WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable(next_page)
            )
            ActionChains(driver).move_to_element(next_page).click().perform()
            time.sleep(3)
            page_number += 1
        else:
            print("Phần tử trang tiếp theo bị vô hiệu hóa.")
            break
    except Exception as e:
        print("Lỗi khi chuyển trang:", e)
        break

driver.quit()