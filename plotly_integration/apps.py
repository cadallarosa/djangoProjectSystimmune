import threading
import time
from django.apps import AppConfig

class PlotlyIntegrationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'plotly_integration'

    def ready(self):
        from django.core.checks import run_checks
        run_checks()  # Ensures Django settings are loaded before importing

        def delayed_import():
            time.sleep(5)  # Delay import by 5 seconds
            try:
                import plotly_integration.empower.create_report_app
                import plotly_integration.homepage
                import plotly_integration.database_manager
                import plotly_integration.empower.sec_report_app
                import plotly_integration.empower.titer_report_app
                import plotly_integration.empower.column_analysis_app
                import plotly_integration.sartoflow_smart.viral_filtration_app
                import plotly_integration.sartoflow_smart.ufdf_app
                import plotly_integration.sartoflow_smart.create_experiment
                import plotly_integration.sartoflow_smart.create_vf_experiment
                import plotly_integration.akta.akta_app.akta_data_import
                import plotly_integration.akta.akta_app.akta_app
                import plotly_integration.process_development.cld_mass_check.cld_mass_check_import_app
                import protein_engineering.homepage
                import protein_engineering.sec_report_app
                import protein_engineering.create_report_app
                import plotly_integration.process_development.cell_culture.nova_flex_2.nova_data_import_app
                import plotly_integration.process_development.cell_culture.nova_flex_2.nova_create_report_app
                import plotly_integration.process_development.cell_culture.nova_flex_2.nova_report_app
                import plotly_integration.process_development.cell_culture.vicell.vicell_data_import_app
                import plotly_integration.process_development.cell_culture.vicell.vicell_create_report_app
                import plotly_integration.process_development.cell_culture.vicell.vicell_report_app
                import plotly_integration.akta.opcua_server.opcua_client_app
            except Exception as e:
                print(f"Error loading modules: {e}")

        # Run the delayed import in a separate thread
        thread = threading.Thread(target=delayed_import)
        thread.start()
