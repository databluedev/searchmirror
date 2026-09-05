from django.conf import settings as _def_
from project.machine import automation_common as _at__common_ 
from project.machine import watchdog as _wd_
from project.machine.bot import snippet as _snippet_

_clean__futures_ = {
	# ENGLISH
	"default": ["people_also_search_for", "skip_to_main_content", "accessibility_help", "accessibility_feedback", "accessibility_links", "why_this_ad?", "feedback", "report", "claim_this_knowledge_panel"],
	
	# GERMANY
	"de": ["links_zur_barrierefreiheit", "zu_den_hauptinhalten_springen", "hilfe_zur_barrierefreiheit", "feedback_zur_barrierefreiheit", "feedback_geben", "warum_sehe_ich_diese_werbung?", "andere_suchten_auch_nach", "anspruch_auf_dieses_knowledge_panel_erheben"],
} 

def __trim__(_value_):
    return _value_.strip()

# SNIPPET CONTENT CHANGES BASED ON EACH LANGUAGE.
def __page_language_based_snippet__(_engine__mode_, _lang_, _data__id_):
	try:
		if _lang_ != "" and _lang_ != None:
			_lang_ = __trim__(_lang_)
			if _lang_ in _snippet_._snippet__futures_:
				return _snippet_._snippet__futures_[_lang_]

	except Exception as e:
		_mode_ = str(_engine__mode_).upper()
		_wd_.coreLog("> "+_mode_+" - PAGE LANGUAGE BASED SNIPPET FUNCTION ERROR >> KEYWORD ID: "+str(_data__id_)+" >>> ERROR MESSAGE: "+ str(e), "ERROR")

	return _snippet_._snippet__futures_['default']

# CLEAN UNWANTED CONTENT FROM THE HTML PAGES.
def __page_language_basis__(_engine__mode_, _lang_, _data__id_):
	try:
		_lang_ = __trim__(_lang_)
		if _lang_ != "" and _lang_ != None:
			if _lang_ in _clean__futures_:
				return _clean__futures_[_lang_]

	except Exception as e:
		_mode_ = str(_engine__mode_).upper()
		_wd_.coreLog("> "+_mode_+" - PAGE LANGUAGE BASIS FUNCTION ERROR >> KEYWORD ID: "+str(_data__id_)+" >>> ERROR MESSAGE: "+ str(e), "ERROR")

	return _clean__futures_['default']

# REMOVE OPTIONAL TAGS AND ATTRIBUTES FROM THE HTML PAGES. 
def __page_desktop_cleaner__(_engine__mode_, _soup_, _lang_, _data__id_):
	try:
		for tag in _soup_.find_all(True): 
			# _bot__clean_ = __page_language_basis__(_engine__mode_, _lang_, _data__id_)      # LANGUAGE BASED HTML CONTENT CLEANER 

			tExtract = True
			if len(tag.findChildren(recursive=True)) != 0 or len(tag.text) != 0:
				if tag.has_attr("id"):
					tId = tag.get("id")
					if tId:
						if tId in ["searchform", "top_nav"]:
							tExtract = False

				if tExtract == False: 
					tag.decompose() 

			if tag.name in ["head", "style", "script", "noscript", "form", "svg", "button", "g-more-link", "g-more-button", "g-fab", "g-dropdown-menu", "g-popup", "g-dialog"]:
				tag.extract()

		for tag in _soup_.find_all(True):
			if tag.name in ["head", "div", "a", "span", "w-debug-content", "g-right-button", "g-left-button", "title-with-lhs-icon", "g-section-with-header", "g-inner-card", "g-scrolling-carousel", "g-image-section", "g-link", "g-img"] and len(tag.findChildren(recursive=True)) == 0 and len(tag.text) == 0: 
				tag.extract()  

	except Exception as e:
		_mode_ = str(_engine__mode_).upper()
		_wd_.coreLog("> "+_mode_+" - PAGE DESKTOP CLEANER FUNCTION ERROR >> KEYWORD ID: "+str(_data__id_)+" >>> ERROR MESSAGE: "+ str(e), "ERROR")

	return _soup_ 


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ 
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ BACKUP CODE FOR REFERENCE ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ 
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def BACKUP_CODE__page_desktop_cleaner__(_engine__mode_, _soup_, _lang_, _data__id_):
	try:
		# _bot__clean_ = __page_language_basis__(_engine__mode_, _lang_, _data__id_)      # LANGUAGE BASED HTML CONTENT CLEANER 

		for tag in _soup_.find_all(True): 
			tExtract = True
			if len(tag.findChildren(recursive=True)) != 0 or len(tag.text) != 0:
				if tag.has_attr("id"):
					tId = tag.get("id")
					if tId:
						if tId in ["searchform", "top_nav"]:
							tExtract = False

				# if tag.has_attr("role"):
				# 	tRole = tag.get("role") 
				# 	if tRole: 
				# 		if tRole in ["navigation", "contentinfo"]:
				# 			tExtract = False

				if tExtract == False: 
					tag.decompose() 
				# else: 	
				# 	# tag.attrs = {} # REMOVE ALL ATTRIBUTES IN TAG 
				# 	attrs = dict(tag.attrs)
				# 	for attr in attrs:
				# 		if tag.name != "html" and attr not in ["id", "class", "role", "href", "src", "data-src", "alt", "height", "width", "data-rw"]:
				# 			del tag[attr]

			#"head", "style", - Super Page Remove from list
			# if tag.name in ["script", "noscript", "form", "svg", "button", "g-more-link", "g-more-button", "g-fab", "g-dropdown-menu", "g-popup", "g-dialog"]: 
			if tag.name in ["head", "style", "script", "noscript", "form", "svg", "button", "g-more-link", "g-more-button", "g-fab", "g-dropdown-menu", "g-popup", "g-dialog"]:
				tag.extract()

			# if tag.text.replace(' ','_').lower() in _bot__clean_:
			# 	tag.extract() 

		for tag in _soup_.find_all(True):
			if tag.name in ["head", "div", "a", "span", "w-debug-content", "g-right-button", "g-left-button", "title-with-lhs-icon", "g-section-with-header", "g-inner-card", "g-scrolling-carousel", "g-image-section", "g-link", "g-img"] and len(tag.findChildren(recursive=True)) == 0 and len(tag.text) == 0: 
				tag.extract()  

	except Exception as e:
		_mode_ = str(_engine__mode_).upper()
		_wd_.coreLog("> "+_mode_+" - PAGE DESKTOP CLEANER FUNCTION ERROR >> KEYWORD ID: "+str(_data__id_)+" >>> ERROR MESSAGE: "+ str(e), "ERROR")

	return _soup_ 