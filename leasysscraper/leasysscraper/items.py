# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy
from scrapy.item import Item, Field


class LeasysItem(Item):
    brand = scrapy.Field()
    model = scrapy.Field()
    version = scrapy.Field()
    trim = scrapy.Field()
    engine = scrapy.Field()
    duration = scrapy.Field()
    mileage = scrapy.Field()
    price = scrapy.Field()
    url = scrapy.Field()
    date_scraped = scrapy.Field()
    #pass
