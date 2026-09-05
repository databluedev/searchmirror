import base64
import sys, os, random, socket, re, cloudscraper, json 
from datetime import datetime, date
from urllib.parse import urlparse

from django.shortcuts import render
from django.conf import settings 

from project.machine.submodels.serpmodels import DKeyword, DGroups
from project.machine.submodels.contentgapmodels import CGADomain, CGADomainCategory, CGADomainUrl, CGASearch, CGASearchCategory, CGASearchMatch
from project.machine import automation_common as _at__common_ 

from rest_framework.decorators import api_view
from django.http import HttpResponse, JsonResponse 

#####################################| CGA CATEGORY - STARTS |#####################################
def default_categories():
    general_categories = {
        "Pages": [],
        "FAQs": [],
        "Blog/Articles": [],
        "Documentation": [],
        "Resources": [],
        "Promotions": [],
        "Locations": [],
        "Media": [],
        "Search/Filters": [],
        "Deposits & Financial Services": [],
        "Banking & Finance": [],
        "E-commerce": [],
        "Products": [],
        "Business": [],
        "Real Estate": [],
        "Automotive": [],
        "Healthcare & Medical": [],
        "Travel & Tourism": [],
        "Government & Public Services": [],
        "Knowledge Base": [],
        "Customer Support": [],
        "Reviews & Testimonials": [],
        "Career & Jobs": [],
        "Legal & Compliance": [],
        "Education & Learning": [],
        "Technology & AI": [],
        "Health & Wellness": [],
        "Uncategorised": []
    }

    category_patterns = {
        "FAQs": [r'/faq', r'/help', r'/support', r'/customer-service', r'/assistance'],
        "Blog/Articles": [r'/blog', r'/news', r'/article', r'/insights', r'/updates', r'/press'],
        "Documentation": [r'/docs', r'/manual', r'/api', r'/guide', r'/how-to'],
        "Resources": [r'/resources', r'/downloads', r'/tools', r'/whitepaper', r'/case-study'],
        "Promotions": [r'/offers', r'/deals', r'/discounts', r'/coupons', r'/sale', r'/special-offers'],
        "Locations": [r'/locations', r'/branches', r'/store-locator', r'/find-us', r'/offices'],
        "Media": [r'/media', r'/gallery', r'/videos', r'/photos', r'/press-release'],
        "Deposits & Financial Services": [r'/banking', r'/loans', r'/credit', r'/deposits', r'/insurance', r'/investment', r'/mortgage', r'/wealth-management', r'/retirement-planning'],
        "Banking & Finance": [r'/bank', r'/fintech', r'/account', r'/loan', r'/atm', r'/trading', r'/forex', r'/cryptocurrency', r'/payment'],
        "E-commerce": [r'/shop', r'/cart', r'/checkout', r'/order', r'/wishlist', r'/ecommerce'],
        "Products": [r'/product', r'/catalog', r'/collections', r'/item', r'/sku'],
        "Business": [r'/partners', r'/clients', r'/b2b', r'/enterprise', r'/solutions'],
        "Real Estate": [r'/real-estate', r'/property', r'/listing', r'/homes', r'/apartments', r'/commercial-property'],
        "Automotive": [r'/cars', r'/vehicles', r'/auto', r'/dealership', r'/showroom'],
        "Healthcare & Medical": [r'/hospital', r'/clinic', r'/pharmacy', r'/medicine', r'/healthcare'],
        "Travel & Tourism": [r'/travel', r'/flights', r'/hotels', r'/vacation', r'/tourism'],
        "Government & Public Services": [r'/gov', r'/public-services', r'/municipal', r'/civic'],
        "Knowledge Base": [r'/knowledge-base', r'/kb', r'/support/knowledge'],
        "Customer Support": [r'/contact-support', r'/live-chat', r'/ticket', r'/customer-support'],
        "Reviews & Testimonials": [r'/reviews', r'/testimonials', r'/feedback', r'/ratings'],
        "Career & Jobs": [r'/careers', r'/jobs', r'/hiring', r'/internships', r'/vacancies'],
        "Legal & Compliance": [r'/terms', r'/privacy', r'/compliance', r'/gdpr', r'/legal'],
        "Education & Learning": [r'/courses', r'/training', r'/certification', r'/elearning', r'/academy'],
        "Technology & AI": [r'/ai', r'/machine-learning', r'/tech', r'/innovation', r'/automation'],
        "Health & Wellness": [r'/health', r'/wellness', r'/fitness', r'/nutrition', r'/medical'], 
        "Search/Filters": [r'/search', r'/filter', r'/browse', r'/find', r'\?q='], 
        "Pages": [r'/home', r'/about', r'/contact', r'/services', r'/company', r'/team']
    }

    return general_categories, category_patterns 

def extract_slug(url):
    # Regex pattern to remove protocol, www, subdomain, domain, and trailing file extension
    pattern = r"^(?:https?:\/\/)?(?:www\.)?[^\/]+\/|(?:\.[a-zA-Z0-9]+)$"
    
    # Remove matched patterns
    slug = re.sub(pattern, "", url)
    
    return slug

def cg_category_analyse(url_list):
    try:
        cg_category_items = {}
        
        if url_list:
            general_categories, category_patterns = default_categories() 

            for url in url_list: 
                categorized = False
                for category, patterns in category_patterns.items():
                    slug = extract_slug(url)
                    if any(re.search(pattern, slug, re.IGNORECASE) for pattern in patterns):
                        general_categories[category].append(url)
                        categorized = True
                        break
                if not categorized: 
                    general_categories["Uncategorised"].append(url) 

            for category, urls in general_categories.items(): 
                if len(urls):
                    cat_name = category.lower()
                    cg_category_items[cat_name] = list(urls)

    except Exception as e:
        pass
        print("Error ", str(e))

    return cg_category_items 

#####################################| CGA CATEGORY -   ENDS |#####################################
