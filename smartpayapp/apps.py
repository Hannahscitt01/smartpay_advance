from django.apps import AppConfig

class SmartpayappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'smartpayapp'

    def ready(self):
        # Import signals to ensure they are registered
        import smartpayapp.signals



