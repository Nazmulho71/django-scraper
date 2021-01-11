# All required imports
from django.views.generic import ListView
import requests
from bs4 import BeautifulSoup

class Index(ListView):

    queryset = []
    context_object_name = "items"
    template_name = "main/index.html"

    def get_context_data(self, *args, **kwargs):

        context = super(Index, self).get_context_data(*args, **kwargs)
        context['queryset'] = self.queryset
        return context

    def get_queryset(self):

        base_url = "https://www.ebay.com/sch/parser.html?_from=R40&_nkw={item}&_ipg=25"
        prices_url = "&_udlo={price_low}&_udhi={price_high}"

        item = self.request.GET.get('item')
        price_low = self.request.GET.get('from')
        price_high = self.request.GET.get('to')

        if self.request.method == 'GET' and item:

            item = "+".join(item.split())
            if price_low and price_high:
                url = (base_url + prices_url).format(item=item,price_low=price_low,price_high=price_high)
            else:
                url = base_url.format(item=item)

            scraper = Scraper(base_url=url)
            app = scraper.run()

            return app


class Scraper(Index):

    def __init__(self, base_url=None):
        super(Scraper, self).__init__()

        self.base_url = base_url

        self.queryset[:] = []

    def run(self):
        try:
            bs = self.make_soup(self.base_url)

            if not bs.get('error'):

                rows = bs.find_all('div', class_="s-item__wrapper")[:10]

                for parser in rows:
                    self.parse_rows(parser)

            else:
                print(bs['error'])

        except Exception as error:
            print(error)
            
        return self.queryset
    
    def parse_rows(self, parser):
        
        name = parser.find('h3', class_="s-item__title")
        if name:
            name = name.text
        else:
            name = ' '
            
        link = parser.find('a', class_="s-item__link")
        if link:
            link = link.get('href')
        else:
            link = ' '
            
        condition = parser.find('span', class_="SECONDARY_INFO")
        if condition:
            condition = condition.text
            
        price = parser.find('span', class_="s-item__price")
        if price:
            price = price.text
        else:
            price = ' '
            
        image = parser.find('img', class_="s-item__image-img").get('src')
        if image == 'https://ir.ebaystatic.com/cr/v/c1/s_1x2.gif':
            soup = self.make_soup(link)
            image = soup.find('img', {'id': "icImg"}).get('src')
            
        self.queryset.append(dict(name=name,link=link,condition=condition,price=price,image=image))

    def make_soup(self, url):
        
        headers = {'Accept': '*/*',
                   'Accept-Encoding': 'gzip, deflate, sdch',
                   'Accept-Language': 'en-US,en;q=0.8',
                   'Cache-Control': 'max-age=0',
                   'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36'}
        
        page = requests.get(url, headers=headers, timeout=15)
        
        if page.status_code == 200:
            soup = BeautifulSoup(page.content, "lxml")
        
        else:
            soup = {'error': "We got status code %s" % page.status_code}
        
        return soup
