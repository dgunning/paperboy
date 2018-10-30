import os
import json
import logging
from datetime import datetime
from paperboy.config import Report
from paperboy.config.storage import ReportListResult
from paperboy.storage import ReportStorage
from .base import BaseSQLStorageMixin, justid
from .models.user import UserSQL
from .models.notebook import NotebookSQL
from .models.job import JobSQL
from .models.report import ReportSQL


class ReportSQLStorage(BaseSQLStorageMixin, ReportStorage):
    def status(self, session, *args, **kwargs):
        return {'total': session.query(ReportSQL).count(),
                'notebook': session.query(ReportSQL).filter(ReportSQL.output == 'notebook').count(),
                'pdf': session.query(ReportSQL).filter(ReportSQL.output == 'pdf').count(),
                'html': session.query(ReportSQL).filter(ReportSQL.output == 'html').count(),
                'email': session.query(ReportSQL).filter(ReportSQL.output == 'email').count(),
                'script': session.query(ReportSQL).filter(ReportSQL.output == 'script').count()}

    def form(self):
        return self._form(Report)

    def search(self, user, params, session, *args, **kwargs):
        return self._search(ReportSQL, 'Report', user, params, session, *args, **kwargs)

    def list(self, user, params, session, *args, **kwargs):
        return self._list(ReportSQL, ReportListResult, 'reports', user, params, session, *args, **kwargs)

    def detail(self, user, params, session, *args, **kwargs):
        return self._detail(ReportSQL, user, params, session, *args, **kwargs)

    def store(self, user, params, session, *args, **kwargs):
        name = params.get('name')
        user_sql = session.query(UserSQL).get(int(user.id))

        notebook = params.get('notebook')
        nb_sql = session.query(NotebookSQL).get(int(justid(notebook)))

        job = params.get('job')
        jb_sql = session.query(JobSQL).get(int(justid(job)))

        type = params.get('type') or 'run'
        output = params.get('output') or 'pdf'
        strip_code = params.get('strip_code') == 'yes'
        parameters = params.get('parameters') or '[]'

        created = datetime.now()
        modified = datetime.now()

        rp = ReportSQL(name=name,
                       userId=user.id,
                       user=user_sql,
                       notebookId=notebook,
                       notebook=nb_sql,
                       jobId=job,
                       job=jb_sql,
                       type=type,
                       output=output,
                       strip_code=strip_code,
                       parameters=parameters,
                       created=created,
                       modified=modified)
        session.add(rp)

        # generate id
        session.flush()
        session.refresh(rp)

        store = rp.to_config(self.config).store()
        logging.critical("Storing report {}".format(rp))
        return store

    def generate(self, user, params, session, *args, **kwargs):
        autogen = params.get('autogen') or False
        if autogen:
            parameters_inline = params.get('parameters_inline') or ''
            parameters = params.get('parameters')
            if not parameters_inline and parameters:
                report_params = parameters.file.read()
            else:
                report_params = parameters_inline
            report_params = report_params.split(os.linesep)
            report_params = [json.loads(p) for p in report_params]

            user_sql = session.query(UserSQL).get(int(user.id))

            notebook = params.get('notebook')
            nb_sql = session.query(NotebookSQL).get(int(justid(notebook)))

            job_name = params.get('name')
            job_id = kwargs.get('jobid')
            jb_sql = session.query(JobSQL).get(int(justid(job_id)))

            type = params.get('type') or 'run'
            output = params.get('output') or 'notebook'
            strip_code = params.get('code') or 'no'

            created = datetime.now()
            modified = datetime.now()

            for i, param in enumerate(report_params):
                name = job_name + '-Report-' + str(i)
                param = json.dumps(param)
                rp = ReportSQL(name=name,
                               userId=user.id,
                               user=user_sql,
                               notebookId=notebook,
                               notebook=nb_sql,
                               jobId=job_id,
                               job=jb_sql,
                               type=type,
                               output=output,
                               strip_code=strip_code,
                               parameters=param,
                               created=created,
                               modified=modified)
                session.add(rp)
            session.flush()

            return len(report_params)
        return False
