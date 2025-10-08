from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User

from .forms import SignUpForm, SalaryAdvanceForm, EmployeeForm, ProfileUpdateForm, LoanRequestForm
from .models import Profile, SalaryAdvanceRequest, Employee, LoanRequest, ChatMessage, SupportChatMessage, Attendance
from .decorators import admin_required
from decimal import Decimal
from django.db.models import Sum, Q, Max, Count
from django.utils import timezone

from collections import OrderedDict, defaultdict
from django.http import JsonResponse

from datetime import datetime, time
from django.views.decorators.csrf import csrf_exempt




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
            # ✅ Call the helper here
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
    """Finance landing page/dashboard with dynamic KPI counts."""
    pending_requests_count = SalaryAdvanceRequest.objects.filter(status="Pending").count()
    context = {
        "pending_salary_requests": pending_requests_count,
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

    # Logged-in employee
    try:
        employee = Employee.objects.get(email=request.user.email)
    except Employee.DoesNotExist:
        employee = None

    # Current date and time
    now = timezone.localtime(timezone.now())
    current_date = now.strftime("%b %d, %Y")
    current_time = now.strftime("%I:%M %p")
    current_month = now.month
    current_year = now.year
    today = now.date()  # Today’s date for attendance

    # Dynamic employee and department counts
    total_employees = Employee.objects.count()
    total_departments = Employee.objects.values("department").distinct().count()

    # Employees who checked in today
    employees_checked_in_today = Attendance.objects.filter(
        date=today,
        clock_in__isnull=False
    ).count()

    # Fetch recent employees (added this month)
    recent_employees = Employee.objects.filter(
        date_joined__year=current_year,
        date_joined__month=current_month,
        date_joined__isnull=False
    ).order_by('-date_joined')

    # Fetch recent loan requests only (latest 5)
    loan_requests = LoanRequest.objects.select_related("employee").order_by("-created_at")[:5]

    # ------------------- New: Total Payroll for Current Month -------------------
    total_payroll = Employee.objects.aggregate(
        total=Sum('salary')
    )['total'] or 0

    # ------------------- New: Pending and Approved Loan Counts -------------------
    pending_loans_count = LoanRequest.objects.filter(status="Pending").count()
    approved_loans_count = LoanRequest.objects.filter(status="Approved").count()

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
        "employees_checked_in_today": employees_checked_in_today,  # existing
        "total_payroll": total_payroll,  # existing new
        "pending_loans_count": pending_loans_count,  # new
        "approved_loans_count": approved_loans_count,  # new
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


# ================================================================
# Employee Check-In & Check-Out View
# ================================================================
def checkin_checkout(request):
    """ Employee Check-In & Check-Out """

    now = timezone.localtime(timezone.now()) 

    # ------------------------------------------------------------
    # Format date and time
    # ------------------------------------------------------------
    current_date = now.strftime("%b %d, %Y") 
    current_time = now.strftime("%I:%M %p")   

    # ------------------------------------------------------------
    # Dynamic greeting based on time
    # ------------------------------------------------------------
    hour = now.hour
    if hour < 12:
        greeting = "Good morning"
    elif 12 <= hour < 18:
        greeting = "Good afternoon"
    else:
        greeting = "Good evening"

    # ------------------------------------------------------------
    # Fetch all employees and group by department
    # ------------------------------------------------------------
    employees = Employee.objects.all().order_by("department", "full_name")
    departments = defaultdict(list)

    for emp in employees:
        # Get today's attendance or create if not exists
        attendance, created = Attendance.objects.get_or_create(
            employee=emp,
            date=now.date()
        )

        # --------------------------------------------------------
        # Determine status for display
        # --------------------------------------------------------
        status_label = "Not Checked In"
        if attendance.clock_in and not attendance.clock_out:
            # Employee checked in but not yet checked out
            if attendance.late_minutes > 0 and attendance.late_minutes <= 30:
                status_label = f"Checked In (Late: {attendance.late_minutes} min, auto-deducted leave)"
            elif attendance.late_minutes > 30:
                status_label = "Checked In (Late – Explanation Required)"
            else:
                status_label = "Checked In"
        elif attendance.clock_in and attendance.clock_out:
            status_label = f"Checked Out ({attendance.hours_worked} hrs)"
        else:
            status_label = "Not Checked In"

        # Attach status to employee object dynamically
        emp.attendance_status = status_label
        emp.attendance_record = attendance

        # Group employees by department
        departments[emp.department].append(emp)

    # ------------------------------------------------------------
    # Context for template
    # ------------------------------------------------------------
    context = {
        "current_date": current_date,
        "current_time": current_time,
        "greeting": greeting,
        "departments": dict(departments), 
    }

    return render(request, "smartpayapp/checkin_checkout.html", context)



# ================================================================
# Attendance Actions (Clock-In / Clock-Out)
# ================================================================

@csrf_exempt
def attendance_action(request):
    """
    Handles AJAX Clock-In / Clock-Out requests.
    
    Updates the Attendance record for today:
        - clock_in or clock_out time
        - calculates hours_worked
        - calculates late_minutes and flags if explanation is needed
    Returns a JSON response for frontend updates.
    """
    if request.method == "POST":
        staff_id = request.POST.get("staff_id")
        action = request.POST.get("action")  # 'checkin' or 'checkout'

        try:
            employee = Employee.objects.get(staff_id=staff_id)
        except Employee.DoesNotExist:
            return JsonResponse({"status": "error", "message": "Employee not found"})

        today = timezone.localtime(timezone.now()).date()
        now_time = timezone.localtime(timezone.now()).time()

        # --- Get or create today's attendance record ---
        attendance, created = Attendance.objects.get_or_create(employee=employee, date=today)

        # --- Organization working hours ---
        weekday = today.weekday()  # Monday=0, Sunday=6
        if weekday < 5:  # Monday-Friday
            start_time = time(8, 0)
            end_time = time(17, 0)
        elif weekday == 5:  # Saturday
            start_time = time(8, 0)
            end_time = time(13, 0)
        else:  # Sunday is non-working
            return JsonResponse({"status": "error", "message": "Today is a non-working day"})

        if action == "checkin":
            attendance.clock_in = now_time

            # --- Calculate lateness ---
            late_delta = datetime.combine(today, now_time) - datetime.combine(today, start_time)
            late_minutes = max(0, int(late_delta.total_seconds() / 60))
            attendance.late_minutes = late_minutes

            # --- Set status ---
            if late_minutes > 30:
                attendance.status = "Late - Needs Explanation"
                attendance.needs_explanation = True
            elif late_minutes > 0:
                attendance.status = "Late (Within Limit)"
            else:
                attendance.status = "Checked In"

            attendance.save()
            return JsonResponse({
                "status": "success",
                "action": "checkin",
                "attendance_status": attendance.status,
                "late_minutes": attendance.late_minutes
            })

        elif action == "checkout":
            if not attendance.clock_in:
                return JsonResponse({"status": "error", "message": "Cannot check out without checking in"})

            attendance.clock_out = now_time
            attendance.calculate_hours()
            attendance.status = "Checked Out"
            attendance.save()
            
            return JsonResponse({
                "status": "success",
                "action": "checkout",
                "hours_worked": attendance.hours_worked,
                "attendance_status": attendance.status
            })

        else:
            return JsonResponse({"status": "error", "message": "Invalid action"})
    else:
        return JsonResponse({"status": "error", "message": "Invalid request method"})


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
# Automatic Leave Deduction and Alerts
# ================================================================
def handle_leave_and_alert(attendance):
    """
    Handles automatic leave deductions if an employee is late within allowed limits.
    Flags excessive lateness requiring explanation.
    """
    if attendance.late_minutes > 0 and attendance.late_minutes <= 30:
       
        leave_deduction = attendance.late_minutes / 480
    
        attendance.status += f" | Leave Deducted: {round(leave_deduction, 3)} days"
    elif attendance.late_minutes > 30:
        attendance.status += " | Action Required: Provide Explanation"
        attendance.needs_explanation = True
    
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
