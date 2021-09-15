# coding: utf-8
import os
import pymysql.cursors
import pymysqlpool

from pytz import timezone
from datetime import date, datetime, timedelta
from logging import getLogger, root

logger = getLogger("asr")

SERVER_URL = os.getenv("SERVER_URL")
DB = os.getenv("DB")
USER_NAME = os.getenv("DB_USER_NAME")
PASSWORD = os.getenv("DB_USER_PASSWORD")

config = {
    'host': SERVER_URL,
    'user': USER_NAME,
    'password': PASSWORD,
    'database': DB,
    'autocommit': True}
pool = pymysqlpool.ConnectionPool(size=10, name='pool', **config)


def get_db_connection():
    return pool.get_connection(timeout=10)


def save(sqlstr):
    with get_db_connection() as c:
        cursor = c.connection.cursor()
        cursor.execute(sqlstr)


def load():
    with get_db_connection() as c:
        cursor = c.connection.cursor(pymysql.cursors.DictCursor)
        cursor.execute("select * from jobs;")
        result = cursor.fetchall()
        return result


def create(dict):
    # convert jst
    start_datetime= dict['start_datetime'].astimezone(timezone('Asia/Tokyo'))
    end_datetime= dict['end_datetime'].astimezone(timezone('Asia/Tokyo'))
    if dict['report_back_duration'] >= timedelta(days=1):
        report_back_duration = f"{dict['report_back_duration'].days * 24}:00:00"
    else:
        report_back_duration = dict['report_back_duration']


    sql = ('''
      INSERT INTO jobs(
        report_request_id,
        report_specifier_id,
        r_ids,
        report_back_duration,
        granularity,
        report_interval,
        start_datetime,
        end_datetime,
        created_at
      )
      VALUES(
        '{report_request_id}',
        '{report_specifier_id}',
        '{r_ids}',
        '{report_back_duration}',
        '{granularity}',
        '{report_interval}',
        '{start_datetime}',
        '{end_datetime}',
        '{created_at}'
      )
      ;
    ''').format(
        report_request_id=str(dict['report_request_id']),
        report_specifier_id=dict['report_specifier_id'],
        r_ids=dict['r_ids'],
        report_back_duration=report_back_duration,
        granularity=dict['granularity'],
        report_interval=dict['report_interval']['duration'],
        start_datetime=start_datetime.strftime('%Y-%m-%d %H:%M:%S'),
        end_datetime=end_datetime.strftime('%Y-%m-%d %H:%M:%S'),
        created_at=datetime.now())

    save(sql)


def job_by_resource_id(report_specifier_id, r_ids):
    with get_db_connection() as c:
        cursor = c.connection.cursor(pymysql.cursors.DictCursor)
        cursor.execute(
            f"select * from jobs where report_specifier_id = '{report_specifier_id}' and r_ids='{r_ids}';")
        result = cursor.fetchone()
        return result


def delete(report_specifier_id, r_ids):
    result = job_by_resource_id(report_specifier_id, r_ids)
    if result:
        save(f"DELETE from jobs where id = '{result['id']}';")


if __name__ == "__main__":
    dict = {
        "report_request_id": "report_request_id",
        "report_specifier_id": "report_specifier_id",
        "r_ids": "101,103",
        'report_back_duration': "PT0H",
        'report_interval': "PT1M",
        'granularity': "PT1M",
        "start_datetime": datetime.now(),
        "end_datetime": datetime.now(),
        "created_at": datetime.now()
    }
    delete("report_specifier_id", "101,103")
    row = create(dict)
    print(load())
