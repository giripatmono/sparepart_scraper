# -*- coding: utf-8 -*-
import re
import json
import urllib.parse as urlparse
from scrapy.spiders import CrawlSpider, Request
from ..items import IsuzuSparepartItem
from .base import BaseSpider


class IsuzuSpider(BaseSpider):
    name = 'isuzu'
    allowed_domains = ['parts.isuzu.astra.co.id']
    start_urls = ['https://parts.isuzu.astra.co.id/marketing/catalog/']
    custom_settings = {
        'DOWNLOAD_DELAY': 1,
        'ITEM_PIPELINES': {
            'scrapy.pipelines.images.ImagesPipeline': 1,
            'sparepart.pipelines.JsonPipeline': 100,
            'sparepart.pipelines.SparepartIsuzuPipeline': 200,
        }
    }

    def parse(self, response):
        super(IsuzuSpider, self).parse(response)

        # Get Vehicle URL and yield Requests
        vehicle_selector = response.css('.description_content a.vehicle')
        for vehicle in vehicle_selector:
            url = vehicle.css('::attr(href)').extract_first()
            type = vehicle.css('::text').extract_first()
            if self.model.lower() in url.lower() or self.model.lower() in type.lower():
                self.logger.log(self.log_lvl, 'model: {}, type: {}, crawling url:{}'.format(self.model, type, url))
                yield Request(urlparse.urljoin(response.url, url), callback=self.parse_index_url,
                              meta={'type': type})
                break

    def parse_index_url(self, response):

        # Get the next illustration index URLs and yield Requests
        next_selector = response.css('table font.tabletitle a.figgrp::attr(href)')
        for url in next_selector.extract():
            yield Request(urlparse.urljoin(response.url, url), callback=self.parse_index_url,
                          meta={'type': response.meta.get('type', None)})

        # Get sparepart detail URLs and yield Requests
        main_group = response.css('table td table td.intable > font.warning::text').extract_first()
        detail_selector = response.css('.intable a[href*="detail.php"]::attr(href)')
        for url in detail_selector.extract():
            yield Request(urlparse.urljoin(response.url, url),
                          callback=self.parse_detail,
                          meta={'main_group': main_group, 'type': response.meta.get('type', None)})

    def parse_detail(self, response):
        """ This function parses a sparepart detail page.
        @scrapes spareparts data
        """

        self.logger.log(self.log_lvl, 'scraping data @ {}'.format(response.url))

        item_list = list()
        image_urls = list()
        # extract image
        try:
            pattern = re.compile(r"(.*imagearray:)(.*)(,.*displaymode.*)", re.MULTILINE | re.DOTALL)
            javascript_containing_images = response.xpath('//script[contains(., "var mygallery=")]/text()').extract()[0]
            images = re.match(pattern, javascript_containing_images).group(2)
            image_array = json.loads(images)
            image_urls = [urlparse.urljoin(response.url, itm[1]) for itm in image_array]
        except Exception as e:
            print("{} - {}".format(type(e), str(e)))

        tipe_mobil = response.css('#content font.vehicleinfo ~ font.warning::text').extract_first()
        model_mobil = response.css('#content font.vehicleinfo::text').extract_first()
        if tipe_mobil.lower() == model_mobil.lower():
            tipe_mobil = response.meta.get('type', None)
        main_group = response.meta.get('main_group', None)
        assembly_set = response.css('#content font.title b::text').extract_first()

        # sparepart items
        for row in response.css('div#content div.content table tr'):
            item = IsuzuSparepartItem()

            # source_url
            item['source_url'] = response.url

            # car model
            item['merk'] = self.name
            item['tipe_mobil'] = tipe_mobil
            item['model_mobil'] = model_mobil

            # images
            item['image_urls'] = image_urls

            # grouping/assembly
            item['main_group'] = main_group
            item['assembly_set'] = assembly_set

            item['key'] = row.css('td.intable:nth-child(1) .detailcontent::text').extract_first()
            item['part_number'] = row.css('td.intable:nth-child(2) .detailcontent::text').extract_first()
            item['itc'] = row.css('td.intable:nth-child(3) .detailcontent::text').extract_first()
            item['description'] = row.css('td.intable:nth-child(4) .detailcontent::text').extract_first()
            item['qty'] = row.css('td.intable:nth-child(5) .detailcontent::text').extract_first()
            item['app_date'] = row.css('td.intable:nth-child(6) .detailcontent::text').extract_first()
            item['lr'] = row.css('td.intable:nth-child(7) .detailcontent::text').extract_first()
            item['model'] = row.css('td.intable:nth-child(8) .detailcontent::text').extract_first()
            item['remarks'] = row.css('td.intable:nth-child(9) .detailcontent::text').extract_first()

            item_list.append(item)

        return item_list
