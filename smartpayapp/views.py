from django.shortcuts import render

# Create your views here.
def index(request):
    return render(request, 'smartpayapp/index.html')

def application(request):
    return render(request, 'smartpayapp/application.html')

def login(request):
    return render(request, 'smartpayapp/login.html') 

def signup(request):
    return render(request,'smartpayapp/sign_up.html' )

def home(request):
    return render(request, 'smartpayapp/home.html')

def request_form(request):
    return render(request, 'smartpayapp/request_form.html')

