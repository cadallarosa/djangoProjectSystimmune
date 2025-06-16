from dash import html, dcc
from django_plotly_dash import DjangoDash

# Initialize the Dash app
app = DjangoDash('lc-ms')

# Define the layout
app.layout = html.Div(
    children=[
        # Header section
        html.Div(
            children=[
                html.H1("LC-MS", style={
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
                'margin-bottom': '10px',
            }
        ),

        # Released Glycan Section
        html.Div(
            children=[
                html.H2("Released N-Glycan", style={
                    'font-size': '28px',
                    'color': '#ffffff',
                    'text-align': 'center',
                    'margin-bottom': '20px'
                }),
                html.Div(
                    children=[
                        dcc.Link(
                            html.Button("Import Released N-Glycan Results", style={
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
                            href="http://localhost:8000/plotly_integration/dash-app/app/GlycanComponentAnalysis/",
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
                            href="http://localhost:8000/plotly_integration/dash-app/app/CreateGlycanReportApp/",
                            target="_blank"
                        ),
                        dcc.Link(
                            html.Button("Glycan Analysis", style={
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
                            href="http://localhost:8000/plotly_integration/dash-app/app/GlycanReportAnalysisApp/",
                            target="_blank"
                        ),


                    ],
                    style={
                        'display': 'flex',
                        'justify-content': 'center',
                        'gap': '20px',
                        'flex-wrap': 'wrap'
                    }
                )
            ],
            style={
                'text-align': 'center',
                'padding': '30px 20px',
                'background-color': '#343a40',
                'border-radius': '8px',
                'margin-top': '30px',
                'width': '100%'
            }
        ),
# Mass Check Section
        html.Div(
            children=[
                html.H2("Mass Check", style={
                    'font-size': '28px',
                    'color': '#ffffff',
                    'text-align': 'center',
                    'margin-bottom': '20px'
                }),
                html.Div(
                    children=[
                        dcc.Link(
                            html.Button("Import Released Mass Check Results", style={
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
                            href="http://localhost:8000/plotly_integration/dash-app/app/MassCheckDataImportApp/",
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
                            href="http://localhost:8000/plotly_integration/dash-app/app/CreateMassCheckReportApp/",
                            target="_blank"
                        ),
                        dcc.Link(
                            html.Button("Mass Check Analysis", style={
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
                            href="http://localhost:8000/plotly_integration/dash-app/app/MassCheckAnalysisApp/",
                            target="_blank"
                        ),


                    ],
                    style={
                        'display': 'flex',
                        'justify-content': 'center',
                        'gap': '20px',
                        'flex-wrap': 'wrap'
                    }
                )
            ],
            style={
                'text-align': 'center',
                'padding': '30px 20px',
                'background-color': '#343a40',
                'border-radius': '8px',
                'margin-top': '30px',
                'width': '100%'
            }
        ),
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
