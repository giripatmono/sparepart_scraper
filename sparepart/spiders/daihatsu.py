# -*- coding: utf-8 -*-
import itertools
import urllib.parse as urlparse
from scrapy.spiders import Request
from scrapy.http import FormRequest
from .base import BaseSpider
from ..items import DaihatsuItem, DaihatsuPartSearchItem
from ..helpers import remove_non_ascii


class DaihatsuSpider(BaseSpider):
    name = 'daihatsu'
    allowed_domains = ['daihatsu-sparepart.com']
    start_urls = ['http://daihatsu-sparepart.com/']
    custom_settings = {
        'DOWNLOAD_DELAY': 1,
        'ITEM_PIPELINES': {
            'scrapy.pipelines.images.ImagesPipeline': 1,
            'sparepart.pipelines.JsonPipeline': 100,
            'sparepart.pipelines.SparepartDaihatsuPipeline': 200,
            'sparepart.pipelines.DaihatsuPartSearchPipeline': 201,
        }
    }
    part_search_url = 'http://daihatsu-sparepart.com/part/search'

    def parse(self, response):
        super(DaihatsuSpider, self).parse(response)

        if self.merk.lower() != 'daihatsu':
            self.logger.error('Merk should be daihatsu')
            raise Exception('Merk should be daihatsu')

        model_selector = response.css('#carouselh a::attr(href)')

        filter = self.model.split(' ')
        for url in model_selector.extract():
            for flt in filter:
                if flt.lower() not in url.lower():
                    break
            else:
                crawl_info = 'model: {}, crawling url:{}'.format(self.model, url)
                if hasattr(self, 'year'):
                    url = 'sparepart{}/{}'.format(url, self.year)
                    crawl_info = 'model: {}, year: {}, crawling url:{}'.format(self.model, self.year, url)

                self.logger.log(self.log_lvl, crawl_info)
                yield Request(urlparse.urljoin(response.url, url), callback=self.parse_model, meta={'model': self.model})

                # crawl part-search url
                model_value = None
                form_element = response.css('form[action*="part/search"]')
                for opt in form_element.css('select[name="model"] option'):
                    if self.model.lower() == opt.css('::text').extract_first().lower():
                        model_value = opt.css('::attr(value)').extract_first()
                        break
                for opt in form_element.css('select[name="searchBy"] option'):
                    if 'figure name' == opt.css('::text').extract_first().lower():
                        search_by = opt.css('::attr(value)').extract_first()
                        break
                try:
                    if model_value:
                        form_data = {"model": model_value, "searchBy": search_by}
                        # print(form_data)
                        yield FormRequest(self.part_search_url, callback=self.parse_part_search, formdata=form_data,
                                          meta={'model': self.model})
                except Exception as e:
                    self.logger.warning('{} - {}'.format(type(e), str(e)))

                break

        else:
            self.logger.warning('model not found for {}'.format(self.model))

    def parse_model(self, response):
        model = response.meta.get('model', None)
        group_selector = response.css('#contentWrapper #thumbView .accordion')
        for group in group_selector:
            group_name = remove_non_ascii(group.css('.title::text').extract_first())
            assembly_set_selector = group.css('.accorList a')
            for itm in assembly_set_selector:
                assembly_set = remove_non_ascii(itm.css('.caption span::text').extract_first())
                url_assembly_set = itm.css('::attr(href)').extract_first()
                # print('group_name: {}, set: {}, url: {}'.format(group_name, assembly_set, url_assembly_set))
                self.logger.log(self.log_lvl, 'crawling url:{}'.format(url_assembly_set))
                yield Request(urlparse.urljoin(response.url, url_assembly_set), callback=self.parse_assembly_set,
                              meta={'model': model, 'group_name': group_name, 'assembly_set': assembly_set})

    def parse_assembly_set(self, response):
        # print('response.meta', response.meta, response.url)
        model = response.meta.get('model', None)
        group_name = response.meta.get('group_name', None)
        assembly_set = response.meta.get('assembly_set', None)
        part_selector = response.css('.wrapper .part-name a')
        for part in part_selector:
            url_part = part.css('::attr(href)').extract_first()
            yield Request(urlparse.urljoin(response.url, url_part), callback=self.parse_item,
                          meta={'model': model, 'group_name': group_name, 'assembly_set': assembly_set})
            break

    def parse_item(self, response):
        # print('response.meta', response.meta)

        self.logger.log(self.log_lvl, 'scraping data @ {}'.format(response.url))

        image = response.css('.titlePage ~ .wrapper img::attr(src)').extract()
        vehicle = {'model_mobil': response.meta.get('model', None), 'group': response.meta.get('group_name', None),
                   'assembly_set': response.meta.get('assembly_set', None), 'merk': 'daihatsu',
                   'source_url': response.url, 'image_urls': [urlparse.urljoin(response.url, src) for src in image]}

        # Parse Sparepart Detail
        items = list()
        for itm in response.css('#part-list-detail tbody tr'):
            item = DaihatsuItem(**vehicle)

            # sparepart details
            item['prod_date'] = itm.css('td:nth-child(1)::text').extract_first()
            item['part_number'] = itm.css('td:nth-child(2)::text').extract_first()
            item['part_name'] = itm.css('td:nth-child(3)::text').extract_first()
            item['price'] = itm.css('td:nth-child(4)::text').extract_first()

            items.append(item)

        return items

    def parse_part_search(self, response):
        # print('response.meta', response.meta)

        self.logger.log(self.log_lvl, 'scraping search part data @ {}'.format(response.url))

        vehicle = {'model_mobil': response.meta.get('model'), 'merk': 'daihatsu', 'source_url': response.url}

        # Parse Search Part Detail
        items = list()
        ref_no = part_name = None
        for itm in response.css('.wrapper table.part-number tbody tr'):
            if itm.css('[class*="part-name-group"]'):
                ref_no = remove_non_ascii(itm.css('td:nth-child(2)::text').extract_first())
                part_name = remove_non_ascii(itm.css('td:nth-child(3)::text').extract_first())
                # print('=== Parent ROW', ref_no, part_name)
            else:
                item = DaihatsuPartSearchItem(**vehicle)
                item['ref_no'] = ref_no
                item['part_name'] = part_name
                item['prod_date'] = remove_non_ascii(itm.css('td:nth-child(1)::text').extract_first())
                item['models'] = remove_non_ascii(itm.css('td:nth-child(2)::text').extract_first())
                item['spec_code'] = remove_non_ascii(itm.css('td:nth-child(3)::text').extract_first())
                item['description'] = remove_non_ascii(itm.css('td:nth-child(4)::text').extract_first())
                item['part_number'] = remove_non_ascii(itm.css('td:nth-child(5)::text').extract_first())
                item['qty'] = remove_non_ascii(itm.css('td:nth-child(6)::text').extract_first())
                item['rev_ref_fr'] = remove_non_ascii(itm.css('td:nth-child(7)::text').extract_first())
                item['rev_ref_to'] = remove_non_ascii(itm.css('td:nth-child(8)::text').extract_first())
                item['weight'] = remove_non_ascii(itm.css('td:nth-child(9)::text').extract_first())
                item['substitution'] = remove_non_ascii(itm.css('td:nth-child(10)::text').extract_first())

                items.append(item)

        return items
