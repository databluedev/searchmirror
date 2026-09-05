import base64
import sys, os, random, socket, re, time
from datetime import datetime, date
from urllib.parse import urlparse
import numpy as np 

from sentence_transformers import SentenceTransformer, util 

from django.shortcuts import render
from django.conf import settings 

from project.machine.submodels.serpmodels import DKeyword, DGroups
from project.machine.submodels.contentgapmodels import CGADomain, CGADomainCategory, CGADomainCategoryUrls, CGADomainUrl, CGASearch, CGASearchCategory, CGASearchCategoryUrls, CGASearchMatch
from project.machine import automation_common as _at__common_ 

from project.machine.contentgap import cga_scraper as cga_scrap
from project.machine.contentgap import cga_category_match as cga_cm
from project.machine.contentgap.cga_serializers import * 

from rest_framework.decorators import api_view
from django.http import HttpResponse, JsonResponse 

# SENTENCE TRANSFORMERS FOR PARAPHRASE ANALYSE
model = SentenceTransformer('paraphrase-MiniLM-L6-v2')

def remove_duplicates(urls):
	return list(set(urls))

def extract_domain(url):
	if not re.match(r'http[s]?://', url):
		url = 'http://' + url  # Add HTTP if missing
	parsed_url = urlparse(url)
	domain = parsed_url.netloc 
	return domain.replace(".", "_") 

def extract_full_slug(url):
	path = urlparse(url).path
	return path.strip('/').replace('-', ' ')

def extract_last_slug(url):
	path = urlparse(url).path
	return path.rstrip('/').split('/')[-1].replace('-', ' ')

def save_to_file(urls, save_path):
	os.makedirs(os.path.dirname(save_path), exist_ok=True)
	with open(save_path, 'w') as file:
		for url in urls:
			file.write(url + '\n') 
	file.close
	return True

def match_urls_by_similarity(urls_a, urls_b, threshold_ranges):
	global model

	# Extract slugs and compute embeddings
	slugs_a = [extract_full_slug(url) for url in urls_a]
	slugs_b = [extract_full_slug(url) for url in urls_b] 

	embeddings_a = model.encode(slugs_a, convert_to_tensor=True)
	embeddings_b = model.encode(slugs_b, convert_to_tensor=True)

	# Compute cosine similarity matrix
	cosine_scores = util.cos_sim(embeddings_a, embeddings_b).cpu().numpy()

	# Prepare result containers
	matched = {f'>{t}%': [] for t in threshold_ranges}
	unmatched_a, unmatched_b = set(urls_a), set(urls_b)

	# Match URLs progressively by decreasing similarity thresholds
	for threshold in sorted(threshold_ranges, reverse=True):
		used_b_indices = set()
		for i, url_a in enumerate(urls_a):
			if url_a not in unmatched_a:
				continue  # Skip if already matched

			best_match = None
			best_score = 0
			best_j = -1
			
			for j, url_b in enumerate(urls_b):
				if j in used_b_indices or url_b not in unmatched_b:
					continue  # Skip if URL in B is already matched

				score = cosine_scores[i][j]
				if score > best_score:
					best_score = score
					best_match = url_b
					best_j = j

			if best_match and best_score >= threshold / 100:
				percentage = int(best_score * 100)
				matched[f'>{threshold}%'].append((url_a, best_match, f'{percentage}%'))
				unmatched_a.discard(url_a)
				unmatched_b.discard(best_match)
				used_b_indices.add(best_j)

	# Sort matches within each threshold by descending score  
	for threshold_key in matched:
		matched[threshold_key].sort(key=lambda x: x[2], reverse=True) 

	return {
		'matched': matched,
		'unmatched_a': list(unmatched_a),
		'unmatched_b': list(unmatched_b)
	}

@api_view(['GET'])
def automation_match_call(request, _ustr_, _kstr_): 
	try:
		_base__result_, _setting__data_  = _at__common_.__base_validation__(request, _ustr_)
		if _base__result_ and _kstr_.isdigit(): 
			
			if int(_kstr_)%2 == 1: 
				_cg__active__data_ = CGASearchCategory.objects.filter(category_status="INIT").values("fk_user_id", "search_category_id", "fk_search_id", "category_name", "fk_self_domain_id", "fk_comp_domain_id", "category_status").order_by('modified_date').first() # ASC ORDER
			else:
				_cg__active__data_ = CGASearchCategory.objects.filter(category_status="INIT").values("fk_user_id", "search_category_id", "fk_search_id", "category_name", "fk_self_domain_id", "fk_comp_domain_id", "category_status").order_by('-modified_date').first()
			
			if _cg__active__data_ and "search_category_id" in _cg__active__data_: 
				CGASearchCategory.objects.filter(search_category_id=_cg__active__data_["search_category_id"]).update(category_status="SCHD") 

				cg_category_urls_list = CGASearchCategoryUrls.objects.filter(fk_search_category_id=_cg__active__data_["search_category_id"]).values('fk_domain_id', 'fk_domain_url_id').all() 
				cg_category_urls_dict = {}

				for each_url_value in cg_category_urls_list:				
					if str(each_url_value['fk_domain_id']) not in cg_category_urls_dict:
						cg_category_urls_dict[str(each_url_value['fk_domain_id'])] = []
					cg_category_urls_dict[str(each_url_value['fk_domain_id'])].append(str(each_url_value['fk_domain_url_id'])) 

				domain_keys = list(cg_category_urls_dict.keys())
				if len(domain_keys) == 2 and str(_cg__active__data_['fk_self_domain_id']) in domain_keys and str(_cg__active__data_['fk_comp_domain_id']) in domain_keys: 
					cg_category_url_id_dict = {}
					cg_self_urls_list = []
					cg_comp_urls_list = []

					# SELF DOMAIN LIST
					cg_self_list = CGADomainUrl.objects.filter(domain_url_id__in=cg_category_urls_dict[str(_cg__active__data_['fk_self_domain_id'])]).values('domain_url_id', 'source_url').all()
					if cg_self_list:
						for each_url in cg_self_list:
							cg_self_urls_list.append(each_url['source_url']) 
							cg_category_url_id_dict[each_url['source_url']] = str(each_url['domain_url_id']) 

					# COMP DOMAIN LIST
					cg_comp_list = CGADomainUrl.objects.filter(domain_url_id__in=cg_category_urls_dict[str(_cg__active__data_['fk_comp_domain_id'])]).values('domain_url_id', 'source_url').all()
					if cg_comp_list:
						for each_url in cg_comp_list:
							cg_comp_urls_list.append(each_url['source_url']) 
							cg_category_url_id_dict[each_url['source_url']] = str(each_url['domain_url_id']) 

					cg_category_output_data = [] 
					if cg_self_urls_list and cg_comp_urls_list:

						cg_self_domain = extract_domain(cg_self_urls_list[0])
						cg_comp_domain = extract_domain(cg_comp_urls_list[0])
						
						point = "Original Length of "+ str(cg_self_domain) +": " + str(len(cg_self_urls_list)) 
						cg_category_output_data.append(point)

						point = "Original Length of "+ str(cg_comp_domain) +": " + str(len(cg_comp_urls_list)) 
						cg_category_output_data.append(point)
						
						if cg_self_urls_list:
							cg_self_urls_list = remove_duplicates(cg_self_urls_list)

						if cg_comp_urls_list:
							cg_comp_urls_list = remove_duplicates(cg_comp_urls_list)

						point = "Unique Length of "+ str(cg_self_domain) +": " + str(len(cg_self_urls_list)) 
						cg_category_output_data.append(point)

						point = "Unique Length of "+ str(cg_comp_domain) +": " + str(len(cg_comp_urls_list)) 
						cg_category_output_data.append(point) 

						thresholds = [95, 90, 85, 80, 75, 70, 65, 60] 
						result = match_urls_by_similarity(cg_self_urls_list, cg_comp_urls_list, thresholds)

						point = "\n\nMatched URLs by similarity range:"
						cg_category_output_data.append(point)

						search_match_serial_data = []
						for range_key, matches in result['matched'].items():
							serializer = SearchMatchUrlsCreateSerializer(matches, many=True, context={"url_data": cg_category_url_id_dict, "active_data": _cg__active__data_}) 
							search_match_serial_data += serializer.data

							if matches:
								point = "\n" + range_key + ":"
								cg_category_output_data.append(point)
								for match in matches:
									point = str(match[0]) + " \n " + str(match[1]) + " \n " + " (Similarity: " + str(match[2]) + ")\n\n"
									cg_category_output_data.append(point) 

						# UN MATCHES OF SELF DOMAIN
						point = str("\n\nUnMatched URLs by " + str(cg_self_domain) + ": ")
						cg_category_output_data.append(point)

						point = "\n\nLength of UnMatched of Domain - " + str(cg_self_domain) + ": " + str(len(result['unmatched_a'])) 
						cg_category_output_data.append(point)

						for value in result['unmatched_a']:
							cg_category_output_data.append(value)

						# UN MATCHES OF COMP DOMAIN
						point = str("\n\nUnMatched URLs by " + str(cg_comp_domain) + ": ")
						cg_category_output_data.append(point)

						point = "\n\nLength of UnMatched of Domain - " + str(cg_comp_domain) + ": " + str(len(result['unmatched_b'])) 
						cg_category_output_data.append(point)

						for value in result['unmatched_b']:
							cg_category_output_data.append(value)

						save_path = os.getcwd()+"/project/files/cga/url_match/cm_"+str(_cg__active__data_["search_category_id"])+".txt"  
						save_to_file(cg_category_output_data, save_path)  

						serializer = SearchUnMatchUrlsCreateSerializer(result['unmatched_a'], many=True, context={"check_key": "unmatched_a", "url_data": cg_category_url_id_dict, "active_data": _cg__active__data_}) 
						search_match_serial_data += serializer.data

						serializer = SearchUnMatchUrlsCreateSerializer(result['unmatched_b'], many=True, context={"check_key": "unmatched_b", "url_data": cg_category_url_id_dict, "active_data": _cg__active__data_})
						search_match_serial_data += serializer.data

						bulk_records = list(filter(None, search_match_serial_data)) 
						cga_matches = CGASearchMatch.objects.bulk_create(bulk_records) 

						if cga_matches: 
							CGASearchCategory.objects.filter(search_category_id=_cg__active__data_['search_category_id']).update(category_status="DONE", metric_status="INIT")
							return JsonResponse({'st': 1, 'status': "mapping completed"}) 
				
				CGASearchCategory.objects.filter(search_category_id=_cg__active__data_['search_category_id']).update(category_status="FAIL", metric_status="INIT")
				return JsonResponse({'st': 1, 'status': "mapping not completed"}) 
			else:
				return JsonResponse({'st': 0, 'status': "No Process were available for mapping"}) 

	except Exception as e:
		return JsonResponse({'st': 0, 'status': str(e)})    
				
	return JsonResponse({'st': 0, 'status': 'OOPS! visit tracker.example'})   
	