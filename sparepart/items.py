# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class IsuzuSparepartItem(scrapy.Item):
    # source_url
    source_url = scrapy.Field()

    # car model
    merk = scrapy.Field()
    model_mobil = scrapy.Field()
    tipe_mobil = scrapy.Field()

    # grouping/assembly
    main_group = scrapy.Field()  # e.g 'ENGINE', 'BODY', 'ELECTRICAL'
    assembly_set = scrapy.Field()  # e.g 'CYLINDER HEAD', 'FRONT BUMPER'
    image_urls = scrapy.Field()
    images = scrapy.Field()

    # sparepart details
    key = scrapy.Field()
    part_number = scrapy.Field()
    itc = scrapy.Field()
    description = scrapy.Field()
    qty = scrapy.Field()
    app_date = scrapy.Field()
    lr = scrapy.Field()
    model = scrapy.Field()
    remarks = scrapy.Field()


class PartsItem(scrapy.Item):
    # source_url
    source_url = scrapy.Field()

    # car model
    merk = scrapy.Field()
    model_year = scrapy.Field()
    model_mobil = scrapy.Field()
    submodel = scrapy.Field()
    engine = scrapy.Field()

    # section/grouping/assembly
    section = scrapy.Field()  # e.g 'ELECTRICAL', 'FUEL SYSTEM', 'ENGINE'
    group = scrapy.Field()  # e.g 'BODY ELECTRICAL', 'CHASSIS ELECTRICAL'
    subgroup = scrapy.Field()  # e.g 'ANTENNA & RADIO', 'KEYLESS ENTRY COMPONENTS'
    image_urls = scrapy.Field()
    images = scrapy.Field()

    # sparepart details
    part_name = scrapy.Field()
    part_number = scrapy.Field()
    price = scrapy.Field()
    description = scrapy.Field()
    lookup_no = scrapy.Field()
    image_id = scrapy.Field()


class MegazipItem(scrapy.Item):
    # source_url
    source_url = scrapy.Field()

    # car model
    merk = scrapy.Field()
    varian = scrapy.Field()
    model_year = scrapy.Field()
    sales_region = scrapy.Field()
    frame = scrapy.Field()
    grade = scrapy.Field()
    body = scrapy.Field()
    engine = scrapy.Field()
    transmission = scrapy.Field()
    destination = scrapy.Field()
    from_date = scrapy.Field()
    to_date = scrapy.Field()
    gear_shift_type = scrapy.Field()
    model = scrapy.Field()
    model_code = scrapy.Field()
    vehicle_model = scrapy.Field()
    model_mark = scrapy.Field()
    seating_capacity = scrapy.Field()
    fuel_induction = scrapy.Field()
    drive = scrapy.Field()
    door_number = scrapy.Field()
    note = scrapy.Field()

    # section/grouping/assembly
    assembly_group = scrapy.Field()  # e.g 'Engine, fuel', 'Electrical'
    assembly_set = scrapy.Field()
    image_urls = scrapy.Field()
    images = scrapy.Field()

    # sparepart details
    reference = scrapy.Field()
    part_name = scrapy.Field()
    part_number = scrapy.Field()
    replacement_for = scrapy.Field()
    description = scrapy.Field()
    price = scrapy.Field()


class SuzukiItem(scrapy.Item):
    # source_url
    source_url = scrapy.Field()

    # car model
    merk = scrapy.Field()
    model = scrapy.Field()

    # section/grouping/assembly
    group = scrapy.Field()  # e.g 'BODY', 'ELECTRICAL'
    assembly_set = scrapy.Field()  # e.g 'CYLINDER HEAD', 'CAMSHAFT & VALVE'
    image_urls = scrapy.Field()
    images = scrapy.Field()

    # sparepart details
    id = scrapy.Field()
    image_id = scrapy.Field()
    part_name = scrapy.Field()
    part_number = scrapy.Field()
    substitution_part_number = scrapy.Field()
    qty = scrapy.Field()
    price = scrapy.Field()
    remarks = scrapy.Field()
    tag_no = scrapy.Field()


class DaihatsuItem(scrapy.Item):
    # source_url
    source_url = scrapy.Field()

    # car model
    merk = scrapy.Field()
    model_mobil = scrapy.Field()

    # section/grouping/assembly
    group = scrapy.Field()  # e.g 'BODY', 'ENGINE'
    assembly_set = scrapy.Field()  # e.g 'FRONT HOOD', 'CAMSHAFT & VALVE'
    image_urls = scrapy.Field()
    images = scrapy.Field()

    # sparepart details
    prod_date = scrapy.Field()
    part_name = scrapy.Field()
    part_number = scrapy.Field()
    price = scrapy.Field()


class DaihatsuPartSearchItem(scrapy.Item):
    # source_url
    source_url = scrapy.Field()

    # car model
    merk = scrapy.Field()
    model_mobil = scrapy.Field()
    models = scrapy.Field()

    # sparepart details
    prod_date = scrapy.Field()
    spec_code = scrapy.Field()
    description = scrapy.Field()
    ref_no = scrapy.Field()
    part_name = scrapy.Field()
    part_number = scrapy.Field()
    qty = scrapy.Field()
    rev_ref_fr = scrapy.Field()
    rev_ref_to = scrapy.Field()
    weight = scrapy.Field()
    substitution = scrapy.Field()

