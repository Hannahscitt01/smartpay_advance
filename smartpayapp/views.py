from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User

from .forms import SignUpForm, SalaryAdvanceForm, EmployeeForm, ProfileUpdateForm, LoanRequestForm
from .models import Profile, SalaryAdvanceRequest, Employee, LoanRequest, ChatMessage, SupportChatMessage
from .decorators import admin_required
from decimal import Decimal
from django.db.models import Sum, Q, Max
from django.utils import timezone

from collections import OrderedDict
from django.http import JsonResponse


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
    return render(request, 'smartpayapp/internal_loan_sucess.html')


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
    
    # Assuming your logged-in user is linked to an Employee instance
    try:
        employee = Employee.objects.get(email=request.user.email)
    except Employee.DoesNotExist:
        employee = None

    current_date = timezone.localtime(timezone.now()).strftime("%b %d, %Y")
    current_time = timezone.localtime(timezone.now()).strftime("%I:%M %p")

    context = {
        "employee": employee,
        "current_date": current_date,
        "current_time": current_time,
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

def hr_track_performance(request):
    """Placeholder view for Track Performance (UI stub)."""
    return render(request, 'smartpayapp/hr_track_performance.html')