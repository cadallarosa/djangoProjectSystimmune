import pandas as pd
import dash
import base64
import io
from dash import dcc, html, dash_table, Input, Output, State
from django_plotly_dash import DjangoDash
from plotly_integration.models import ProjectID

# Define the Dash app
app = DjangoDash('CLDDataApp')

app.layout = html.Div(
    style={"backgroundColor": "#ffffff", "padding": "20px", "minHeight": "100vh"},
    children=[
        html.H3("CLD Data Upload & Preview Before Inserting",
                style={"textAlign": "center", "color": "#003f7f", "marginBottom": "20px"}),

        # Upload Component
        dcc.Upload(
            id='upload-data',
            children=html.Div([
                'Drag and Drop or ',
                html.A('Select an Excel File')
            ]),
            style={
                "width": "100%", "height": "60px", "lineHeight": "60px",
                "borderWidth": "2px", "borderStyle": "dashed",
                "borderColor": "#003f7f", "borderRadius": "8px",
                "textAlign": "center", "marginBottom": "20px",
                "backgroundColor": "#d6e0ff"
            },
            multiple=False
        ),

        html.Div(id='output-data-upload'),  # Displays file name

        # ✅ Table to Preview Uploaded Spreadsheet
        html.H4("Uploaded File Preview"),
        dash_table.DataTable(
            id="uploaded-data-table",

            page_size=20,
            style_table={"overflowX": "auto"},
            style_header={
                "backgroundColor": "#003f7f",
                "color": "white",
                "fontWeight": "bold"
            },
            style_cell={
                "textAlign": "center",
                "padding": "8px",
                "border": "1px solid #ccd6f6"
            }
        ),

        # ✅ Button to confirm upload & save data
        html.Button("Confirm Upload", id="confirm-upload", n_clicks=0,
                    style={"backgroundColor": "#003f7f", "color": "white",
                           "border": "none", "padding": "10px 20px",
                           "borderRadius": "5px", "cursor": "pointer",
                           "display": "block", "margin": "20px auto"}),
        html.Div(id="upload-status-message"),  # ✅ Display upload status

        # ✅ Table to display existing database records
        html.H4("Loaded Data from Database"),
        dash_table.DataTable(
            id="loaded-data-table",
            columns=[],
            data=[],
            page_size=10,
            sort_action="native",  # ✅ Enable sorting
            sort_mode="multi",  # ✅ Allow sorting by multiple columns
            style_table={'overflowX': 'auto'},
            style_header={
                "backgroundColor": "#003f7f",
                "color": "white",
                "fontWeight": "bold"
            },
            style_cell={
                "textAlign": "center",
                "padding": "8px",
                "border": "1px solid #ccd6f6"  # Subtle gray-blue border
            }

        ),

        # ✅ Button to refresh existing data
        html.Button("Show Existing Data", id="show-upload-preview", n_clicks=0,
                    style={"backgroundColor": "#003f7f", "color": "white",
                           "border": "none", "padding": "10px 20px",
                           "borderRadius": "5px", "cursor": "pointer",
                           "display": "block", "margin": "20px auto"}),
    ])

# Define the exact column names as they appear in the Django `ProjectID` model
DB_COLUMNS = {
    "Project ": "project",
    "SIP number": "sip_number",
    "FB ID": "fb_id",
    "Sample ID": "cell_line",
    "Description (MP/BP/ BP SCC/MP SCC)": "description",
    "Analyst (CLD)": "analyst",
    "harvest date": "harvest_date",
    "UNIFI#": "unifi_number",
    "Titer Comment": "titer_comment",
    "CLD 30ml Octet titer (g/L)": "cld_30ml_octet_titer",
    "ProAqa Titer (g/L)": "pro_aqa_titer",
    "Fast ProA Recovery %": "fast_pro_a_recovery",
    "Purification recovery A280 (g/L)": "purification_recovery_a280",
    "ProA eluate A280 conc (mg/ml)": "proa_eluate_a280_conc",
    "ProA eluate volume (ml)": "proa_eluate_volume",
    "HCCF loading volume (ml)": "hccf_loading_volume",
    "ProA Recovery (%)": "proa_recovery",
    "ProA column size(mL)": "proa_column_size",
    "Column ID": "column_id",
    "Note": "note",
    "sec_2_wks_a_conc": "sec_2_wks_a_conc",
    "sec_2wks_n_conc": "sec_2wks_n_conc"
}

# ✅ Store the uploaded dataframe in memory
uploaded_df_store = {}


# Function to parse uploaded content
def parse_contents(contents, filename):
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)

    try:
        if 'csv' in filename:
            df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
        elif 'xls' in filename:
            df = pd.read_excel(io.BytesIO(decoded))
    except Exception as e:
        return None, html.Div(["There was an error processing this file."])

    # Drop columns that should not be stored
    columns_to_remove = ['intact_or_reduced', 'mass_confirmed', 'sample_id']
    df = df.drop(columns=[col for col in columns_to_remove if col in df.columns], errors='ignore')

    # Rename columns based on mapping
    df = df.rename(columns=DB_COLUMNS)

    # Drop columns that are not in the model
    df = df[[col for col in DB_COLUMNS.values() if col in df.columns]]

    # Fill missing values for critical fields
    critical_columns = ["project", "sip_number", "description", "analyst", "harvest_date"]
    for col in critical_columns:
        if col in df.columns:
            df[col] = df[col].ffill()

    # Replace NaN with None for MySQL compatibility
    df = df.where(pd.notna(df), None)

    return df, None


# Callback to preview uploaded data (without saving to database)
@app.callback(
    [Output('output-data-upload', 'children'),
     Output('uploaded-data-table', 'columns'),
     Output('uploaded-data-table', 'data')],
    Input('upload-data', 'contents'),
    State('upload-data', 'filename')
)
def update_output(contents, filename):
    global uploaded_df_store  # ✅ Store the uploaded dataframe in memory

    if contents is None:
        return html.Div("No file uploaded yet."), [], []

    df, error_message = parse_contents(contents, filename)

    if df is None or df.empty:
        return html.Div("Error: No valid data to process."), [], []

    uploaded_df_store["df"] = df  # ✅ Store dataframe for later upload confirmation

    columns = [{"name": col, "id": col} for col in df.columns]
    return html.Div(f"Successfully uploaded {filename}"), columns, df.to_dict("records")


# Callback to confirm upload and save data
@app.callback(
    Output("upload-status-message", "children"),
    Input("confirm-upload", "n_clicks")
)
def confirm_upload(n_clicks):
    global uploaded_df_store

    if n_clicks == 0:
        return ""

    df = uploaded_df_store.get("df", None)
    if df is None or df.empty:
        return "No data available for upload."

    # ✅ Store data in the database
    for _, row in df.iterrows():
        project_data = row.to_dict()

        # ✅ Convert NaN values to None (MySQL cannot store NaN)
        project_data = {key: (None if pd.isna(value) else value) for key, value in project_data.items()}

        # Ensure primary key (fb_id) exists before updating/creating records
        if project_data.get("fb_id") and project_data["fb_id"] is not None:
            ProjectID.objects.update_or_create(
                fb_id=project_data["fb_id"],  # Primary Key
                defaults=project_data
            )

    uploaded_df_store.clear()  # ✅ Clear stored data after saving

    return "Data successfully uploaded to the database!"


# Callback to display the already loaded database records
@app.callback(
    Output("loaded-data-table", "columns"),
    Output("loaded-data-table", "data"),
Output("loaded-data-table", "page_size"),  # ✅ Dynamically adjust page size
    Input("show-upload-preview", "n_clicks")
)
def load_existing_data(n_clicks):
    queryset = ProjectID.objects.all().values()
    if not queryset.exists():
        return [], [] , 10

    df = pd.DataFrame.from_records(queryset)
    columns = [{"name": col, "id": col} for col in df.columns]
    return columns, df.to_dict("records"), 20
