from django.conf import settings
from urllib.parse import urlparse
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.core.mail import send_mail
from serp.models import *
from datetime import date,datetime,timedelta
from math import floor

def totalKeywordsCount(userid):
    usrId = userid
    try:
        AccUsgIns = Accountusage.objects.filter(fb_user_id=usrId).first()
        pln__kwd__lmt = AccUsgIns.plan_keyword_limit
        kwds__usd__cnt = Keyword.objects.filter(fk_user_id=usrId).count()
        bc__kwds__usd__cnt = brandObtain.objects.filter(fk_user_id=usrId).count()
        totl__kwds__cnt = kwds__usd__cnt + bc__kwds__usd__cnt
        kwd__sts = True if pln__kwd__lmt > totl__kwds__cnt else False
        return kwd__sts,totl__kwds__cnt

    except Exception as e:
      return False,0

def userPaymode(userid, AccUsgIns=None):
    """Whether this account may use the product. It always may.

    Tracker is self-hosted and bring-your-own-key: every rank check is billed
    to the operator's own provider key, the plan limits are unmetered, and
    there is nothing to sell. There is therefore no such thing as a lapsed
    account here.

    This used to read UserSubscriptions and return "dead" unless a paid
    subscription row said otherwise, and 35 places in the frontend refuse to add a
    project, add a keyword, run a search or export anything when it does.
    Accountusage.user_type is "custom" or "free" for accounts created by this
    build, which happened to fall through to "free" -- but any row left at
    "trial", "stripe" or "redeem" locked the whole product with no way to pay
    to unlock it.

    The signature is unchanged: 21 call sites outside the payment app unpack
    two values, and the second is the plan-overrun flag, which cannot trip
    against unmetered limits.
    """
    return "free", 0


def f_to_i(value):
    """Round a score for display -- never truncate.

    int() floors, so a project holding one #5 among 29 keywords scored 0.69
    and was shown "0 out of 100", i.e. "you have no visibility" while the
    ranking existed. Every visibility figure goes through here, so the same
    floor also turned 44.9 into 44 on the dashboard and the competitor cards.
    """
    return int(floor(float(value) + 0.5))

def CVF(idVal):   # CHECK VALUE FORMAT
    try: 
        if type(idVal) is list:
            numberList[:] = [int(number - int(settings.UNIQUE_KEYWORD_ID)) for number in idVal]
            return numberList
        elif type(idVal) is int:
            singleNumber = idVal - int(settings.UNIQUE_KEYWORD_ID)
            return singleNumber if singleNumber > 0 else False
    except: 
        pass

    return False

def validate_uuid4(uuid_string):
    try:
        uuidVal = UUID(str(uuid_string), version=4) 
    except ValueError:
        return False

    return True

def checkstatus(num): 
    if num > 0:
        return 'U'        
    elif num == 0:
        return '-'
    else:
        return 'D'

def extract_domain(url, remove_http=True):
    uri = urlparse(url)
    if remove_http:
        domain_name = f"{uri.netloc}"
    else:
        domain_name = f"{uri.scheme}://{uri.netloc}"
    return domain_name

# Add keyword engine.
def host_domain(url, remove_http=True): 
    uri = urlparse(url)
    if remove_http:
        domain_name = f"{uri.netloc}".replace("www.", "") 
    else:
        domain_name = f"{uri.scheme}://{uri.netloc}"
    return domain_name 

# Add keyword engine.
def host_path(url): 
    domain = urlparse(url)
    if domain.path == "":
        domain_name = f"{domain.netloc}".replace("www.", "") 
    elif f"{domain.path}" == "/":
        domain_name = f"{domain.netloc}".replace("www.", "") 
    else:
        domain_name = domain.path
    return domain_name

# Mail Function
def sendMail(template, context, subject, receiver): # 000 
    email_html_message = render_to_string(template, context)
    msg = EmailMultiAlternatives(
        subject, 
        # message:
        "Welcome Content",
        # from:
        settings.HOST_MAIL,
        # to:
        receiver
    )
    msg.attach_alternative(email_html_message, "text/html") 
    return msg.send() 

# Mail record table and refferral page same program
def mail_record_update(userid,email,mailtype):
    mailIns = Mailrecords.objects.filter(userid=userid,types=mailtype)
    if mailIns.exists() == False:
        maildata = Mailrecords()
        maildata.userid = userid
        maildata.types = mailtype
        maildata.mail_list = [email]
        maildata.save()
    elif email not in mailIns[0].mail_list:
        mailIns.update(mail_list = mailIns[0].mail_list + [email])
        # mailIns.mail_list = mailIns.mail_list + [email]
        # mailIns.save(update_fields=['mail_list'])

def isfloat_isdigit(num):
    s = 0
    if num:
        try:
            s = int(num) if num.isdigit() else float(num)
        except ValueError:
            pass

    return s


def last_of_day(date_obj):
    import pytz
    last_minute_day= date_obj.replace(hour=23, minute=59, second=59, tzinfo=pytz.UTC)
    return last_minute_day
