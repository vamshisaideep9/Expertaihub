from rest_framework import serializers
from .models import Advisor, Country

class AdvisorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Advisor
        fields = ["id", "name", "slug", "description", "is_active"]
        read_only_fields = ["slug"]

class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = ["id", "name", "code", "is_active"]