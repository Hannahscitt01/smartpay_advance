from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver
from .models import Profile, Employee

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Signal to automatically create a Profile (and optional Employee) 
    whenever a new User is created.

    - Profile is always created.
    - Employee is created if not assigned manually by HR/admin.
    - Role is stored in Employee, not Profile.
    """
    if created:
        # 1️⃣ Create a default Employee (if you want automatic role assignment)
        employee = Employee.objects.create(
            full_name=instance.username,  # default to username
            email=instance.email,
            role="employee"
        )

        # 2️⃣ Create Profile and link to Employee
        Profile.objects.create(user=instance, employee=employee)

    else:
        # Optional: sync profile on User updates
        if hasattr(instance, "profile"):
            instance.profile.save()
