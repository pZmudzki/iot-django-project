from django.apps import AppConfig


class LedAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'led_app'

    def ready(self):
        from .background import start_background_tasks
        start_background_tasks()
