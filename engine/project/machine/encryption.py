import random
import string
import base64, re
from uuid import uuid4, UUID

CODE_LIST_LOWER = ["a", "b", "c", "d", "e", "f"]

def ESCAPE_UPPER_CHARACTERS(ESTRING):
    REGEX = "[A-Z]"
    return (re.sub(REGEX, "", ESTRING)) 

def ESCAPE_CHARACTERS(ESTRING): 
    REGEX = "[a-zA-Z]"
    return (re.sub(REGEX, "", ESTRING))

def base64E(dataCode):
	message_bytes = dataCode.encode('ascii')
	base64_bytes = base64.b64encode(message_bytes)
	return base64_bytes.decode('ascii')

def base64D(dataCode):
	base64_bytes = dataCode.encode('ascii') 
	message_bytes = base64.b64decode(base64_bytes)
	return message_bytes.decode('ascii')

def short_random_code(ESTRING, ECODE_LENGTH=12):
	ESTRING_LENGTH = len(str(ESTRING))
	while (ESTRING_LENGTH < ECODE_LENGTH):
		RANDOM_INC_NUMBER = random.randint(0,int(ESTRING_LENGTH))
		RANDOM_CHAR = random.choice(CODE_LIST_LOWER) 
		ESTRING_LIST = list(ESTRING)
		ESTRING_LIST.insert(RANDOM_INC_NUMBER, RANDOM_CHAR)
		ESTRING = ''.join(map(str, ESTRING_LIST))
		ESTRING_LENGTH = len(ESTRING)
	return ESTRING

def combine_random_code(ESTRING, ECODE_LENGTH=100):
	ESTRING_LENGTH = len(str(ESTRING))
	while (ESTRING_LENGTH < ECODE_LENGTH):
		RANDOM_INC_NUMBER = random.randint(0,int(ESTRING_LENGTH))
		RANDOM_CHAR = random.choice(string.ascii_uppercase) 
		ESTRING_LIST = list(ESTRING)
		ESTRING_LIST.insert(RANDOM_INC_NUMBER, RANDOM_CHAR)
		ESTRING = ''.join(map(str, ESTRING_LIST))
		ESTRING_LENGTH = len(ESTRING)
	return ESTRING

def validate_uuid4(uuid_string, response_type=None):
    try:
        uuidVal = UUID(str(uuid_string), version=4) 
    except ValueError:
        return False
    
    if response_type:
    	return uuidVal
    else:
    	return True

def encode_page_url(user_id, keyword_id, uuid_val):
	_uuid__val_ = validate_uuid4(uuid_val, "UUID") 
	if _uuid__val_:
		AUTH_USER_IDS = short_random_code(str(user_id))
		AUTH_KEY_IDS = short_random_code(str(keyword_id)) 
		AUTH_UUID_HEX = _uuid__val_.hex
		AUTH_CODE = str(AUTH_USER_IDS)+str(AUTH_UUID_HEX)+str(AUTH_KEY_IDS)
		AUTH_ENCRYPT = base64E(combine_random_code(AUTH_CODE))
		return AUTH_ENCRYPT

	return "-"