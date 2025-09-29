from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver
from .models import Profile


@receiver(post_save, sender=User)
def manage_user_profile(sender, instance, created, **kwargs):
    """
    Signal: Fired whenever a User is saved.

    - On creation → create Profile with default role 'employee'.
    - Role stays 'employee' unless HR updates the linked Employee's department.
    - Admin role must be manually assigned in the DB or via superuser creation.
    """
    if created:
        # Always default to employee (not admin)
        profile, _ = Profile.objects.get_or_create(user=instance, role="employee")

        # If linked Employee exists, adjust role
        if profile.employee:
            if profile.employee.department == "Finance":
                profile.role = "finance"
            elif profile.employee.department == "HR":
                profile.role = "hr"
            else:
                profile.role = "employee"  # fallback
            profile.save()
    else:
        # Sync profile on user update
        if hasattr(instance, "profile"):
            instance.profile.save()
