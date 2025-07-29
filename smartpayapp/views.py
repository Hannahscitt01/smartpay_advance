from django.shortcuts import render

# Create your views here.
def home(request):
    return render(request, 'smartpayapp/index.html')

def application(request):
    return render(request, 'smartpayapp/application.html')
