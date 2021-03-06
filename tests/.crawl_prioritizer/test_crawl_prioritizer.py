import unittest
import time

from datetime import datetime, timedelta

import ujson
import psycopg2
from psycopg2.extensions import cursor

from crawl_prioritizer import CrawlPrioritizer
from crawl_prioritizer import hashfy, get_url_domain
from crawl_prioritizer import settings


class TestCrawlPrioritizer(unittest.TestCase):
    def setUp(self):
        '''Configure connection with PostgreSQL
        '''

        # The database created in other module, in:
        # https://github.com/MPMG-DCC-UFMG/C04/blob/master/src/auto_scheduler/auto_scheduler/database_handler.py 
        # but to run the tests independently, they are also created here, if necessary.
        self._create_db_if_not_exists()

        self.conn = psycopg2.connect(
            # Name of the database that saved the crawl metadata,
            # see https://github.com/MPMG-DCC-UFMG/C04/issues/238 for more details
            dbname='auto_scheduler',
            user=settings.POSTGRESQL_USER,
            password=settings.POSTGRESQL_PASSWORD,
            host=settings.POSTGRESQL_HOST,
            port=settings.POSTGRESQL_PORT)

        self.conn.set_session(autocommit=True)
        self.cursor = self.conn.cursor()
        
        # For the same reason as creating the database above,
        # the table is created here, if necessary.
        self._create_table_if_not_exists()
    
    def _db_exists(self, cur: cursor) -> bool:
        '''Checks if a database already exists.

        Args:
            cur: Cursor for SQL queries.
            db_name: Database name.

        Returns:
            True, if the database exists, False otherwise.

        '''

        sql_query = 'SELECT datname FROM pg_catalog.pg_database WHERE datname = \'auto_scheduler\';'
        cur.execute(sql_query)

        return cur.fetchone() is not None

    def _create_db_if_not_exists(self):
        '''Creates the database, if it does not exist, since PostgreSQL does not have "CREATE DATABASE IF NOT EXISTS"
        '''

        conn = psycopg2.connect(user=settings.POSTGRESQL_USER, password=settings.POSTGRESQL_PASSWORD,
                                host=settings.POSTGRESQL_HOST, port=settings.POSTGRESQL_PORT)
        conn.set_session(autocommit=True)

        cur = conn.cursor()

        if not self._db_exists(cur):
            sql_query = 'CREATE DATABASE auto_scheduler;'
            cur.execute(sql_query)

        cur.close()
        conn.close()

    def _create_table_if_not_exists(self):
        '''Creates the table to save the crawl history, if it does not exist.
        '''

        sql_query = 'CREATE TABLE IF NOT EXISTS CRAWL_HISTORIC' \
                    '(CRAWLID CHAR(32) PRIMARY KEY NOT NULL, ' \
                    'CRAWL_HISTORIC JSONB);'

        self.cursor.execute(sql_query)
    
    def _delete_crawl_historic_in_database(self, crawlid: str):
        '''Deletes a crawl historic in the database
        '''

        sql_query = 'DELETE FROM CRAWL_HISTORIC WHERE CRAWLID = %s'
        data = (crawlid,)

        self.cursor.execute(sql_query, data)

    def _insert_crawl_historic_in_database(self, crawlid: str, crawl_historic: dict):
        '''Insert a crawl historic in the database
        '''
        value = ujson.dumps(crawl_historic)

        sql_query = 'INSERT INTO CRAWL_HISTORIC (CRAWLID, CRAWL_HISTORIC) VALUES (%s, %s);'
        data = (crawlid, value)

        self.cursor.execute(sql_query, data)


    def test_get_crawl_statistics(self):
        '''Checks whether retrieving statistics about a crawl in the database is correct.
        '''

        crawl_priotizer = CrawlPrioritizer()
        crawlid = 'some_unique_crawlid'

        self._delete_crawl_historic_in_database(crawlid)

        now = datetime.now()
        curr_timestamp = now.timestamp()

        simple_crawl_historic = {
            'last_visit_timestamp': curr_timestamp,
            'estimated_frequency_changes': 345
        }

        self._insert_crawl_historic_in_database(crawlid, simple_crawl_historic)

        time_since_last_crawl, change_frequency = crawl_priotizer.get_crawl_statistics(crawlid)

        last_timestamp = curr_timestamp
        curr_timestamp = datetime.now().timestamp()

        self._delete_crawl_historic_in_database(crawlid)

        self.assertTrue(time_since_last_crawl > 0)
        self.assertTrue(time_since_last_crawl <= (curr_timestamp - last_timestamp))
        self.assertTrue(change_frequency == 345)

    def test_get_crawl_statistics_without_estimate_frequency_change(self):
        '''Checks whether the retrieval of statistics about a crawl in the database is correct.
        '''

        crawl_priotizer = CrawlPrioritizer()
        crawlid = 'some_unique_crawlid_2'

        self._delete_crawl_historic_in_database(crawlid)

        now = datetime.now()

        visits = {"0": list()}
        visit_group = visits["0"]

        for _ in range(3):
            visit_group.append({
                'timestamp': now.timestamp()
            })

            now -= timedelta(seconds=15)

        simple_crawl_historic = {
            'visits': visits,
            'last_visit_timestamp': visit_group[0]['timestamp'],
            'estimated_frequency_changes': None
        }

        self._insert_crawl_historic_in_database(crawlid, simple_crawl_historic)
        _, change_frequency = crawl_priotizer.get_crawl_statistics(crawlid)

        self._delete_crawl_historic_in_database(crawlid)

        self.assertTrue(change_frequency is not None)

    def test_get_expanded_priority_equation(self):
        '''Checks whether the expansion of the priority equation with the current values is correct.
        '''

        settings.PRIORITY_EQUATION = 'crawl_priority = domain_prio + time_since_last_crawl / change_frequency'

        crawl_priotizer = CrawlPrioritizer()
        expr = crawl_priotizer.get_expanded_priority_equation(3, 4, 5)

        self.assertTrue(expr == 'crawl_priority = 3 + 4 / 5')

    def test_calculate_priority(self):
        '''Checks whether the priority calculation is correct using the priority equation.
        '''

        crawl_req = {'url': 'wwww.some_url.com/content/1'}

        crawlid = hashfy(crawl_req['url'])
        crawl_domain = get_url_domain(crawl_req['url'])

        self._delete_crawl_historic_in_database(crawlid)

        settings.PRIORITY_EQUATION = 'crawl_priority = domain_prio + time_since_last_crawl * 0 + change_frequency'
        settings.DOMAIN_PRIORITY[crawl_domain] = 11

        crawl_priotizer = CrawlPrioritizer()

        curr_timestamp = datetime.now().timestamp()
        simple_crawl_historic = {
            'last_visit_timestamp': curr_timestamp,
            'estimated_frequency_changes': 3
        }

        self._insert_crawl_historic_in_database(crawlid, simple_crawl_historic)

        crawl_priority = crawl_priotizer.calculate_priority(crawl_req)

        self._delete_crawl_historic_in_database(crawlid)
        self.assertTrue(crawl_priority == 14)

    def test_calculate_priority_never_made_crawl(self):
        '''Checks whether the priority set for a crawl never made is being applied correctly.
        '''

        crawl_req = {'url': 'wwww.some_another_url.com/content_never_seen/1'}

        crawlid = hashfy(crawl_req['url'])
        crawl_domain = get_url_domain(crawl_req['url'])

        self._delete_crawl_historic_in_database(crawlid)

        settings.PRIORITY_NEVER_MADE_CRAWL = 37
        crawl_priotizer = CrawlPrioritizer()

        crawl_priority = crawl_priotizer.calculate_priority(crawl_req)

        self.assertTrue(crawl_priority == 37)
