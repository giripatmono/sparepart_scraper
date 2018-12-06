# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html

import os
import datetime
from scrapy.pipelines.images import ImagesPipeline
from shutil import copy2
from pathlib import Path
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from .models import SparepartIsuzu, ImageLinkIsuzu, ImageIsuzu, SparepartParts, ImageParts,\
    SparepartMegazip, ImageMegazip, SparepartSuzuki, ImageSuzuki, SparepartDaihatsu, SparepartDaihatsuPartSearch, ImageDaihatsu, \
    db_connect
from .items import DaihatsuItem, DaihatsuPartSearchItem
from .helpers import get_or_create
from scrapy.utils.project import get_project_settings
from scrapy.exporters import JsonItemExporter

try:
    from cStringIO import StringIO as BytesIO
except ImportError:
    from io import BytesIO

from PIL import Image

import logging
logger = logging.getLogger()

IMAGES_STORE = get_project_settings().get("IMAGES_STORE")
NO_VALUE = '-'


def save_image_relation_m2m(session, img_cls, img_link_cls, img):
    """
    Add image Many 2 Many relation for sparepart
    """

    # save images to database
    imagelink = img_link_cls()
    full_path = '{}/{}'.format(IMAGES_STORE, img['path'])
    img.update({'full_path': full_path})
    imagelink.image = get_or_create(session, img_cls, **img)

    # remove downloaded images
    try:
        os.remove(full_path)
        pass
    except:
        logger.debug('remove image failed.')

    return imagelink

def save_image(session, img_cls, img):
    """
    Save image to database
    """

    # save images to database
    full_path = '{}/{}'.format(IMAGES_STORE, img['path'])
    img.update({'full_path': full_path})
    image = get_or_create(session, img_cls, **img)

    # remove downloaded images
    try:
        os.remove(full_path)
        logger.debug('file {} removed'.format(full_path))
    except:
        logger.debug('remove failed for {}'.format(full_path))

    return image


class BasePipeline(object):
    def __init__(self):
        """
        Initializes database connection and sessionmaker.
        """
        if os.environ.get('CONNECTION_STRING'):
            engine = db_connect()
            self.Session = sessionmaker(bind=engine)


class SparepartIsuzuPipeline(BasePipeline):

    def process_item(self, item, spider):
        """Save isuzu spareparts in the database.

        This method is called for every item pipeline component.
        """

        if os.environ.get('SAVE_AS_JSON'):
            return item

        session = self.Session()
        sparepart = SparepartIsuzu(**{'job_id': spider._job})
        sparepart.merk = item["merk"]
        sparepart.model_mobil = item["model_mobil"]
        sparepart.tipe_mobil = item["tipe_mobil"]
        sparepart.main_group = item["main_group"]
        sparepart.assembly_set = item["assembly_set"]
        sparepart.key = item["key"]
        sparepart.part_number = item["part_number"]
        sparepart.itc = item["itc"]
        sparepart.description = item["description"]
        sparepart.qty = item["qty"]
        sparepart.app_date = item["app_date"]
        sparepart.lr = item["lr"]
        sparepart.model = item["model"]
        sparepart.remarks = item["remarks"]
        sparepart.source_url = item["source_url"]

        try:

            # save images relation
            try:
                for img in item.get("images", None):
                    img.update({'image_name': item['assembly_set'],
                                'merk': item['merk'], 'model': item['model_mobil'], 'type': item['tipe_mobil'], })
                    imagelink = save_image_relation_m2m(session, ImageIsuzu, ImageLinkIsuzu, img)
                    sparepart.images.append(imagelink)

            except Exception as e:
                spider.logger.warning("{} - {}".format(type(e), str(e)))

            session.add(sparepart)
            session.commit()

        except IntegrityError as e:
            spider.logger.warning("IntegrityError Exception. {} - {}".format(type(e), str(e)))
            session.rollback()
        except Exception as e:
            spider.logger.error("EXCEPTION... {} - {}".format(type(e), str(e)))
            session.rollback()
            # raise
        finally:
            session.close()

        return item


class SparepartPartsPipeline(BasePipeline):

    def process_item(self, item, spider):
        if os.environ.get('SAVE_AS_JSON'):
            return item

        session = self.Session()
        sparepart = SparepartParts(**{'job_id': spider._job})
        sparepart.merk = item.get("merk") if item.get("merk") != '' else NO_VALUE
        sparepart.model_year = item.get("model_year") if item.get("model_year") != '' else NO_VALUE
        sparepart.model_mobil = item.get("model_mobil") if item.get("model_mobil") != '' else NO_VALUE
        sparepart.submodel = item.get("submodel") if item.get("submodel") != '' else NO_VALUE
        sparepart.engine = item.get("engine") if item.get("engine") != '' else NO_VALUE
        sparepart.section = item.get("section") if item.get("section") != '' else NO_VALUE
        sparepart.group = item.get("group") if item.get("group") != '' else NO_VALUE
        sparepart.subgroup = item.get("subgroup") if item.get("subgroup") != '' else NO_VALUE
        sparepart.part_name = item.get("part_name") if item.get("part_name") != '' else NO_VALUE
        sparepart.part_number = item.get("part_number") if item.get("part_number") != '' else NO_VALUE
        sparepart.price = item.get("price") if item.get("price") != '' else NO_VALUE
        sparepart.description = item.get("description") if item.get("description") != '' else NO_VALUE
        sparepart.source_url = item.get("source_url") if item.get("source_url") != '' else NO_VALUE
        sparepart.lookup_no = item.get("lookup_no") if item.get("lookup_no") != '' else NO_VALUE

        try:

            # save images relation
            try:
                if 'images' in item:
                    for img in item.get("images"):
                        img.update({'image_name': sparepart.subgroup, 'merk': sparepart.merk,
                                    'model': sparepart.model_mobil, 'type': sparepart.submodel})
                        image = save_image(session, ImageParts, img)
                        sparepart.image_id = image.id

            except Exception as e:
                spider.logger.warning("{} - {}".format(type(e), str(e)))

            session.add(sparepart)
            session.commit()

        except IntegrityError as e:
            spider.logger.warning("IntegrityError Exception. {} - {}".format(type(e), str(e)))
            session.rollback()
        except Exception as e:
            spider.logger.error("EXCEPTION... {} - {}".format(type(e), str(e)))
            session.rollback()
            # raise
        finally:
            session.close()

        return item


class SparepartMegazipPipeline(BasePipeline):

    def process_item(self, item, spider):
        if os.environ.get('SAVE_AS_JSON'):
            return item

        session = self.Session()
        sparepart = SparepartMegazip(**{'job_id': spider._job})

        sparepart.merk = item.get("merk") if item.get("merk") != '' else NO_VALUE
        sparepart.varian = item.get("varian") if item.get("varian") != '' else NO_VALUE
        sparepart.model_year = item.get("model_year") if item.get("model_year") != '' else NO_VALUE
        sparepart.sales_region = item.get("sales_region") if item.get("sales_region") != '' else NO_VALUE
        sparepart.frame = item.get("frame") if item.get("frame") != '' else NO_VALUE
        sparepart.grade = item.get("grade") if item.get("grade") != '' else NO_VALUE
        sparepart.body = item.get("body") if item.get("body") != '' else NO_VALUE
        sparepart.engine = item.get("engine") if item.get("engine") != '' else NO_VALUE
        sparepart.transmission = item.get("transmission") if item.get("transmission") != '' else NO_VALUE
        sparepart.destination = item.get("destination") if item.get("destination") != '' else NO_VALUE
        sparepart.from_date = item.get("from_date") if item.get("from_date") != '' else NO_VALUE
        sparepart.to_date = item.get("to_date") if item.get("to_date") != '' else NO_VALUE
        sparepart.gear_shift_type = item.get("gear_shift_type") if item.get("gear_shift_type") != '' else NO_VALUE
        sparepart.model = item.get("model") if item.get("model") != '' else NO_VALUE
        sparepart.vehicle_model = item.get("vehicle_model") if item.get("vehicle_model") != '' else NO_VALUE
        if item.get("vehicle_model", None):
            sparepart.model = item.get("vehicle_model") if item.get("vehicle_model") != '' else NO_VALUE
        elif item.get("model_code", None):
            sparepart.model = item.get("model_code") if item.get("model_code") != '' else NO_VALUE

        sparepart.model_mark = item.get("model_mark") if item.get("model_mark") != '' else NO_VALUE
        sparepart.seating_capacity = item.get("seating_capacity") if item.get("seating_capacity") != '' else NO_VALUE
        sparepart.fuel_induction = item.get("fuel_induction") if item.get("fuel_induction") != '' else NO_VALUE
        sparepart.drive = item.get("drive") if item.get("drive") != '' else NO_VALUE
        sparepart.door_number = item.get("door_number") if item.get("door_number") != '' else NO_VALUE
        sparepart.note = item.get("note") if item.get("note") != '' else NO_VALUE
        sparepart.assembly_group = item.get("assembly_group")
        sparepart.assembly_set = item.get("assembly_set") if item.get("assembly_set") != '' else NO_VALUE

        sparepart.reference = item.get("reference") if item.get("reference") != '' else NO_VALUE
        sparepart.part_name = item.get("part_name") if item.get("part_name") != '' else NO_VALUE
        sparepart.part_number = item.get("part_number") if item.get("part_number") != '' else NO_VALUE
        sparepart.replacement_for = item.get("replacement_for") if item.get("replacement_for") != '' else NO_VALUE
        sparepart.description = item.get("description") if item.get("description") != '' else NO_VALUE
        sparepart.price = item.get("price") if item.get("price") != '' else NO_VALUE
        sparepart.source_url = item.get("source_url") if item.get("source_url") != '' else NO_VALUE

        try:

            # save images relation
            try:
                for img in item.get("images", None):
                    img.update({'image_name': sparepart.assembly_set, 'merk': sparepart.merk,
                                'model': sparepart.model if sparepart.model else sparepart.vehicle_model,
                                'type': sparepart.frame,
                                # 'force_create_new': True
                                })
                    image = save_image(session, ImageMegazip, img)
                    spider.logger.debug('-------------- image type: {}'.format(type(image)))
                    try:
                        spider.logger.debug('-------------- image id: {}'.format(image.id))
                    except Exception as e:
                        spider.logger.warning("exception image_id.{} - {}".format(type(e), str(e)))

                    sparepart.image_id = image.id

            except Exception as e:
                spider.logger.warning("{} - {}".format(type(e), str(e)))

            session.add(sparepart)
            session.commit()
        except IntegrityError as e:
            spider.logger.warning("IntegrityError Exception. {} - {}".format(type(e), str(e)))
            session.rollback()
        except Exception as e:
            spider.logger.error("EXCEPTION... {} - {}".format(type(e), str(e)))
            session.rollback()
            # raise
        finally:
            session.close()

        return item


class SparepartSuzukiPipeline(BasePipeline):

    def process_item(self, item, spider):
        """Save spareparts in the database.
        This method is called for every item pipeline component.
        """

        if os.environ.get('SAVE_AS_JSON'):
            return item

        session = self.Session()
        sparepart = SparepartSuzuki(**{'job_id': spider._job})

        sparepart.id = item.get("id") if item.get("id") != '' else NO_VALUE
        sparepart.image_id = item.get("image_id") if item.get("image_id") != '' else NO_VALUE
        sparepart.source_url = item.get("source_url") if item.get("source_url") != '' else NO_VALUE
        sparepart.merk = item.get("merk") if item.get("merk") != '' else NO_VALUE
        sparepart.model = item.get("model") if item.get("model") != '' else NO_VALUE
        sparepart.group = item.get("group") if item.get("group") != '' else NO_VALUE
        sparepart.assembly_set = item.get("assembly_set") if item.get("assembly_set") != '' else NO_VALUE

        sparepart.part_name = item.get("part_name") if item.get("part_name") != '' else NO_VALUE
        sparepart.part_number = item.get("part_number") if item.get("part_number") != '' else NO_VALUE
        sparepart.substitution_part_number = item.get("substitution_part_number") if item.get("substitution_part_number") != '' else NO_VALUE
        sparepart.qty = item.get("qty") if item.get("qty") != '' else NO_VALUE
        sparepart.price = item.get("price") if item.get("price") != '' else NO_VALUE
        sparepart.remarks = item.get("remarks") if item.get("remarks") != '' else NO_VALUE
        sparepart.tag_no = item.get("tag_no") if item.get("tag_no") != '' else NO_VALUE

        try:

            # save images relation
            try:
                for img in item.get("images", None):
                    img.update({'image_name': sparepart.assembly_set, 'merk': sparepart.merk,
                                'model': sparepart.model, 'id': sparepart.image_id, 'group': sparepart.group})
                    image = save_image(session, ImageSuzuki, img)

            except Exception as e:
                spider.logger.warning("{} - {}".format(type(e), str(e)))

            session.add(sparepart)
            session.commit()

        except IntegrityError as e:
            spider.logger.warning("IntegrityError Exception. {} - {}".format(type(e), str(e)))
            session.rollback()
        except Exception as e:
            spider.logger.error("EXCEPTION... {} - {}".format(type(e), str(e)))
            session.rollback()
            # raise
        finally:
            session.close()

        return item


class SparepartDaihatsuPipeline(BasePipeline):

    def process_item(self, item, spider):
        """Save spareparts in the database.
        This method is called for every item pipeline component.
        """

        spider.logger.debug("Item type: {}".format(type(item)))

        if os.environ.get('SAVE_AS_JSON') or not isinstance(item, DaihatsuItem):
            return item

        session = self.Session()
        sparepart = SparepartDaihatsu(**{'job_id': spider._job})

        sparepart.source_url = item.get("source_url") if item.get("source_url") != '' else NO_VALUE
        sparepart.merk = item.get("merk") if item.get("merk") != '' else NO_VALUE
        sparepart.model = item.get("model_mobil") if item.get("model_mobil") != '' else NO_VALUE
        sparepart.group = item.get("group") if item.get("group") != '' else NO_VALUE
        sparepart.assembly_set = item.get("assembly_set") if item.get("assembly_set") != '' else NO_VALUE

        sparepart.prod_date = item.get("prod_date") if item.get("prod_date") != '' else NO_VALUE
        sparepart.part_name = item.get("part_name") if item.get("part_name") != '' else NO_VALUE
        sparepart.part_number = item.get("part_number") if item.get("part_number") != '' else NO_VALUE
        sparepart.price = item.get("price") if item.get("price") != '' else NO_VALUE

        try:

            # save images relation
            try:
                for img in item.get("images", None):
                    img.update({'image_name': sparepart.assembly_set, 'merk': sparepart.merk,
                                'model': sparepart.model, 'group': sparepart.group})
                    image = save_image(session, ImageDaihatsu, img)
                    sparepart.image_id = image.id

            except Exception as e:
                spider.logger.warning("{} - {}".format(type(e), str(e)))

            session.add(sparepart)
            session.commit()

        except IntegrityError as e:
            spider.logger.warning("IntegrityError Exception. {} - {}".format(type(e), str(e)))
            session.rollback()
        except Exception as e:
            spider.logger.error("EXCEPTION... {} - {}".format(type(e), str(e)))
            session.rollback()
            # raise
        finally:
            session.close()

        return item


class DaihatsuPartSearchPipeline(BasePipeline):

    def process_item(self, item, spider):
        """Save spareparts in the database.
        This method is called for every item pipeline component.
        """

        spider.logger.debug("Item type: {}".format(type(item)))

        if os.environ.get('SAVE_AS_JSON') or not isinstance(item, DaihatsuPartSearchItem):
            return item

        session = self.Session()
        sparepart = SparepartDaihatsuPartSearch(**{'job_id': spider._job})

        sparepart.source_url = item.get("source_url") if item.get("source_url") != '' else NO_VALUE
        sparepart.merk = item.get("merk") if item.get("merk") != '' else NO_VALUE
        sparepart.model = item.get("model_mobil") if item.get("model_mobil") != '' else NO_VALUE
        sparepart.models = item.get("models") if item.get("models") != '' else NO_VALUE

        sparepart.prod_date = item.get("prod_date") if item.get("prod_date") != '' else NO_VALUE
        sparepart.part_name = item.get("part_name") if item.get("part_name") != '' else NO_VALUE
        sparepart.part_number = item.get("part_number") if item.get("part_number") != '' else NO_VALUE
        sparepart.spec_code = item.get("spec_code") if item.get("spec_code") != '' else NO_VALUE
        sparepart.description = item.get("description") if item.get("description") != '' else NO_VALUE
        sparepart.ref_no = item.get("ref_no") if item.get("ref_no") != '' else NO_VALUE
        sparepart.qty = item.get("qty") if item.get("qty") != '' else NO_VALUE
        sparepart.rev_ref_fr = item.get("rev_ref_fr") if item.get("rev_ref_fr") != '' else NO_VALUE
        sparepart.rev_ref_to = item.get("rev_ref_to") if item.get("rev_ref_to") != '' else NO_VALUE
        sparepart.weight = item.get("weight") if item.get("weight") != '' else NO_VALUE
        sparepart.substitution = item.get("substitution") if item.get("substitution") != '' else NO_VALUE

        try:
            # save sparepart
            session.add(sparepart)
            session.commit()

        except IntegrityError as e:
            spider.logger.warning("IntegrityError Exception. {} - {}".format(type(e), str(e)))
            session.rollback()
        except Exception as e:
            spider.logger.error("EXCEPTION... {} - {}".format(type(e), str(e)))
            session.rollback()
            # raise
        finally:
            session.close()

        return item


class JsonPipeline(object):
    file = None
    image_dir = None
    exporter = None

    def open_spider(self, spider):
        if not os.environ.get('SAVE_AS_JSON'):
            return False

        if hasattr(spider, '_job'):
            filename = '{}_{}'.format(datetime.datetime.now().strftime("%Y%m%d-%H%M%S"), spider._job)
        else:
            filename = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")

        # create data dir
        path = Path(os.path.dirname(__file__)).parent
        filename_path = "{}/data/{}/{}.json".format(path, spider.name, filename)
        os.makedirs(os.path.dirname(filename_path), exist_ok=True)
        self.image_dir = '{}/images'.format(os.path.dirname(filename_path))
        os.makedirs(self.image_dir, exist_ok=True)

        self.file = open(filename_path, 'wb')
        self.exporter = JsonItemExporter(self.file, encoding='utf-8', ensure_ascii=False)
        self.exporter.start_exporting()

    def close_spider(self, spider):
        if not os.environ.get('SAVE_AS_JSON'):
            return False

        self.exporter.finish_exporting()
        self.file.close()

    def process_item(self, item, spider):
        if not os.environ.get('SAVE_AS_JSON'):
            return item

        # copy images to respective spider directory
        if 'images' in item:
            for img in item.get("images", None):
                img_path = '{}/{}'.format(IMAGES_STORE, img['path'])
                copy2(img_path, '{}/{}'.format(self.image_dir, img_path.split('/')[-1]))

        # export item
        self.exporter.export_item(item)
        return item


class MyImagesPipeline(ImagesPipeline):

    def convert_image(self, image, size=None):
        # if image.format == 'PNG' and image.mode == 'RGBA':
        #     pass
        #     # background = Image.new('RGBA', image.size, (255, 255, 255))
        #     # background.paste(image, image)
        #     # image = background.convert('RGB')
        # elif image.mode == 'P':
        #     pass
        #     image = image.convert("RGBA")
        #     background = Image.new('RGBA', image.size, (255, 255, 255))
        #     background.paste(image, image)
        #     image = background.convert('RGB')
        # elif image.mode != 'RGB':
        #     image = image.convert('RGB')

        if size:
            image = image.copy()
            image.thumbnail(size, Image.ANTIALIAS)

        buf = BytesIO()
        image.save(buf, image.format)

        return image, buf
