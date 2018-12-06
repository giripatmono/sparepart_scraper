from sparepart.models import db_connect, create_table


engine = db_connect()
create_table(engine)
