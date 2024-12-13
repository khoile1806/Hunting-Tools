import requests
from bs4 import BeautifulSoup
import pandas as pd

# Base URL for pagination
base_url = "https://scam.vn/danh-sach?trang={}"

# Placeholder for all table data
table_data = []

# Column headers for the Excel file
columns = ["#", "Định danh", "Số tiền chiếm đoạt (VNĐ) (*)", "Lượt xem", "Ngày thêm"]

# Loop through all pages
for i in range(1, 476):
    url = base_url.format(i)
    print(f"Fetching page {i}: {url}")
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')
    rows = soup.select("tbody tr")
    for row_index, row in enumerate(rows, start=1):
        columns_data = row.find_all("td")
        row_data = [col.text.strip() for col in columns_data]
        table_data.append(row_data)
        # Debug print for each row
        print(f"Page {i}, Row {row_index}: {row_data}")

df = pd.DataFrame(table_data, columns=columns)

output_file = "scam_data.xlsx"
df.to_excel(output_file, index=False)

print(f"Data successfully saved to {output_file}")