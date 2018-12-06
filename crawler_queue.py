import os
import sqlite3
import json
from datetime import datetime

SPIDER_LIST = ['isuzu', 'daihatsu', 'suzuki', 'megazip', 'parts.com']


class CrawlerQueue(object):
    """
    Simple FIFO Queue using SQLite as persistent storage
    """

    _sql_create = (
        'CREATE TABLE IF NOT EXISTS `queue_{}` '
        '(id INTEGER PRIMARY KEY AUTOINCREMENT, input_param TEXT, date_added TEXT)'
    )
    _sql_size = 'SELECT COUNT(*) FROM `queue_{}`'
    _sql_push = 'INSERT INTO `queue_{}` (input_param, date_added) VALUES (?, ?)'
    _sql_pop = 'SELECT id, input_param, date_added FROM `queue_{}` ORDER BY id LIMIT 1'
    _sql_del = 'DELETE FROM `queue_{}` WHERE id = ?'

    def __init__(self, path='dbs/crawler_queue.db', spiders=SPIDER_LIST):
        self._path = os.path.abspath(path)
        self._db = sqlite3.Connection(self._path, timeout=60)
        self._db.text_factory = bytes
        with self._db as conn:
            for spider in spiders:
                conn.execute(self._sql_create.format(spider))

    def push(self, spider, input_param='{}'):
        with self._db as conn:
            if not isinstance(input_param, str):
                input_param = json.dumps(input_param)

            conn.execute(self._sql_push.format(spider), (input_param, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

    def pop(self, spider):
        with self._db as conn:
            for id_, input_param, date_added in conn.execute(self._sql_pop.format(spider)):
                conn.execute(self._sql_del.format(spider), (id_,))
                return input_param.decode(), date_added.decode()

    def delete(self, spider, id_):
        with self._db as conn:
            cur = conn.cursor()
            cur.execute(self._sql_del.format(spider), (id_,))
            return cur.rowcount

    def count(self, spider):
        with self._db as conn:
            return self.__len__(spider)

    def get_all_queue(self):
        queue_select_query = 'SELECT *, "queue_{}" as spider FROM `queue_{}`'
        query = '\n union \n'.join([queue_select_query.format(spider, spider) for spider in SPIDER_LIST])
        query += '\n ORDER BY id'
        # print('query..', query)
        with self._db as conn:
            result = {spider: [] for spider in SPIDER_LIST}
            for id_, input_param, date_added, spider in conn.execute(query).fetchall():
                # print(id_, input_param.decode(), date_added.decode(), spider.decode())
                result[spider.decode().split('_')[1]].append((id_, input_param.decode(), date_added.decode()))
            # print('result', result)
            return result

    def close(self, spider):
        size = self.__len__(spider)
        self._db.close()

    def __len__(self, spider):
        with self._db as conn:
            return next(conn.execute(self._sql_size.format(spider)))[0]

