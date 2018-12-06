# -*- coding: utf-8 -*-
# some useful helper function
import requests
import logging
from lxml.html import fromstring
from .models import ImageMegazip

logger = logging.getLogger('helpers')
logging.addLevelName(35, "CRAWL_INFO")

def get_or_create(session, img_cls, **kwargs):
    """Get or Create an SQLAlchemy model instance.
    """
    instance = session.query(img_cls).filter_by(checksum=kwargs['checksum'], url=kwargs['url']).first()
    if instance and 'force_create_new' not in kwargs:
        return instance
    else:
        data = {'checksum': kwargs['checksum'], 'image_name': kwargs['image_name'],
                'url': kwargs['url'],
                'data': read_file(kwargs['full_path']),
                'merk': kwargs['merk'], 'model': kwargs['model'],
                'type': kwargs.get('type', None)}
        if 'id' in kwargs:
            data['id'] = int(kwargs['id'])
        if 'group' in kwargs:
            data['group'] = kwargs['group']
        if 'job_id' in kwargs:
            data['job_id'] = kwargs['job_id']
        instance = img_cls(**data)
        session.add(instance)
        session.flush()
        return instance


def read_file(filename):
    with open(filename, 'rb') as f:
        file = f.read()
    return file


def remove_non_ascii(text):
    if not text:
        return
    return ''.join(i for i in text if ord(i) < 128)
