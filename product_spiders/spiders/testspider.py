import scrapy
import time
import logging
from curl_cffi import requests as cureq
from scrapy_playwright.page import PageMethod
from .util import utils
from .util.excluded import excluded_categories, excluded_subcategories
from product_spiders.items import ProductSpidersItem


class TestSpiderSpider(scrapy.Spider):
    name = "testspider"
    allowed_domains = ["www.perekrestok.ru"]
    custom_settings = {
        # Отключение headless режима для отладки
        'PLAYWRIGHT_LAUNCH_OPTIONS': {'headless': False},
    }

    def start_requests(self):
        self.logger.info("Запуск парсинга...")
        yield scrapy.Request(
            url="https://www.perekrestok.ru/cat/32/p/salat-iz-svekly-s-cesnokom-perekrestok-select-200g-4252526",
            meta={
                "playwright": True,
                "playwright_include_page": True,
                "playwright_page_coroutines": [
                    PageMethod("wait_for_selector",
                               "networkidle"),
                    PageMethod("evaluate", "window.scrollBy(0, 5000)"),
                    PageMethod("wait_for_selector",
                               "button:has-text('О товаре')"),
                    PageMethod(
                        'evaluate', "page.mouse.wheel(0, 150000);"),
                    PageMethod("click", "button:has-text('О товаре')"),
                    PageMethod("wait_for_timeout", 15000),
                ],
            },
            callback=self.parse,
            errback=self.error_handler
        )

    async def parse(self, response):
        # Получаем объект Playwright Page
        playwright_page = response.meta["playwright_page"]

        # Список для хранения данных ответов
        captured_responses = []

        # Устанавливаем обработчик для ответов
        def handle_response(res):
            if "/api/customer/1.4.1.0/catalog/product/plu" in res.url:
                captured_responses.append(res)

        playwright_page.on("response", handle_response)

        try:
            # Дожидаемся выполнения JavaScript на странице
            await playwright_page.wait_for_timeout(5000)

            # Обрабатываем захваченные запросы
            for res in captured_responses:
                try:
                    # Получаем тело ответа
                    body = await res.body()
                    self.logger.info(f"URL запроса: {res.url}")
                    self.logger.info(f"Тело ответа: {body.decode('utf-8')}")

                    # Преобразуем тело ответа в JSON
                    json_data = await res.json()  # Используйте .json() для объекта response
                    self.logger.info(f"JSON данные: {json_data}")

                    yield json_data  # Возвращаем данные в Scrapy pipeline

                except Exception as e:
                    self.logger.error(f"Ошибка при обработке ответа: {e}")

        finally:
            # Закрываем страницу в любом случае
            await playwright_page.close()

    def error_handler(self, failure):
        """Обрабатывает ошибки запросов."""
        self.logger.error(f"Ошибка запроса: {failure}")

    # async def parse_product_detail(self, response):
    #     page = response.meta['playwright_page']

    #     results = []

    #     async def handle_response(playwright_response):
    #         result = self.check_json(playwright_response)
    #         if result:
    #             results.append(result)

    #     page.on("response", handle_response)

    #     yield results

    async def parse_product_detail(self, response):
        # Парсинг данных после нажатия
        allergens = response.xpath(
            '//div[@class="product-info-string-value"]//a[@class="product-feature-link"]/text()').getall()

        # Для второго элемента (текстовые аллергены):
        additional_info = response.xpath(
            '//div[@class="product-info-string-value"]/text()').get()

        # Логирование, чтобы проверить успешность парсинга
        if additional_info:
            self.logger.info(
                "Button click successful, additional info loaded.")
        else:
            self.logger.warning(
                "Button click failed or additional info not loaded.")

        yield {

            'additional_info': additional_info if additional_info else '',

            'allergens': [allergen.strip() for allergen in allergens] if allergens else []
        }
