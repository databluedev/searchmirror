from serp.models import DomainTracking
from rest_framework import serializers
from serp.models import *

class DomainTrackSerializer(serializers.Serializer):

    class Meta:
        model = DomainTracking

    def to_representation(self, instance):
        # Customize the representation of the Book model
        representation = super().to_representation(instance)
        representation["da_metrics"] = instance["da_metrics"][::-1] if self.context.get('order_by') =="asc" else instance["da_metrics"]
        representation["dr_metrics"] = instance["dr_metrics"][::-1] if self.context.get('order_by') =="asc" else instance["dr_metrics"]
        if instance['page_speed_metrics'] != None:
            representation["page_speed_metrics"] = instance["page_speed_metrics"][::-1] if self.context.get('order_by') =="asc" else instance["page_speed_metrics"]

        return representation

class GSCWeeklyQDataSerializer(serializers.Serializer):

    class Meta:
        model = GSCWeeklyQuery

    def to_representation(self, instance):
        # Customize the representation of the Book model
        representation = super().to_representation(instance)
        representation["week_start_date"] = instance["week_start_date"]
        representation["week_end_date"] = instance["week_end_date"]
        representation["queries"] = instance["queries"]
        representation["pages"] = instance["pages"]
        representation['overview'] = instance['overview']

        return representation


class GSCMonthlyQDataSerializer(serializers.Serializer):

    class Meta:
        model = GSCMonthlyQuery

    def to_representation(self, instance):
        # Customize the representation of the Book model
        representation = super().to_representation(instance)
        representation["month_start_date"] = instance["month_start_date"]
        representation["month_end_date"] = instance["month_end_date"]
        representation["queries"] = instance["queries"]
        representation["pages"] = instance["pages"]
        representation['overview'] = instance['overview']

        return representation