from django.contrib import admin
from .models import Profile, SalaryAdvanceRequest, Employee, LoanRequest

# Register your models here.
admin.site.register(Profile)
admin.site.register(SalaryAdvanceRequest)
admin.site.register(Employee)
admin.site.register(LoanRequest)
