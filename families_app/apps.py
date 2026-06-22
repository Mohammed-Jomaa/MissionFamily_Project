from django.apps import AppConfig


class FamiliesAppConfig(AppConfig):
    name = 'families_app'

    def ready(self):
        import families_app.signals
