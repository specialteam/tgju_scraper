"""
مثال استفاده از اسکریپر TGJU
"""

from tgju_scraper import TGJUScraper


def example_basic():
    """مثال ساده استفاده"""
    scraper = TGJUScraper()
    currencies = scraper.scrape()
    
    if currencies:
        scraper.print_currencies(currencies)
        scraper.save_to_json(currencies)


def example_custom_output():
    """مثال با خروجی سفارشی"""
    scraper = TGJUScraper()
    currencies = scraper.scrape()
    
    if currencies:
        print("\n=== قیمت ارزها ===")
        for curr in currencies:
            print(f"{curr['name']}: {curr['price']}")


def example_filter():
    """مثال با فیلتر کردن ارزهای خاص"""
    scraper = TGJUScraper()
    currencies = scraper.scrape()
    
    # فقط ارزهای دلار و یورو
    filtered = [
        c for c in currencies 
        if 'دلار' in c['name'] or 'یورو' in c['name'] or 'Dollar' in c['name'] or 'Euro' in c['name']
    ]
    
    if filtered:
        scraper.print_currencies(filtered)


if __name__ == "__main__":
    print("مثال 1: استفاده ساده")
    example_basic()
    
    print("\n" + "="*60 + "\n")
    
    print("مثال 2: خروجی سفارشی")
    example_custom_output()

