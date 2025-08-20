from django.urls import path
from .views import(
    index,
    application,
    login,
    signup,
    home,
    request_form,
    internal_loan,
    message_finance,
    chat_finance,
    support_query,
    signup_sucess
)

urlpatterns = [
    path('', index, name='index'),
    path('application/', application, name='application'),
    path('login/', login, name='login'),
    path('signup/', signup,name='signup'),
    path('home/', home, name='home'),
    path('request_form/', request_form, name= 'request_form'),
    path('internal_loan/', internal_loan, name= 'internal_loan'),
    path('message_finance/', message_finance, name= 'message_finance'),
    path('chat_finance/', chat_finance,name='chat_finance'),
    path('support_query/', support_query,name='support_query'),
    path('signup_sucess/', signup_sucess,name='signup_sucess')
     
]
