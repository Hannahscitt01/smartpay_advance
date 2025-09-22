from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User

from .forms import SignUpForm, SalaryAdvanceForm, EmployeeForm, ProfileUpdateForm, LoanRequestForm
from .models import Profile, SalaryAdvanceRequest, Employee, LoanRequest, ChatMessage, SupportChatMessage
from .decorators import admin_required
from decimal import Decimal
from django.db.models import Sum, Q
from django.utils import timezone


# ================================================================
# Landing & Static Views
# ================================================================
def index(request):
    """Landing page view."""
    return render(request, 'smartpayapp/index.html')


def application(request):
    """Application info page."""
    return render(request, 'smartpayapp/application.html')


def signup_sucess(request):
    """Simple success card page shown after account creation."""
    return render(request, 'smartpayapp/signup_sucess.html')


@login_required
def internal_loan(request):
    """Internal loan request page view."""
    profile = request.user.profile
    employee = profile.employee  # Get logged in employee

    if request.method == "POST":
        form = LoanRequestForm(request.POST, employee=employee)
        if form.is_valid():
            loan = form.save(commit=False)
            loan.employee = employee
            loan.save()
            messages.success(request, "Loan request submitted successfully.")
            return redirect("internal_loan_success")  # define this URL
    else:
        form = LoanRequestForm(employee=employee)

    # Calculate eligibility
    monthly_salary = employee.salary
    max_loan = monthly_salary * 2
    active_loans = LoanRequest.objects.filter(employee=employee, status="Approved").aggregate(
    total=Sum("amount")
    )["total"] or 0


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
    """Internal loan request success view."""
    return render(request, 'smartpayapp/internal_loan_sucess.html')


def message_finance(request):
    """Finance messaging placeholder view."""
    return render(request, 'smartpayapp/message_finance.html')


@login_required
def chat_finance(request):
    user = request.user
    finance_officer, created = User.objects.get_or_create(
        username="finance",
        defaults={"first_name": "Finance", "last_name": "Dept", "email": "finance@company.com"}
    )

    # Fetch all messages between logged in user and finance
    messages = ChatMessage.objects.filter(
        Q(sender=user, receiver=finance_officer) |
        Q(sender=finance_officer, receiver=user)
    ).order_by("timestamp")



    # Mark received messages as read
    messages.filter(receiver=user, is_read=False).update(is_read=True)

    if request.method == "POST":
        msg = request.POST.get("message")
        if msg.strip():
            ChatMessage.objects.create(
                sender=user,
                receiver=finance_officer,
                message=msg
            )
        return redirect("chat_finance")

    context = {
        "messages": messages,
        "finance_officer": finance_officer
    }
    return render(request, "smartpayapp/chat_finance.html", context)



@login_required
def support_query(request):
    """Support query placeholder view."""
    user = request.user

    # Assume support staff is a specific user or group; for now, pick the first admin
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
        return redirect("support_query")

    # Fetch conversation
    messages = []
    if support_user:
        messages = SupportChatMessage.objects.filter(
            Q(sender=user, receiver=support_user) |
            Q(sender=support_user, receiver=user)
        ).order_by("timestamp")

    context = {"messages": messages}
    return render(request, "smartpayapp/support-query.html", context)



def admin_home(request):
    """Admin landing page (post-login)."""
    return render(request, 'smartpayapp/admin_home.html')


# ================================================================
# Authentication: Sign Up & Login
# ================================================================
def signup(request):
    """
    Handle staff account creation.

    - On POST: validate SignUpForm and create user + profile.
    - On success: redirect to success page.
    - On failure: re-render with error messages.
    """
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, "Account created successfully! Please log in.")
                return redirect("signup_sucess")
            except Exception as e:
                # Catch unexpected issues (e.g., DB errors)
                messages.error(request, f"Signup failed: {str(e)}")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = SignUpForm()

    return render(request, "smartpayapp/sign_up.html", {"form": form})


def login_view(request):
    """
    Authenticate users using Staff ID as username.

    - On success: redirect based on role (Admin → dashboard, Staff → home).
    - On failure: show error and reload login form.
    """
    if request.method == "POST":
        staffid = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=staffid, password=password)
        if user:
            login(request, user)
            # Redirect based on role
            if hasattr(user, "profile") and user.profile.role == "ADMIN":
                return redirect("admin_dashboard")
            return redirect("home")
        else:
            messages.error(request, "Invalid Staff ID or password")

    return render(request, "smartpayapp/login.html")


# ================================================================
# Staff / User Dashboard & Profile Management
# ================================================================

# ================================================================
# Home Dashboard View
# ================================================================
@login_required
def home(request):
    """
    Dashboard view for logged-in employees.
    Displays:
    - Current salary and advance eligibility.
    - Outstanding loans and advances.
    - Loan and salary advance history with repayment progress.
    """

    # Get the logged-in user's profile and linked employee record
    profile = request.user.profile
    employee = getattr(profile, "employee", None)

    # Defaults for context
    current_salary = "N/A"
    advance_eligibility = "N/A"
    active_loans = 0
    salary_advances = []
    internal_loans = []

    if employee and employee.salary is not None:
        salary = employee.salary

        # Format salary and eligibility for display
        current_salary = f"KSh {salary:,.2f}"
        advance_eligibility = f"Eligible — Up to KSh {float(salary) * 0.5:,.2f}"

        # ================================
        # Salary Advances
        # ================================
        salary_advances = SalaryAdvanceRequest.objects.filter(
            user=request.user
        ).order_by("-date_requested")

        # Attach remaining salary info per advance
        for advance in salary_advances:
            if advance.status == "Approved":
                # Deduct only if approved
                advance.remaining_salary = float(salary) - float(advance.amount)
            else:
                # For Pending or Rejected → full salary remains
                advance.remaining_salary = float(salary)

        # ================================
        # Internal Loans
        # ================================
        internal_loans = LoanRequest.objects.filter(
            employee=employee
        ).order_by("-created_at")

        # Attach repayment progress per loan
        for loan in internal_loans:
            if loan.status == "Approved":
                # Example: Simple static repayment progress (customize later)
                loan.repayment_progress = 70
            else:
                # Pending or Rejected loans → no repayment yet
                loan.repayment_progress = 0

        # ================================
        # Outstanding Loan Balance
        # ================================
        active_loans = LoanRequest.objects.filter(
            employee=employee, status="Approved"
        ).aggregate(total=Sum("amount"))["total"] or 0

    # ================================
    # Context for Template
    # ================================
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
    Allow staff to update their profile picture.

    - On POST: save uploaded picture.
    - On GET: display current profile.
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
# Salary Advance Requests
# ================================================================
@login_required
def request_form(request):
    """
    Salary advance request form.

    - On POST: validate and save request linked to logged-in user.
    - On GET: show blank form.
    """
    profile = request.user.profile
    employee = profile.employee  # Linked Employee object

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
    """Success page after employee requests salary advance."""
    return render(request, 'smartpayapp/request_form_success.html')

# ================================================================
# Employee Management (HR/Admin)
# ================================================================
def employee_creation(request):
    """
    Create a new employee record.

    - On POST: validate and save employee form.
    - On success: show confirmation page.
    - On GET: render empty form.
    """
    if request.method == "POST":
        form = EmployeeForm(request.POST)
        if form.is_valid():
            employee = form.save()
            return render(
                request,
                "smartpayapp/employee_creation_success.html",
                {"employee": employee},
            )
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = EmployeeForm()

    return render(request, "smartpayapp/employee_creation.html", {"form": form})


def employee_creation_success(request):
    """Success page after employee creation."""
    return render(request, 'smartpayapp/employee_creation_success.html')



def employee_list(request):
    """Shows a list of all employees grouped by department."""
    departments = [dept[0] for dept in Employee.DEPARTMENTS]
    grouped_employees = {}

    for dept in departments:
        grouped_employees[dept] = Employee.objects.filter(department=dept).order_by("full_name")

    context = {
        "grouped_employees": grouped_employees
    }
    return render(request, "smartpayapp/employee_list.html", context)


# ================================================================
# Admin Views
# ================================================================
@admin_required
def admin_dashboard(request):
    """Admin dashboard view (restricted by custom decorator)."""
    return render(request, "smartpayapp/admin_dashboard.html")


def redirect_after_login(request):
    """Helper: redirect based on role after login."""
    if request.user.profile.role == "ADMIN":
        return redirect("admin_dashboard")
    return redirect("staff_dashboard")


# ================================================================
# Finance Views
# ===============================================================
def finance(request):
    """finance view """
    return render(request, "smartpayapp/finance.html")