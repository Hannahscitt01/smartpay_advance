from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User

from .forms import SignUpForm, SalaryAdvanceForm, EmployeeForm, ProfileUpdateForm, LoanRequestForm
from .models import Profile, SalaryAdvanceRequest, Employee, LoanRequest, ChatMessage, SupportChatMessage, Attendance, LeaveRequest, EmployeeLeaveBalance
from .decorators import admin_required
from decimal import Decimal
from django.db.models import Sum, Q, Max, Count, Case, When, Value, IntegerField
from django.utils import timezone

from collections import OrderedDict, defaultdict
from django.http import JsonResponse

from datetime import datetime, time, date, timedelta
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

import json

# ================================================================
# 1. Landing & Static Pages
# ================================================================
def index(request):
    """Landing page view."""
    return render(request, 'smartpayapp/index.html')


def application(request):
    """General application info page."""
    return render(request, 'smartpayapp/application.html')


def signup_sucess(request):
    """Displayed after successful account creation."""
    return render(request, 'smartpayapp/signup_sucess.html')


def admin_home(request):
    """Admin landing page (after login)."""
    return render(request, 'smartpayapp/admin_home.html')


# ================================================================
# 2. Authentication (Sign Up & Login)
# ================================================================
def signup(request):
    """
    Handle staff account creation.

    - On POST: validate SignUpForm and create user + profile.
    - On success: redirect to success page.
    - On failure: show error messages.
    """
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, "Account created successfully! Please log in.")
                return redirect("signup_sucess")
            except Exception as e:
                messages.error(request, f"Signup failed: {str(e)}")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = SignUpForm()

    return render(request, "smartpayapp/sign_up.html", {"form": form})


def login_view(request):
    """
    Authenticate users with Staff ID and password.
    Redirect to dashboard based on role.
    """
    if request.method == "POST":
        staffid = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=staffid, password=password)
        if user:
            login(request, user)
            #  Call the helper here
            return redirect_after_login(request)
        else:
            messages.error(request, "Invalid Staff ID or password")

    return render(request, "smartpayapp/login.html")

def redirect_after_login(request):
    """Redirect users to their dashboard based on employee role."""
    employee = getattr(request.user.profile, "employee", None)

    if not employee:
        # If no employee is linked, send them to a safe fallback
        return redirect("home")

    role = employee.role.lower()  # assuming Employee has a 'role' field

    if role == "admin":
        return redirect("admin")
    elif role == "finance":
        return redirect("finance")
    elif role == "hr":
        return redirect("hr_home")
    else:
        return redirect("home")  # employee dashboard




# ================================================================
# 3. Employee Dashboard & Profile Management
# ================================================================
def employee_dashboard(request):
    return render(request, 'smartpayapp/employee_dashboard.html')

@login_required
def home(request):
    """
    Employee dashboard.

    Displays:
    - Current salary and advance eligibility.
    - Outstanding loans and advances.
    - Loan and salary advance history with repayment progress.
    """
    profile = request.user.profile
    employee = getattr(profile, "employee", None)

    current_salary = "N/A"
    advance_eligibility = "N/A"
    active_loans = 0
    salary_advances = []
    internal_loans = []

    if employee and employee.salary is not None:
        salary = employee.salary
        current_salary = f"KSh {salary:,.2f}"
        advance_eligibility = f"Eligible — Up to KSh {float(salary) * 0.5:,.2f}"

        # Salary advances linked to the user
        salary_advances = SalaryAdvanceRequest.objects.filter(
            user=request.user
        ).order_by("-date_requested")

        for advance in salary_advances:
            advance.remaining_salary = (
                float(salary) - float(advance.amount) if advance.status == "Approved" else float(salary)
            )

        # Internal loan requests
        internal_loans = LoanRequest.objects.filter(
            employee=employee
        ).order_by("-created_at")

        for loan in internal_loans:
            loan.repayment_progress = 70 if loan.status == "Approved" else 0

        active_loans = LoanRequest.objects.filter(
            employee=employee, status="Approved"
        ).aggregate(total=Sum("amount"))["total"] or 0

    context = {
        "profile": profile,
        "current_salary": current_salary,
        "advance_eligibility": advance_eligibility,
        "active_loans": active_loans,
        "salary_advances": salary_advances,
        "internal_loans": internal_loans,
    }

    return render(request, "smartpayapp/home.html", context)


@login_required
def update_profile(request):
    """
    Allow staff to update profile information (e.g., picture).
    """
    profile = request.user.profile
    if request.method == "POST":
        form = ProfileUpdateForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect("home")
    else:
        form = ProfileUpdateForm(instance=profile)

    return render(request, "smartpayapp/update_profile.html", {"form": form})


# ================================================================
# 4. Salary Advance Requests
# ================================================================
@login_required
def request_form(request):
    """
    Salary advance request.

    - On POST: validate and save linked to logged-in user.
    - On GET: render blank form.
    """
    profile = request.user.profile
    employee = profile.employee

    if request.method == "POST":
        form = SalaryAdvanceForm(request.POST)
        if form.is_valid():
            salary_request = form.save(commit=False)
            salary_request.user = request.user
            salary_request.save()
            messages.success(request, "Salary advance request submitted.")
            return redirect("request_form_success")
    else:
        form = SalaryAdvanceForm()

    return render(
        request,
        "smartpayapp/request_form.html",
        {"form": form, "employee": employee},
    )


def request_form_success(request):
    """Confirmation page after salary advance request submission."""
    return render(request, 'smartpayapp/request_form_success.html')


# ================================================================
# 5. Internal Loans
# ================================================================
@login_required
def internal_loan(request):
    """
    Employee internal loan request.

    - Validates and saves a loan request for logged-in employee.
    - Displays loan eligibility and active loans.
    """
    profile = request.user.profile
    employee = profile.employee

    if request.method == "POST":
        form = LoanRequestForm(request.POST, employee=employee)
        if form.is_valid():
            loan = form.save(commit=False)
            loan.employee = employee
            loan.save()
            messages.success(request, "Loan request submitted successfully.")
            return redirect("internal_loan_success")
    else:
        form = LoanRequestForm(employee=employee)

    monthly_salary = employee.salary
    max_loan = monthly_salary * 2
    active_loans = LoanRequest.objects.filter(
        employee=employee, status="Approved"
    ).aggregate(total=Sum("amount"))["total"] or 0

    return render(
        request,
        "smartpayapp/internal_loan.html",
        {
            "form": form,
            "employee": employee,
            "monthly_salary": monthly_salary,
            "max_loan": max_loan,
            "active_loans": active_loans,
        },
    )


def internal_loan_success(request):
    """Confirmation page after successful loan request."""
    return render(request, 'smartpayapp/internal_loan_success.html')


# ================================================================
# 6. Employee Management (HR/Admin)
# ================================================================


def employee_creation(request):
    """
    Create a new employee record.
    """
    if request.method == "POST":
        form = EmployeeForm(request.POST)
        if form.is_valid():
            employee = form.save()  # staff_id auto-generated in model.save()
            messages.success(
                request,
                f"Employee {employee.full_name} created successfully with ID {employee.staff_id}"
            )
            return render(
                request,
                "smartpayapp/employee_creation_success.html",
                {"employee": employee},
            )
        else:
            # Debug form errors in console
            print("Form errors:", form.errors)
            messages.error(request, "Please correct the errors below.")
    else:
        form = EmployeeForm()

    return render(request, "smartpayapp/employee_creation.html", {"form": form})




def employee_creation_success(request):
    """Displayed after successful employee creation."""
    return render(request, 'smartpayapp/employee_creation_success.html')


def employee_list(request):
    """Display list of employees grouped by department."""
    departments = [dept[0] for dept in Employee.DEPARTMENTS]
    grouped_employees = {dept: Employee.objects.filter(department=dept).order_by("full_name") for dept in departments}

    context = {"grouped_employees": grouped_employees}
    return render(request, "smartpayapp/employee_list.html", context)


# ================================================================
# 7. Admin Views
# ================================================================
@admin_required
def admin_dashboard(request):
    """Main admin dashboard view."""
    return render(request, "smartpayapp/admin_dashboard.html")


# ================================================================
# 8. Finance Views
# ================================================================


@login_required
def finance(request):
    """Finance landing page/dashboard with dynamic KPI counts and finance officer details."""
    # Count pending salary requests
    pending_requests_count = SalaryAdvanceRequest.objects.filter(status="Pending").count()

    # Get the finance officer's profile and linked employee info
    profile = Profile.objects.filter(user=request.user).select_related("employee").first()
    finance_user = None
    if profile and profile.employee:
        finance_user = profile.employee

    context = {
        "pending_salary_requests": pending_requests_count,
        "finance_user": finance_user,
        "current_date": timezone.now().strftime("%B %d, %Y"),
        "current_time": timezone.now().strftime("%I:%M %p"),
    }
    return render(request, "smartpayapp/finance.html", context)



@login_required
def finance_salary_request(request):
    """
    Finance salary request management page.
    - Groups requests by staff department for cleaner readability.
    """
    salary_requests = SalaryAdvanceRequest.objects.select_related(
        "user__profile__employee"
    ).order_by("-date_requested")

    grouped = OrderedDict()
    for sr in salary_requests:
        dept = "Unassigned"
        emp = getattr(getattr(sr.user, "profile", None), "employee", None)
        if emp and getattr(emp, "department", None):
            dept = emp.department
        grouped.setdefault(dept, []).append(sr)

    context = {
        "grouped_requests": grouped,
        "total_requests": salary_requests.count(),
    }
    return render(request, "smartpayapp/finance_salary_requests.html", context)



@login_required
def approve_salary_request(request, pk):
    if request.method != "POST":
        messages.error(request, "Invalid request method.")
        return redirect('finance_salary_request')

    sr = get_object_or_404(SalaryAdvanceRequest, pk=pk)

    emp = getattr(getattr(request.user, "profile", None), "employee", None)
    role_name = getattr(emp, "role", "").lower() if emp else None

    if not (request.user.is_superuser or role_name == "finance"):
        messages.error(request, "Permission denied. Only finance officers can approve requests.")
        return redirect('finance_salary_request')

    if sr.status != "Pending":
        messages.warning(request, "Request already processed.")
        return redirect('finance_salary_request')

    sr.status = "Approved"
    sr.approved_by = request.user  # record finance officer
    sr.action_datetime = timezone.now()  # record date/time
    sr.save()

    messages.success(request, f"Salary request for {sr.user.get_full_name() or sr.user.username} approved.")
    return redirect('finance_salary_request')

@login_required
def reject_salary_request(request, pk):
    if request.method != "POST":
        messages.error(request, "Invalid request method.")
        return redirect('finance_salary_request')

    sr = get_object_or_404(SalaryAdvanceRequest, pk=pk)

    emp = getattr(getattr(request.user, "profile", None), "employee", None)
    role_name = getattr(emp, "role", "").lower() if emp else None

    if not (request.user.is_superuser or role_name == "finance"):
        messages.error(request, "Permission denied. Only finance officers can reject requests.")
        return redirect('finance_salary_request')

    if sr.status != "Pending":
        messages.warning(request, "Request already processed.")
        return redirect('finance_salary_request')

    sr.status = "Rejected"
    sr.approved_by = request.user  # record finance officer
    sr.action_datetime = timezone.now()  # record date/time
    sr.save()

    messages.success(request, f"Salary request for {sr.user.get_full_name() or sr.user.username} rejected.")
    return redirect('finance_salary_request')





@login_required
def finance_internal_loan_request(request):
    """Finance internal loan request management page."""
    return render(request, "smartpayapp/finance_internal_loan_request.html")



# ================================================================
# 9. Finance Messaging (Staff ↔ Finance)
# ================================================================
def message_finance(request):
    """Placeholder view for messaging finance (UI stub)."""
    return render(request, 'smartpayapp/message_finance.html')


@login_required
def chat_finance(request):
    """
    One-to-one chat between staff and finance department.
    """
    user = request.user
    finance_officer, created = User.objects.get_or_create(
        username="finance",
        defaults={"first_name": "Finance", "last_name": "Dept", "email": "finance@company.com"}
    )

    messages_qs = ChatMessage.objects.filter(
        Q(sender=user, receiver=finance_officer) |
        Q(sender=finance_officer, receiver=user)
    ).order_by("timestamp")

    messages_qs.filter(receiver=user, is_read=False).update(is_read=True)

    if request.method == "POST":
        msg = request.POST.get("message")
        if msg.strip():
            ChatMessage.objects.create(sender=user, receiver=finance_officer, message=msg)
        return redirect("chat_finance")

    context = {"messages": messages_qs, "finance_officer": finance_officer}
    return render(request, "smartpayapp/chat_finance.html", context)


@login_required
def finance_message_centre(request):
    """
    Message centre for finance team.

    Displays latest threads from staff (grouped by sender).
    """
    latest_threads = (
        ChatMessage.objects
        .values("sender")
        .annotate(latest_time=Max("timestamp"))
        .order_by("-latest_time")
    )

    threads = []
    for entry in latest_threads:
        latest_msg = (
            ChatMessage.objects
            .filter(sender=entry["sender"], timestamp=entry["latest_time"])
            .first()
        )
        if latest_msg:
            threads.append({
                "sender": latest_msg.sender,
                "latest_message": latest_msg.message,
                "timestamp": latest_msg.timestamp,
                "is_read": latest_msg.is_read,
            })

    context = {"threads": threads}
    return render(request, "smartpayapp/finance_message_centre.html", context)


def finance_chat_detail(request, user_id):
    """
    Finance view for detailed chat thread with a specific staff member.
    """
    chat_user = get_object_or_404(User, id=user_id)

    messages_qs = ChatMessage.objects.filter(
        Q(sender=request.user, receiver=chat_user) |
        Q(sender=chat_user, receiver=request.user)
    ).order_by("timestamp")
    messages_qs.filter(receiver=request.user, is_read=False).update(is_read=True)

    if request.method == "POST":
        text = request.POST.get("content")
        if text:
            ChatMessage.objects.create(sender=request.user, receiver=chat_user, message=text)
        return redirect("finance_chat_detail", user_id=chat_user.id)

    staff_users = User.objects.filter(received_messages__receiver=request.user).distinct()
    for u in staff_users:
        u.has_unread = ChatMessage.objects.filter(sender=u, receiver=request.user, is_read=False).exists()

    return render(request, "smartpayapp/finance_chat_detail.html", {
        "chat_user": chat_user,
        "messages": messages_qs,
        "all_threads": staff_users,
    })


# ================================================================
# 10. Support Messaging (Staff ↔ Support)
# ================================================================
@login_required
def support_query(request):
    """
    Staff support chat.

    - Sends queries to support staff (assumed as first superuser).
    - Displays conversation history.
    """
    user = request.user
    support_user = User.objects.filter(is_superuser=True).first()

    if request.method == "POST":
        msg = request.POST.get("message")
        if msg and support_user:
            SupportChatMessage.objects.create(
                sender=user,
                receiver=support_user,
                message=msg,
                timestamp=timezone.now()
            )
        return redirect("support_chat")

    messages_qs = []
    if support_user:
        messages_qs = SupportChatMessage.objects.filter(
            Q(sender=user, receiver=support_user) |
            Q(sender=support_user, receiver=user)
        ).order_by("timestamp")

    context = {"messages": messages_qs}
    return render(request, "smartpayapp/support-query.html", context)


# ================================================================
# 11. HR Views
# ================================================================
@login_required
def hr_home(request):
    """HR landing page/dashboard."""

    # --- Existing code untouched ---
    try:
        employee = Employee.objects.get(email=request.user.email)
    except Employee.DoesNotExist:
        employee = None

    now = timezone.localtime(timezone.now())
    current_date = now.strftime("%b %d, %Y")
    current_time = now.strftime("%I:%M %p")
    current_month = now.month
    current_year = now.year
    today = now.date()

    total_employees = Employee.objects.count()
    total_departments = Employee.objects.values("department").distinct().count()

    employees_checked_in_today = Attendance.objects.filter(
        date=today,
        clock_in__isnull=False
    ).count()

    recent_employees = Employee.objects.filter(
        date_joined__year=current_year,
        date_joined__month=current_month,
        date_joined__isnull=False
    ).order_by('-date_joined')

    loan_requests = LoanRequest.objects.select_related("employee").order_by("-created_at")[:5]

    total_payroll = Employee.objects.aggregate(total=Sum('salary'))['total'] or 0

    pending_loans_count = LoanRequest.objects.filter(status="Pending").count()
    approved_loans_count = LoanRequest.objects.filter(status="Approved").count()

    # ------------------- New: Fetch Leave Requests -------------------
    leave_requests = LeaveRequest.objects.select_related("employee").order_by("-start_date")



    # ------------------- Context -------------------
    context = {
        "employee": employee,
        "current_date": current_date,
        "current_time": current_time,
        "total_employees": total_employees,
        "total_departments": total_departments,
        "recent_employees": recent_employees,
        "current_month_name": now.strftime("%B"),
        "current_year": current_year,
        "loan_requests": loan_requests,
        "employees_checked_in_today": employees_checked_in_today,
        "total_payroll": total_payroll,
        "pending_loans_count": pending_loans_count,
        "approved_loans_count": approved_loans_count,
        "leave_requests": leave_requests,  
    }

    return render(request, "smartpayapp/hr_dashboard.html", context)


@login_required
def hr_departments(request):
    """HR Departments page: display all departments and their details."""
    return render(request, 'smartpayapp/hr_departments.html')

@login_required
def payroll_payslips(request):
    """Placeholder view for Payroll & Payslips (UI stub)."""
    return render(request, 'smartpayapp/payroll_payslips.html')

@login_required
def hr_track_performance(request):
    """Placeholder view for Track Performance (UI stub)."""
    return render(request, 'smartpayapp/hr_track_performance.html')

@login_required
def hr_departments(request):
    """Placeholder view for HR Departments (UI stub)."""
    return render(request, 'smartpayapp/hr_departments.html')

@login_required
def attendance_tracking(request):
    """Placeholder view for Attendance & Tracking (UI stub)."""
    return render(request, 'smartpayapp/attendance_tracking.html')

@login_required
def hr_message_centre(request):
    """Placeholder view for HR Message Centre (UI stub)."""
    return render(request, 'smartpayapp/hr_message_centre.html')

@login_required
def hr_loan_requests(request):
    """Placeholder view for HR Loan Requests (UI stub)."""
    return render(request, 'smartpayapp/hr_loan_requests.html')

@login_required
def hr_reports(request):
    """Placeholder view for HR Reports (UI stub)."""
    return render(request, 'smartpayapp/hr_reports.html')


@login_required
def employee_today(request):
    """Placeholder view for Employees Today (UI stub)."""
    return render(request, 'smartpayapp/employee_today.html')


@login_required
def hr_leaves_offs(request):
    """Placeholder view for Leaves & Offs (UI stub)."""
    return render(request, 'smartpayapp/hr_leaves_offs.html')

@login_required
def hr_settings(request):
    """Placeholder view for Hr settings (UI stub)."""
    return render(request, 'smartpayapp/hr_settings.html')

@login_required
def hr_settings(request):
    """Placeholder view for Hr settings (UI stub)."""
    return render(request, 'smartpayapp/hr_settings.html')

@login_required
def hr_appraissals(request):
    """Placeholder view for hr appraissals (UI stub)."""
    return render(request, 'smartpayapp/hr_appraissals.html')

@login_required
def hr_profile(request):
    """Placeholder view for hr profile (UI stub)."""
    return render(request, 'smartpayapp/hr_profile.html')


@login_required
def approve_leave(request, leave_id):
    """
    Approve a leave request:
    - HR can specify partial approval by setting leave.start_date and leave.end_date
    - System dynamically calculates total approved days and sets approved_at
    - Resumption date is next working day after leave ends (skip Sundays)
    """
    leave = get_object_or_404(LeaveRequest, id=leave_id)
    employee = leave.employee

    if leave.status != "Pending":
        messages.warning(request, "Leave already processed.")
        return redirect("hr_home")

    # Calculate approved leave days dynamically
    if leave.end_date < leave.start_date:
        messages.error(request, "End date cannot be before start date.")
        return redirect("hr_home")

    approved_days = (leave.end_date - leave.start_date).days + 1
    leave.total_days = approved_days
    leave.status = "Approved"
    leave.approved_at = timezone.now()

    # Calculate resumption date
    resumption_date = leave.end_date + timedelta(days=1)
    if resumption_date.weekday() == 6:  # Sunday
        resumption_date += timedelta(days=1)  # Skip to Monday
    leave.resumption_date = resumption_date

    # Clear rejected fields if any
    leave.rejected_at = None

    leave.save()

    # Deduct leave balance only for approved days
    leave_balance, _ = EmployeeLeaveBalance.objects.get_or_create(employee=employee)
    try:
        leave_balance.deduct_leave(leave.leave_type, leave.total_days)
    except Exception:
        pass  # handle LeaveType mismatch if necessary

    messages.success(request, f"{employee.full_name}'s leave approved ({approved_days} days).")
    return redirect("hr_home")


@login_required
def reject_leave(request, leave_id):
    """
    Reject a leave request:
    - Status = 'Rejected'
    - System sets rejected_at timestamp
    - HR cannot modify this timestamp
    """
    leave = get_object_or_404(LeaveRequest, id=leave_id)

    if leave.status != "Pending":
        messages.warning(request, "Leave already processed.")
        return redirect("hr_home")

    leave.status = "Rejected"
    leave.rejected_at = timezone.now()

    # Clear approved fields if any
    leave.approved_at = None
    leave.resumption_date = None
    leave.total_days = 0

    leave.save()

    messages.success(request, f"{leave.employee.full_name}'s leave rejected.")
    return redirect("hr_home")



@csrf_exempt
@login_required
def update_leave_status(request):
    if request.method == "POST":
        data = json.loads(request.body)
        leave_id = data.get("leave_id")
        action = data.get("action")

        leave = get_object_or_404(LeaveRequest, id=leave_id)
        now = timezone.now()

        if action == "approve":
            leave.status = "Approved"
            leave.approved_at = now
            leave.resumption_date = leave.end_date + timedelta(days=1)
        elif action == "reject":
            leave.status = "Rejected"
            leave.rejected_at = now
        leave.save()

        return JsonResponse({
            "success": True,
            "status": leave.status,
            "resumption_date": leave.resumption_date.strftime("%b %d, %Y") if leave.resumption_date else None,
            "action_time": now.strftime("%b %d, %Y %I:%M %p"),
        })

    return JsonResponse({"success": False}, status=400)


@login_required
def hr_leave_details(request, leave_id):
    leave = get_object_or_404(LeaveRequest, id=leave_id)

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "approve":
            leave.status = "Approved"
            leave.approval_date = timezone.now().date()
            leave.save()
        elif action == "reject":
            leave.status = "Rejected"
            leave.approval_date = timezone.now().date()
            leave.save()

        return redirect("annual_leave_detail", leave_id=leave.id)

    return render(request, "smartpayapp/hr_leave_detail.html", {"leave": leave})


def hr_leave_management(request):
    """
    Display all leave requests dynamically with search, filter,
    and proper ordering by status (Pending → Approved → Rejected).
    """

    search_query = request.GET.get("search", "").strip()
    status_filter = request.GET.get("status", "").strip()

    # Base queryset
    leaves = LeaveRequest.objects.select_related('employee').all()

    # Apply search
    if search_query:
        leaves = leaves.filter(
            Q(employee__full_name__icontains=search_query) |
            Q(employee__staff_id__icontains=search_query) |
            Q(leave_type__icontains=search_query)
        )

    # Apply status filter
    if status_filter:
        leaves = leaves.filter(status=status_filter)

    # Annotate for status ordering
    status_order = Case(
        When(status="Pending", then=Value(0)),
        When(status="Approved", then=Value(1)),
        When(status="Rejected", then=Value(2)),
        default=Value(3),
        output_field=IntegerField(),
    )

    # Split by leave type and order
    annual_leaves = leaves.filter(leave_type="Annual Leave") \
                          .annotate(status_order=status_order) \
                          .order_by("status_order", "-created_at")

    sick_leaves = leaves.filter(leave_type="Sick Leave") \
                        .annotate(status_order=status_order) \
                        .order_by("status_order", "-created_at")

    off_days = leaves.filter(leave_type="Off Day") \
                     .annotate(status_order=status_order) \
                     .order_by("status_order", "-created_at")

    context = {
        "annual_leaves": annual_leaves,
        "sick_leaves": sick_leaves,
        "off_days": off_days,
        "search_query": search_query,
        "status_filter": status_filter,
    }

    return render(request, "smartpayapp/hr_leave_management.html", context)




def update_annual_leave(request, leave_id):
    """HR can approve or reject annual leave"""
    leave = get_object_or_404(LeaveRequest, id=leave_id)

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "approve":
            leave.status = "Approved"
            leave.approved_at = timezone.now()
            leave.rejected_at = None

            # Calculate resumption date (skip Sundays)
            resumption = leave.end_date + timedelta(days=1)
            while resumption.weekday() == 6:
                resumption += timedelta(days=1)
            leave.resumption_date = resumption

            leave.save()
            messages.success(request, f" {leave.employee.full_name}'s annual leave has been approved.")

        elif action == "reject":
            leave.status = "Rejected"
            leave.rejected_at = timezone.now()
            leave.approved_at = None
            leave.resumption_date = None
            leave.save()
            messages.error(request, f" {leave.employee.full_name}'s annual leave has been rejected.")

        return redirect("hr_annual_leaves")

    return redirect("hr_annual_leaves")

@login_required
def hr_sick_leaves(request):
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')

    sick_leaves = LeaveRequest.objects.filter(leave_type='Sick Leave')

    if search_query:
        sick_leaves = sick_leaves.filter(
            Q(employee__first_name__icontains=search_query) |
            Q(employee__last_name__icontains=search_query) |
            Q(employee__staff_id__icontains=search_query)
        )

    if status_filter:
        sick_leaves = sick_leaves.filter(status=status_filter)

    context = {
        'sick_leaves': sick_leaves,
        'search_query': search_query,
        'status_filter': status_filter,
    }
    return render(request, 'smartpayapp/hr_sick_leaves.html', context)


@login_required
def hr_annual_leaves(request):
    search_query = request.GET.get("search", "")
    status_filter = request.GET.get("status", "")

    annual_leaves = LeaveRequest.objects.filter(leave_type="Annual Leave")

    if search_query:
        annual_leaves = annual_leaves.filter(employee__full_name__icontains=search_query)

    if status_filter:
        annual_leaves = annual_leaves.filter(status=status_filter)

    context = {
        "annual_leaves": annual_leaves,
        "search_query": search_query,
        "status_filter": status_filter,
    }
    return render(request, "smartpayapp/hr_annual_leaves.html", context)


@login_required
def hr_off_days(request):
    search_query = request.GET.get("search", "")
    status_filter = request.GET.get("status", "")

    # Filter only Off Days
    off_days = LeaveRequest.objects.filter(leave_type="Off Day")

    if search_query:
        off_days = off_days.filter(
            Q(employee__first_name__icontains=search_query)
            | Q(employee__last_name__icontains=search_query)
            | Q(employee__staff_id__icontains=search_query)
        )

    if status_filter:
        off_days = off_days.filter(status=status_filter)

    context = {
        "off_days": off_days,
        "search_query": search_query,
        "status_filter": status_filter,
    }
    return render(request, "smartpayapp/hr_off_days.html", context)



# ================================================================
# Employee Check-In & Check-Out View
# ================================================================

def checkin_checkout(request):
    """ Employee Check-In & Check-Out Dashboard """

    now = timezone.localtime(timezone.now())

    # ------------------------------------------------------------
    # Date & Time formatting
    # ------------------------------------------------------------
    current_date = now.strftime("%b %d, %Y")
    current_time = now.strftime("%I:%M %p")

    # ------------------------------------------------------------
    # Dynamic greeting based on time of day
    # ------------------------------------------------------------
    hour = now.hour
    if hour < 12:
        greeting = "Good morning"
    elif 12 <= hour < 18:
        greeting = "Good afternoon"
    else:
        greeting = "Good evening"

    # ------------------------------------------------------------
    # Fetch employees grouped by department with today's attendance
    # ------------------------------------------------------------
    employees = Employee.objects.all().order_by("department", "full_name")
    departments = defaultdict(list)
    today = now.date()

    for emp in employees:
        # Get today’s attendance record (create if doesn’t exist)
        attendance, _ = Attendance.objects.get_or_create(
            employee=emp,
            date=today,
            defaults={"status": "Not Checked In"}
        )

        # Determine display status
        if attendance.clock_in and not attendance.clock_out:
            if attendance.late_minutes > 30:
                status_label = "Checked In (Late – Explanation Required)"
            elif 0 < attendance.late_minutes <= 30:
                status_label = f"Checked In (Late: {attendance.late_minutes} min)"
            else:
                status_label = "Checked In"
        elif attendance.clock_in and attendance.clock_out:
            status_label = f"Checked Out ({attendance.hours_worked or 0} hrs)"
        else:
            status_label = "Not Checked In"

        # Attach fields for table rendering
        emp.attendance_status = status_label
        emp.attendance_record = attendance
        emp.hours_worked = attendance.hours_worked or 0

        # Group by department
        departments[emp.department].append(emp)

        for emp in employees:
            attendance = Attendance.objects.filter(employee=emp, date=today).first()
            if attendance:
                emp.attendance_status = attendance.status or "Not Checked In"
                emp.attendance_record = attendance
            else:
                emp.attendance_status = "Not Checked In"
                emp.attendance_record = None


    # ------------------------------------------------------------
    # Render template
    # ------------------------------------------------------------
    context = {
        "current_date": current_date,
        "current_time": current_time,
        "greeting": greeting,
        "departments": dict(departments),
        "emps": employees, 
    }

    return render(request, "smartpayapp/checkin_checkout.html", context)


# ================================================================
# Attendance Actions (Clock-In / Clock-Out)
# ================================================================


@csrf_exempt
def attendance_action(request):
    """
    Handles AJAX Clock-In / Clock-Out actions and updates Attendance records.

    Features:
    - Determines lateness and early departures.
    - Updates 'status', 'late_minutes', 'needs_explanation', and 'hours_worked'.
    - Returns a JSON response for frontend dynamic table updates.
    """

    # -------------------------------
    # Validate request
    # -------------------------------
    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "Invalid request method"})

    staff_id = request.POST.get("staff_id")
    action = request.POST.get("action")

    # -------------------------------
    # Validate employee existence
    # -------------------------------
    try:
        employee = Employee.objects.get(staff_id=staff_id)
    except Employee.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Employee not found"})

    # -------------------------------
    # Setup base time references
    # -------------------------------
    now = timezone.localtime(timezone.now())
    today = now.date()
    now_time = now.time()

    # Working hours setup
    weekday = today.weekday()  # Monday = 0, Sunday = 6
    if weekday < 5:  # Monday–Friday
        start_time = time(8, 0)
        end_time = time(17, 0)
    elif weekday == 5:  # Saturday
        start_time = time(8, 0)
        end_time = time(13, 0)
    else:
        return JsonResponse({"status": "error", "message": "Non-working day"})

    # -------------------------------
    # Get or create attendance record
    # -------------------------------
    attendance, _ = Attendance.objects.get_or_create(employee=employee, date=today)

    # -------------------------------
    # CLOCK-IN HANDLING
    # -------------------------------
    if action == "checkin":
        if attendance.clock_in:
            return JsonResponse({"status": "error", "message": "Already checked in today"})

        attendance.clock_in = now_time

        # Determine lateness
        if now_time > start_time:
            diff = datetime.combine(today, now_time) - datetime.combine(today, start_time)
            late_minutes = diff.seconds // 60
            attendance.late_minutes = late_minutes
            attendance.status = "Late Check-In"
            # Require explanation if > 30 min late
            attendance.needs_explanation = late_minutes > 30
        else:
            attendance.late_minutes = 0
            attendance.status = "Checked In"
            attendance.needs_explanation = False

        attendance.save()

        return JsonResponse({
            "status": "success",
            "action": "checkin",
            "attendance_status": attendance.status,
            "late_minutes": attendance.late_minutes,
            "needs_explanation": attendance.needs_explanation,
        })

    # -------------------------------
    # CLOCK-OUT HANDLING
    # -------------------------------
    elif action == "checkout":
        if not attendance.clock_in:
            return JsonResponse({"status": "error", "message": "Cannot check out before checking in"})
        if attendance.clock_out:
            return JsonResponse({"status": "error", "message": "Already checked out today"})

        attendance.clock_out = now_time

        # Calculate total hours worked
        datetime_in = datetime.combine(today, attendance.clock_in)
        datetime_out = datetime.combine(today, now_time)
        worked = datetime_out - datetime_in
        worked_hours = round(worked.total_seconds() / 3600, 2)
        attendance.hours_worked = worked_hours

        # Determine early leave
        if now_time < end_time:
            attendance.status = "Left Early"
            attendance.needs_explanation = True
        else:
            attendance.status = "Checked Out"
            attendance.needs_explanation = False

        attendance.save()

        return JsonResponse({
            "status": "success",
            "action": "checkout",
            "attendance_status": attendance.status,
            "hours_worked": attendance.hours_worked,
            "needs_explanation": attendance.needs_explanation,
        })

    # -------------------------------
    # INVALID ACTION
    # -------------------------------
    else:
        return JsonResponse({"status": "error", "message": "Invalid action"})



# ================================================================
# Attendance History View
# ================================================================

def attendance_history(request):
    """
    Displays historical attendance for all employees.
    Can filter by month, week, or individual employee.
    Shows worked hours, late arrivals, and early leaves.
    Useful for HR reporting.
    """
    employees = Employee.objects.all().order_by("department", "full_name")
    departments = defaultdict(list)

    for emp in employees:
        emp_attendance = emp.attendances.order_by("-date")  
        departments[emp.department].append({
            "employee": emp,
            "attendance": emp_attendance
        })

    context = {
        "departments": dict(departments)
    }

    return render(request, "smartpayapp/attendance_history.html", context)


# ================================================================
# Unified Daily Attendance Evaluation Function
# ================================================================

def evaluate_attendance(attendance, start_time, end_time):
    """
    Evaluates both lateness (clock-in) and early departure (clock-out).
    Dynamically computes hours worked and flags HR explanation when needed.
    """

    today = attendance.date
    clock_in = attendance.clock_in
    clock_out = attendance.clock_out

    # 1. CLOCK-IN EVALUATION
    if clock_in:
        # Calculate lateness in minutes
        late_delta = datetime.combine(today, clock_in) - datetime.combine(today, start_time)
        late_minutes = max(0, int(late_delta.total_seconds() / 60))
        attendance.late_minutes = late_minutes

        # Apply logic based on lateness severity
        if late_minutes == 0:
            attendance.status = "Checked In on Time"
            attendance.needs_explanation = False
        elif late_minutes <= 30:
            attendance.status = f"Late by {late_minutes} min (Within Limit)"
            attendance.needs_explanation = False
            # Optional leave deduction (1 workday = 480 minutes)
            leave_deduction = late_minutes / 480
            attendance.status += f" | Leave Deducted: {round(leave_deduction, 3)} days"
        else:
            attendance.status = f"Late by {late_minutes} min (Requires Explanation)"
            attendance.needs_explanation = True
    else:
        attendance.status = "No Clock-In Recorded"
        attendance.needs_explanation = True
        attendance.save()
        return  # Can't proceed further without clock-in

    # 2. CLOCK-OUT EVALUATION
    if clock_out:
        # Calculate worked hours
        worked_duration = datetime.combine(today, clock_out) - datetime.combine(today, clock_in)
        worked_hours = round(worked_duration.total_seconds() / 3600, 2)
        attendance.hours_worked = worked_hours

        # Determine early leave
        early_delta = datetime.combine(today, end_time) - datetime.combine(today, clock_out)
        early_minutes = max(0, int(early_delta.total_seconds() / 60))

        if early_minutes > 0:
            attendance.status += f" | Left Early by {early_minutes} min (Requires Explanation)"
            attendance.needs_explanation = True
        else:
            attendance.status += f" | Completed Full Day"

    else:
        attendance.status += " | No Clock-Out Recorded"

    attendance.save()




def attendance_overview(request):
    today = timezone.localtime(timezone.now()).date()
    employees = Employee.objects.all().order_by("department", "full_name")
    
    attendance_data = []
    for emp in employees:
        att, created = Attendance.objects.get_or_create(employee=emp, date=today)
        status = "Not Checked In"
        if att.clock_in and not att.clock_out:
            status = "Checked In"
        elif att.clock_out:
            status = "Checked Out"
        
        attendance_data.append({
            "id": emp.id,
            "full_name": emp.full_name,
            "staff_id": emp.staff_id,
            "department": emp.department,
            "status": status,
            "clock_in": att.clock_in.strftime("%I:%M %p") if att.clock_in else "-",
            "clock_out": att.clock_out.strftime("%I:%M %p") if att.clock_out else "-"
        })

    context = {
        "attendance_data": attendance_data
    }
    return render(request, "smartpayapp/attendance_overview.html", context)


def attendance_overview_data(request):
    today = timezone.localtime(timezone.now()).date()
    employees = Employee.objects.all()
    data = []

    for emp in employees:
        att, _ = Attendance.objects.get_or_create(employee=emp, date=today)
        status = "Not Checked In"
        if att.clock_in and not att.clock_out:
            status = "Checked In"
        elif att.clock_out:
            status = "Checked Out"

        data.append({
            "id": emp.id,
            "full_name": emp.full_name,
            "status": status,
            "clock_in": att.clock_in.strftime("%I:%M %p") if att.clock_in else "-",
            "clock_out": att.clock_out.strftime("%I:%M %p") if att.clock_out else "-"
        })
    return JsonResponse({"attendance_data": data})



def attendance_page(request):
    employees = Employee.objects.all()
    today = date.today()
    departments = {}

    for emp in employees:
        # Get today’s attendance record if exists
        attendance = Attendance.objects.filter(employee=emp, date=today).first()
        emp.attendance_status = (
            attendance.status if attendance else "Not Checked In"
        )
        emp.clock_in = attendance.clock_in if attendance else None
        emp.clock_out = attendance.clock_out if attendance else None
        emp.hours_worked = attendance.hours_worked if attendance else 0
        emp.late_minutes = attendance.late_minutes if attendance else 0
        emp.needs_explanation = attendance.needs_explanation if attendance else False

        departments.setdefault(emp.department, []).append(emp)

    return render(request, "attendance.html", {
        "departments": departments,
        "current_date": timezone.localdate(),
        "current_time": timezone.localtime().strftime("%H:%M"),
        "greeting": "Welcome Back",
    })


@csrf_exempt  
def update_attendance(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            emp_id = data.get("emp_id")
            state = data.get("state")

            employee = Employee.objects.get(staff_id=emp_id)

            # Create or update today’s attendance
            today = datetime.date.today()
            attendance, created = Attendance.objects.get_or_create(
                employee=employee,
                date=today,
                defaults={"status": state}
            )

            if not created:
                attendance.status = state
                attendance.save()

            return JsonResponse({"success": True, "message": f"{employee.full_name} {state}"})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=500)

    return JsonResponse({"success": False, "error": "Invalid method"}, status=400)


# ================================================================
# 12. PR Views
# ================================================================
def pr(request):
    return render(request, 'smartpayapp/pr_page.html')

def booking(request):
    return render(request, 'smartpayapp/booking.html')

def personal_profile(request):
    return render(request, 'smartpayapp/personal_profile.html')

def product_overview(request):
    return render(request, 'smartpayapp/product_overview.html')

def buy_product(request):
    return render(request, 'smartpayapp/buy_product.html')