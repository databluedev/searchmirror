# TESTING PURPOSE AND INITIATIVE
import base64, gzip, io, string 
import sys, os, random, socket, re, cloudscraper, json 
from datetime import datetime, date
from urllib.parse import urlparse

from django.shortcuts import render
from django.conf import settings 

# from project.machine.submodels.serpmodels import DKeyword, DGroups
# from project.machine.submodels.contentgapmodels import CGADomain, CGADomainCategory, CGADomainCategoryUrls, CGADomainUrl, CGASearch, CGASearchCategory, CGASearchMatch 
# from project.machine import automation_common as _at__common_ 
# from project.machine.contentgap.cga_serializers import * 

# from project.machine.contentgap import cga_category
# from rest_framework.decorators import api_view
# from django.http import HttpResponse, JsonResponse 

from bs4 import BeautifulSoup
from urllib.parse import urljoin

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from fake_useragent import UserAgent 

# Comma-separated in CONTENTGAP_PROXIES; empty means direct requests.
PROXY_LIST = [p for p in os.environ.get("CONTENTGAP_PROXIES", "").split(",") if p.strip()] 

def cg_sitemap_slugs(domain):
	sitemap_list = []
	if not domain:
		return sitemap_list

	suffixes = ["sitemap.xml", "sitemap-index.xml", "sitemap_index.xml", "sitemap", "sitemap/sitemap.xml"] 
	# suffixes = ["sitemap.xml"] 

	for suffix in suffixes:
		sitemap_list.append(f"{domain}{suffix}") 

	return sitemap_list 

def cg_user_agents():
	_DEFAULT__HEADERS_ = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36" 
	
	try:
		ua = UserAgent(browsers=["chrome", "firefox", "safari"], platforms="pc") 
		return ua.random

	except Exception as e:
		pass

	return _DEFAULT__HEADERS_

def cg_request_headers(): 
	_headers_ = {
		"User-Agent": str(cg_user_agents()), 
		"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
		"Accept-Encoding": "gzip, deflate, br", 
		"Accept-Language": "en-US,en;q=0.5",
		"Connection": "keep-alive"
	} 
	return _headers_

def cg_domain_return(domain): 
	if domain:
		return domain if domain.endswith("/") else str(domain) + "/"

	return None

def create_scraper(): 
	proxy_address = random.choice(PROXY_LIST)
	scraper = cloudscraper.create_scraper()
	scraper.headers.update(cg_request_headers()) 
	scraper.proxies= proxy_address
	return scraper

def cg_fetch_sitemap(scraper, url):
	try:
		response = scraper.get(url, timeout=10)
		return response.status_code, response.content
	except Exception as e:
		print("cg_fetch_sitemap error: ", str(e)) 
	return 0, None 

def cg_parse_xml_sitemap(content, current_sitemap):
	try:
		urls = []
		nested_sitemaps = []

		if content and current_sitemap:
			netloc = extract_domain(current_sitemap)  
			soup = BeautifulSoup(content, 'xml')

			for loc in soup.find_all('loc'):
				if loc.parent.name == 'url' or loc.parent.name == 'sitemap':
					loc_url = loc.text.strip()
					if loc_url.endswith('.xml'):
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
		soup = BeautifulSoup(content, 'html.parser')
		for a_tag in soup.find_all('a', href=True):
			href = a_tag['href'].strip()
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
    return re.sub(r'^(https?:\/\/)?(www\.)?', r'\1', url)

def extract_domain(url):
    if not re.match(r'http[s]?://', url):
        url = 'http://' + url  # Add HTTP if missing
    parsed_url = urlparse(url)
    domain = parsed_url.netloc 
    domain = remove_www(domain)  
    return domain

def cg_compressed_data(compressed_data): 
	decompressed_data = ""
	with gzip.GzipFile(fileobj=io.BytesIO(compressed_data), mode='rb') as f:
		decompressed_data = f.read()
	if decompressed_data:
		return decompressed_data.decode('utf-8', errors='ignore') 
	return None

def configure_driver(use_headless=True):
	chromedriver_path = os.environ.get("CHROMEDRIVER_PATH", "/usr/bin/chromedriver")

	# proxy_address = random.choice(PROXY_LIST) - Not Working 

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

	# Attach proxy
	# chrome_options.add_argument(f'--proxy-server={proxy_address}')    

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
			cg_flag = 0
			full_urls = []
			flag = 0

			for each_sitemap in domain_sitemap:
				to_process = [each_sitemap]

				while to_process: 
					current_sitemap = to_process.pop(0) 
					cg_scrap_status, cg_scrap_content = cg_fetch_sitemap(cg_scraper, current_sitemap) 

					if cg_scrap_status == 200 and cg_scrap_content:
						if cg_scrap_content[:2] == b'\x1f\x8b': 
							cg_deflate_data = cg_compressed_data(cg_scrap_content)
							cg_scrap_content = cg_deflate_data if cg_deflate_data else cg_scrap_content 

						extracted_urls, nested_sitemaps = cg_parse_xml_sitemap(cg_scrap_content, current_sitemap)

						if len(extracted_urls) == 0 and not current_sitemap.endswith(".xml"):
							html_urls = cg_parse_html_sitemap(cg_scrap_content, current_sitemap) 
							if html_urls:
								urls.extend(html_urls) 
								cg_flag += 1
								flag += 1
						else:
							urls.extend(extracted_urls)
							cg_flag += 1
							flag += 1 

						if nested_sitemaps:
							to_process.extend(nested_sitemaps) 
					
					if flag == 0: 
						nested_sitemaps = [] 
						netloc = extract_domain(each_sitemap)  
						
						cg_scrap_status, cg_scrap_content = cg_selenium_sitemap(current_sitemap) 
						
						if cg_scrap_status == 200 and cg_scrap_content:
							if cg_scrap_content[:2] == b'\x1f\x8b': 
								cg_deflate_data = cg_compressed_data(cg_scrap_content) 
								cg_scrap_content = cg_deflate_data if cg_deflate_data else cg_scrap_content 

							soup = BeautifulSoup(cg_scrap_content, 'html.parser') 

							for loc in soup.find_all('loc'):
								href = loc.text.strip()
								if href.startswith("http") and href.endswith('.xml'):
									if href not in full_urls:
										nested_sitemaps.append(href)
										full_urls.append(href) 
								elif href.startswith("http"):
									if netloc in href:
										urls.append(href)
										cg_flag += 1 
										
							for a_tag in soup.find_all('a', href=True): 
								href = a_tag['href'].strip()
								if href.startswith("http") and href.endswith('.xml'):
									if href not in full_urls:
										nested_sitemaps.append(href)
										full_urls.append(href) 
								elif href.startswith("http"):
									if netloc in href:
										urls.append(href)
										cg_flag += 1  

						if nested_sitemaps: 
							to_process.extend(nested_sitemaps) 
 
				if cg_flag and urls and len(to_process) == 0:
					print("LENGTH of org: ", len(urls))
					urls = remove_duplicates(urls)
					print("LENGTH of filter: ", len(urls))

					# domain_file_name = re.sub(r"[./]", "_", domain) 

					# url_file = os.getcwd()+"/project/files/cga/domain_url/url__"+str(domain_file_name)+".json" 
					# with open(url_file, 'w') as f:
					# 	json.dump(urls, f, indent=4) 
					# f.close 

					# BREAK THE LOOP AFTER THE XML OCCURANCE
					break 

	except Exception as e:
		print("cg_scraper_request ", str(e))
		raise e

	return urls

# @api_view(['GET'])  
def testing(request):
	cg_return = []
	startTime = datetime.now()
	# domain = "https://www.trioangle.com" 
	domain = "https://appinventiv.com"  
	# domain = "https://example.com" 
	# domain = "https://iob.in" 
	domain = cg_domain_return(domain)
	sitemap_choices = cg_sitemap_slugs(domain)

	if sitemap_choices:
		cg_return = cg_scraper_request(sitemap_choices, domain)


	endTime = datetime.now() 
	return JsonResponse({'pflag': cg_return, "st": startTime, "et": endTime, "taken": str(date.today())})  
