from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User

from .forms import SignUpForm, SalaryAdvanceForm, EmployeeForm, ProfileUpdateForm
from .models import Profile, SalaryAdvanceRequest, Employee
from .decorators import admin_required


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


def internal_loan(request):
    """Internal loan request placeholder view."""
    return render(request, 'smartpayapp/internal_loan.html')


def message_finance(request):
    """Finance messaging placeholder view."""
    return render(request, 'smartpayapp/message_finance.html')


def chat_finance(request):
    """Finance chat placeholder view."""
    return render(request, 'smartpayapp/chat_finance.html')


def support_query(request):
    """Support query placeholder view."""
    return render(request, 'smartpayapp/support-query.html')


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
@login_required
def home(request):
    """Staff dashboard (main home after login)."""
    profile = Profile.objects.get(user=request.user)
    return render(request, "smartpayapp/home.html", {"profile": profile})


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
            return redirect("home")
    else:
        form = SalaryAdvanceForm()

    return render(
        request,
        "smartpayapp/request_form.html",
        {"form": form, "employee": employee},
    )


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
