from django.db.models.signals import pre_save ,post_save, post_delete
from django.contrib.auth.models import User
from django.dispatch import receiver
from django.utils import timezone
from .models import Profile, Employee, Role, Department,Project,ProjectLog
from django.utils.crypto import get_random_string

# ================================================================
# Create Profile and linked Employee when a new User is created
# ================================================================
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Safely create a Profile and linked Employee for new users if they don't exist.
    """
    if created:
        # Skip if a Profile already exists (prevents duplicates)
        if hasattr(instance, 'profile'):
            return

        # ---------------- Create or get default department ----------------
        default_department, _ = Department.objects.get_or_create(name="General")
        
        # ---------------- Create or get default role ----------------
        default_role, _ = Role.objects.get_or_create(name="employee")
        
        # ---------------- Create Employee if it doesn't exist ----------------
        employee, _ = Employee.objects.get_or_create(
            email=instance.email,
            defaults={
                'full_name': instance.get_full_name() or instance.username,
                'department': default_department,
                'job_title': "Employee",
                'employment_type': "Permanent",
                'role': default_role,
                'salary': 0.0,
                'date_joined': timezone.now(),
            }
        )
        
        # ---------------- Create Profile linked to Employee ----------------
        Profile.objects.get_or_create(user=instance, defaults={'employee': employee})


# ================================================================
# Sync Employee info when User is updated
# ================================================================
@receiver(post_save, sender=User)
def update_user_employee(sender, instance, **kwargs):
    profile = getattr(instance, 'profile', None)
    if profile and profile.employee:
        employee = profile.employee
        employee.full_name = instance.get_full_name() or employee.full_name
        employee.email = instance.email or employee.email
        employee.save()


# ================================================================
# Cleanup linked Profile and Employee when a User is deleted
# ================================================================
@receiver(post_delete, sender=User)
def delete_user_profile(sender, instance, **kwargs):
    profile = getattr(instance, 'profile', None)
    if profile:
        employee = profile.employee
        profile.delete()
        if employee:
            employee.delete()


@receiver(pre_save, sender=Project)
def generate_order_id(sender, instance, **kwargs):
    if not instance.order_id:
        # Example: PRJ-YYYYMMDD-RANDOM
        date_str = timezone.now().strftime("%Y%m%d")
        random_str = get_random_string(length=5).upper()
        instance.order_id = f"PRJ-{date_str}-{random_str}"


@receiver(post_save, sender=Project)
def log_project_creation(sender, instance, created, **kwargs):
    if created:
        ProjectLog.objects.create(
            project=instance,
            action_by=instance.created_by,
            action_type="Project Created",
            notes=f"Project '{instance.name}' created and assigned to departments: {', '.join([d.name for d in instance.departments.all()])}"
        )
