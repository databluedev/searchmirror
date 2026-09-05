from account import verify as authPermission
from serp.models import Roles, Account
from django.http import JsonResponse, HttpResponse
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.views import APIView
from rest_framework.decorators import api_view
import json
from rest_framework.decorators import permission_classes
from team_management.models import TeamAccount
from account.team_permissions import TEAM_MODULES


def _valid_modules(modules):
    return (
        isinstance(modules, dict)
        and set(modules).issubset(TEAM_MODULES)
        and all(isinstance(actions, list) for actions in modules.values())
        and "Prjcts" in modules
    )

# def create_role(request):
#     try:
#         if request.method=='POST' and authPermission.validate(request, 'POST'):
#             if set(request.data).issubset({'userid', 'rl', 'desc', 'mdles'}):
#                 userid = request.data.get('userid')
#                 role = request.data.get('rl', '')
#                 desc = request.data.get('desc', '')
#                 modules = request.data.get('mdles')
#                 if userid:
#                     acc = Account.objects.get(id=userid)
#                     role = Roles(fk_user=acc, role={'rl':role, 'desc':desc}, modules=modules)
#                     role.save()
#                     return JsonResponse({'st':1, 'dt':'Role Created'})
#         return JsonResponse({'st':404, 'dt':'Something went wrong'})
#     except Exception as e:
#         print(f"create_role {str(e)}")
#         return JsonResponse({'st':404, 'dt':'Something went wrong'})
    

class MyView(APIView):
    """Role list / create / update for the account that owns them.

    Was `View`, not `APIView`. `permission_classes` on a plain Django View is
    an attribute nothing reads, so GET served anyone -- verified live: an
    unauthenticated GET /my_view/ returned 200 with the role list. POST and PUT
    hand-rolled their own check by comparing the Authorization header against
    the Token row for the userid in the BODY, which is the same comparison
    UserIdOwnershipMiddleware now makes for every view at once.

    As an APIView the DRF defaults finally apply -- TokenAuthentication plus
    IsAuthenticated -- so the hand-rolled comparison is gone rather than left
    beside the real one.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            if request.GET.get('userid'):
                userid = request.GET.get('userid')
                roles = list(Roles.objects.filter(fk_user_id=userid).values('role', 'modules', 'id').all())
                roles = [{'rl_id': i['id'], 'rl': i['role'], 'mdles': i['modules']} for i in roles]
                return JsonResponse({'st': 1, 'dt': roles})
            return JsonResponse({'st': 404, 'dt': 'Something went wrong'})
        except Exception:
            return JsonResponse({'st': 404, 'dt': 'Something went wrong'})

    def post(self, request):
        try:
            data = request.data
            userid = data.get('userid')
            if userid and set(data.keys()).issubset({'id', 'userid', 'rl', 'mdles'}):
                role = data.get('rl', '')
                modules = data.get('mdles')
                if not role.strip() or not _valid_modules(modules):
                    return JsonResponse({'st': 0, 'dt': 'Role and permissions are required'})
                if Roles.objects.filter(fk_user_id=userid, role=role.casefold()).exists():
                    return JsonResponse({'st': 0, 'dt': 'Role already existed'})
                acc = Account.objects.get(id=userid)
                Roles(fk_user=acc, role=role.casefold(), modules=modules).save()
                return JsonResponse({'st': 1, 'dt': 'Role Created'})
            return JsonResponse({'st': 404, 'dt': 'Something went wrong'})
        except Exception:
            return JsonResponse({'st': 404, 'dt': 'Something went wrong'})

    def put(self, request):
        try:
            data = request.data
            userid = data.get('userid')
            if userid and set(data.keys()).issubset({'id', 'userid', 'rl', 'mdles'}):
                role_id = data.get('id')
                role = data.get('rl', '')
                modules = data.get('mdles')
                if not role.strip() or not _valid_modules(modules):
                    return JsonResponse({'st': 0, 'dt': 'Role and permissions are required'})
                if Roles.objects.filter(fk_user_id=userid, role=role.casefold()).exclude(id=role_id).exists():
                    return JsonResponse({'st': 0, 'dt': 'Role already existed'})
                role_instance = Roles.objects.get(id=role_id, fk_user_id=userid)
                role_instance.role = role.casefold()
                role_instance.modules = modules
                role_instance.save()
                TeamAccount.objects.filter(
                    fk_user_id=userid, role_id=role_id
                ).update(role=role.casefold())
                return JsonResponse({'st': 1, 'dt': 'Role Updated'})
            return JsonResponse({'st': 404, 'dt': 'Something went wrong'})
        except Exception:
            return JsonResponse({'st': 404, 'dt': 'Something went wrong'})

@api_view(['POST'])
@permission_classes((IsAuthenticated,))
def role_delete(request):
    try:
        if request.method=='POST' and authPermission.validate(request, "POST"):
            if set(request.data).issubset({'userid', 'rl_id'}):
                userid = request.data.get('userid')
                role = request.data.get('rl_id')
                if userid and role:
                    owned_role = Roles.objects.filter(id=role, fk_user_id=userid)
                    if TeamAccount.objects.filter(fk_user_id=userid, role_id=role).exists():
                        return JsonResponse({'st':0, 'dt':"Role is assigned to a team member"})
                    if owned_role.exists():
                        owned_role.delete()
                        return JsonResponse({'st':1, 'dt':"Role Deleted Successfully"})
                    else:
                        return JsonResponse({'st':0, 'dt':"Role doesn't exist"})
        return JsonResponse({'st':404, 'dt':"Something went wrong"})
    except Exception as e:
        return JsonResponse({'st':404, 'dt':"Something went wrong"})
