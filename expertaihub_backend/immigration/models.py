# # app/models.py
# from django.contrib.auth import get_user_model
# from django.db import models


# User = get_user_model()

# class Case(models.Model):
#     user = models.ForeignKey(User, on_delete=models.CASCADE)
#     receipt_number = models.CharField(max_length=50, unique=True)
#     current_status = models.CharField(max_length=255, blank=True)
#     last_checked = models.DateTimeField(auto_now=True)

# class CaseHistory(models.Model):
#     case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name='history')
#     status = models.CharField(max_length=255)
#     timestamp = models.DateTimeField(auto_now_add=True)