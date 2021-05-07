# Scrapy and Twister libs
import scrapy
from scrapy.linkextractors import LinkExtractor

# Other external libs
import logging
import re
import json
import datetime
import requests
import time

from crawling.spiders.base_spider import BaseSpider
from crawling.items import RawResponseItem

import crawling_utils

LARGE_CONTENT_LENGTH = 1e9
HTTP_HEADERS = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.66 Safari/537.36'}

class StaticPageSpider(BaseSpider):
    # nome temporário, que será alterado no __init__
    name = 'temp_name'

    def __init__(self, name: str, *args, **kwargs):
        # nome único do spider, para que não haja conflitos entre coletores
        super(StaticPageSpider, self).__init__(*args, **kwargs)
        self.name = name

    def get_url_info(self, url: str) -> tuple:
        """Retrieves the type of URL content and its size"""
        res = self.request_session.head(url, allow_redirects=True, headers=HTTP_HEADERS)

        content_type = res.headers.get('Content-Type')
        content_lenght = int(res.headers.get('Content-Length', '0'))
        content_disposition = res.headers.get('Content-Disposition', '')

        return url, content_lenght, content_type, content_disposition

    def filter_urls_by_regex(self, urls, pattern):
        """Filter a list of urls according to a regex pattern."""
        def allow(url):
            search_results = re.search(pattern, url)
            return bool(search_results)
        return list(filter(allow, urls))

    def filter_urls_by_content_type(self, urls_info: list, content_types: set) -> list:
        def allow(url_info: tuple):
            url, _, ctype, cdisp = url_info
            guesseds_content_type = self.detect_file_extensions(url, ctype, cdisp)
            common_content_types = content_types.intersection(guesseds_content_type)
            return len(common_content_types) > 0
        return list(filter(allow, urls_info))

    def extract_links(self, response):
        """Filter and return a set with links found in this response."""
        links_extractor = LinkExtractor(
            allow_domains=self.config["link_extractor_allow_domains"],
            tags=self.config["link_extractor_tags"],
            attrs=self.config["link_extractor_attrs"],
            process_value=self.config["link_extractor_process_value"],
        )

        urls_found = set(i.url for i in links_extractor.extract_links(response))

        pattern = self.config["link_extractor_allow_url"]
        if bool(pattern):
            urls_found = self.filter_urls_by_regex(urls_found, pattern)

        if self.config["link_extractor_check_type"]:
            urls_info = list(self.get_url_info(url) for url in urls_found)
            urls_info_filtered = self.filter_urls_by_content_type(urls_info, {'html'})
            urls_found = set(url for url, _, _, _ in urls_info_filtered)
        
        else:
            urls_found = set(urls_found)

        self._logger.info(f"[Spider:  {self.config['source_name']}] +{len(urls_found)} urls found in \"{response.url}\"...")

        return urls_found

    def extract_files(self, response):
        """Filter and return a set with links found in this response."""
        self._logger.info(f"[Spider:  {self.config['source_name']}] Trying to extract urls files in \"{response.url}\"...")

        links_extractor = LinkExtractor(
            allow_domains=self.config["download_files_allow_domains"],
            tags=self.config["download_files_tags"],
            attrs=self.config["download_files_attrs"],
            process_value=self.config["download_files_process_value"],
            deny_extensions=self.config["download_files_deny_extensions"]
        )

        urls_found = set(link.url for link in links_extractor.extract_links(response))

        exclude_html_and_php_regex_pattern = r"(.*\.[a-z]{3,4}$)(.*(?<!\.html)$)(.*(?<!\.php)$)" 
        urls_found = self.filter_urls_by_regex(urls_found, exclude_html_and_php_regex_pattern)

        pattern = self.config["download_files_allow_url"]
        if bool(pattern):
            urls_found = self.filter_urls_by_regex(urls_found, pattern)

        if self.config["download_files_check_type"]:
            urls_info = list(self.get_url_info(url) for url in urls_found)
            urls_info_filtered = self.filter_urls_by_content_type(urls_info, self.download_allowed_extensions)
            urls_found = set(url for url, _, _, _ in urls_info_filtered)

        else:
            urls_found = set(urls_found)

        self._logger.info(f"[Spider:  {self.config['source_name']}] +{len(urls_found)} files found in \"{response.url}\"...")

        return urls_found

    def extract_imgs(self, response):
        url_domain = crawling_utils.get_url_domain(response.url)

        src = []
        for img in response.xpath("//img"):
            img_src = img.xpath('@src').extract_first()
            if img_src[0] == '/':
                img_src = url_domain + img_src[1:]
            src.append(img_src)

        self._logger.info(f"[Spider:  {self.config['source_name']}] +{len(src)} imgs found at page {response.url}")
        
        return set(src)

    def response_to_item(self, response, files_found: set, images_found: set) -> RawResponseItem:
        item = RawResponseItem()

        item['appid'] = response.meta['appid']
        item['crawlid'] = response.meta['crawlid']

        item["url"] = response.request.url
        item["response_url"] = response.url
        item["status_code"] = response.status

        item["body"] = response.body
        item["encoding"] = response.encoding

        item["referer"] = response.meta["attrs"]["referer"]
        item["content_type"] = response.headers['Content-type'].decode()
        item["crawler_id"] = self.config["crawler_id"]
        item["instance_id"] = self.config["instance_id"]
        item["crawled_at_date"] = str(datetime.datetime.today())

        item["files_found"] = files_found
        item["images_found"] = images_found

        return item

    def parse(self, response):
        """
        Parse responses of static pages.
        Will try to follow links if config["explore_links"] is set.
        """
        referer = response.meta["attrs"]["referer"]
        self._logger.info(f"[Spider:  {self.config['source_name']}] Parsing \"{response.url}\" originated from \"{referer}\"")


        if self.config.get("explore_links", False):
            for link in self.extract_links(response):
                yield scrapy.Request(
                    url=link,
                    callback=self.parse,
                    meta={"attrs": {'referer': response.url}},
                    errback=self.errback_httpbin
                )

        files_found = set()
        if self.config.get("download_files", False):
            files_found = self.extract_files(response)

        images_found = set()
        if self.config.get("download_imgs", False):
            images_found = self.extract_imgs(response)

        yield self.response_to_item(response, files_found, images_found)