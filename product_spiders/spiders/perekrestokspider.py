import scrapy
from scrapy_playwright.page import PageMethod
from .util import utils
from .util.excluded import excluded_categories, excluded_subcategories
from product_spiders.items import ProductSpidersItem


class PerekrestokspidereSpider(scrapy.Spider):
    name = "perekrestokspider"
    allowed_domains = ["www.perekrestok.ru"]

    def start_requests(self):
        yield scrapy.Request("https://www.perekrestok.ru/cat/",
                             meta={
                                 "playwright": True,
                                 "playwright_include_page": True,
                                 "playwright_page_coroutines": [PageMethod(
                                     "wait_for_selector", "div.category-card__title")]
                             },
                             callback=self.parse_categories
                             )

    def parse_categories(self, response):
        category_map = utils.extract_links(
            response,
            'div.sc-gsTEea.hfvcqA div.Box-sc-149qidf-0 a.sc-kstqJO',
            'div.category-card__title',
        )

        self.logger.info(f"Collected {len(category_map)} categories in map.")
        self.logger.debug(f"Category map: {category_map}")

        filtered_map = utils.filter_items(category_map, excluded_categories)

        self.logger.info(f"Using {len(filtered_map)} filtered categories.")

        for name, url in filtered_map.items():
            self.logger.info(f"Processing category: {name} ({url})")
            yield scrapy.Request(
                url=url,
                meta={
                    "playwright": True,
                    "playwright_include_page": True,
                    "playwright_page_coroutines": [PageMethod(
                        "wait_for_selector", "a.products-slider__header")]
                },
                callback=self.parse_subcategory
            )

    def parse_subcategory(self, response):
        self.logger.info(f"Parsing product subcategory from {response.url}")

        subcategory_link_selector = 'a.products-slider__header'
        subcategory_name_selector = 'h2.products-slider__title'

        try:
            subcategory_map = utils.extract_links(
                response, subcategory_link_selector, subcategory_name_selector
            )
            self.logger.info(
                f"Collected {len(subcategory_map)} product subcategories.")
            self.logger.debug(f"Subcategory map: {subcategory_map}")

            filtered_subcategories = utils.filter_items(
                subcategory_map, excluded_subcategories)

            self.logger.info(
                f"Using {len(filtered_subcategories)} filtered subcategories.")

            for name, url in filtered_subcategories.items():
                self.logger.info(f"Processing subcategory: {name} ({url})")
                yield scrapy.Request(
                    url=url,
                    meta={
                        "playwright": True,
                        "playwright_include_page": True,
                        "playwright_page_coroutines": [PageMethod(
                            "wait_for_selector", "div.product-card__title")]
                    },
                    callback=self.parse_product,
                )

        except Exception as e:
            self.logger.error(
                f"Error during product subcategories parsing: {e}")

    def parse_product(self, response):
        product_links = response.css(
            'a.product-card__link::attr(href)').getall()

        unique_links = set(product_links)

        self.logger.info(
            f"Using {len(unique_links)} unique links of products.")

        for link in list(unique_links):
            absolute_link = response.urljoin(link)

            yield scrapy.Request(
                absolute_link,
                meta=dict(
                    playwright=True,
                    playwright_include_page=True,
                    playwright_page_coroutines=[
                        PageMethod("wait_for_selector",
                                   "networkidle"),
                        PageMethod("evaluate", "window.scrollBy(0, 5000)"),
                        PageMethod("wait_for_selector",
                                   "button:has-text('О товаре')"),
                        PageMethod(
                            'evaluate', "page.mouse.wheel(0, 150000);"),
                        PageMethod("click", "button:has-text('О товаре')"),]
                ),
                callback=self.parse_product_detail)

    def parse_product_detail(self, response):
        item = ProductSpidersItem()

        item['lable'] = response.xpath(
            '//h1[@class="sc-fubCzh ibFUIH product__title" and @itemprop="name"]/text()'
        ).get()

        item['image'] = response.xpath(
            '//img[@itemprop="image"]/@src'
        ).get()

        item['ingredients'] = response.xpath(
            '//p[@class="sc-dWddBi kBxBKK"]/text()').get()

        additional_info = response.xpath(
            '//div[@class="product-info-string-value"]/text()'
        ).get()
        item['additional_info'] = additional_info if additional_info else ''

        allergens = response.xpath(
            '//div[@class="product-info-string-value"]/a/text()'
        ).getall()
        item['allergens'] = [allergen.strip()
                             for allergen in allergens] if allergens else []

        yield item
