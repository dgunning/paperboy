import logging
import math
from sqlalchemy import or_
from paperboy.config import ListResult


class BaseSQLStorageMixin(object):
    def _form(self, ConfigCls):
        return ConfigCls(self.config).form()

    def _search(self, SqlCls, ClsName, user, params, session, *args, **kwargs):
        name = params.get('name', '')
        count = int(params.get('count', 10))
        if name is None or name == '':
            return []
        nbs = session.query(SqlCls) \
            .filter(SqlCls.name.like(lookfor(name))) \
            .filter(SqlCls.userId == int(user.id) or
                    (hasattr(SqlCls, 'privacy') and SqlCls.privacy == 'public')) \
            .limit(count)

        return [{'id': ClsName + '-' + str(nb.id), 'name': nb.name} for nb in nbs]

    def _list(self, SqlCls, setter, user, params, session, *args, **kwargs):
        base = session.query(SqlCls) \
                .filter(or_(SqlCls.userId.like((user.id)),
                        (hasattr(SqlCls, 'privacy') and SqlCls.privacy == 'public'))) \

        page = int(params.get('page', 1))
        nbs = base[25*(page-1):25*page]

        result = ListResult()
        result.total = base.count()
        result.count = len(nbs)
        result.page = page
        result.pages = math.ceil(result.total/25) if result.count > 0 else 1

        logging.critical('list : {}, result : {} - {}'.format(SqlCls, result.total, len(nbs)))

        result.results = [x.to_config(self.config) for x in nbs]
        return result.to_json()

    def _detail(self, SqlCls, user, params, session, *args, **kwargs):
        id = justid(params.get('id') or -1)
        try:
            id = int(id)
        except ValueError:
            return {}

        if id < 0:
            return {}

        nb_sql = session.query(SqlCls).get(id)  # FIXME permission?

        logging.critical('detail : {}, result : {}'.format(id, nb_sql))

        if nb_sql:
            return nb_sql.to_config(self.config).edit()
        return {}


def lookfor(s):
    if '*' in s or '_' in s:
        return s.replace('_', '__')\
                .replace('*', '%')\
                .replace('?', '_')
    return '%{0}%'.format(s)


def justid(id):
    if isinstance(id, int):
        return id
    if '-' in id:
        return id.split('-', 1)[-1]
    return id
