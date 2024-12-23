from django.apps import AppConfig


class PlotlyIntegrationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'plotly_integration'

    def ready(self):
        import plotly_integration.dash_app
