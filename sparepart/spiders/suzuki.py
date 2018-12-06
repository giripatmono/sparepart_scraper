# -*- coding: utf-8 -*-
import json
import re
from scrapy.spiders import Request
from ..items import SuzukiItem
from .base import BaseSpider
from ..helpers import remove_non_ascii


class SuzukiSpider(BaseSpider):
    name = 'suzuki'
    base_api = 'https://www.suzuki.co.id/eparts/api'
    allowed_domains = ['suzuki.co.id']
    start_urls = ['https://www.suzuki.co.id/eparts/api/get_vehicles']
    custom_settings = {
        'DOWNLOAD_DELAY': 1,
        'ITEM_PIPELINES': {
            'scrapy.pipelines.images.ImagesPipeline': 1,
            'sparepart.pipelines.JsonPipeline': 100,
            'sparepart.pipelines.SparepartSuzukiPipeline': 200,
        }
    }
    Type = {
        '5': 'Engine',
        '6': 'Transmission',
        '7': 'Electrical',
        '8': 'Suspension',
        '9': 'Body',
    }

    def parse(self, response):
        super(SuzukiSpider, self).parse(response)
        # print('response', type(json.loads(response.body)))

        vehicles = json.loads(response.body).get('automobile', None)
        # print('vehicles===== ', (vehicles))

        # create filter from self.model -> '  Sx4, nEO (JKD12) 1& 2  '
        myfilter = re.sub('[,()&]', ' ', self.model).lower().strip().split(' ')  # ['sx4', 'neo', 'jkd12', '1', '2']
        while '' in myfilter:
            myfilter.remove('')

        for itm in vehicles:  # filter url
            vehicle_model = itm.get('name', None)
            vehicle_model = re.sub('[,()&]', ' ', vehicle_model).lower().strip().split(' ')
            while '' in vehicle_model:
                vehicle_model.remove('')
            if myfilter == vehicle_model:  # match found
                model_id = itm.get('id', None)
                group_url = '{}/get_preview_tags/{}'.format(self.base_api, model_id)
                yield Request(group_url, callback=self.parse_group, meta={'model': itm.get('name'), 'model_id': model_id})
                self.logger.log(self.log_lvl, 'model: {}, crawling url: {}'.format(str(vehicle_model), group_url))
                break

    def parse_group(self, response):

        group = json.loads(response.body)
        model_id = response.meta.get('model_id', None)
        model = response.meta.get('model', None)
        if group is not False and len(group) > 0:
            for itm in group:
                type_id = itm.get('type_id', None)
                group_name = itm.get('name', None)
                assembly_set_url = '{}/get_figures/{}/{}'.format(self.base_api, type_id, model_id)
                self.logger.log(self.log_lvl, 'crawling url: {}'.format(assembly_set_url))
                yield Request(assembly_set_url, callback=self.parse_assembly_set, meta={'model': model,
                                                                                        'group': group_name})

        else:  # crawl figure index
            figure_index_url = '{}/get_figure_index/{}'.format(self.base_api, model_id)
            self.logger.log(self.log_lvl, 'Crawling Figure-Index: {}'.format(figure_index_url))
            yield Request(figure_index_url, callback=self.parse_assembly_set, meta={'model_id': model_id,
                                                                                    'model': model, 'group': None})

    def parse_assembly_set(self, response):

        # Get Illustration Figure URL and yield Requests
        assembly_set = json.loads(response.body)
        for itm in assembly_set:

            assembly_set_id = itm.get('id', None)
            assembly_set = itm.get('name', None)
            image_url = itm.get('file_url', None)
            model = response.meta.get('model', None)
            group = response.meta.get('group', None)
            try:
                if not group:
                    group = self.Type[itm.get('type_id')]
            except Exception as e:
                self.logger.warning('parse_assembly_set. {} - {}'.format(type(e), str(e)))

            parts_url = '{}/get_parts/{}'.format(self.base_api, assembly_set_id)
            self.logger.log(self.log_lvl, ('crawl Assembly Set url: {}'.format(parts_url)))
            yield Request(parts_url, callback=self.parse_parts,
                          meta={'model': model, 'group': group, 'assembly_set': assembly_set, 'image_url': image_url})

    def parse_parts(self, response):
        """Scrape Parts Item"""

        self.logger.log(self.log_lvl, 'scraping data @ {}'.format(response.url))

        vehicle = {}
        vehicle['source_url'] = response.url
        vehicle['merk'] = 'suzuki'
        vehicle['model'] = response.meta.get('model', None)

        # section/grouping/assembly
        vehicle['group'] = response.meta.get('group', None)
        vehicle['assembly_set'] = response.meta.get('assembly_set', None)

        parts = json.loads(response.body)
        item_list = []
        for itm in parts:
            item = SuzukiItem(**vehicle)

            # illustration image
            item['image_urls'] = [response.meta.get('image_url', None)]

            # sparepart details
            item['id'] = itm.get('id', None)
            item['image_id'] = itm.get('figure_id', None)
            part_name = itm.get('name', None)
            item['part_name'] = remove_non_ascii(part_name)
            item['part_number'] = itm.get('part_no', None)
            item['substitution_part_number'] = itm.get('sub_part_no', None)
            item['remarks'] = itm.get('remarks', None)
            item['qty'] = itm.get('qty', None)
            item['price'] = itm.get('price', None)
            item['tag_no'] = itm.get('tag_no', None)

            item_list.append(item)

        return item_list
