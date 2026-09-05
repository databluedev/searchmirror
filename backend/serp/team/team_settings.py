from serp.models import *
from team_management.models import *
from django.http import JsonResponse
from rest_framework.decorators import api_view
from account import verify as authPermission
from django.views import View
from rest_framework.views import APIView
from django.views.decorators.csrf import csrf_exempt
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
import json
from django.utils.decorators import method_decorator
from rest_framework.decorators import permission_classes

@api_view(['POST'])
@permission_classes((IsAuthenticated,))
def get_team(request):
    try:
        if request.method=='POST' and authPermission.validate(request, 'POST'):
            userid = request.data.get('userid')
            if userid:
                tm_dtls = list()
                teams = TeamAccount.objects.filter(fk_user_id=userid).prefetch_related('teamproject_set').order_by('-created_date')
                for team in teams:
                    tm={'nm':team.name, 'clml':team.email, 'prnt': team.fk_user_id, 'isSelectorDisabled': int(team.fk_user_id)==int(userid), 'rl': team.role, 'rl_id': team.role_id, 'prjcts':[i.group for i in team.teamproject_set.filter(fk_user_id=userid, client_id=team.id)]}
                    tm_dtls.append(tm)
                return JsonResponse({'st':1, 'dt':tm_dtls})
        return JsonResponse({'st':404, 'dt': 'Something went wrong'})
    except Exception as e:
        # print(request)
        print(f"{str(e)}")
        return JsonResponse({'st':404, 'dt': 'Something went wrong'})
    
@api_view(['POST'])
@permission_classes((IsAuthenticated,))
def delete_team(request):
    try:
        if request.method=='POST' and authPermission.validate(request, 'POST'):
            if set(request.data).issubset({'userid', 'email'}):
                userid = request.data['userid']
                email = request.data['email']
                if userid and email:
                    owned_team = TeamAccount.objects.filter(fk_user_id=userid, email=email)
                    if owned_team.exists():
                        owned_team.delete()
                        return JsonResponse({'st':1, 'dt':'Account Deleted'})
        return JsonResponse({'st':404, 'dt':'Something went wrong'})
    except Exception as e:
        print(f'{str(e)}')
        return JsonResponse({'st':404, 'dt': 'Something went wrong'})

@api_view(["POST"])
@permission_classes((IsAuthenticated,))
def manage_projects(request):
    try:
        if request.method == "POST" and authPermission.validate(request, "POST"):
            if set(request.data).issubset({'userid', 'em', 'prjcts', 'type'}):
                userid = request.data.get('userid')
                email = request.data.get('em')
                projects = request.data.get('prjcts')
                new_grps = list()
                project_added = False
                if userid and email:
                    team = TeamAccount.objects.filter(fk_user_id=userid, email=email).prefetch_related('teamproject_set').first()
                    if team is None:
                        return JsonResponse({'st':0, 'dt':'Team member does not exist'})
                    owned_projects = set(
                        Groups.objects.filter(fk_user_id=userid, id__in=projects).values_list('id', flat=True)
                    )
                    requested_projects = {int(project) for project in projects}
                    if owned_projects != requested_projects:
                        return JsonResponse({'st':0, 'dt':'One or more projects do not belong to this account'})
                    remvble_grp = team.teamproject_set.filter(Q(fk_user_id=userid), Q(client=team.id), ~Q(group__in=projects)).delete()
                    ex_grps=[i['group'] for i in team.teamproject_set.filter(fk_user_id=userid, client=team.id).values('group').all()]
                    # if ex_grps:
                    for i in projects:
                        if i not in ex_grps:
                            new_grps.append(TeamProject(group=i, client=team, fk_user_id=userid))
                    project_added=TeamProject.objects.bulk_create(new_grps)
                    if remvble_grp[0] or project_added:
                        return JsonResponse({'st':1, 'dt':'Project Updated'})
                    else:
                        return JsonResponse({'st':0, 'dt': 'Projects already exists'})
        return JsonResponse({'st':404, 'dt':'Something went wrong'})
    except Exception as e:
        print(f"Error from reset_client {str(e)}")
        return JsonResponse({'st':404, 'dt':'Something went wrong'})
    
class TeamView(APIView):
    permission_classes = (IsAuthenticated,)

    # CREATE TEAM
    def post(self, request):
        try:
            if request.method=='POST' and authPermission.validate(request, 'POST'):
                if set(request.data).issubset({'userid', 'nm', 'eml', 'pass', 'role', 'rl_id'}):
                    userid = request.data['userid']
                    team_name = request.data['nm']
                    email = request.data['eml']
                    password = request.data['pass']
                    role = request.data['role']
                    rl_id = request.data['rl_id']
                    owned_role = Roles.objects.filter(
                        id=rl_id, fk_user_id=userid, role=role
                    ).first()
                    if owned_role is None:
                        return JsonResponse({'st':0, 'dt': 'Select a role owned by this account'})
                    if len(team_name.strip()) < 3 or len(password) < 8:
                        return JsonResponse({'st':0, 'dt': 'Name or password is too short'})
                    if TeamAccount.objects.filter(email=email).exists() or Account.objects.filter(email=email).exists():
                        return JsonResponse({'st':0, 'dt': 'Account already exists'})
                    acc_instance = Account.objects.get(id=userid)
                    new_team = TeamAccount(fk_user=acc_instance, name=team_name.strip(), email=email.lower(), role=owned_role.role, role_id=rl_id)
                    new_team.set_password(password)
                    new_team.save()
                    return JsonResponse({'st':1, 'dt': 'Team Created Successfully'})
                else:
                    return JsonResponse({'st':0, 'dt': 'One of the field is missing.'})
            return JsonResponse({'st':404, 'dt': 'Something went wrong'})
        except Exception as e:
            print(f"{str(e)}")
            return JsonResponse({'st':404, 'dt': 'Something went wrong'})

class TeamEdit(APIView):
    """Rename a team member or reset their password.

    Was `View`, not `APIView`, while its neighbour TeamView was already an
    APIView. On a plain Django View `permission_classes` is an attribute
    nothing reads, so this had NO authentication of any kind: an anonymous
    PUT reached the body and, given a real member's address, reset that
    member's password. Verified live -- an unauthenticated PUT returned this
    view's own 200 JSON rather than a 401.

    IsAuthenticated now applies, and UserIdOwnershipMiddleware ties the
    userid in the body to the caller's token.
    """

    permission_classes = [IsAuthenticated]

    def put(self, request):
        try:
            data = request.data
            if set(data.keys()).issubset({'userid', 'pass', 'nm', 'type', 'email'}):
                ed_type = data.get('type')
                userid = data.get('userid')
                email = data.get('email')
                password = data.get('pass')
                name = data.get('nm')
                if userid:
                    team_acc = TeamAccount.objects.get(fk_user_id=userid, email=email)
                    if ed_type == 'pass':
                        team_acc.set_password(password)
                        team_acc.save()
                        return JsonResponse({'st':1, 'dt': 'Password Changed successfully'})
                    elif ed_type == 'nm':
                        team_acc.name = name
                        team_acc.save()
                        return JsonResponse({'st':1, 'dt': 'Name Changed successfully'})
            return JsonResponse({'st':404, 'dt': 'Something went wrong'})
        except Exception as e:
            return JsonResponse({'st':404, 'dt': 'Something went wrong'})
