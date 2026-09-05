from django.conf import settings
from rest_framework.decorators import api_view

from serp.models import *
from serp.common import *
from serp.custom_serializer.notes_serializers import *

from account import verify as authPermission
from django.http import HttpResponse,JsonResponse 
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone

def get_date(dateTime):
    return str(timezone.localtime(dateTime).date())

@api_view(['POST'])
@permission_classes((IsAuthenticated,))
def delete_note(request):
    try:
        if request.method == 'POST' and authPermission.validate(request, "POST"):
            userid = str(request.data['userid'])
            grpid = str(request.data['grpid'])
            kid = str(request.data['kky'])
            nid = str(request.data['nky']) 

            if userid.isdigit() and grpid.isdigit() and kid.isdigit() and nid.isdigit(): 

                if int(nid) > 0:
                    noteupdate = kwNotes.objects.filter(id=nid, fk_keyword_id=kid, fk_user_id=userid, fk_group_id=grpid).delete()
                    
                    notes_data = kwNotes.objects.filter(fk_keyword_id=kid, fk_user_id=userid, fk_group_id=grpid).values("id", "title", "notes", "note_date", "fk_keyword_id").order_by("-created_date").all()
                    notes_count = kwNotes.objects.filter(fk_keyword_id=kid, fk_user_id=userid, fk_group_id=grpid).count() 

                    serializer_data = ViewNoteSerializer(notes_data, many=True).data
                    notes_data = list(filter(None, serializer_data))

                    return JsonResponse({'st': 1, 'ct': notes_count, 'dt': notes_data, 'ms': "Notes deleted successfully"}) 
    except Exception as e:
        return JsonResponse({'st': -1, 'ms': 'Error, try again later'}) 
                
    return JsonResponse({'st': 0, 'ms': 'Something went wrong'}) 

@api_view(['POST'])
def view_all_notes(request):
    try:    
        if request.method == 'POST' and authPermission.validate(request, "POST"):
            userid = str(request.data['userid'])  
            grpid = str(request.data['grpid'])
            kid = str(request.data['kid'])
            dataType = str(request.data['type']) if 'type' in request.data else None
                        
            if userid and grpid and kid:

                if userid.isdigit() and grpid.isdigit() and kid.isdigit():
                    noteDateList = kwNotes.objects.filter(fk_keyword_id=kid).values_list('note_date', flat=True) 
                    notes_count = kwNotes.objects.filter(fk_keyword_id=kid, fk_user_id=userid, fk_group_id=grpid).count()  

                    if noteDateList:
                        noteDateList = list(set(map(get_date, noteDateList)))
                        noteDateList.sort()
                    else:
                        noteDateList = list()
                    
                    if dataType == "cnt":
                        return JsonResponse({'st': 1, 'ct': notes_count, "nl": noteDateList})

                    notes_data = kwNotes.objects.filter(fk_keyword_id=kid, fk_user_id=userid, fk_group_id=grpid).values("id", "title", "notes", "note_date", "fk_keyword_id").order_by("-created_date").all()
                    serializer_data = ViewNoteSerializer(notes_data, many=True).data
                    notes_data = list(filter(None, serializer_data))

                    return JsonResponse({'st': 1, 'ct': notes_count, 'dt': notes_data, "nl": noteDateList})  
    
    except Exception as e:
        return JsonResponse({'status': -1, 'dt': 'Error, try again later'}) 


    return JsonResponse({'status': 0, 'dt': 'Something went wrong'})
