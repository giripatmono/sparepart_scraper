# -*- coding: utf-8 -*-
import json
import re
import os
import requests
import urllib.parse as urlparse
from requests.exceptions import ReadTimeout
from scrapy.spiders import Request
from ..items import MegazipItem
from .base import BaseSpider
from ..helpers import remove_non_ascii


class MegazipSpider(BaseSpider):
    name = 'megazip'
    allowed_domains = ['www.megazip.net']
    start_urls = ['https://www.megazip.net/zapchasti-dlya-avtomobilej']
    custom_settings = {
        'DOWNLOAD_DELAY': 15,
        'AUTOTHROTTLE_START_DELAY': 5,
        'ITEM_PIPELINES': {
            # 'scrapy.pipelines.images.ImagesPipeline': 1,
            'sparepart.pipelines.MyImagesPipeline': 1,
            'sparepart.pipelines.JsonPipeline': 100,
            'sparepart.pipelines.SparepartMegazipPipeline': 200,
        },
        'DOWNLOADER_MIDDLEWARES': {
            'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
            'sparepart.middlewares.RandomUAMiddleware': 400,
            'sparepart.middlewares.UserAgentMiddleware': 401,
            'scrapy.downloadermiddlewares.retry.RetryMiddleware': None,
            'sparepart.middlewares.TooManyRequestsRetryMiddleware': 543,
        }
    }

    def is_year_included(self, year):  # year => '2005', '2008 - 2012'
        year_array = [itm.strip() for itm in year.split(' - ')]  # year_array => ['2005'], ['2008', '2012']
        min_year = min(year_array)
        max_year = max(year_array)
        # check year
        if min_year <= self.year <= max_year:
            return True
        return False

    def parse(self, response):
        super(MegazipSpider, self).parse(response)

        merk_selector = response.css('li.manufacturers__item a::attr(href)')
        for url in merk_selector.extract():
            if self.merk and self.merk.lower() in url.lower():  # crawl car brand
                self.logger.log(self.log_lvl, 'merk: {}, crawling url:{}'.format(self.merk, url))
                yield Request(urlparse.urljoin(response.url, url), callback=self.parse_merk)
                break

    def parse_merk(self, response):

        model_selector = response.css('.filtred_item a::attr(href)')
        model_filter = [x for a in [itm2.split(' ') for itm2 in [itm.strip() for itm in self.model.split('/')]] for x in a]
        # print(model_filter)  # filter e.g. ['INNOVA', 'KIJANG', 'REVO', 'UNSER', 'ZACE']

        if hasattr(self, 'region'):  # filter region
            self.logger.log(self.log_lvl, ' Filter region : {}'.format(self.region))

            # extract region data
            try:
                pattern = re.compile(r"(.*var filter_data = )(.*)(;.*var filters_xr)", re.MULTILINE | re.DOTALL)
                javascript_containing_region_data = response \
                    .xpath('//script[contains(., "var filter_data = ")]/text()').extract()[0]
                region_data = re.match(pattern, javascript_containing_region_data).group(2)
                region_data_array = json.loads(region_data)
            except Exception as e:
                self.logger.warning("{} - {}".format(type(e), str(e)))

            # get filter ids
            filter_ids = []
            for k, v in region_data_array.items():
                if self.region.lower() in [x.lower() for x in v['sales-region']]:
                    filter_ids.append(k)
            # filter_ids ['38211', '38219', '38229', '38234', '38267']

            self.logger.debug('region_ids: {}'.format(str(filter_ids)))
            found = False
            for fltid in filter_ids:
                for url in model_selector.extract():
                    if fltid in url:
                        for flt in model_filter:
                            if flt.lower() not in url.lower():
                                break
                        else:
                            self.logger.log(self.log_lvl, 'model: {}, crawling url:{}'.format(self.model, url))
                            yield Request(urlparse.urljoin(response.url, url), callback=self.parse_model)
                            found = True
                            break
            if not found:
                self.logger.log(self.log_lvl, 'model:{} not found in region:{}'.format(self.model, self.region))

        else:  # crawl all region
            self.logger.log(self.log_lvl, ' Crawl All region')

            for url in model_selector.extract():
                for flt in model_filter:
                    if flt.lower() not in url.lower():
                        break
                else:
                    self.logger.log(self.log_lvl, 'model: {}, crawling url:{}'.format(self.model, url))
                    yield Request(urlparse.urljoin(response.url, url), callback=self.parse_model)
                    break

    def parse_model(self, response):

        varian_selector = response.css('.filtred_item a::attr(href)')

        if hasattr(self, 'year'):  # filter year
            self.logger.log(self.log_lvl, ' Filter model year : {}'.format(self.year))

            # extract year data
            try:
                pattern = re.compile(r"(.*var filter_data = )(.*)(;.*var filters_xr)", re.MULTILINE | re.DOTALL)
                javascript_containing_year_data = response\
                    .xpath('//script[contains(., "var filter_data = ")]/text()').extract()[0]
                year_data = re.match(pattern, javascript_containing_year_data).group(2)
                year_data_array = json.loads(year_data)
            except Exception as e:
                self.logger.warning("{} - {}".format(type(e), str(e)))

            # get year_ids e.g ['45072', '45089']
            year_ids = []

            for k, v in year_data_array.items():
                for year in v['year']:
                    if self.is_year_included(year):
                        year_ids.append(k)
                        break

            self.logger.debug('year_ids: {}'.format(str(year_ids)))
            for year_id in year_ids:  # filter year
                for url in varian_selector.extract():
                    if year_id in url:  # filter year
                        if hasattr(self, 'varian'):
                            if self.varian.lower() in url.lower():  # filter varian
                                self.logger.log(self.log_lvl, 'year: {}, varian: {}, crawling url:{}'.format(self.year, self.varian, url))
                                yield Request(urlparse.urljoin(response.url, url), callback=self.parse_varian)
                        else:
                            self.logger.log(self.log_lvl, 'year: {}, crawling url:{}'.format(self.year, url))
                            yield Request(urlparse.urljoin(response.url, url), callback=self.parse_varian)
                        break

        else:  # crawl all year
            self.logger.log(self.log_lvl, ' Crawl all year')
            for url in varian_selector.extract():
                if hasattr(self, 'varian'):
                    if self.varian.lower() in url.lower():  # filter varian
                        self.logger.log(self.log_lvl, 'all year varian: {}, crawling url:{}'.format(self.varian, url))
                        yield Request(urlparse.urljoin(response.url, url), callback=self.parse_varian)
                else:
                    self.logger.log(self.log_lvl, 'all year. crawling url:{}'.format(url))
                    yield Request(urlparse.urljoin(response.url, url), callback=self.parse_varian)

    def parse_varian(self, response):
        index_list_selector = response.css('li.s-catalog__body-variants-item.tech_row')
        self.logger.log(self.log_lvl, 'parse_varian {}'.format(response.url))

        # filter year, engine or transmission
        if hasattr(self, 'year') or hasattr(self, 'engine') or hasattr(self, 'transmisi'):
            filter_message = ''
            for x in ['year', 'engine', 'transmisi']:
                if hasattr(self, x):
                    filter_message += ', {}:{}'.format(x, self.__getattribute__(x))
            self.logger.log(self.log_lvl, 'Filter crawling{}'.format(filter_message))

            # extract filter data for year
            try:
                pattern = re.compile(r"(.*var filter_data = )(.*)(;.*var js_filters =)", re.MULTILINE | re.DOTALL)
                javascript_containing_filter_data = response \
                    .xpath('//script[contains(., "var filter_data = ")]/text()').extract()[0]
                filter_data = re.match(pattern, javascript_containing_filter_data).group(2)
                # print('filter_data', filter_data)
                filter_data_array = json.loads(filter_data)
                self.logger.debug('filter_data_array: {}'.format(str(filter_data_array)))
            except Exception as e:
                import inspect
                self.logger.warning('{} - {} @ {} | {}'.format(type(e), str(e),
                                                               str(inspect.currentframe().f_code),
                                                               inspect.currentframe().f_code.co_name))

            # compile year filter
            if hasattr(self, 'year'):
                year_ids = set()
                for k, v in filter_data_array.items():
                    for year in v['year']:
                        if self.is_year_included(year):
                            year_ids.add(k)
                            break

            for url in index_list_selector:
                url_link = url.css('.s-catalog__body-variants-item-content a::attr(href)').extract_first()

                # filter year
                if hasattr(self, 'year'):
                    found = False
                    for id in year_ids:
                        if id in url_link:
                            found = True
                            break
                    if not found:
                        continue

                car_attribute = url.css('.s-catalog__attrs:last-child dt')

                # filter engine
                if hasattr(self, 'engine'):
                    found = False
                    for attr in car_attribute:
                        if attr.css('::text').extract_first().lower() == 'engine':
                            if self.engine.lower() in attr.css('dt + dd::text').extract_first().strip().lower():
                                found = True
                                break
                    if not found:
                        continue

                # filter transmission
                if hasattr(self, 'transmisi'):
                    found = False
                    for attr in car_attribute:
                        if attr.css('::text').extract_first().lower() == 'transmission':
                            if self.transmisi.lower() in attr.css('dt + dd::text').extract_first().strip().lower():
                                found = True
                                break
                    if not found:
                        continue

                self.logger.log(self.log_lvl, 'crawling url:{}'.format(url_link))
                yield Request(urlparse.urljoin(response.url, url_link), callback=self.parse_index_list)

        else:  # no filter

            self.logger.log(self.log_lvl, 'No Filter')

            for url in index_list_selector:
                url_link = url.css('.s-catalog__body-variants-item-content a::attr(href)').extract_first()
                self.logger.log(self.log_lvl, 'crawling url:{}'.format(url_link))
                yield Request(urlparse.urljoin(response.url, url_link), callback=self.parse_index_list)

    def parse_index_list(self, response):

        # extract assembly group data
        group_options = response.css('.s-catalog__filter #group_level_1 option')
        group_list = {}
        for opt in group_options:
            key = opt.css('::attr(value)').extract_first()
            if key is not "":
                group_list[int(key)] = opt.css('::text').extract_first().strip()

        # extract items grouping
        try:
            pattern = re.compile(r"(.*var items_groups = )(.*)(;.*var images_path =)", re.MULTILINE | re.DOTALL)
            javascript_containing_filter_data = response \
                .xpath('//script[contains(., "var base_items_link = ")]/text()').extract()[0]
            filter_data = re.match(pattern, javascript_containing_filter_data).group(2)
            filter_data_array = json.loads(filter_data)
            # self.logger.debug('filter_data_array: {}'.format(str(filter_data_array)))
        except Exception as e:
            import inspect
            self.logger.warning('{} - {} @ {} | {}'.format(type(e), str(e),
                                                           str(inspect.currentframe().f_code),
                                                           inspect.currentframe().f_code.co_name))

        def find(lst, item_id):
            for i, dic in enumerate(lst):
                if dic['id'] == item_id:
                    return i
            return -1

        # Get Assembly Set URL and yield Requests
        assembly_set_selector = response.css('.part-group__item a::attr(href)')
        for url in assembly_set_selector.extract():
            group = None
            try:
                curr_id = url.split('-')[-1]
                index = find(filter_data_array, curr_id)
                group_id = int(filter_data_array[index]['group_id'][0])
                group = group_list[group_id]
            except Exception as e:
                self.logger.warning('{} - {} @ parse_index_list'.format(type(e), str(e)))

            self.logger.log(self.log_lvl, 'group: "{}", crawling url:{}'.format(group, url))
            yield Request(urlparse.urljoin(response.url, url), callback=self.parse_assembly_set,
                          meta={'assembly_group': group})

    def parse_assembly_set(self, response):

        self.logger.log(self.log_lvl, 'scraping data @ {}'.format(response.url))
        # vehicle description
        vehicle = {}
        vehicle['merk'] = response.css('.breadcrumbs li:nth-child(3) a span[itemprop="name"]::text').extract_first()
        vehicle['varian'] = getattr(self, 'varian', None)
        vehicle['engine'] = getattr(self, 'mesin', None)
        vehicle['assembly_group'] = response.meta.get('assembly_group', '-')
        vehicle['assembly_set'] = response.css('.breadcrumbs li:last-child::text').extract_first()
        vehicle['image_urls'] = response.css('img#items_list_image::attr(src)').extract()
        for k, v in enumerate(vehicle['image_urls']):
            vehicle['image_urls'][k] = urlparse.urljoin(response.url, v)

        vehicle['model_year'] = response.css('.s-catalog__header .s-catalog__attrs_type_dotted .s-catalog__attrs-data::text')\
            .extract_first()
        page_description = response.css('.s-catalog__header .s-catalog__attrs:last-child dt')
        for desc in page_description:
            if desc.css('::text').extract_first().lower() == 'sales region':
                vehicle['sales_region'] = desc.css('dt + dd::text').extract_first()
            elif desc.css('::text').extract_first().lower() == 'frame':
                vehicle['frame'] = desc.css('dt + dd::text').extract_first()
            elif desc.css('::text').extract_first().lower() == 'grade':
                vehicle['grade'] = desc.css('dt + dd::text').extract_first()
            elif desc.css('::text').extract_first().lower() == 'body':
                vehicle['body'] = desc.css('dt + dd::text').extract_first()
            elif desc.css('::text').extract_first().lower() == 'engine':
                vehicle['engine'] = desc.css('dt + dd::text').extract_first()
            elif desc.css('::text').extract_first().lower() == 'transmission':
                vehicle['transmission'] = desc.css('dt + dd::text').extract_first()
            elif desc.css('::text').extract_first().lower() == 'destination':
                vehicle['destination'] = desc.css('dt + dd::text').extract_first()
            elif desc.css('::text').extract_first().lower() == 'model':
                vehicle['model'] = desc.css('dt + dd::text').extract_first()
            elif desc.css('::text').extract_first().lower() == 'from':
                vehicle['from_date'] = desc.css('dt + dd::text').extract_first()
            elif desc.css('::text').extract_first().lower() == 'to':
                vehicle['to_date'] = desc.css('dt + dd::text').extract_first()
            elif desc.css('::text').extract_first().lower() == 'model code':
                vehicle['model_code'] = desc.css('dt + dd::text').extract_first()
            elif desc.css('::text').extract_first().lower() == 'vehicle model':
                vehicle['vehicle_model'] = desc.css('dt + dd::text').extract_first()
            elif desc.css('::text').extract_first().lower() == 'seating capacity':
                vehicle['seating_capacity'] = desc.css('dt + dd::text').extract_first()
            elif desc.css('::text').extract_first().lower() == 'gear shift type':
                vehicle['gear_shift_type'] = desc.css('dt + dd::text').extract_first()
            elif desc.css('::text').extract_first().lower() == 'fuel induction':
                vehicle['fuel_induction'] = desc.css('dt + dd::text').extract_first()
            elif desc.css('::text').extract_first().lower() == 'no.of doors':
                vehicle['door_number'] = desc.css('dt + dd::text').extract_first()
            elif desc.css('::text').extract_first().lower() == 'number of doors':
                vehicle['door_number'] = desc.css('dt + dd::text').extract_first()
            elif desc.css('::text').extract_first().lower() == 'note':
                vehicle['note'] = desc.css('dt + dd::text').extract_first()

        # sparepart details
        replacement_for = None
        item_list = []
        empty_count = 0
        for itm in response.css('table#items_list tr.items-list__row'):
            item = MegazipItem(**vehicle)
            try:
                data = json.loads(itm.css('::attr(data-item)').extract_first())
            except Exception as e:
                empty_count += 1
                continue

            if itm.css('[class*="items-list__row_first-in-block"]'):
                # print('=== FIRST ROW')
                replacement_for = data.get('number', None)
            else:
                # print('=== REPLACEMENT ROW')
                item['replacement_for'] = replacement_for

            item['reference'] = data.get('ref', None)
            item['part_name'] = remove_non_ascii(data.get('name', None))
            item['part_number'] = data.get('number', None)
            try:
                item['description'] = remove_non_ascii(data['itemsset_description'][:254]) if data.get('itemsset_description', None) else None
            except:
                item['description'] = None
            try:
                price = data['original'][0]['price']
            except:
                price = None
            item['price'] = price
            item['source_url'] = response.url
            item_list.append(item)

        if empty_count > 0:
            self.logger.log(self.log_lvl, 'There are {} empty data-items found in the page'.format(empty_count))

        return item_list
