from django.db import models
from django.contrib.auth.hashers import make_password, check_password
import uuid 

class TeamAccount(models.Model):
    id = models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")
    fk_user = models.ForeignKey('account.Account', on_delete=models.CASCADE)
    name = models.CharField(max_length=30)
    email = models.EmailField(verbose_name="email", max_length=60, unique=True,error_messages={'unique': "User with this email already exists.",})
    # Django's PBKDF2 hashes are longer than the original 30-character field.
    password = models.CharField(max_length=128)
    role = models.CharField(max_length=30)
    role_id = models.IntegerField(default=0)
    white_label = models.JSONField(default=dict)
    last_logout = models.DateTimeField(verbose_name='last logout',null=True)
    # Indexed because it is looked up by value on every request a team member
    # makes: account/authentication.py falls through to this when the owner
    # token misses, and account/ownership.py does the same lookup again. The
    # owner side was already covered -- authtoken_token.key is DRF's primary
    # key -- but this was a collection scan proportional to the number of
    # members on the instance.
    token = models.UUIDField(default = uuid.uuid4, editable = False, db_index=True)
    created_date = models.DateTimeField(auto_now_add=True, auto_now=False)
    modified_date = models.DateTimeField(auto_now_add=False, auto_now=True)

    def set_password(self, raw_password):
        self.password = make_password(raw_password)
    
    def check_password(self, raw_password):
        return check_password(raw_password, self.password)

    def __str__(self):
        return self.name
    
    class Meta:
        db_table = "team_account"

class TeamProject(models.Model):
    fk_user = models.ForeignKey('account.Account', on_delete=models.CASCADE)
    client = models.ForeignKey(TeamAccount, on_delete=models.CASCADE)
    group = models.IntegerField(default=0)
    created_date = models.DateTimeField(auto_now_add=True, auto_now=False)
    modified_date = models.DateTimeField(auto_now_add=False, auto_now=True)

    class Meta:
        db_table = "team_projects"


# Create your models here.
