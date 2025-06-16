from dash import Output, Input, html
from django_plotly_dash import DjangoDash
from .layout.layout import app_layout, view_samples_layout, create_samples_layout, \
    sample_set_table_layout, sample_set_view_samples_layout, sample_set_sec_report_layout
import dash_bootstrap_components as dbc


app = DjangoDash("CLDSampleManagementApp2", external_stylesheets=[dbc.themes.BOOTSTRAP], title="CLD Sample Manager")
# app = DjangoDash("CLDSampleManagementApp2")
app.layout = app_layout

from .callbacks.view_sample_set import sample_sets
from .callbacks.view_sample_set import view_samples
from .callbacks import create_samples
from .callbacks import view_samples
from .callbacks.view_sample_set import sec_report

# Page routing
@app.callback(
    Output("page-content", "children"),
    Input("url", "pathname")
)
def display_page(pathname):
    if pathname == "/sample-sets/table":
        return sample_set_table_layout()
    elif pathname == "/sample-sets/view":
        return sample_set_view_samples_layout()
    elif pathname == "/sample-sets/sec":
        return sample_set_sec_report_layout()
    elif pathname == "/view-samples":
        return view_samples_layout()
    elif pathname == "/create-samples":
        return create_samples_layout()
    return html.Div("404 - Page Not Found")