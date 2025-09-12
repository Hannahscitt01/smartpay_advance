from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .forms import SignUpForm, SalaryAdvanceForm, EmployeeForm
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from .models import Profile, SalaryAdvanceRequest
from .decorators import admin_required


# Create your views here.
def index(request):
    return render(request, 'smartpayapp/index.html')

def application(request):
    return render(request, 'smartpayapp/application.html')

def signup_sucess(request):
    return render(request, 'smartpayapp/signup_sucess.html')


def login_view(request):
    if request.method == "POST":
        staffid = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=staffid, password=password)
        if user:
            login(request, user)

            if hasattr(user, "profile"):
                print("USER ROLE:", user.profile.role)  
                if user.profile.role == "ADMIN":
                    return redirect("admin_dashboard")
                else:
                    return redirect("home")
            else:
                messages.error(request, "No profile found for this user.")
                return redirect("login")
        else:
            messages.error(request, "Invalid Staff ID or password")

    return render(request, "smartpayapp/login.html")


def signup(request):
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            # Success → go to signup_success.html
            return render(request, "smartpayapp/signup_sucess.html")
        else:
            # Failure → return back with errors
            return render(request, "smartpayapp/sign_up.html", {
                "form": form,
                "success": False
            })
    else:
        form = SignUpForm()
    return render(request, "smartpayapp/sign_up.html", {"form": form})

def request_form(request):
    profile = get_object_or_404(Profile, user=request.user)

    if request.method == "POST":
        form = SalaryAdvanceForm(request.POST)
        if form.is_valid():
            salary_request = form.save(commit=False)   
            salary_request.user = request.user        
            salary_request.save()                      
            return redirect("home")  
    else:
        form = SalaryAdvanceForm()

    return render(request, "smartpayapp/request_form.html", {
        "form": form,
        "profile": profile
    })




def login_view(request):
    if request.method == "POST":
        staffid = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=staffid, password=password)
        if user:
            login(request, user)
            return redirect("home")
        else:
            messages.error(request, "Invalid Staff ID or password")
    return render(request, "smartpayapp/login.html")

def home(request):
    return render(request, 'smartpayapp/home.html')

def request_form(request):
    profile = get_object_or_404(Profile, user=request.user)

    if request.method == "POST":
        form = SalaryAdvanceForm(request.POST)
        if form.is_valid():
            salary_request = form.save(commit=False)   
            salary_request.user = request.user        
            salary_request.save()                      
            return redirect("home")  
    else:
        form = SalaryAdvanceForm()

    return render(request, "smartpayapp/request_form.html", {
        "form": form,
        "profile": profile
    })



def internal_loan(request):
    return render(request, 'smartpayapp/internal_loan.html')

def message_finance(request):
    return render(request, 'smartpayapp/message_finance.html')

def chat_finance(request):
    return render(request, 'smartpayapp/chat_finance.html')

def support_query(request):
    return render(request, 'smartpayapp/support-query.html')

def internal_loan(request):
    return render(request, 'smartpayapp/internal_loan.html')

def message_finance(request):
    return render(request, 'smartpayapp/message_finance.html')

def chat_finance(request):
    return render(request, 'smartpayapp/chat_finance.html')

def support_query(request):
    return render(request, 'smartpayapp/support-query.html')


def employee_creation(request):
    return render(request, "smartpayapp/employee_creation.html")


def employee_creation(request):
    if request.method == "POST":
        form = EmployeeForm(request.POST)
        if form.is_valid():
            employee = form.save()
            messages.success(request, f"Employee {employee.full_name} added successfully with Staff ID {employee.staff_id}")
            return redirect('employee_creation_success')  # reload page after successful submission
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = EmployeeForm()

    return render(request, "smartpayapp/employee_creation.html", {"form": form})



def employee_creation_success(request):
    return render(request, 'smartpayapp/employee_creation_success.html')
##########################################################
@admin_required
def admin_dashboard(request):
    return render(request, "smartpayapp/admin_dashboard.html")

def redirect_after_login(request):
    if request.user.profile.role == "ADMIN":
        return redirect("admin_dashboard")
    else:
        return redirect("staff_dashboard")


