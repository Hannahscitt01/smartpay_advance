from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.validators import MinValueValidator  
from django.utils import timezone


# ================================================================
# Profile Model
# ================================================================
class Profile(models.Model):
    """
    Extension of the built-in Django User model to store 
    additional staff-related information.
    - Links each User account to an Employee record (if available).
    - Defines staff role (Admin/Staff).
    - Stores a profile picture with a default avatar fallback.
    """

    ROLE_CHOICES = (
        ("ADMIN", "Admin"),
        ("STAFF", "Staff"),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    employee = models.OneToOneField("Employee", on_delete=models.SET_NULL, null=True, blank=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default="STAFF")
    profile_picture = models.ImageField(
        upload_to="profile_pics/",
        default="profile_pics/default_avatar.png",
        blank=True,
        null=True
    )

    def __str__(self):
        """Readable representation using employee name if available, else fallback to username."""
        if self.employee:
            return f"{self.employee.full_name} ({self.role})"
        return f"{self.user.username} ({self.role})"


# ================================================================
# Salary Advance Request Model
# ================================================================
class SalaryAdvanceRequest(models.Model):
    """
    Stores salary advance requests made by staff.
    - Links the request to a User.
    - Tracks amount, reason, request date, and approval status.
    """

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
        """Return username and requested amount for quick identification."""
        return f"{self.user.username} - {self.amount}"


# ================================================================
# Employee Model
# ================================================================
class Employee(models.Model):
    """
    Core employee database model containing personal, employment,
    and contact details.
    - Staff ID is auto-generated if not provided.
    - Age is auto-calculated from date of birth.
    - Used to link HR records to User accounts and Profiles.
    """

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
    dob = models.DateField(null=True, blank=True)  # Date of Birth (optional for migration safety)
    age = models.PositiveIntegerField(null=True, blank=True)  # Auto-calculated on save()

    # ---------------- Employment Info ----------------
    staff_id = models.CharField(max_length=10, unique=True, blank=True)  # Auto-generated if empty
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
        """
        Custom save() logic:
        - Automatically calculates employee age if DOB is provided.
        - Generates a staff ID in format 'SP-XXXX' if not already set.
        """
        if self.dob:
            today = timezone.now().date()
            self.age = today.year - self.dob.year - (
                (today.month, today.day) < (self.dob.month, self.dob.day)
            )

        if not self.staff_id:
            latest_id = Employee.objects.all().count() + 1
            self.staff_id = f"SP-{latest_id:04d}"  # e.g., SP-0001

        super().save(*args, **kwargs)

    def __str__(self):
        """Return full name with staff ID for easy reference."""
        return f"{self.full_name} ({self.staff_id})"


# ================================================================
# Signals - Auto Profile Creation
# ================================================================
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Automatically create a Profile for each new User instance.
    Defaults the role to 'STAFF'.
    """
    if created:
        Profile.objects.create(user=instance, role="STAFF")

# ================================================================
# Loan Request Mode;
# ================================================================
class LoanRequest(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    repayment_period = models.IntegerField(help_text="Repayment period in months")
    reason = models.TextField(blank=True, null=True)
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2, default=10.0)  # 10% p.a.
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20,
        choices=[("Pending", "Pending"), ("Approved", "Approved"), ("Rejected", "Rejected")],
        default="Pending"
    )

    def __str__(self):
        return f"LoanRequest({self.employee.staff_id} - {self.amount})"



# ================================================================
# Chat Message Model
# ================================================================
class ChatMessage(models.Model):
    sender = models.ForeignKey(User, related_name="sent_messages", on_delete=models.CASCADE)
    receiver = models.ForeignKey(User, related_name="received_messages", on_delete=models.CASCADE)
    message = models.TextField()
    timestamp = models.DateTimeField(default=timezone.now)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"From {self.sender.username} to {self.receiver.username} at {self.timestamp}"


# ================================================================
# Support Query Model
# ================================================================

class SupportChatMessage(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name="support_sent")
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name="support_received")
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"SupportChat from {self.sender.username} to {self.receiver.username}"
