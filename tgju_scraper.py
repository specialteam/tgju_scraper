"""
اسکریپر قیمت ارزهای سایت tgju.org
با استفاده از requests و BeautifulSoup و شبیه‌سازی مرورگر
"""

import requests
from bs4 import BeautifulSoup
import json
import re
from typing import Dict, List


class TGJUScraper:
    """کلاس برای اسکراپ کردن قیمت ارزها از سایت tgju.org"""
    
    def __init__(self):
        self.base_url = "https://www.tgju.org/currency"
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
        """دریافت صفحه قیمت ارزها"""
        try:
            response = self.session.get(self.base_url, timeout=10)
            response.raise_for_status()
            response.encoding = 'utf-8'
            return response
        except requests.exceptions.RequestException as e:
            print(f"خطا در دریافت صفحه: {e}")
            raise
    
    def parse_currencies(self, html_content: str) -> List[Dict]:
        """پارس کردن HTML و استخراج قیمت ارزها"""
        soup = BeautifulSoup(html_content, 'lxml')
        currencies = []
        seen_names = set()  # جلوگیری از تکرار
        
        # روش اصلی: جستجوی div های fs-row (ساختار واقعی سایت tgju)
        fs_rows = soup.find_all('div', class_='fs-row')
        for fs_row in fs_rows:
            # بررسی محتوای داخلی div
            # ممکن است شامل عناصر فرزند باشد یا فقط متن
            text_content = fs_row.get_text(separator='\n', strip=True)
            
            # تقسیم به خطوط
            lines = [line.strip() for line in text_content.split('\n') if line.strip()]
            
            for line in lines:
                # فیلتر کردن خط header و خطوط غیرضروری
                header_keywords = ['عنوان', 'قیمت زنده', 'زمان', 'جدول', 'نرخ', 'مقدار', 'واحد', 'مبدا', 'نتیجه', 'محاسبه', 'مقصد', 'شاخص', 'حواله', 'مثقال', 'طلا', 'عیار', 'سکه', 'بورس', 'نفت', 'سال', 'ماه', 'روز']
                
                # رد کردن خطوطی که فقط header هستند
                line_clean = line.strip()
                
                # اگر خط با کلمات header شروع می‌شود و قیمت ندارد، رد می‌شود
                if any(line_clean.startswith(keyword) for keyword in ['عنوان', 'جدول', 'مقدار', 'واحد', 'شاخص']) and not re.search(r'\d{1,3}(?:,\d{3})+', line):
                    continue
                
                # رد کردن خطوطی که شامل کلمات زیادی از header هستند
                header_word_count = sum(1 for keyword in header_keywords if keyword in line)
                if header_word_count >= 3 and len(line.split()) < 5:
                    continue
                
                # الگوی regex برای استخراج داده‌های ارز
                # فرمت: نام_ارز قیمت (درصد%) مقدار_تغییر کمترین بیشترین تاریخ
                # مثال: دلار 1,141,700 (0%) 0 1,135,800 1,144,200 ۶ آذر
                
                # پیدا کردن فقط قیمت‌های با کاما (مثلاً 1,141,700) - حداقل 4 رقم
                # الگوی بهبود یافته: اعدادی که دارای کاما هستند و حداقل 4 رقم دارند
                price_pattern = r'(\d{1,3}(?:,\d{3})+)'
                prices = re.findall(price_pattern, line)
                
                if len(prices) >= 3:  # باید حداقل 3 قیمت داشته باشیم (قیمت اصلی، کمترین، بیشترین)
                    try:
                        # پیدا کردن نام ارز (قبل از اولین قیمت)
                        first_price_match = re.search(price_pattern, line)
                        if not first_price_match:
                            continue
                            
                        name_part = line[:first_price_match.start()].strip()
                        
                        # حذف کلمات اضافی مثل "عنوان" اگر وجود دارد
                        name_words = [w for w in name_part.split() if w not in ['عنوان', 'قیمت', 'زنده', 'کمترین', 'بیشترین', 'تغییر', 'زمان', 'جدول', 'نرخ']]
                        currency_name = ' '.join(name_words).strip() if name_words else name_part.strip()
                        
                        # فیلتر دقیق‌تر برای رد کردن header ها
                        invalid_names = ['عنوان', 'جدول', 'مقدار', 'واحد', 'زمان', 'قیمت زنده', 'نرخ', 'شاخص', 'محاسبه', 'مقصد', 'مبدا', '']
                        currency_name_lower = currency_name.lower().strip()
                        
                        # فیلترهای جامع برای حذف header ها و خطوط نامعتبر
                        if (not currency_name or 
                            currency_name in invalid_names or 
                            currency_name_lower in [kw.lower() for kw in header_keywords] or
                            currency_name.startswith('جدول') or
                            currency_name.startswith('شاخص') or
                            currency_name.startswith('مقدار') or
                            currency_name.startswith('واحد') or
                            'جدول نرخ' in line or
                            re.match(r'^[\d,]+$', currency_name) or
                            len(currency_name) < 2 or
                            ('شاخص' in currency_name and len(currency_name.split()) < 3)):
                            continue
                        
                        # بررسی اینکه نام ارز معتبر است (نه فقط اعداد و کلمات کلیدی)
                        if all(word in header_keywords for word in currency_name.split()):
                            continue
                        
                        # استخراج قیمت‌ها
                        # فرمت: نام قیمت_اصلی (درصد%) مقدار_تغییر کمترین بیشترین تاریخ
                        # prices شامل: [قیمت_اصلی, کمترین, بیشترین]
                        price = prices[0].replace(',', '')
                        min_price = prices[1].replace(',', '') if len(prices) > 1 else ''
                        max_price = prices[2].replace(',', '') if len(prices) > 2 else ''
                        
                        # استخراج درصد تغییر (داخل پرانتز)
                        percent_match = re.search(r'\(([^)]+)\)', line)
                        percent_change = percent_match.group(1) if percent_match else ''
                        
                        # استخراج مقدار تغییر (عدد بعد از پرانتز و قبل از کمترین)
                        # الگو: ) فاصله عدد_بدون_کاما فاصله عدد_با_کاما(کمترین)
                        change_match = re.search(r'\)\s+(-?\d+)\s+' + re.escape(prices[1]), line)
                        change_amount = change_match.group(1) if change_match else ''
                        
                        # استخراج تاریخ (آخرین بخش - تاریخ فارسی)
                        date_match = re.search(r'([\u06F0-\u06F9\u0621-\u064A]+\s+[\u0621-\u064A]+)$', line)
                        date = date_match.group(0) if date_match else ''
                        
                        # اضافه کردن به لیست اگر معتبر باشد
                        # فیلترهای hardcode: رد کردن نام‌های خاص و نام‌های طولانی
                        if (currency_name == "جدول نرخ های امروز" or 
                            currency_name == "مقدار" or 
                            len(currency_name) > 25):
                            continue
                            
                        if currency_name and price and currency_name not in seen_names:
                            currencies.append({
                                'name': currency_name,
                                'price': price,
                                'percent_change': percent_change,
                                'change': change_amount,
                                'min_price': min_price,
                                'max_price': max_price,
                                'date': date
                            })
                            seen_names.add(currency_name)
                            
                    except Exception as e:
                        # در صورت بروز خطا، خط را نادیده می‌گیریم
                        continue
            
            # اگر خطوط مستقیماً کار نکرد، سعی می‌کنیم از عناصر فرزند استفاده کنیم
            # بررسی اینکه آیا div شامل عناصر ساختاریافته است
            currency_items = fs_row.find_all(['div', 'span', 'a'], recursive=True)
            if currency_items:
                # اگر عناصر ساختاریافته وجود دارد، از آن‌ها استفاده می‌کنیم
                # این بخش برای ساختارهای پیچیده‌تر
                pass
        
        # اگر با fs-row چیزی پیدا نشد، روش‌های دیگر را امتحان می‌کنیم
        if currencies:
            return currencies
        
        # روش 1: جستجوی جداول
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all(['td', 'th'])
                # حداقل 2 ستون باید باشد (نام و قیمت)
                if len(cells) >= 2:
                    try:
                        currency_name = cells[0].get_text(strip=True)
                        price = cells[1].get_text(strip=True)
                        change_text = cells[2].get_text(strip=True) if len(cells) > 2 else ""
                        min_price = cells[3].get_text(strip=True) if len(cells) > 3 else ""
                        max_price = cells[4].get_text(strip=True) if len(cells) > 4 else ""
                        date = cells[5].get_text(strip=True) if len(cells) > 5 else ""
                        
                        # تجزیه ستون تغییر به درصد و مقدار
                        # فرمت: (0%) 0
                        percent_change = ''
                        change = ''
                        if change_text:
                            percent_match = re.search(r'\(([^)]+)\)', change_text)
                            if percent_match:
                                percent_change = percent_match.group(1)
                            # بعد از پرانتز، مقدار تغییر است
                            change_match = re.search(r'\)\s+(-?\d+)', change_text)
                            if change_match:
                                change = change_match.group(1)
                        
                        # فیلتر کردن ردیف‌های header و خالی
                        # فیلترهای hardcode: رد کردن نام‌های خاص و نام‌های طولانی
                        if (currency_name == "جدول نرخ های امروز" or 
                            currency_name == "مقدار" or 
                            len(currency_name) > 20):
                            continue
                            
                        if currency_name and price and currency_name not in seen_names:
                            # فیلتر کردن عناوین جدول
                            if currency_name.lower() not in ['نام', 'ارز', 'قیمت', 'تغییر', 'currency', 'price', 'change', 'name', 'عنوان', 'زمان']:
                                currencies.append({
                                    'name': currency_name,
                                    'price': price,
                                    'percent_change': percent_change,
                                    'change': change,
                                    'min_price': min_price,
                                    'max_price': max_price,
                                    'date': date
                                })
                                seen_names.add(currency_name)
                    except Exception:
                        continue
        
        # روش 2: جستجوی div های با ساختار خاص tgju
        if not currencies:
            # جستجوی div با class های مختلف
            currency_containers = soup.find_all('div', class_=lambda x: x and isinstance(x, list))
            
            # جستجوی با id
            currency_sections = soup.find_all(id=lambda x: x and 'currency' in x.lower() if x else False)
            
            # جستجوی لینک‌های ارز
            currency_links = soup.find_all('a', href=lambda x: x and '/currency/' in str(x) if x else False)
            for link in currency_links:
                try:
                    parent = link.find_parent(['div', 'li', 'tr'])
                    if parent:
                        name = link.get_text(strip=True)
                        price_elem = parent.find(['span', 'div'], class_=lambda x: x and 'price' in str(x).lower() if x else False)
                        # فیلترهای hardcode: رد کردن نام‌های خاص و نام‌های طولانی
                        if (name == "جدول نرخ های امروز" or 
                            name == "مقدار" or 
                            len(name) > 20):
                            continue
                            
                        if name and price_elem and name not in seen_names:
                            currencies.append({
                                'name': name,
                                'price': price_elem.get_text(strip=True),
                                'percent_change': '',
                                'change': '',
                                'min_price': '',
                                'max_price': '',
                                'date': ''
                            })
                            seen_names.add(name)
                except Exception:
                    continue
        
        # روش 3: جستجوی با data attributes
        if not currencies:
            data_items = soup.find_all(attrs={'data-name': True}) or soup.find_all(attrs={'data-currency': True})
            for item in data_items:
                try:
                    name = item.get('data-name') or item.get('data-currency') or item.get_text(strip=True)
                    price_elem = item.find(['span', 'div', 'strong'], class_=lambda x: x and 'price' in str(x).lower() if x else False)
                    price = price_elem.get_text(strip=True) if price_elem else ''
                    
                    # فیلترهای hardcode: رد کردن نام‌های خاص و نام‌های طولانی
                    if (name == "جدول نرخ های امروز" or 
                        name == "مقدار" or 
                        len(name) > 20):
                        continue
                        
                    if name and price and name not in seen_names:
                        currencies.append({
                            'name': name,
                            'price': price,
                            'percent_change': '',
                            'change': '',
                            'min_price': '',
                            'max_price': '',
                            'date': ''
                        })
                        seen_names.add(name)
                except Exception:
                    continue
        
        # روش 4: جستجوی لیست‌های ul/ol
        if not currencies:
            lists = soup.find_all(['ul', 'ol'], class_=lambda x: x and 'currency' in str(x).lower() if x else False)
            for ul in lists:
                items = ul.find_all('li')
                for item in items:
                    try:
                        text = item.get_text(strip=True)
                        # تلاش برای استخراج نام و قیمت از متن
                        parts = [p.strip() for p in text.split() if p.strip()]
                        if len(parts) >= 2:
                            # معمولاً آخرین قسمت قیمت است
                            name = ' '.join(parts[:-1])
                            price = parts[-1]
                            # فیلترهای hardcode: رد کردن نام‌های خاص و نام‌های طولانی
                            if (name == "جدول نرخ های امروز" or 
                                name == "مقدار" or 
                                len(name) > 20):
                                continue
                                
                            if name not in seen_names and any(c.isdigit() for c in price):
                                currencies.append({
                                    'name': name,
                                    'price': price,
                                    'percent_change': '',
                                    'change': '',
                                    'min_price': '',
                                    'max_price': '',
                                    'date': ''
                                })
                                seen_names.add(name)
                    except Exception:
                        continue
        
        # روش 5: جستجوی داده‌های JavaScript/JSON درون صفحه
        if not currencies:
            scripts = soup.find_all('script')
            for script in scripts:
                if script.string and 'currency' in script.string.lower():
                    # تلاش برای استخراج داده‌های JSON از اسکریپت
                    json_matches = re.findall(r'\{[^{}]*"name"[^{}]*"price"[^{}]*\}', script.string)
                    for match in json_matches:
                        try:
                            data = json.loads(match)
                            if 'name' in data and 'price' in data:
                                name = data['name']
                            # فیلترهای hardcode: رد کردن نام‌های خاص و نام‌های طولانی
                            if (name == "جدول نرخ های امروز" or 
                                name == "مقدار" or 
                                len(name) > 20):
                                continue
                                
                            if name not in seen_names:
                                currencies.append({
                                    'name': name,
                                    'price': str(data.get('price', '')),
                                    'percent_change': str(data.get('percent_change', '')),
                                    'change': str(data.get('change', '')),
                                    'min_price': str(data.get('min_price', '')),
                                    'max_price': str(data.get('max_price', '')),
                                    'date': str(data.get('date', ''))
                                })
                                seen_names.add(name)
                        except Exception:
                            continue
        
        return currencies
    
    def scrape(self) -> List[Dict]:
        """متد اصلی برای اسکراپ کردن قیمت ارزها"""
        print("در حال دریافت صفحه...")
        response = self.fetch_page()
        
        print("در حال پارس کردن داده‌ها...")
        currencies = self.parse_currencies(response.text)
        
        return currencies
    
    def save_to_json(self, data: List[Dict], filename: str = 'currencies.json'):
        """ذخیره داده‌ها در فایل JSON"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"داده‌ها در فایل {filename} ذخیره شدند.")
    
    def print_currencies(self, currencies: List[Dict]):
        """چاپ قیمت ارزها در کنسول"""
        if not currencies:
            print("هیچ داده‌ای یافت نشد!")
            return
        
        print("\n" + "="*80)
        print(f"{'نام ارز':<20} {'قیمت':<15} {'تغییر':<15} {'کمترین':<15} {'بیشترین':<15}")
        print("="*80)
        
        for currency in currencies:
            name = currency.get('name', 'نامشخص')
            price = currency.get('price', 'نامشخص')
            percent_change = currency.get('percent_change', '-')
            change = currency.get('change', '-')
            min_price = currency.get('min_price', '-')
            max_price = currency.get('max_price', '-')
            
            # نمایش تغییر با درصد
            change_display = f"{percent_change} ({change})" if percent_change else change
            
            print(f"{name:<20} {price:<15} {change_display:<15} {min_price:<15} {max_price:<15}")


def main():
    """تابع اصلی"""
    scraper = TGJUScraper()
    
    try:
        currencies = scraper.scrape()
        
        if currencies:
            scraper.print_currencies(currencies)
            scraper.save_to_json(currencies)
            print(f"\n✓ تعداد {len(currencies)} ارز پیدا شد.")
        else:
            print("هیچ ارزی پیدا نشد. ممکن است ساختار سایت تغییر کرده باشد.")
            print("\nلطفاً HTML صفحه را ذخیره کنید تا بتوان ساختار آن را بررسی کرد.")
            
            # ذخیره HTML برای بررسی
            response = scraper.fetch_page()
            with open('page_source.html', 'w', encoding='utf-8') as f:
                f.write(response.text)
            print("HTML صفحه در فایل page_source.html ذخیره شد.")
            
    except Exception as e:
        print(f"خطا: {e}")


if __name__ == "__main__":
    # تنظیم encoding برای Windows console
    import sys
    if sys.platform == 'win32':
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
    main()

