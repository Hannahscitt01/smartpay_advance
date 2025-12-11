from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.validators import MinValueValidator
from django.utils import timezone

from datetime import datetime, time
from django.db.models import Sum
from datetime import timedelta
from django.db.models.signals import post_save

from django.conf import settings
from django.contrib.auth import get_user_model

from decimal import Decimal
from django.db.models import Sum
# ================================================================
# Employee Model (Created by HR)
# ================================================================



# ================================================================
# Role Model
# ================================================================
class Role(models.Model):
    name = models.CharField(max_length=50, unique=True) 

    def __str__(self):
        return self.name

# ================================================================
# Department Model
# ================================================================


class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)
    head = models.ForeignKey(
        'Employee',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='headed_departments',
        help_text="Head of Department must be an existing employee"
    )

    def save(self, *args, **kwargs):
        # Ensure the head belongs to this department
        if self.head and self.head.department != self:
            raise ValueError("The Head of Department must belong to this department")
        super().save(*args, **kwargs)

    def __str__(self):
        if self.head:
            return f"{self.name} (Head: {self.head.full_name})"
        return self.name

# ================================================================
# Employee Model (Created by HR)
# ================================================================
class Employee(models.Model):
    EMPLOYMENT_TYPES = [
        ('Permanent', 'Permanent'),
        ('Contract', 'Contract'),
        ('Internship', 'Internship'),
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
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    job_title = models.CharField(max_length=100)
    employment_type = models.CharField(max_length=20, choices=EMPLOYMENT_TYPES)
    salary = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )

    # ---------------- Role Info ----------------
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True)

    # ---------------- Contact Info ----------------
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20)
    address = models.TextField(blank=True, null=True)

    # ---------------- Last Updated Info ----------------
    last_updated_by = models.ForeignKey(
        'auth.User', null=True, blank=True, on_delete=models.SET_NULL, related_name='updated_employees'
    )
    last_updated_at = models.DateTimeField(null=True, blank=True)


    # ---------------- Save Override ----------------
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

    # ---------------- String Representation ----------------
    def __str__(self):
        role_name = self.role.name if self.role else "Employee"
        return f"{self.full_name} ({self.staff_id}) - {role_name}"


# ================================================================
# Profile Model (Links User to Employee)
# ================================================================
class Profile(models.Model):
    # ---------------- User & Employee Link ----------------
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    employee = models.OneToOneField(
        'Employee',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    # ---------------- Profile Info ----------------
    profile_picture = models.ImageField(
        upload_to="profile_pics/",
        default="profile_pics/default_avatar.png",
        blank=True,
        null=True
    )

    # ---------------- String Representation ----------------
    def __str__(self):
        if self.employee:
            role_name = self.employee.role.name if self.employee.role else "Employee"
            return f"{self.employee.full_name} ({role_name})"
        return self.user.username

    # ---------------- Role Property ----------------
    @property
    def role(self):
        """
        Returns the employee's role dynamically from the linked Employee record.
        Defaults to 'employee' if no employee is linked.
        """
        return self.employee.role.name if self.employee and self.employee.role else "employee"

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


class OpenPosition(models.Model):
    # ------------------------ Choices ------------------------
    POSITION_REASON_CHOICES = [
        ("Resignation", "Resignation"),
        ("Termination", "Termination"),
        ("New Role", "New Role / Expansion"),
        ("Replacement", "Replacement"),
        ("Other", "Other"),
    ]

    GENDER_CHOICES = [
        ("Any", "Any"),
        ("Male", "Male"),
        ("Female", "Female"),
    ]

    STATUS_CHOICES = [
        ("Open", "Open"),
        ("In Recruitment", "In Recruitment"),
        ("Closed", "Closed / Filled"),
    ]

    # ------------------------ Position Info ------------------------
    department = models.ForeignKey(
        "Department", on_delete=models.CASCADE, related_name="open_positions"
    )
    job_title = models.CharField(max_length=255)
    reason = models.CharField(max_length=50, choices=POSITION_REASON_CHOICES)
    vacancy_date = models.DateField(default=timezone.now)
    number_of_positions = models.PositiveIntegerField(default=1)

    # ------------------------ Salary & Requirements ------------------------
    salary_range_min = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    salary_range_max = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    qualifications_text = models.TextField(
        null=True, blank=True, help_text="List qualifications here"
    )
    qualifications_file = models.FileField(
        upload_to="qualifications/",
        null=True,
        blank=True,
        help_text="Upload detailed qualifications PDF"
    )

    age_requirement_min = models.PositiveIntegerField(null=True, blank=True)
    age_requirement_max = models.PositiveIntegerField(null=True, blank=True)
    gender_requirement = models.CharField(max_length=10, choices=GENDER_CHOICES, default="Any")

    job_ad_attachment = models.FileField(
        upload_to="job_ads/",
        null=True,
        blank=True,
        help_text="Upload job advert (PDF or image)"
    )

    # ------------------------ Status ------------------------
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Open")

    # ------------------------ Digital Footprint ------------------------
    created_by = models.ForeignKey(
        "Employee", on_delete=models.SET_NULL, null=True, blank=True, editable=False,
        related_name="positions_created"
    )
    created_by_id_no = models.CharField(max_length=20, null=True, blank=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Open Position"
        verbose_name_plural = "Open Positions"

    def save(self, *args, **kwargs):
        # Auto-populate digital footprint ID if created_by is set
        if self.created_by and not self.created_by_id_no:
            self.created_by_id_no = self.created_by.staff_id
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.job_title} - {self.department.name} ({self.status})"



# ================================================================
# Employee Contract Model
# ================================================================
class EmployeeContract(models.Model):
    employee = models.OneToOneField(
        'Employee',
        on_delete=models.CASCADE,
        related_name='contract',
        help_text="The employee this contract belongs to"
    )
    contract_file = models.FileField(
        upload_to='contracts/',
        null=True,
        blank=True,
        help_text="Upload the contract document (PDF or image)"
    )
    contract_expiry_date = models.DateField(
        null=True,
        blank=True,
        help_text="Expiry date for contract or internship employees"
    )

    # ---------------- Digital Footprint ----------------
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        editable=False,
        related_name='created_contracts'
    )
    created_at = models.DateTimeField(auto_now_add=True, editable=False)

    def save(self, *args, **kwargs):
        # Clear expiry if permanent
        if self.employee.employment_type == "Permanent":
            self.contract_expiry_date = None
        super().save(*args, **kwargs)

    def __str__(self):
        status = f"Expires: {self.contract_expiry_date}" if self.contract_expiry_date else "Permanent Employee"
        return f"{self.employee.full_name} - {status}"


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
    # -----------------------------
    # Leave Status Choices
    # -----------------------------
    STATUS_CHOICES = [
        ("Pending", "Pending"),
        ("Approved", "Approved"),
        ("Rejected", "Rejected"),
    ]

    # -----------------------------
    # Leave Type Choices (restricted to three types)
    # -----------------------------
    LEAVE_TYPE_CHOICES = [
        ("Sick Leave", "Sick Leave"),
        ("Off Day", "Off Day"),
        ("Annual Leave", "Annual Leave"),
    ]

    employee = models.ForeignKey("Employee", on_delete=models.CASCADE)
    leave_type = models.CharField(max_length=20, choices=LEAVE_TYPE_CHOICES, default="Annual Leave")
    start_date = models.DateField()
    end_date = models.DateField()
    total_days = models.IntegerField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Pending")

    # -----------------------------
    # Audit fields (system-generated, not editable)
    # -----------------------------
    approved_at = models.DateTimeField(null=True, blank=True, editable=False)
    rejected_at = models.DateTimeField(null=True, blank=True, editable=False)
    
    resumption_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    doctor_letter = models.FileField(upload_to='doctor_letters/', null=True, blank=True)

    # -----------------------------
    # Calculate leave days excluding Sundays
    # -----------------------------
    def calculate_leave_days(self):
        if not self.start_date or not self.end_date:
            return 0

        day_count = 0
        current_day = self.start_date
        while current_day <= self.end_date:
            if current_day.weekday() != 6:  # Skip Sunday
                day_count += 1
            current_day += timedelta(days=1)
        return day_count

    # -----------------------------
    # Override save for business rules
    # -----------------------------
    def save(self, *args, **kwargs):
        now = timezone.now()
        total_days = self.calculate_leave_days()

        if self.status == "Approved":
            if not self.approved_at:
                self.approved_at = now
            self.rejected_at = None
            self.total_days = total_days

            # Calculate next working resumption date
            resumption = self.end_date + timedelta(days=1)
            while resumption.weekday() == 6:  # Skip Sunday
                resumption += timedelta(days=1)
            self.resumption_date = resumption

        elif self.status == "Rejected":
            if not self.rejected_at:
                self.rejected_at = now
            self.approved_at = None
            self.resumption_date = None
            self.total_days = 0

        elif self.status == "Pending":
            self.approved_at = None
            self.rejected_at = None
            self.resumption_date = None
            self.total_days = total_days

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.employee.full_name} - {self.leave_type} ({self.status})"


# ================================================================
# Signal: Create employee leave balance on registration
# ================================================================
@receiver(post_save, sender=Employee)
def create_employee_leave_balance(sender, instance, created, **kwargs):
    if created:
        EmployeeLeaveBalance.objects.create(employee=instance)



# ================================================================
# Smarrtpay app project tracker models
# ================================================================



# --------------------------
# Status Choices
# --------------------------

PROJECT_STATUS_CHOICES = [
    ("not_started", "Not Started"),
    ("planning", "Planning"),
    ("pending_approval", "Pending Approval"),
    ("in_progress", "In Progress"),
    ("on_hold", "On Hold"),
    ("delayed", "Delayed"),
    ("completed", "Completed"),
    ("cancelled", "Cancelled"),
    ("closed", "Closed"),
]

STAGE_STATUS_CHOICES = [
    ("pending", "Pending"),
    ("in_progress", "In Progress"),
    ("waiting_for_approval", "Waiting for Approval"),
    ("completed", "Completed"),
    ("approved", "Approved"),
    ("rejected", "Rejected"),
    ("dispatched", "Dispatched / Delivered"),
]

TASK_STATUS_CHOICES = [
    ("pending", "Pending"),
    ("in_progress", "In Progress"),
    ("completed", "Completed"),
    ("approved", "Approved"),
    ("rejected", "Rejected"),
]


class Project(models.Model):
    name = models.CharField(max_length=255)
    order_id = models.CharField(max_length=50, unique=True, editable=False)
    description = models.TextField(blank=True, null=True)
    departments = models.ManyToManyField(Department, related_name='projects', editable=False)
    overall_status = models.CharField(max_length=20, choices=PROJECT_STATUS_CHOICES, default="not_started")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    project_file = models.FileField(upload_to="project_docs/", blank=True, null=True)

    def __str__(self):
        return f"{self.name} ({self.order_id}) - {self.overall_status}"


class ProjectStage(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='stages')
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    employees = models.ManyToManyField(User, blank=True, related_name='assigned_stages')
    status = models.CharField(max_length=30, choices=STAGE_STATUS_CHOICES, default="pending")
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.project.name} - {self.department.name} ({self.status})"


class ProjectTask(models.Model):
    stage = models.ForeignKey(ProjectStage, on_delete=models.CASCADE, related_name='tasks')
    description = models.TextField()
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='tasks')
    assigned_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='assigned_tasks')
    status = models.CharField(max_length=20, choices=TASK_STATUS_CHOICES, default="pending")
    start_date = models.DateTimeField(null=True, blank=True)
    due_date = models.DateTimeField(null=True, blank=True)
    completion_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.description} - {self.status}"


class AssignmentAcknowledgment(models.Model):
    task = models.ForeignKey(ProjectTask, on_delete=models.CASCADE, related_name='acknowledgments')
    from_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='sent_acks')
    to_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='received_acks')
    ack_type = models.CharField(max_length=50)  # e.g., completion, handover, verification
    timestamp = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"Ack from {self.from_user} to {self.to_user} ({self.ack_type})"


class ProjectLog(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="logs")
    task = models.ForeignKey(ProjectTask, on_delete=models.CASCADE, null=True, blank=True)
    action_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action_type = models.CharField(max_length=100)  # e.g., Task Assigned, Task Completed, Handover Sent
    notes = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.project.name} - {self.action_type} by {self.action_by} at {self.timestamp}"



# Department Documents / Policies
class DepartmentDocument(models.Model):
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name="documents")
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to="department_documents/")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Department Document"
        verbose_name_plural = "Department Documents"

    def __str__(self):
        return f"{self.title} ({self.department.name})"


# Succession & Training Plans
class SuccessionPlan(models.Model):
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name="succession_plans")
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to="succession_plans/")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Succession Plan"
        verbose_name_plural = "Succession Plans"

    def __str__(self):
        return f"{self.title} ({self.department.name})"


class EmployeePayrollProfile(models.Model):
    employee = models.OneToOneField(User, on_delete=models.CASCADE)

    payroll_employee_id = models.CharField(max_length=20, unique=True)
    department = models.CharField(max_length=100)

    base_salary = models.DecimalField(max_digits=12, decimal_places=2)
    house_allowance_rate = models.DecimalField(max_digits=5, decimal_places=2, default=13)  # %

    loan_repayment = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    bonus = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    hse_levy = models.DecimalField(max_digits=12, decimal_places=2, default=300)
    hr_comments = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.employee.username} Payroll Profile"


class PayrollPeriod(models.Model):
    month = models.IntegerField()
    year = models.IntegerField()
    start_date = models.DateField()
    end_date = models.DateField()

    def __str__(self):
        return f"{self.month}/{self.year}"



class EmployeePayslip(models.Model):

    # all your fields here...
    employee = models.ForeignKey(User, on_delete=models.CASCADE)
    period = models.ForeignKey(PayrollPeriod, on_delete=models.CASCADE)

    gross_salary = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    house_allowance = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    overtime_hours = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    overtime_rate = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    overtime_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    paye = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    nhif = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    nssf = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    loan_deduction = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    hse_levy = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    total_deductions = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    net_pay = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    status = models.CharField(max_length=30, default="Draft")

    generated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("employee", "period")

    def __str__(self):
        return f"{self.employee} - {self.period}"


    def generate_payslip(self):
        from decimal import Decimal
        from django.db.models import Sum
        from .models import EmployeePayrollProfile, OvertimeAssignment, OvertimeRate

        profile = EmployeePayrollProfile.objects.get(employee=self.employee)

        # Base components
        base = profile.base_salary
        house = (profile.house_allowance_rate / Decimal(100)) * base

        # Overtime
        overtime_hours = OvertimeAssignment.objects.filter(
            employee=self.employee,
            month=self.period.month,
            year=self.period.year,
            status="Approved"
        ).aggregate(Sum('hours'))["hours__sum"] or Decimal(0)

        rate_obj = OvertimeRate.objects.first()
        overtime_rate = rate_obj.rate_per_hour if rate_obj else Decimal(0)
        overtime_amount = overtime_hours * overtime_rate

        # Gross Pay
        gross = base + house + overtime_amount + profile.bonus

        # Deductions
        paye = gross * Decimal("0.30")    # 30%
        nhif = gross * Decimal("0.0275")  # 2.75%
        nssf = gross * Decimal("0.06")    # 6%

        total_deductions = (
            paye + nhif + nssf + profile.loan_repayment + profile.hse_levy
        )

        net_pay = gross - total_deductions

        # Save computed values
        self.house_allowance = house
        self.overtime_hours = overtime_hours
        self.overtime_rate = overtime_rate
        self.overtime_amount = overtime_amount
        self.gross_salary = gross

        self.paye = paye
        self.nhif = nhif
        self.nssf = nssf
        self.loan_deduction = profile.loan_repayment
        self.hse_levy = profile.hse_levy

        self.total_deductions = total_deductions
        self.net_pay = net_pay

        self.save()


# ----------------------------
# Overtime Rate Model
# ----------------------------
class OvertimeRate(models.Model):
    rate_per_hour = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    effective_from = models.DateField()
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.rate_per_hour} per hour (from {self.effective_from})"


# ----------------------------
# Overtime Assignment Model
# ----------------------------
class EmployeeOvertimeAssignment(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    ]

    employee = models.ForeignKey(User, on_delete=models.CASCADE)
    month = models.IntegerField()
    year = models.IntegerField()
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    hours = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    approved_by = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL, related_name='approved_overtimes'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ('employee', 'month', 'year')

    def __str__(self):
        return f"{self.employee.username} - {self.month}/{self.year} ({self.status})"

