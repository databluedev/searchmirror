from rest_framework import serializers

from account.models import Account
from django.db.models import Q
from django.utils import timezone

class RegistrationSerializer(serializers.ModelSerializer):

	password2 = serializers.CharField(style={'input_type': 'password'}, write_only=True)

	class Meta:
		model = Account
		# fields = ['email', 'username', 'designation','password', 'password2']
		fields = ['email', 'username', 'designation','password', 'password2', 'campaign', 'medium', 'source', 'referral']
		# save() already treats all five as optional, but ModelSerializer makes
		# a CharField required at VALIDATION time unless told otherwise -- and
		# validation runs first. So signup answered "This field may not be
		# blank." for a job title and four campaign-attribution fields that
		# nothing requires. Declaring them optional here is what makes the
		# serializer agree with its own save().
		_OPTIONAL = {'required': False, 'allow_blank': True}
		extra_kwargs = {
			'password': {'write_only': True},
			'designation': _OPTIONAL,
			'campaign': _OPTIONAL,
			'medium': _OPTIONAL,
			'source': _OPTIONAL,
			'referral': _OPTIONAL,
		}	


	def	save(self):

		account = Account(
					email=self.validated_data['email'],
					username=self.validated_data['username']
				)
		password = self.validated_data['password']
		password2 = self.validated_data['password2']
		# Everything below is optional. Reading them with [] raised KeyError out
		# of the serializer, so the PUBLIC signup endpoint answered 500 -- not a
		# validation error -- whenever a client posted without them. designation
		# is a job title and the other four are campaign attribution; none of
		# them is something registration should refuse to proceed without.
		designation = self.validated_data.get('designation', '')
		campaign = self.validated_data.get('campaign', '')
		medium = self.validated_data.get('medium', '')
		source = self.validated_data.get('source', '')
		referral = self.validated_data.get('referral', '')
		if password != password2:
			raise serializers.ValidationError({'password': 'Passwords must match'})
		account.set_password(password)
		account.google_id="-"
		account.designation = designation
		account.account_status="normal"
		account.normal_mode="enable"
		account.social_mode="disable"
		account.last_login = timezone.now()
		account.last_logout = timezone.now()
		# new details
		account.campaign = campaign
		account.medium = medium
		account.source = source
		account.referral = referral
		# new details
		account.save()
		return account 


class ChangePasswordSerializer(serializers.Serializer):

	old_password 				= serializers.CharField(required=True)
	new_password 				= serializers.CharField(required=True)
	confirm_new_password 		= serializers.CharField(required=True)
