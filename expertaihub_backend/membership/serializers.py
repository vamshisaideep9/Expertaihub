from rest_framework import serializers
from .models import Membership, MonthlyUsage

class MembershipSerializer(serializers.ModelSerializer):
    class Meta:
        model = Membership
        fields = '__all__'
        read_only_fields = ['start_date']


class MonthlyUsageSerializer(serializers.ModelSerializer):
    class Meta:
        model = MonthlyUsage
        fields = '__all__'
        read_only_fields = ['start_date']