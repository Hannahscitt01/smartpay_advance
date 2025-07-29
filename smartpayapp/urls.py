from django.urls import path
from .views import(
    home,
    application
)

urlpatterns = [
    path('', home, name='home'),
    path('application/', application, name='application')
]
