from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.validators import MinValueValidator
from django.utils import timezone

from datetime import datetime, time
from django.db.models import Sum


# ================================================================
# Employee Model (Created by HR)
# ================================================================

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

    ROLES = [
        ("admin", "Admin"),
        ("hr", "HR"),
        ("finance", "Finance"),
        ("employee", "Employee"),
    ]

    # ---------------- Personal Info ----------------
    full_name = models.CharField(max_length=150)
    national_id = models.CharField(max_length=20, unique=True)
    dob = models.DateField(null=True, blank=True)
    age = models.PositiveIntegerField(null=True, blank=True)  

    # ---------------- Employment Info ----------------
    staff_id = models.CharField(
        max_length=20,
        unique=True,
        editable=False,
        blank=True,
        null=True,
    )
    date_joined = models.DateField(default=timezone.now)
    department = models.CharField(max_length=50, choices=DEPARTMENTS)
    job_title = models.CharField(max_length=100)
    employment_type = models.CharField(max_length=20, choices=EMPLOYMENT_TYPES)
    salary = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )

    # ---------------- Role Info ----------------
    role = models.CharField(max_length=20, choices=ROLES, default="employee")

    # ---------------- Contact Info ----------------
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20)
    address = models.TextField(blank=True, null=True)

    def save(self, *args, **kwargs):
        # --- Auto-calc age of the staff employee ---
        if self.dob:
            today = timezone.now().date()
            self.age = today.year - self.dob.year - (
                (today.month, today.day) < (self.dob.month, self.dob.day)
            )

        # --- Auto-generate sequential staff_id (SP-0001, SP-0002, ...) ---
        if not self.staff_id:
            last_employee = Employee.objects.exclude(staff_id__isnull=True).order_by('-id').first()
            if last_employee and last_employee.staff_id and last_employee.staff_id.startswith("SP-"):
                try:
                    last_number = int(last_employee.staff_id.replace("SP-", ""))
                except ValueError:
                    last_number = 0
                new_number = last_number + 1
                self.staff_id = f"SP-{new_number:04d}"
            else:
                self.staff_id = "SP-0001"

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.full_name} ({self.staff_id}) - {self.role}"



# ================================================================
# Profile Model (Links User to Employee)
# ================================================================
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    employee = models.OneToOneField(Employee, on_delete=models.CASCADE, null=True, blank=True)
    profile_picture = models.ImageField(
        upload_to="profile_pics/",
        default="profile_pics/default_avatar.png",
        blank=True,
        null=True
    )

    def __str__(self):
        if self.employee:
            return f"{self.employee.full_name} ({self.employee.role})"
        return self.user.username

    @property
    def role(self):
        """
        Returns the employee's role dynamically from the linked Employee record.
        Defaults to 'employee' if no employee is linked.
        """
        return self.employee.role if self.employee else "employee"


# ================================================================
# Salary Advance Request Model
# ================================================================

class SalaryAdvanceRequest(models.Model):
    """
    Tracks staff requests for salary advances.

    - Linked to a User account.
    - Stores amount, reason, timestamp, and approval status.
    - Tracks which finance officer approved/rejected and when.
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reason = models.TextField(blank=True, null=True)
    date_requested = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20,
        choices=[("Pending", "Pending"), ("Approved", "Approved"), ("Rejected", "Rejected")],
        default="Pending"
    )

    # -------- Audit Trail Fields --------
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_salary_requests",
        editable=False
    )
    action_datetime = models.DateTimeField(null=True, blank=True, editable=False)

    def __str__(self):
        """Readable format: username and requested amount."""
        return f"{self.user.username} - {self.amount}"



# ================================================================
# Loan Request Model
# ================================================================
class LoanRequest(models.Model):
    """
    Tracks staff loan requests.

    - Linked to Employee records (HR-controlled).
    - Stores amount, repayment details, reason, interest, and status.
    """

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    repayment_period = models.IntegerField(help_text="Repayment period in months")
    reason = models.TextField(blank=True, null=True)
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2, default=10.0)  # 10% per annum
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20,
        choices=[("Pending", "Pending"), ("Approved", "Approved"), ("Rejected", "Rejected")],
        default="Pending"
    )

    def __str__(self):
        """Readable format: staff ID with loan amount."""
        return f"LoanRequest({self.employee.staff_id} - {self.amount})"


# ================================================================
# Chat Message Model
# ================================================================
class ChatMessage(models.Model):
    """
    Internal messaging model.

    - Supports direct communication between staff and departments.
    - Tracks sender, receiver, message content, timestamp, and read status.
    """

    sender = models.ForeignKey(User, related_name="sent_messages", on_delete=models.CASCADE)
    receiver = models.ForeignKey(User, related_name="received_messages", on_delete=models.CASCADE)
    message = models.TextField()
    timestamp = models.DateTimeField(default=timezone.now)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        """Readable format: sender → receiver with timestamp."""
        return f"From {self.sender.username} to {self.receiver.username} at {self.timestamp}"    


# ================================================================
# Support Query Model
# ================================================================
class SupportChatMessage(models.Model):
    """
    Dedicated support messaging model.

    - Separates general chat from support queries.
    - Tracks sender, receiver, content, timestamp, and read status.
    """

    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name="support_sent")
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name="support_received")
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        """Readable format for audit/logging purposes."""
        return f"SupportChat from {self.sender.username} to {self.receiver.username}"


# ================================================================
# Signals - Auto Profile Creation
# ================================================================
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Signal to auto-create a Profile when a new User is registered.

    - Default role = 'employee'.
    - HR/Admin can update role later based on department or position.
    """
    if created:
        Profile.objects.create(user=instance)


# ================================================================
# Attendance Model
# ================================================================
class Attendance(models.Model):
    """
    Tracks daily attendance for each employee.

    - Records clock-in and clock-out times.
    - Calculates total hours worked.
    - Determines late arrival and whether an explanation is needed.
    """

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='attendances')
    date = models.DateField(default=timezone.now)
    clock_in = models.TimeField(null=True, blank=True)
    clock_out = models.TimeField(null=True, blank=True)
    hours_worked = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=50, default="Not Checked In")  # Not Checked In, Checked In, Checked Out, Late
    late_minutes = models.PositiveIntegerField(default=0)
    needs_explanation = models.BooleanField(default=False)

    class Meta:
        unique_together = ('employee', 'date') 
        ordering = ['-date']

    # ------------------------------------------------------------
    # Methods
    # ------------------------------------------------------------
    def calculate_hours(self):
        """Calculate worked hours from clock_in and clock_out"""
        if self.clock_in and self.clock_out:
            datetime_in = datetime.combine(self.date, self.clock_in)
            datetime_out = datetime.combine(self.date, self.clock_out)
            worked = datetime_out - datetime_in
            self.hours_worked = round(worked.total_seconds() / 3600, 2)
            self.save()

    def __str__(self):
        return f"{self.employee.full_name} - {self.date} - {self.status}"


# ================================================================
# Leave Types
# ================================================================
class LeaveType(models.TextChoices):
    REGULAR = "Regular", "Regular Leave"
    OFF = "Off", "Off Day"
    SICK = "Sick", "Sick Leave"

# ================================================================
# Employee Leave Balance
# ================================================================
class EmployeeLeaveBalance(models.Model):
    """
    Tracks the annual leave, off days, and sick leave usage for each employee.
    """

    employee = models.OneToOneField(Employee, on_delete=models.CASCADE, related_name="leave_balance")
    regular_leave = models.IntegerField(default=21)  # 21 days per year
    off_days = models.IntegerField(default=7)        # 7 off days per year
    sick_leave_taken = models.IntegerField(default=0)  # Track total sick days taken

    def deduct_leave(self, leave_type, days):
        """Deduct leave days when redeemed."""
        if leave_type == LeaveType.REGULAR:
            self.regular_leave = max(self.regular_leave - days, 0)
        elif leave_type == LeaveType.OFF:
            self.off_days = max(self.off_days - days, 0)
        elif leave_type == LeaveType.SICK:
            self.sick_leave_taken += days
        self.save()

    def __str__(self):
        return f"{self.employee.full_name} Leave Balance"

# ================================================================
# Leave Request Model
# ================================================================
class LeaveRequest(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    leave_type = models.CharField(max_length=10, choices=LeaveType.choices)
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField(blank=True, null=True)
    doctor_letter = models.FileField(upload_to="doctor_letters/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    STATUS_CHOICES = [
        ("Pending", "Pending"),
        ("Approved", "Approved"),
        ("Rejected", "Rejected"),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="Pending")

    @property
    def total_days(self):
        return (self.end_date - self.start_date).days + 1

    def __str__(self):
        return f"{self.employee.full_name} - {self.leave_type} ({self.total_days} days)"

    

# ================================================================
# Signal: Auto-create leave balance for new employees
# ================================================================
@receiver(post_save, sender=Employee)
def create_employee_leave_balance(sender, instance, created, **kwargs):
    """Initialize leave balances when a new employee is added."""
    if created:
        EmployeeLeaveBalance.objects.create(employee=instance)
