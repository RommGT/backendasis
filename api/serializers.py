from rest_framework import serializers
from .models import Api, AttendanceRecord


class ApiSerializer(serializers.ModelSerializer):
    class Meta:
        model = Api
        fields = ('id','title','description','technology','created_at')
        read_only_fields = ('created_at',)

class AttendanceRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = AttendanceRecord
        fields = '__all__'