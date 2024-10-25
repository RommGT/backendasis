from django.db import models

# Create your models here.
class Api(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    technology = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)

class AttendanceRecord(models.Model):
    email = models.EmailField()
    class_name = models.CharField(max_length=100)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.email} attended {self.class_name} at {self.timestamp}"