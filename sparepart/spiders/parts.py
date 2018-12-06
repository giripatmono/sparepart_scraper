# -*- coding: utf-8 -*-
import urllib.parse as urlparse
from scrapy.spiders import Spider, Request
from ..items import PartsItem
from .base import BaseSpider
from ..helpers import remove_non_ascii


class PartsSpider(BaseSpider):
    diagram_urls = set()
    crawled_diagram_urls = set()
    name = 'parts.com'
    allowed_domains = ['parts.com']
    start_urls = ['https://parts.com/']
    custom_settings = {
        'DOWNLOAD_DELAY': 5,
        'AUTOTHROTTLE_START_DELAY': 5,
        'ITEM_PIPELINES': {
            'scrapy.pipelines.images.ImagesPipeline': 1,
            'sparepart.pipelines.JsonPipeline': 100,
            'sparepart.pipelines.SparepartPartsPipeline': 200,
        },
        'DOWNLOADER_MIDDLEWARES': {
            'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
            'sparepart.middlewares.RandomUAMiddleware': 400,
            'sparepart.middlewares.UserAgentMiddleware': 401,
            'scrapy.downloadermiddlewares.retry.RetryMiddleware': 500
        }
    }

    def __init__(self, *args, **kwargs):
        super(PartsSpider, self).__init__(*args, **kwargs)
        self.submodel = kwargs.get('mesin', None)
        if self.submodel:
            self.submodel = self.submodel.split(' ')[0]

    def parse(self, response):
        super(PartsSpider, self).parse(response)

        vehicle_selector = response.css('#make-icons .item-effect .item-image a::attr(href)')
        for url in vehicle_selector.extract():
            if self.merk.lower() in url.lower():  # crawl car brand
                self.logger.log(self.log_lvl, 'merk: {}, crawling url: {}'.format(self.merk, url))
                yield Request(urlparse.urljoin(response.url, url), callback=self.parse_vehicle)
                break

    def parse_vehicle(self, response):

        model_year_selector = response.css('.shop-your-make .row a::attr(href)')
        url_list = model_year_selector.extract()

        if hasattr(self, 'year'):  # filter year
            self.logger.log(self.log_lvl, 'filter year: {}'.format(self.year))
            for url in url_list:
                if self.year.lower() in url.lower():  # crawl car year
                    self.logger.log(self.log_lvl, 'year: {}, crawling url: {}'.format(self.year, url))
                    yield Request(urlparse.urljoin(response.url, url), callback=self.parse_model_year)
                    break
        else:  # crawl all year
            self.logger.log(self.log_lvl, 'crawl all year')
            for url in url_list:
                self.logger.log(self.log_lvl, 'crawling url: {}'.format(url))
                yield Request(urlparse.urljoin(response.url, url), callback=self.parse_model_year)

    def parse_model_year(self, response):

        model_selector = response.css('.shop-your-make .row a::attr(href)')
        for url in model_selector.extract():
            model = None
            href = url.split('&')
            for k, v in enumerate(href):
                if 'model=' in v.lower():
                    model = v
                    break
            if model and self.model.lower() in model.lower():  # crawl car model
                self.logger.log(self.log_lvl, 'model: {}, crawling url: {}'.format(self.model, url))
                yield Request(urlparse.urljoin(response.url, url), callback=self.parse_model)
                break
        else:
            self.logger.log(self.log_lvl, 'model: {} not found @ {}'.format(self.model, url))

    def parse_model(self, response):

        mesin_selector = response.css('.shop-your-make a.Mark')
        if hasattr(self, 'mesin'):  # crawl spesifik submodel/mesin
            self.logger.log(self.log_lvl, 'filter mesin: {}'.format(self.mesin))
            filter_data = self.mesin.split(' ')  # e.g ['LE', 'L4', '1.5', 'GAS']
            links = response.css('.shop-your-make a.Mark::text')
            for link in links.extract():
                print('link..', self.mesin, link.strip() == self.mesin.strip())
            is_found = False
            for itm in mesin_selector:
                url = itm.css('::attr(href)').extract_first()
                link = itm.css('::text').extract_first()
                for flt in filter_data:
                    if flt.lower() not in urlparse.unquote(url).lower():
                        break
                else:
                    if link.strip() == self.mesin.strip():
                        is_found = True
                        self.logger.log(self.log_lvl, 'mesin: {}, crawling url: {}'.format(self.mesin, url))
                        yield Request(urlparse.urljoin(response.url, url), callback=self.parse_mesin)

            if not is_found:
                self.logger.log(self.log_lvl, 'filter mesin: {} not found @ {}'.format(self.mesin, response.url))

        else:  # crawl all mesin
            self.logger.log(self.log_lvl, 'crawl all mesin')
            for url in mesin_selector.extract():
                yield Request(urlparse.urljoin(response.url, url), callback=self.parse_mesin)

    def parse_mesin(self, response):

        section_selector = response.css('.shop-your-make a.Mark::attr(href)')
        parsed_url = urlparse.urlparse(response.url)
        submodel = urlparse.parse_qs(parsed_url.query)['submodel'][0]
        engine = urlparse.parse_qs(parsed_url.query)['Engine']
        for url in section_selector.extract():
            yield Request(urlparse.urljoin(response.url, url),
                          callback=self.parse_section, meta={'submodel': submodel, 'engine': engine[0]})

    def parse_section(self, response):

        # Get Group URL and yield Requests
        group_selector = response.css('#selectPreGroupOpen a.section-link::attr(href)')
        for url in group_selector.extract():
            yield Request(urlparse.urljoin(response.url, url),
                          callback=self.parse_group,
                          meta={'submodel': response.meta.get('submodel', None),
                                'engine': response.meta.get('engine', None)})

    def parse_group(self, response):

        # Get Subgroup URL and yield Requests
        subgroup_selector = response.css('#selectSubGroupOpen a::attr(href)')
        for url in subgroup_selector.extract():
            yield Request(urlparse.urljoin(response.url, url),
                          callback=self.parse_item,
                          meta={'submodel': response.meta.get('submodel', None),
                                'engine': response.meta.get('engine', None)})

    def parse_item(self, response):

        # car model
        merk = response.css('.container .breadcrumb li:nth-child(3) a::text').extract_first()
        model_year = response.css('.container .breadcrumb li:nth-child(2) a::text').extract_first()
        model_mobil = response.css('.container .breadcrumb li:nth-child(4) a::text').extract_first()
        submodel = response.meta.get('submodel', None)
        engine = response.meta.get('engine', None)
        parsed_url = urlparse.urlparse(response.url)

        # section/grouping/assembly
        section = urlparse.parse_qs(parsed_url.query)['section'][0]
        group = urlparse.parse_qs(parsed_url.query)['group'][0]
        subgroup = urlparse.parse_qs(parsed_url.query)['subgroup'][0]
        # img_urls = response.css('.container .sidebar-items img::attr(src)').extract()
        # image_urls = []
        # for itm in img_urls:
        #     image_urls.append(urlparse.urljoin(response.url, itm))

        # Parse Sparepart Detail
        items = list()
        for itm in response.css('.summary-row article'):

            # add Diagram URL Request if contain diagram link
            diagram_link = itm.css('#description-notes dd a::attr(href)').extract_first()
            if diagram_link:
                self.diagram_urls.add(diagram_link)

            # else append item
            else:
                item = PartsItem()

                # source_url
                item['source_url'] = response.url

                # car model
                item['merk'] = merk
                item['model_year'] = model_year
                item['model_mobil'] = model_mobil
                item['submodel'] = submodel
                item['engine'] = engine

                # section/grouping/assembly
                item['section'] = section
                item['group'] = group
                item['subgroup'] = subgroup

                # sparepart details
                item['part_name'] = itm.css('.preview-item-name a::text').extract_first()
                item['part_number'] = itm.css('section .preview-part-number + dd::text').extract_first()
                item['price'] = itm.css('.preview-part-info dd.price::text').extract_first()
                item['description'] = itm.css('section dl#description-notes > dd:first-of-type::text').extract_first()
                item['lookup_no'] = '-'

                items.append(item)
                yield item

        # crawl diagram url
        url_to_crawl = self.diagram_urls.difference(self.crawled_diagram_urls)
        for diagram_url in url_to_crawl:
            self.crawled_diagram_urls.add(diagram_url)
            yield Request(urlparse.urljoin(response.url, diagram_url),
                          callback=self.parse_item_diagram,
                          meta={'submodel': submodel, 'engine': engine, 'section': section, 'group': group,
                                'subgroup': subgroup})

        # return items
        if len(items) > 0:
            self.logger.log(self.log_lvl, 'scraping data @ {}'.format(response.url))

    def parse_item_diagram(self, response):

        self.logger.log(self.log_lvl, 'scraping data in diagram @ {}'.format(response.url))

        # car model
        merk = response.css('.container .breadcrumb li:nth-child(3) a strong::text').extract_first()
        model_year = response.css('.container .breadcrumb li:nth-child(2) a strong::text').extract_first()
        model_mobil = response.css('.container .breadcrumb li:nth-child(4) a strong::text').extract_first()
        submodel = response.meta.get('submodel', None)
        engine = response.meta.get('engine', None)

        # section/grouping/assembly
        section = response.meta.get('section', None)
        group = response.meta.get('group', None)
        subgroup = response.meta.get('subgroup', None)

        img_urls = response.css('.container .diagram-row .img-responsive::attr(src)').extract()
        image_urls = []
        for itm in img_urls:
            image_urls.append(urlparse.urljoin(response.url, itm))

        # Parse Sparepart Detail in Diagram
        items = list()
        for itm in response.css('.summary-row article'):
            item = PartsItem()

            # source_url
            item['source_url'] = response.url

            # car model
            item['merk'] = merk
            item['model_year'] = model_year
            item['model_mobil'] = model_mobil
            item['submodel'] = submodel
            item['engine'] = engine

            # section/grouping/assembly
            item['section'] = section
            item['group'] = group
            item['subgroup'] = subgroup
            item['image_urls'] = image_urls

            # sparepart details
            part_name = itm.css('.preview-item-name a::text').extract_first()
            try:
                part_name = part_name.split('[')
                item['part_name'] = part_name[0]
            except Exception as e:
                self.logger.log(self.log_lvl, 'part_name exception. {} - {}'.format(type(e), str(e)))
            item['part_number'] = itm.css('section .preview-part-number + dd::text').extract_first()
            item['price'] = itm.css('.preview-part-info dd.price::text').extract_first()
            item['description'] = '-'
            lookup_no = itm.css('#preview-savings-info dd .dfn-label::text').extract_first()
            item['lookup_no'] = remove_non_ascii(lookup_no)

            items.append(item)

        return items
