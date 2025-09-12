from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.validators import MinValueValidator  
from django.utils import timezone

# Create your models here.


#User profile creation model to handle role based access of either a staff or an admin
class Profile(models.Model):
    ROLE_CHOICES = (
        ("ADMIN", "Admin"),
        ("STAFF", "Staff"),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    staffid = models.CharField(max_length=100, unique=True)
    department = models.CharField(max_length=100, blank=True, null=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default="STAFF")

    def __str__(self):
        return f"{self.user.username} ({self.role})"
    
    
class SalaryAdvanceRequest(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reason = models.TextField(blank=True, null=True)
    date_requested = models.DateTimeField(null=True, auto_now_add=True)
    status = models.CharField(
        max_length=20,
        choices=[("Pending", "Pending"), ("Approved", "Approved"), ("Rejected", "Rejected")],
        default="Pending"
    )

    def __str__(self):
        return f"{self.user.username} - {self.amount}"


class Employee(models.Model):
    EMPLOYMENT_TYPES = [
        ('Permanent', 'Permanent'),
        ('Contract', 'Contract'),
        ('Internship', 'Internship'),
    ]

    DEPARTMENTS = [
        ('Finance', 'Finance'),
        ('HR', 'HR'),
        ('IT', 'IT'),
        ('Operations', 'Operations'),
    ]

    # ---------------- Personal Info ----------------
    full_name = models.CharField(max_length=150)
    national_id = models.CharField(max_length=20, unique=True)
    dob = models.DateField(null=True, blank=True)  # nullable for migration safety
    age = models.PositiveIntegerField(null=True, blank=True)  # auto-calculated

    # ---------------- Employment Info ----------------
    staff_id = models.CharField(max_length=10, unique=True, blank=True)  # auto-generated
    date_joined = models.DateField(default=timezone.now)
    department = models.CharField(max_length=50, choices=DEPARTMENTS)
    job_title = models.CharField(max_length=100)
    employment_type = models.CharField(max_length=20, choices=EMPLOYMENT_TYPES)
    salary = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )

    # ---------------- Contact Info ----------------
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20)
    address = models.TextField(blank=True, null=True)

    # ---------------- Save Method ----------------
    def save(self, *args, **kwargs):
        # Auto-calculate age if DOB is provided
        if self.dob:
            today = timezone.now().date()
            self.age = today.year - self.dob.year - ((today.month, today.day) < (self.dob.month, self.dob.day))

        # Auto-generate staff_id if not set
        if not self.staff_id:
            latest_id = Employee.objects.all().count() + 1
            self.staff_id = f"SP-{latest_id:04d}"  # e.g., SP-0001

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.full_name} ({self.staff_id})"


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(
            user=instance,
            staffid=f"STAFF-{instance.id}",   # auto-generate staffid
            department="",                    # or default department
            role="STAFF"
        )