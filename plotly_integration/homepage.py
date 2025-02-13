from dash import html, dcc
from django_plotly_dash import DjangoDash

# Initialize the Dash app
app = DjangoDash('homepage')

# Define the layout
app.layout = html.Div(
    children=[
        # Header section
        html.Div(
            children=[
                html.H1("Process Development Sample Analysis", style={
                    'font-size': '36px',
                    'color': '#ffffff',
                    'margin-bottom': '20px',
                }),
                html.P("Select an option below to proceed.", style={
                    'font-size': '18px',
                    'color': '#eaeaea'
                }),
            ],
            style={
                'text-align': 'center',
                'padding': '30px 20px',
                'background-color': '#0056b3',
                'border-radius': '8px',
                'margin-bottom': '30px',
            }
        ),
        # Button section
        html.Div(
            children=[
                dcc.Link(
                    html.Button("Database Management", style={
                        'width': '250px',
                        'height': '60px',
                        'font-size': '18px',
                        'color': '#ffffff',
                        'background-color': '#007bff',
                        'border': 'none',
                        'border-radius': '8px',
                        'cursor': 'pointer',
                        'box-shadow': '2px 2px 5px rgba(0, 0, 0, 0.2)'
                    }),
                    href="http://localhost:8000/plotly_integration/dash-app/app/DatabaseManagerApp/",
                    target="_blank"
                ),
                dcc.Link(
                    html.Button("Create Report", style={
                        'width': '250px',
                        'height': '60px',
                        'font-size': '18px',
                        'color': '#ffffff',
                        'background-color': '#28a745',
                        'border': 'none',
                        'border-radius': '8px',
                        'cursor': 'pointer',
                        'box-shadow': '2px 2px 5px rgba(0, 0, 0, 0.2)'
                    }),
                    href="http://localhost:8000/plotly_integration/dash-app/app/ReportApp/",
                    target="_blank"
                ),
                dcc.Link(
                    html.Button("Report", style={
                        'width': '250px',
                        'height': '60px',
                        'font-size': '18px',
                        'color': '#ffffff',
                        'background-color': '#ffc107',
                        'border': 'none',
                        'border-radius': '8px',
                        'cursor': 'pointer',
                        'box-shadow': '2px 2px 5px rgba(0, 0, 0, 0.2)'
                    }),
                    href="http://localhost:8000/plotly_integration/dash-app/app/TimeSeriesApp/",
                    target="_blank"
                ),
                dcc.Link(
                    html.Button("Column Analysis", style={
                        'width': '250px',
                        'height': '60px',
                        'font-size': '18px',
                        'color': '#ffffff',
                        'background-color': '#ff7f00',
                        'border': 'none',
                        'border-radius': '8px',
                        'cursor': 'pointer',
                        'box-shadow': '2px 2px 5px rgba(0, 0, 0, 0.2)'
                    }),
                    href="http://localhost:8000/plotly_integration/dash-app/app/ColumnUsageApp/",
                    target="_blank"
                )
            ],
            style={
                'display': 'flex',
                'justify-content': 'center',
                'gap': '20px',
                'margin-top': '20px'
            }
        )
    ],
    style={
        'display': 'flex',
        'flex-direction': 'column',
        'align-items': 'center',
        'padding': '40px',
        'font-family': 'Arial, sans-serif',
        'background-color': '#f4f6f9',
        'min-height': '100vh'
    }
)
