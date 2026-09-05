# HEADERS
import base64, gzip, io, string
import sys, os, random, socket, re, cloudscraper, json
from datetime import datetime, date
from urllib.parse import urlparse

from django.shortcuts import render
from django.conf import settings

from project.machine.submodels.serpmodels import DKeyword, DGroups
from project.machine.submodels.contentgapmodels import CGADomain, CGADomainCategory, CGADomainCategoryUrls, CGADomainUrl, CGASearch, CGASearchCategory, CGASearchMatch
from project.machine import automation_common as _at__common_
from project.machine.contentgap.cga_serializers import *

from project.machine.contentgap import cga_category
from rest_framework.decorators import api_view
from django.http import HttpResponse, JsonResponse

from bs4 import BeautifulSoup
from urllib.parse import urljoin

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from fake_useragent import UserAgent
import requests

# Residential proxies, comma-separated in CONTENTGAP_PROXIES. An empty list
# means direct requests -- correct for a self-hoster with no proxy pool.
PROXY_LIST = [p for p in os.environ.get("CONTENTGAP_PROXIES", "").split(",") if p.strip()]


def cg_user_agents():
    _DEFAULT__HEADERS_ = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"

    try:
        ua = UserAgent(browsers=["chrome", "firefox", "safari"], platforms="pc")
        return ua.random

    except Exception as e:
        pass

    return _DEFAULT__HEADERS_


def cg_request_headers():
    _headers_ = {"User-Agent": str(cg_user_agents()), "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8", "Accept-Encoding": "gzip, deflate, br", "Accept-Language": "en-US,en;q=0.5", "Connection": "keep-alive"}

    return _headers_


def cg_domain_return(domain):
    if domain:
        return domain if domain.endswith("/") else str(domain) + "/"

    return None


def cg_sitemap_slugs(domain):
    sitemap_list = []
    if not domain:
        return sitemap_list

    suffixes = [
        "sitemap.xml",
        "sitemap-index.xml",
        "sitemap_index.xml",
        "sitemap",
        "sitemap/sitemap.xml",
    ]

    for suffix in suffixes:
        sitemap_list.append(f"{domain}{suffix}")

    return sitemap_list


def create_scraper():
    proxy_address = random.choice(PROXY_LIST)
    scraper = cloudscraper.create_scraper()
    scraper.headers.update(cg_request_headers())
    scraper.proxies = proxy_address
    return scraper


def cg_fetch_sitemap(scraper, url):
    try:
        response = scraper.get(url, timeout=10)
        return response.status_code, response.content
    except Exception as e:
        pass
    return 0, None


def cg_scraping_dog_sitemap(url):
    try:
        response = requests.get(
            "https://api.scrapingdog.com/scrape",
            params={
                "api_key": os.environ.get("SCRAPINGDOG_API_KEY", ""),
                "url": url,
                "dynamic": "false",
            },
        )
        return response.status_code, response.text
    except Exception as e:
        pass
    return 0, None


def extract_xml_links_from_robots(url):
    try:
        response = requests.get(
            "https://api.scrapingdog.com/scrape",
            params={
                "api_key": os.environ.get("SCRAPINGDOG_API_KEY", ""),
                "url": url,
                "dynamic": "false",
            },
        )

        # response = requests.get(url, timeout=30)  # Timeout after 5 seconds
        response.raise_for_status()  # Raise an error for bad status codes
        robots_txt = response.text

        # Regex to find all URLs ending in .xml
        xml_links = re.findall(r"https?://[^\s]+\.xml", robots_txt)
        return xml_links

    except Exception as e:
        print(f"Error while fetching or parsing robots.txt: {e}")
        return []


def cg_parse_xml_sitemap(content, current_sitemap):
    try:
        urls = []
        nested_sitemaps = []

        if content and current_sitemap:
            netloc = extract_domain(current_sitemap)
            soup = BeautifulSoup(content, "xml")

            for loc in soup.find_all("loc"):
                if loc.parent.name == "url" or loc.parent.name == "sitemap":
                    loc_url = loc.text.strip()
                    if loc_url.endswith(".xml"):
                        nested_sitemaps.append(loc_url)
                    elif netloc in loc_url:
                        urls.append(loc_url)

    except Exception as e:
        pass

    return urls, nested_sitemaps


def cg_parse_html_sitemap(content, base_url):
    urls = []
    try:
        netloc = extract_domain(base_url)
        soup = BeautifulSoup(content, "html.parser")
        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"].strip()
            if not href.startswith("http"):
                href = urljoin(base_url, href)  # Convert relative to absolute URL

            if netloc in href:
                urls.append(href)

    except Exception as e:
        pass

    return urls


def remove_duplicates(urls):
    return list(set(urls))


def remove_www(url):
    return re.sub(r"^(https?:\/\/)?(www\.)?", r"\1", url)


def extract_domain(url):
    if not re.match(r"http[s]?://", url):
        url = "http://" + url  # Add HTTP if missing
    parsed_url = urlparse(url)
    domain = parsed_url.netloc
    domain = remove_www(domain)
    return domain


def cg_compressed_data(compressed_data):
    decompressed_data = ""
    with gzip.GzipFile(fileobj=io.BytesIO(compressed_data), mode="rb") as f:
        decompressed_data = f.read()
    if decompressed_data:
        return decompressed_data.decode("utf-8", errors="ignore")
    return None


def configure_driver(use_headless=True):
    chromedriver_path = os.environ.get("CHROMEDRIVER_PATH", "/usr/bin/chromedriver")

    # User Agent
    ua_agent = str(cg_user_agents())

    # Selenium Chrome Options
    chrome_options = Options()
    if use_headless:
        chrome_options.add_argument("--headless")  # Enable headless mode

    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--incognito")
    chrome_options.add_argument(f"user-agent={ua_agent}")

    # Set up ChromeDriver
    service = Service(chromedriver_path)  # Update this to your ChromeDriver path
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver


def cg_selenium_sitemap(current_sitemap):
    raw_data = ""
    raw_status = 0
    try:
        driver = configure_driver()
        driver.get(current_sitemap)
        driver.implicitly_wait(2)
        raw_data = driver.page_source
        if raw_data:
            raw_status = 200
        driver.quit()
    except Exception as e:
        pass

    return raw_status, raw_data


def cg_scraper_request(domain_sitemap, domain):
    urls = []

    try:
        if domain_sitemap:
            cg_scraper = create_scraper()
            full_urls = []

            for each_sitemap in domain_sitemap:
                to_process = [each_sitemap]

                while to_process:
                    to_process = list(set(to_process))
                    current_sitemap = to_process.pop(0)

                    if current_sitemap not in full_urls:
                        full_urls.append(current_sitemap)

                    nested_sitemaps = []

                    # GENERAL SCRAPING
                    cg_scrap_status, cg_scrap_content = cg_fetch_sitemap(cg_scraper, current_sitemap)

                    if cg_scrap_status == 200 and cg_scrap_content:
                        if cg_scrap_content[:2] == b"\x1f\x8b":
                            cg_deflate_data = cg_compressed_data(cg_scrap_content)
                            cg_scrap_content = cg_deflate_data if cg_deflate_data else cg_scrap_content

                        if current_sitemap.endswith(".xml"):
                            extracted_urls, nested_sitemaps = cg_parse_xml_sitemap(cg_scrap_content, current_sitemap)
                            if len(extracted_urls):
                                urls.extend(extracted_urls)

                        if not current_sitemap.endswith(".xml"):
                            html_urls = cg_parse_html_sitemap(cg_scrap_content, current_sitemap)
                            if html_urls:
                                urls.extend(html_urls)

                    # SELENIUM
                    netloc = extract_domain(current_sitemap)
                    if len(urls) == 0:
                        cg_scrap_status, cg_scrap_content = cg_selenium_sitemap(current_sitemap)

                        if cg_scrap_content[:2] == b"\x1f\x8b":
                            cg_deflate_data = cg_compressed_data(cg_scrap_content)
                            cg_scrap_content = cg_deflate_data if cg_deflate_data else cg_scrap_content

                        soup = BeautifulSoup(cg_scrap_content, "html.parser")
                        for loc in soup.find_all("loc"):
                            href = loc.text.strip()
                            if href.startswith("http") and href.endswith(".xml"):
                                nested_sitemaps.append(href)

                            elif href.startswith("http"):
                                if netloc in href:
                                    urls.append(href)

                        for a_tag in soup.find_all("a", href=True):
                            href = a_tag["href"].strip()
                            if href.startswith("http") and href.endswith(".xml"):
                                nested_sitemaps.append(href)
                            elif href.startswith("http"):
                                if netloc in href:
                                    urls.append(href)

                    # SCRAPING DOG
                    if len(urls) == 0:
                        cg_scrap_status, cg_scrap_content = cg_scraping_dog_sitemap(current_sitemap)
                        print(cg_scrap_content)
                        if cg_scrap_content[:2] == b"\x1f\x8b":
                            cg_deflate_data = cg_compressed_data(cg_scrap_content)
                            cg_scrap_content = cg_deflate_data if cg_deflate_data else cg_scrap_content

                        if current_sitemap.endswith(".xml"):
                            extracted_urls, nested_sitemaps = cg_parse_xml_sitemap(cg_scrap_content, current_sitemap)
                            if len(extracted_urls):
                                urls.extend(extracted_urls)

                        if not current_sitemap.endswith(".xml"):
                            html_urls = cg_parse_html_sitemap(cg_scrap_content, current_sitemap)
                            if html_urls:
                                urls.extend(html_urls)

                    if nested_sitemaps:
                        nested_sitemaps = list(set(nested_sitemaps))
                        for each_url in nested_sitemaps:
                            if each_url not in full_urls:
                                to_process.append(each_url)

                    to_process = list(set(to_process))

            if urls:
                urls = remove_duplicates(urls)
                domain_file_name = re.sub(r"[./]", "_", domain)

                url_file = os.getcwd() + "/project/files/cga/domain_url/url__" + str(domain_file_name) + ".json"
                with open(url_file, "w") as f:
                    json.dump(urls, f, indent=4)
                f.close

    except Exception as e:
        print("cg_scraper_request ", str(e))
        raise e

    return urls


# @api_view(['GET'])
# def automation_cga_scraper(request):
def automation_cga_scraper(cg_data, cg_search_id):  # ORIGINAL
    try:
        cg_flag = 0

        # cg_search_id = "c0c61404-5800-4878-9ae8-456ef84e7694"
        # cg_data = [{"id": "c4729c21-ed15-4692-9fd1-0d13b39d2e91", "fd": "https://www.kotak.com", "pd": "www.kotak.com"}, {"id": "fff39f91-b7f9-4955-94a8-d11d66f30697", "fd": "https://www.hdfcbank.com", "pd": "www.hdfcbank.com"}]
        # cg_data = [{"id": "c4729c21-ed15-4692-9fd1-0d13b39d2e91", "fd": "https://www.kotak.com", "pd": "www.kotak.com"}]
        # cg_data = [{"id": "fff39f91-b7f9-4955-94a8-d11d66f30697", "fd": "https://www.hdfcbank.com", "pd": "www.hdfcbank.com"}]

        # print("cg_data: ", cg_data, "\n\n")

        if cg_search_id and cg_data:
            for each_data in cg_data:
                if "fd" in each_data:
                    CGADomain.objects.filter(domain_id=each_data["id"]).update(track_status="SCHD", last_track_date=datetime.now())

                    domain = cg_domain_return(each_data["fd"])

                    # print("DN : ", domain, "\n\n")

                    sitemap_choices = cg_sitemap_slugs(domain)

                    robots_url = f"{domain}robots.txt"

                    robots_sitemaps = extract_xml_links_from_robots(robots_url)

                    sitemap_choices = list(set(sitemap_choices + robots_sitemaps))

                    if sitemap_choices:

                        cg_return = cg_scraper_request(sitemap_choices, domain)

                        if cg_return:
                            cg_category_data = cga_category.cg_category_analyse(cg_return)

                            if cg_return and cg_category_data:
                                # print("CATEGORY Length: ", len(cg_category_data), "\n\n")

                                # print(domain, cg_category_data.keys())

                                # SAVE ALL CATEGORY INTO FILES
                                domain_file_name = re.sub(r"[./]", "_", domain)

                                url_file = os.getcwd() + "/project/files/cga/domain_category/category__" + str(domain_file_name) + ".json"
                                with open(url_file, "w") as f:
                                    json.dump(cg_category_data, f, indent=4)
                                f.close

                                # CREATE BULK URLS
                                serializer = UrlCreateSerializer(cg_return, many=True, context={"domain": each_data["id"]})
                                bulk_urls = CGADomainUrl.objects.bulk_create(serializer.data)

                                # MAP BULK URLS WITH PRIMARY KEYS
                                domain_url_keys = {}
                                for obj in bulk_urls:
                                    domain_url_keys[obj.source_url] = obj.domain_url_id

                                # CREATE BULK CATEGORY
                                serializer = CategoryCreateSerializer(list(cg_category_data.keys()), many=True, context={"domain": each_data["id"]})
                                bulk_categories = CGADomainCategory.objects.bulk_create(serializer.data)

                                # MAP BULK CATEGORY WITH PRIMARY KEYS
                                domain_cat_keys = {}
                                for obj in bulk_categories:
                                    domain_cat_keys[obj.category_name] = obj.domain_category_id

                                # CREATE DOMAIN CATEGORY URLS
                                cg_category_records = []
                                for each_category_data in cg_category_data:
                                    serializer = CategoryUrlCreateSerializer(cg_category_data[each_category_data], many=True, context={"domain": each_data["id"], "durls": domain_url_keys, "dcats": domain_cat_keys, "cat": each_category_data})
                                    cg_category_records = cg_category_records + serializer.data

                                cg_category_records = list(filter(None, cg_category_records))
                                bulk_categories_urls = CGADomainCategoryUrls.objects.bulk_create(cg_category_records)

                                # DOMAIN STATUS UPDATE
                                message = str(domain) + " was tracked and retrieved data successfully"
                                CGADomain.objects.filter(domain_id=each_data["id"]).update(track_status="COMP", track_message=message, last_track_date=datetime.now())

                                cg_flag += 1
                            else:
                                error_message = "The domain categorization was failed"
                                CGADomain.objects.filter(domain_id=each_data["id"]).update(track_status="FAIL", track_message=error_message, last_track_date=datetime.now())
                        else:
                            error_message = "The domain sitemap tracking was returned empty"
                            CGADomain.objects.filter(domain_id=each_data["id"]).update(track_status="FAIL", track_message=error_message, last_track_date=datetime.now())
                else:
                    # UPDATE AS FAILED AGAIN ON THE DOMAIN TABLE
                    error_message = "The domain value (fd) seems not present in the set"
                    CGADomain.objects.filter(domain_id=each_data["id"]).update(track_status="FAIL", track_message=error_message, last_track_date=datetime.now())

            if cg_flag == len(cg_data):
                return True

    except Exception as e:
        print("cg_scraper_request ", str(e))
        pass

    return False
    # return JsonResponse({'st': 0})
