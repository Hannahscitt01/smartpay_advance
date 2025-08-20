from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import SignUpForm
from django.contrib.auth import authenticate, login


# Create your views here.
def index(request):
    return render(request, 'smartpayapp/index.html')

def application(request):
    return render(request, 'smartpayapp/application.html')

def login(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")
        
        # Authenticate using Django's built-in system
        user = authenticate(request, username=email, password=password)
        
        if user is not None:
            login(request, user)
            return redirect("home")  # successful login
        else:
            messages.error(request, "Invalid email or password")
    
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


def signup_sucess(request):
    return render(request, 'smartpayapp/signup_sucess.html')

def home(request):
    return render(request, 'smartpayapp/home.html')

def request_form(request):
    return render(request, 'smartpayapp/request_form.html')

def internal_loan(request):
    return render(request, 'smartpayapp/internal_loan.html')

def message_finance(request):
    return render(request, 'smartpayapp/message_finance.html')

def chat_finance(request):
    return render(request, 'smartpayapp/chat_finance.html')

def support_query(request):
    return render(request, 'smartpayapp/support-query.html')