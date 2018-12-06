import datetime
from sqlalchemy import create_engine, Column, ForeignKey, Sequence
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import (Integer, String, BLOB, Text, DateTime, CLOB, TEXT, TIMESTAMP)

from scrapy.utils.project import get_project_settings

DeclarativeBase = declarative_base()


def db_connect():
    """
    Performs database connection using database settings from settings.py.
    Returns sqlalchemy engine instance
    """
    return create_engine(get_project_settings().get("CONNECTION_STRING"), echo=True)


def create_table(engine):
    """Create new table from declarative base"""
    DeclarativeBase.metadata.create_all(engine)


class ImageMixin(object):
    checksum = Column('checksum', String(32))
    url = Column('url', String(255))
    data = Column('data', BLOB(length=2097152))
    image_name = Column('image_name', String(255))
    merk = Column('merk', String(50))
    model = Column('model', String(50))
    type = Column('type', String(50))


class JobMixin(object):
    job_id = Column('job_id', String(32), primary_key=True)


class SparepartIsuzu(JobMixin, DeclarativeBase):
    __tablename__ = "scraping_sparepart_isuzu"

    id = Column(Integer, Sequence('scraping_sparepart_isuzu_id_seq'), primary_key=True)
    merk = Column('merk', String(50))
    model_mobil = Column('model_mobil', String(50))
    tipe_mobil = Column('tipe_mobil', String(50))
    main_group = Column('main_group', String(100))
    assembly_set = Column('assembly_set', String(255))
    key = Column('key_', String(10))
    part_number = Column('part_number', String(255))
    itc = Column('itc', String(10))
    description = Column('description', String(255))
    qty = Column('qty', String(10))
    app_date = Column('app_date', String(10))
    lr = Column('lr', String(10))
    model = Column('model', String(100))
    remarks = Column('remarks', String(255))
    source_url = Column('source_url', String(255))
    images = relationship("ImageLinkIsuzu", back_populates="sparepart")

    def __repr__(self):
        return "<part_number='%s', description='%s'>" % (self.part_number, self.description)


class ImageLinkIsuzu(DeclarativeBase):
    __tablename__ = 'scraping_image_link_isuzu'

    part_id = Column(Integer, ForeignKey('scraping_sparepart_isuzu.id'), primary_key=True)
    image_id = Column(Integer, ForeignKey('scraping_image_isuzu.id'), primary_key=True)
    image = relationship("ImageIsuzu", back_populates="spareparts")
    sparepart = relationship("SparepartIsuzu", back_populates="images")


class ImageIsuzu(ImageMixin, DeclarativeBase):
    __tablename__ = 'scraping_image_isuzu'

    id = Column(Integer,  Sequence('scraping_image_isuzu_id_seq'), primary_key=True)
    spareparts = relationship("ImageLinkIsuzu", back_populates="image")


class SparepartParts(JobMixin, DeclarativeBase):
    __tablename__ = "scraping_sparepart_parts"

    id = Column(Integer, Sequence('scraping_sparepart_parts_id_seq'), primary_key=True)
    source_url = Column('source_url', String(255))
    merk = Column('merk', String(50))
    model_year = Column('model_year', String(25))
    model_mobil = Column('model_mobil', String(50))
    submodel = Column('submodel', String(50))
    engine = Column('engine', String(50))
    section = Column('section', String(100))
    group = Column('group', String(100))
    subgroup = Column('subgroup', String(100))
    part_name = Column('part_name', String(255))
    part_number = Column('part_number', String(255))
    price = Column('price', String(100))
    description = Column('description', String(255))
    # images = relationship("ImageLinkParts", back_populates="sparepart")
    lookup_no = Column('lookup_no', String(50))
    image_id = Column(Integer, nullable=True)

    def __repr__(self):
        return "<part_number='%s', description='%s'>" % (self.part_number, self.part_name)


class ImageParts(ImageMixin, DeclarativeBase):
    __tablename__ = 'scraping_image_parts'

    id = Column(Integer,  Sequence('scraping_image_parts_id_seq'), primary_key=True)
    # spareparts = relationship("ImageLinkParts", back_populates="image")


class SparepartMegazip(JobMixin, DeclarativeBase):
    __tablename__ = "scraping_sparepart_megazip"

    id = Column(Integer, Sequence('scraping_sparepart_megazip_id_seq'), primary_key=True)
    image_id = Column(Integer, ForeignKey('scraping_image_megazip.id'), nullable=True)
    source_url = Column('source_url', String(255))
    merk = Column('merk', String(50))
    varian = Column('varian', String(25))
    model = Column('model', String(50))
    vehicle_model = Column('vehicle_model', String(50))
    model_mark = Column('model_mark', String(50))
    model_year = Column('model_year', String(25))
    frame = Column('frame', String(50))
    grade = Column('grade', String(50))
    body = Column('body', String(50))
    engine = Column('engine', String(50))
    transmission = Column('transmission', String(50))
    destination = Column('destination', String(50))
    from_date = Column('from_date', String(10))
    to_date = Column('to_date', String(10))
    gear_shift_type = Column('gear_shift_type', String(50))
    transmission = Column('transmission', String(50))
    seating_capacity = Column('seating_capacity', String(50))
    fuel_induction = Column('fuel_induction', String(50))
    drive = Column('drive', String(50))
    door_number = Column('door_number', String(50))
    note = Column('note', String(50))
    assembly_group = Column('assembly_group', String(255))
    assembly_set = Column('assembly_set', String(255))
    reference = Column('reference', String(25))
    part_name = Column('part_name', String(255))
    part_number = Column('part_number', String(255))
    replacement_for = Column('replacement_for', String(255))
    price = Column('price', String(255))
    description = Column('description', String(255))
    image = relationship("ImageMegazip", back_populates="spareparts")

    def __repr__(self):
        return "<part_number='%s', description='%s'>" % (self.part_number, self.part_name)

class ImageMegazip(ImageMixin, DeclarativeBase):
    __tablename__ = 'scraping_image_megazip'

    id = Column(Integer,  Sequence('scraping_image_megazip_id_seq'), primary_key=True)
    spareparts = relationship("SparepartMegazip", back_populates="image")


class SparepartSuzuki(JobMixin, DeclarativeBase):
    __tablename__ = "scraping_sparepart_suzuki"

    id = Column(Integer, primary_key=True, autoincrement=False)
    image_id = Column(Integer, nullable=True)
    source_url = Column('source_url', String(255))
    merk = Column('merk', String(50))
    model = Column('model', String(50))
    group = Column('group', String(50))
    assembly_set = Column('assembly_set', String(255))
    part_name = Column('part_name', String(255))
    part_number = Column('part_number', String(255))
    substitution_part_number = Column('substitution_part_number', String(100))
    qty = Column('qty', String(10))
    price = Column('price', String(255))
    remarks = Column('remarks', String(255))
    tag_no = Column('tag_no', String(255))
    # image = relationship("ImageSuzuki", back_populates="spareparts")

    def __repr__(self):
        return "<part_number='%s', description='%s'>" % (self.part_number, self.part_name)


class ImageSuzuki(ImageMixin, DeclarativeBase):
    __tablename__ = 'scraping_image_suzuki'

    id = Column(Integer, primary_key=True, autoincrement=False)
    group = Column('group', String(50))
    # spareparts = relationship("SparepartSuzuki", back_populates="image")


class SparepartDaihatsu(JobMixin, DeclarativeBase):
    __tablename__ = "scraping_sparepart_daihatsu"

    id = Column(Integer, Sequence('scraping_sparepart_daihatsu_id_seq'), primary_key=True)
    image_id = Column(Integer, ForeignKey('scraping_image_daihatsu.id'), nullable=True)
    source_url = Column('source_url', String(255))
    merk = Column('merk', String(50))
    model = Column('model', String(50))
    group = Column('group', String(50))
    assembly_set = Column('assembly_set', String(255))
    prod_date = Column('prod_date', String(100))
    part_name = Column('part_name', String(255))
    part_number = Column('part_number', String(255))
    price = Column('price', String(255))
    image = relationship("ImageDaihatsu", back_populates="spareparts")

    def __repr__(self):
        return "<part_number='%s', description='%s'>" % (self.part_number, self.part_name)


class ImageDaihatsu(ImageMixin, DeclarativeBase):
    __tablename__ = 'scraping_image_daihatsu'

    id = Column(Integer, Sequence('scraping_image_daihatsu_id_seq'), primary_key=True)
    group = Column('group', String(50))
    spareparts = relationship("SparepartDaihatsu", back_populates="image")


class SparepartDaihatsuPartSearch(JobMixin, DeclarativeBase):
    __tablename__ = "scraping_daihatsu_partsearch"

    id = Column(Integer, Sequence('scraping_daihatsu_partsearch_id_seq'), primary_key=True)
    source_url = Column('source_url', String(255))
    merk = Column('merk', String(50))
    model = Column('model', String(50))
    models = Column('models', String(100))
    prod_date = Column('prod_date', String(100))
    part_name = Column('part_name', String(255))
    part_number = Column('part_number', String(255))
    spec_code = Column('spec_code', String(100))
    description = Column('description', String(255))
    ref_no = Column('ref_no', String(255))
    qty = Column('qty', String(10))
    rev_ref_fr = Column('rev_ref_fr', String(50))
    rev_ref_to = Column('rev_ref_to', String(50))
    weight = Column('weight', String(50))
    substitution = Column('substitution', String(255))


class ScrapingJob(DeclarativeBase):
    __tablename__ = 'scraping_job'

    id = Column(String(32), primary_key=True)
    spider = Column('spider', String(50))
    input_param = Column('input_param', String(1000))
    status = Column('status', String(25))
    reason = Column('reason', String(25))
    start = Column('start', TIMESTAMP, nullable=True)
    finish = Column('finish', TIMESTAMP, nullable=True)
    log = Column('log', Text(length=1073741824), nullable=True)
    jobdir = Column('jobdir', String(100), nullable=True)

