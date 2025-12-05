"""
اسکریپر قیمت سکه سایت tgju.org
با استفاده از requests و BeautifulSoup و شبیه‌سازی مرورگر
"""

import requests
from bs4 import BeautifulSoup
import json
import re
from typing import Dict, List


class TGJUCoinScraper:
    """کلاس برای اسکراپ کردن قیمت سکه از سایت tgju.org"""
    
    def __init__(self):
        self.base_url = "https://www.tgju.org/coin"
        self.session = requests.Session()
        self._setup_headers()
    
    def _setup_headers(self):
        """تنظیم هدرهای مرورگر برای شبیه‌سازی"""
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'fa-IR,fa;q=0.9,en-US;q=0.8,en;q=0.7',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0',
        })
    
    def fetch_page(self) -> requests.Response:
        """دریافت صفحه قیمت سکه"""
        try:
            response = self.session.get(self.base_url, timeout=10)
            response.raise_for_status()
            response.encoding = 'utf-8'
            return response
        except requests.exceptions.RequestException as e:
            print(f"خطا در دریافت صفحه: {e}")
            raise
    
    def parse_coin(self, html_content: str) -> List[Dict]:
        """پارس کردن HTML و استخراج قیمت سکه"""
        soup = BeautifulSoup(html_content, 'lxml')
        coin_items = []
        seen_names = set()  # جلوگیری از تکرار
        
        # پیدا کردن همه جداول
        tables = soup.find_all('table')
        
        for table in tables:
            # پیدا کردن ردیف‌ها
            rows = table.find_all('tr')
            current_category = None
            
            for row in rows:
                cells = row.find_all(['td', 'th'])
                
                if len(cells) < 2:
                    continue
                
                try:
                    # استخراج نام از اولین سلول
                    name = cells[0].get_text(strip=True)
                    
                    # چک کردن آیا این یک ردیف header است (عنوان جدول)
                    header_keywords = ['قیمت سکه', 'قیمت نقدی', 'قیمت تک فروشی', 'حباب سکه', 
                                     'سکه در بورس', 'سایر سکه‌ها', 'قیمت زنده', 'تغییر', 
                                     'کمترین', 'بیشترین', 'زمان']
                    
                    # بررسی اینکه آیا این یک ردیف header جدول است
                    price_cell_text = cells[1].get_text(strip=True) if len(cells) > 1 else ""
                    is_header_row = 'قیمت زنده' in price_cell_text
                    
                    if is_header_row:
                        # این یک عنوان جدول است - تشخیص category
                        if 'قیمت نقدی' in name or ('قیمت سکه' in name and 'تک' not in name):
                            current_category = 'قیمت نقدی'
                        elif 'تک فروشی' in name or 'تک‌فروشی' in name:
                            current_category = 'قیمت تک فروشی'
                        elif 'حباب' in name:
                            current_category = 'حباب سکه'
                        elif 'بورس' in name:
                            current_category = 'سکه در بورس'
                        elif 'سایر' in name:
                            current_category = 'سایر سکه‌ها'
                        
                        continue
                    
                    # فیلتر کردن ردیف‌های header
                    if (name in ['قیمت سکه', 'قیمت نقدی', 'قیمت تک فروشی', 'حباب سکه', 
                                'سکه در بورس', 'سایر سکه‌ها', 'قیمت زنده', 'تغییر', 
                                'کمترین', 'بیشترین', 'زمان'] or
                        all(keyword in name for keyword in ['قیمت', 'زنده']) and 'سکه' not in name):
                        continue
                    
                    # استخراج قیمت از سلول دوم
                    price_text = cells[1].get_text(strip=True) if len(cells) > 1 else ""
                    
                    # اگر قیمت نداریم، رد می‌کنیم
                    if not price_text or not any(c.isdigit() for c in price_text):
                        continue
                    
                    # پاک کردن کاما از قیمت
                    price = price_text.replace(',', '').replace('،', '')
                    
                    # استخراج تغییرات (درصد و مقدار) از سلول سوم
                    change_text = cells[2].get_text(strip=True) if len(cells) > 2 else ""
                    percent_change = ''
                    change = ''
                    
                    if change_text:
                        # استخراج درصد تغییر از فرمت (0%) یا (0.39%)
                        percent_match = re.search(r'\(([^)]+)\)', change_text)
                        if percent_match:
                            percent_change = percent_match.group(1)
                        
                        # استخراج مقدار تغییر (عدد بعد از پرانتز)
                        change_match = re.search(r'\)\s*([\u2191\u2193\uf067\uf068]?\s*-?\d+(?:,\d{3})*)', change_text)
                        if not change_match:
                            # اگر بعد از پرانتز نیست، سعی می‌کنیم کل متن را بررسی کنیم
                            change_match = re.search(r'(-?\d+(?:,\d{3})*)', change_text.replace(percent_change, ''))
                        if change_match:
                            change = change_match.group(1).replace(',', '').replace('،', '').strip()
                    
                    # استخراج کمترین و بیشترین
                    min_price = ''
                    max_price = ''
                    if len(cells) > 3:
                        min_text = cells[3].get_text(strip=True)
                        if min_text and any(c.isdigit() for c in min_text):
                            min_price = min_text.replace(',', '').replace('،', '')
                    
                    if len(cells) > 4:
                        max_text = cells[4].get_text(strip=True)
                        if max_text and any(c.isdigit() for c in max_text):
                            max_price = max_text.replace(',', '').replace('،', '')
                    
                    # استخراج تاریخ/زمان از آخرین سلول
                    date = ''
                    if len(cells) > 5:
                        date_text = cells[5].get_text(strip=True)
                        if date_text:
                            date = date_text
                    
                    # فیلترهای اضافی برای رد کردن header ها و داده‌های نامعتبر
                    invalid_names = ['قیمت سکه', 'قیمت نقدی', 'قیمت تک فروشی', 'حباب سکه', 
                                   'سکه در بورس', 'سایر سکه‌ها', 'قیمت زنده', 'تغییر', 
                                   'کمترین', 'بیشترین', 'زمان', 'سکه', 'جدول نرخ های امروز']
                    
                    # فیلتر کردن نام‌های خیلی کوتاه یا خیلی طولانی
                    if (not name or 
                        name in invalid_names or
                        len(name) < 3 or
                        len(name) > 50 or
                        all(word in header_keywords for word in name.split()) or
                        name.replace(' ', '').replace('/', '').replace('-', '').isdigit() or
                        # فیلتر کردن نام‌هایی که فقط شامل اعداد و کاراکترهای خاص هستند
                        re.match(r'^[\d\s,\.:]+$', name)):
                        continue
                    
                    # فیلتر کردن قیمت‌های نامعتبر (خیلی کوچک یا خیلی بزرگ)
                    try:
                        price_num = int(price) if price else 0
                        if price_num < 100 or price_num > 1000000000000:  # کمتر از 100 یا بیشتر از 1 تریلیون
                            continue
                    except:
                        continue
                    
                    # اگر category مشخص نیست و هنوز تنظیم نشده، سعی می‌کنیم از نام تشخیص دهیم
                    if not current_category:
                        if 'بورس' in name or 'صندوق' in name:
                            current_category = 'سکه در بورس'
                        elif 'حباب' in name:
                            current_category = 'حباب سکه'
                        elif 'قبل' in name or 'پارسیان' in name:
                            current_category = 'سایر سکه‌ها'
                    
                    # ساخت کلید یکتا برای جلوگیری از تکرار
                    unique_key = f"{name}_{price}"
                    if unique_key in seen_names:
                        continue
                    
                    # اضافه کردن به لیست
                    coin_item = {
                        'name': name,
                        'price': price,
                        'percent_change': percent_change,
                        'change': change,
                        'min_price': min_price,
                        'max_price': max_price,
                        'date': date
                    }
                    
                    # اضافه کردن category اگر مشخص شده باشد
                    if current_category:
                        coin_item['category'] = current_category
                    
                    coin_items.append(coin_item)
                    seen_names.add(unique_key)
                    
                except Exception as e:
                    # در صورت بروز خطا، ردیف را نادیده می‌گیریم
                    continue
        
        return coin_items
    
    def scrape(self) -> List[Dict]:
        """متد اصلی برای اسکراپ کردن قیمت سکه"""
        print("در حال دریافت صفحه...")
        response = self.fetch_page()
        
        print("در حال پارس کردن داده‌ها...")
        coin_items = self.parse_coin(response.text)
        
        return coin_items
    
    def save_to_json(self, data: List[Dict], filename: str = 'coin.json'):
        """ذخیره داده‌ها در فایل JSON"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"داده‌ها در فایل {filename} ذخیره شدند.")
    
    def print_coin(self, coin_items: List[Dict]):
        """چاپ قیمت سکه در کنسول"""
        if not coin_items:
            print("هیچ داده‌ای یافت نشد!")
            return
        
        # گروه‌بندی بر اساس category
        categories = {}
        for item in coin_items:
            category = item.get('category', 'سایر')
            if category not in categories:
                categories[category] = []
            categories[category].append(item)
        
        print("\n" + "="*90)
        print(f"{'نام':<30} {'قیمت':<18} {'تغییر':<18} {'کمترین':<15} {'بیشترین':<15}")
        print("="*90)
        
        # چاپ هر category جداگانه
        for category, items in categories.items():
            if category:
                print(f"\n[{category}]")
                print("-" * 90)
            
            for item in items:
                name = item.get('name', 'نامشخص')
                price = item.get('price', 'نامشخص')
                percent_change = item.get('percent_change', '-')
                change = item.get('change', '-')
                min_price = item.get('min_price', '-')
                max_price = item.get('max_price', '-')
                
                # فرمت کردن قیمت‌ها با کاما
                try:
                    price_formatted = f"{int(price):,}" if price and price.isdigit() else price
                    min_formatted = f"{int(min_price):,}" if min_price and min_price.isdigit() else min_price
                    max_formatted = f"{int(max_price):,}" if max_price and max_price.isdigit() else max_price
                except:
                    price_formatted = price
                    min_formatted = min_price
                    max_formatted = max_price
                
                # نمایش تغییر با درصد
                if percent_change and change:
                    change_display = f"{percent_change} ({change})"
                elif percent_change:
                    change_display = percent_change
                elif change:
                    change_display = change
                else:
                    change_display = '-'
                
                print(f"{name:<30} {price_formatted:<18} {change_display:<18} {min_formatted:<15} {max_formatted:<15}")


def main():
    """تابع اصلی"""
    scraper = TGJUCoinScraper()
    
    try:
        coin_items = scraper.scrape()
        
        if coin_items:
            scraper.print_coin(coin_items)
            scraper.save_to_json(coin_items)
            print(f"\n✓ تعداد {len(coin_items)} آیتم سکه پیدا شد.")
        else:
            print("هیچ داده‌ای پیدا نشد. ممکن است ساختار سایت تغییر کرده باشد.")
            print("\nلطفاً HTML صفحه را ذخیره کنید تا بتوان ساختار آن را بررسی کرد.")
            
            # ذخیره HTML برای بررسی
            response = scraper.fetch_page()
            with open('coin_page_source.html', 'w', encoding='utf-8') as f:
                f.write(response.text)
            print("HTML صفحه در فایل coin_page_source.html ذخیره شد.")
            
    except Exception as e:
        print(f"خطا: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # تنظیم encoding برای Windows console
    import sys
    if sys.platform == 'win32':
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
    main()
