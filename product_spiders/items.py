# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class ProductSpidersItem(scrapy.Item):
    lable = scrapy.Field
    image = scrapy.Field
    ingredients = scrapy.Field
    additional_info = scrapy.Field
    allergens = scrapy.Field

