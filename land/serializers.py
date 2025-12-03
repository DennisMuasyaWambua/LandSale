from rest_framework import serializers
from .models import Land

class LandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Land
        fields = '__all__'