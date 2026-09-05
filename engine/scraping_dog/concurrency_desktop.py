import os
import time, random, string, os, json, sys, requests
from datetime import datetime, date 
from bs4 import BeautifulSoup 
import concurrent.futures as automation_futures
from datetime import datetime, date

startTime = datetime.now() 
successCall = 0
failureCall = 0

def save_file(data, keyword): 
    if data: 
        keyword = keyword.replace(' ', '_')

        # Save the HTML to a file
        automate_letters = ''.join(random.choice(string.ascii_lowercase) for _ in range(6))
        output_file_path = os.path.join(os.getcwd(), f"json/search_{keyword}_{automate_letters}.json")

        with open(output_file_path, 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=4) 

        # print(f"JSON saved to: {output_file_path}") 
        return True

    return False 

def concurrent_fetch(keyword): 
    global successCall, failureCall

    api_key = os.environ.get("SCRAPINGDOG_API_KEY", "")
    url = "https://api.scrapingdog.com/google"
    
    params = {
        "api_key": api_key,
        "query": keyword,   
        "results": 100,
        "country": "us",
        "language": "en",
        "page": 0,
        "uule": "w+CAIQICINVW5pdGVkIFN0YXRlcw",
        "advance_search": "false" 
    }

    print("CRAWL START: ", keyword, str(datetime.now()))
    response = requests.get(url, params=params)  
    print("CRAWL END: ", keyword, str(datetime.now()))

    if response.status_code == 200: 
        successCall += 1
        data = response.json() 
        
        save_file(data, keyword)

        print('SUCCESS: ', keyword, str(response.status_code), str(datetime.now()))
    else:
        failureCall += 1
        print('FAILED: ', keyword, str(response.status_code), str(datetime.now()))

    return True

#######################|    MAIN   |#######################|
try:
    # keywords = ["letgo clone", "tinder clone", "whatsapp clone", "azar clone", "periscope clone", "rental script", "bigo clone", "bigo live clone", "taxi booking script", "random video chat script"]  
    # keywords = ["letgo clone", "tinder clone", "whatsapp clone", "azar clone", "periscope clone"]   
    keywords = [k for k in os.environ.get("TEST_KEYWORDS", "").split(",") if k]

    MAX_WORKERS = 10
    # MAX_WORKERS = len(keywords) 
    QUERIES_COUNT = 1

    print("STARTED PROCESSING")
    print(f"THREAD WORKERS: {MAX_WORKERS}, KEYWORDS: {len(keywords)}, QUERIES: {QUERIES_COUNT}", "\n\n")  

    # for keyword in keywords:
    #     concurrent_fetch(keyword)

    with automation_futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        executor_result = {executor.submit(concurrent_fetch, keyword=keyword): keyword for keyword in keywords}  
        for each_result in automation_futures.as_completed(executor_result):
            print(": ", each_result.result()) 
        executor.shutdown(wait=False)   

    endTime = datetime.now()
    print('\n\nStart Time: '+str(startTime)+' End Time: '+str(endTime))
    print("\n")
    print('SUCCESS COUNT (200): '+str(successCall)) 
    print('FAILURE COUNT (---): '+str(failureCall))
    print("\n")
    print('Time Taken: '+ str(endTime - startTime)) 
except Exception as e:
    print("ERROR: ", str(e))  
