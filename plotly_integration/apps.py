from django.apps import AppConfig


class PlotlyIntegrationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'plotly_integration'

    def ready(self):
        import plotly_integration.create_report_app  # Ensure Dash app initializes correctly
        import plotly_integration.homepage
        import plotly_integration.database_manager
        import plotly_integration.report_app
        import plotly_integration.column_analysis_app