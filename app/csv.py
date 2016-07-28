from cStringIO import StringIO
import unicodecsv

def create_csv(q, cls):
    """
    :param q: SQLAlchemy Query object
    :param cls: class type for query results
    :return: csv formatted StringIO
    """
    f = StringIO()
    c = unicodecsv.writer(f, encoding='utf-8')

    c.writerow(cls.get_column_names())
    for i in q.all():
        c.writerow(i.get_row())

    return f.getvalue()