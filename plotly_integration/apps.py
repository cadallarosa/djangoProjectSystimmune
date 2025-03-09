from django.apps import AppConfig


class PlotlyIntegrationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'plotly_integration'

    def ready(self):
        from django.core.checks import run_checks
        run_checks()  # This ensures Django settings are loaded before importing
        try:
            import plotly_integration.empower.create_report_app  # Ensure Dash app initializes correctly
            import plotly_integration.homepage
            import plotly_integration.database_manager
            import plotly_integration.empower.sec_report_app
            import plotly_integration.empower.titer_report_app
            import plotly_integration.empower.column_analysis_app
            import plotly_integration.sartoflow_smart.viral_filtration_app
            # import plotly_integration.sartoflow_smart.process_sartoflow_data
            import plotly_integration.sartoflow_smart.ufdf_app
            import plotly_integration.sartoflow_smart.create_experiment
            import plotly_integration.sartoflow_smart.create_vf_experiment
            import plotly_integration.akta.akta_data_import
            import plotly_integration.akta.akta_app
            import plotly_integration.process_development.cld_mass_check.cld_mass_check_import_app
        except Exception as e:
            print(f"Warning: Dash app import failed - {e}")

