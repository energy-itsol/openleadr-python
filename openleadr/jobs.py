from dataclasses import dataclass, asdict
from functools import partial
import time
from datetime import datetime, timezone, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from openleadr import db
from openleadr import utils
import logging

logger = logging.getLogger('openleadr')


class Job:
    def __init__(self, callback):
        self.scheduler = AsyncIOScheduler()
        self.callback = callback

    def load(self, scheduler_id=None):
        results = db.load()
        for result in results:
            self._add(result)

    def _add(self, dataset):
        scheduler_id = dataset['id']
        date_start_on = dataset['start_datetime']
        date_start_off = dataset['end_datetime']
        duration = dataset['report_back_duration']

        scheduler_type = 'cron'
        config = utils.cron_config(utils.parse_duration(duration))
        args_on = dict(config, start_date=date_start_on, end_date=date_start_off)

        cb = partial(
            self.callback,
            report_request_id=dataset['report_request_id'])

        self.scheduler.add_job(cb, scheduler_type,
                               id='%son' % scheduler_id, **args_on)
        logger.info('add job' + str(args_on))

    def add(self, dataset):
        db.create(dataset)
        row = db.job_by_resource_id(dataset['report_specifier_id'], dataset['r_ids'])
        self._add(row)

    def reload(self, scheduler_id):
        self.delete_job(scheduler_id)
        self.load(int(scheduler_id))
        logger.info('Reload       ID = %s' % scheduler_id)

    def delete_job(self, scheduler_id):
        self.scheduler.remove_job(str(scheduler_id) + 'on')
        logger.info('Delete Job   ID = %s' % scheduler_id)
        if isinstance(scheduler_id, int):
            scheduler_id = int(scheduler_id)
            db.delete(scheduler_id)
            logger.info('Delete DB    ID = %s' % scheduler_id)

    def delete_db(self, scheduler_id):
        if isinstance(scheduler_id, int):
            scheduler_id = int(scheduler_id)
            db.delete(scheduler_id)
            logger.info('Delete DB    ID = %s' % scheduler_id)

    async def restart(self):
        logger.info('stopping for restart')
        self.scheduler.shutdown(0)
        self.scheduler = AsyncIOScheduler()
        self.scheduler.start()
        self.load()
        logger.info('neu initialisiert')

    async def start(self):
        self.scheduler.start()
        self.load()
        logger.info('start')


if __name__ == "__main__":
    async def sample(scheduler_id):
        logger.info(scheduler_id)
        logger.info(str(datetime.now()).split(".")[0])

    try:
        f = sample
        job = Job(f)
        
        import asyncio
        loop = asyncio.get_event_loop()
        loop.create_task(job.restart())
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logger.error(e)
