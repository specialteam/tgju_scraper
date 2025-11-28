"""بررسی ساختار واقعی جدول"""
from bs4 import BeautifulSoup
import requests

url = "https://www.tgju.org/currency"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

response = requests.get(url, headers=headers)
response.encoding = 'utf-8'
soup = BeautifulSoup(response.text, 'lxml')

# بررسی جدول‌ها
tables = soup.find_all('table')
print(f"تعداد جداول: {len(tables)}")

for i, table in enumerate(tables[:2]):
    print(f"\n=== جدول {i+1} ===")
    rows = table.find_all('tr')[:3]  # فقط 3 ردیف اول
    for j, row in enumerate(rows):
        cells = row.find_all(['td', 'th'])
        print(f"ردیف {j+1}: {len(cells)} ستون")
        for k, cell in enumerate(cells):
            text = cell.get_text(strip=True)[:50]
            print(f"  ستون {k+1}: {text}")

