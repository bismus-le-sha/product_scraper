# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
import pandas as pd


# class ProductSpidersPipeline:
#     def process_item(self, item, spider):
#         return item


class PandasPipeline:
    def __init__(self):
        self.df = pd.DataFrame(
            columns=['label', 'image', 'ingredients', 'additional_info', 'allergens'])

    def process_item(self, item, spider):
        self.df = pd.concat([self.df, pd.DataFrame([item])], ignore_index=True)
        return item

    def close_spider(self, spider):
        self.df.to_csv('products.csv', index=False)
