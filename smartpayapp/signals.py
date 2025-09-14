from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver
from .models import Profile


# ================================================================
# User  & Profile Signal Handlers
# ================================================================
@receiver(post_save, sender=User)
def manage_user_profile(sender, instance, created, **kwargs):
    """
    Signal: Fired whenever a User is saved.

    - On creation → ensure a Profile is created for the new user.
    - On update   → ensure the linked Profile is saved (keeps profile in sync).
    """
    if created:
        # Create profile if user is new (safe against duplicates)
        Profile.objects.get_or_create(user=instance)
    else:
        # Save existing profile if user details are updated
        if hasattr(instance, "profile"):
            instance.profile.save()

