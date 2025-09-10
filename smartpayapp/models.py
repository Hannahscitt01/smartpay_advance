from django.db import models
from  django.contrib.auth.models import User
from  django.db.models.signals import post_save
from django.dispatch import receiver

# Create your models here.
class Profile(models.Model):
   ROLE_CHOICE=(("ADMIN","Admin"),
                ("STAFF","Staff"),
                )
   user=models.OneToOneField(User,on_delete=models.CASCADE)
   staffid=models.CharField(max_length=100,unique=True)
   department=models.CharField(max_length=100,blank=True,null=True)
   role=models.CharField(max_length=10,choices=ROLE_CHOICE,default="STAFF")

   def __str__(self):
      return f"{self.user.username} ({self.role})"
   

class SalaryAdvancerequest(models.Model):
    user= models.ForeignKey(User, on_delete=models.CASCADE)
    amount=models.DecimalField(max_digits=10, decimal_places=2)
    reason=models.TextField(blank=True,null=True)
    date_requested=models.DateTimeField(auto_now_add=True)
    status=models.CharField(max_length=20, choices=[("pending","pending",),("Aproved","Aproved"),("Rejected","Rejected")],default="pending")

    def __str__(self):
     return f"{self.user.username}-{self.amout}"