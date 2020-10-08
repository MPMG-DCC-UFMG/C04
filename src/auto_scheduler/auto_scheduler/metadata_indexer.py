import os
import ujson
from datetime import datetime, timedelta

from bs4 import BeautifulSoup

from auto_scheduler.utils import hashfy
from auto_scheduler.auto_scheduler import AutoScheduler
from auto_scheduler import settings


class MetadataIndexer:
    '''Class responsible for persisting tracking metadata and calling the estimator when it has enough data to generate an estimate

    '''
    @staticmethod
    def persist(crawl: dict):
        '''Responsible for persisting some metadata of crawls made by Scrapy Cluster

        Args:
            crawl: Dictionary containing a crawl made by SC

        '''
        url = crawl['url']
        body = crawl['body']
        timestamp = datetime.strptime(
            crawl['timestamp'], '%Y-%m-%dT%H:%M:%S.%f').timestamp()

        soup = BeautifulSoup(body, 'html.parser')

        crawlid = hashfy(url)
        crawl_hash = hashfy(soup.html.text)

        group_visit = 0
        num_visits = 0

        historic_filename = settings.HISTORIC_FOLDER + crawlid
        if os.path.exists(historic_filename):
            with open(historic_filename) as f:
                crawl_historic = ujson.loads(f.read())

                # turns the visit dictionary keys to integers
                visit_historic = dict((int(item[0]), item[1]) for item in crawl_historic['visits'].items())
                group_visit = sorted(visit_historic.keys())[-1]

                crawl_historic['visits'] = visit_historic

                num_visits = len(crawl_historic['visits'][group_visit])
                if num_visits == settings.NUMBER_VISITS_TO_GENERATE_ESTIMATE:
                    group_visit += 1

        else:
            crawl_historic = {
                'visits': dict(),
                'last_visit_timestamp': timestamp,
                'estimated_frequency_changes': None
            }

        if group_visit not in crawl_historic['visits']:
            crawl_historic['visits'][group_visit] = list()

        historic = {
            'timestamp': timestamp,
            'crawl_hash': crawl_hash,
            'crawl_url': url
        }

        crawl_historic['visits'][group_visit].append(historic)
        num_visits += 1

        if num_visits == settings.NUMBER_VISITS_TO_GENERATE_ESTIMATE:
            estimated_frequency_changes = AutoScheduler.update_crawl_frequency(
                crawlid, crawl_historic['visits'][group_visit])
            crawl_historic['estimated_frequency_changes'] = estimated_frequency_changes

        with open(historic_filename, 'w') as f:
            f.write(ujson.dumps(crawl_historic, indent=4))
