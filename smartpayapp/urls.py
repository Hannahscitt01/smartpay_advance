from django.urls import path
from .views import(
    index,
    application,
    login,
    signup,
    home,
    request_form
)

urlpatterns = [
    path('', index, name='index'),
    path('application/', application, name='application'),
    path('login/', login, name='login'),
    path('signup/', signup,name='signup'),
    path('home/', home, name='home'),
    path('request_form/', request_form, name= 'request_form')
]
