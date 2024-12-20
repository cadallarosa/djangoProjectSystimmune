from .forms import PlotValuesForm
import matplotlib.pyplot as plt
from django.http import HttpResponse
from .forms import DatabaseSampleForm
import io
import base64
from .utils import main_workflow
from django.shortcuts import render
import re
from django.http import JsonResponse
from django.db import connection, Error

def plot_view(request):
    # Check if form is submitted
    if request.method == 'POST':
        form = PlotValuesForm(request.POST)

        # Check if form input is valid
        if form.is_valid():
            x_values = list(map(int, form.cleaned_data['x_values'].split(',')))
            y_values = list(map(int, form.cleaned_data['y_values'].split(',')))
            z_values = list(map(int, form.cleaned_data['z_values'].split(',')))

            # Plot entered values
            plt.plot(x_values, y_values)
            plt.savefig('myplot.png')

            with open('myplot.png', 'rb') as f:
                return HttpResponse(f.read(), content_type='image/png')
    else:
        form = PlotValuesForm()

    # Render form
    return render(request, 'plot.html', {'form': form})


db_name = 'C:/Users/cdallarosa/DataAlchemy/Database Management/Database Management/Empower.db'


def database_sample_view(request):
    if request.method == 'POST':
        form = DatabaseSampleForm(request.POST)
        if form.is_valid():
            sample_name = form.cleaned_data['sample_name']
            channels = form.cleaned_data['channels']

            fig = main_workflow(
                db_name,
                sample_name,
                mode="overlay",
                channel_plot_logic={channel: True for channel in channels}
            )

            buf = io.BytesIO()
            fig.savefig(buf, format='png')  # adjust this line
            buf.seek(0)
            string = base64.b64encode(buf.read())
            image_base64 = string.decode('utf-8')
            plt.close(fig)

            return render(request, "database_sample.html", {'form': form, 'image_base64': image_base64})
    else:
        form = DatabaseSampleForm()

    return render(request, "database_sample.html", {'form': form})


def reports_page(request):
    if request.method == 'GET':
        action = request.GET.get('action', None)

        if action == 'get_project_ids':
            # Fetch unique project IDs from the database using raw SQL
            with connection.cursor() as cursor:
                cursor.execute("SELECT DISTINCT project_name FROM project_id")
                project_ids = cursor.fetchall()
                project_list = [project[0] for project in project_ids if project is not None]

                # Function to get the numeric value for sorting
                def get_sort_key(a):
                    if a is None:
                        return 0
                    # Find all groups of digits in the name
                    num = re.findall(r'\d+', a)  # This returns a list of all numbers found in the string
                    return int(num[0]) if num else 0  # If no numbers are found, return 0

                # Sort the project list using the custom sort key
                project_list = sorted(project_list, key=get_sort_key)

            # Return project IDs as a JSON response

            return JsonResponse(project_list, safe=False)

        elif action == 'filter_samples':
            # Retrieve parameters from the GET request
            report_name = request.GET.get('report_name', '')
            project_id = request.GET.get('project_id', None)
            sample_type = request.GET.get('sample_type', None)
            analysis_type = request.GET.get('analysis_type', None)

            # Build the SQL query dynamically based on the input filters
            sql_query = "SELECT sample_name, description, analyst, harvest_date FROM project_id WHERE 1=1"
            params = []

            if project_id:
                sql_query += " AND project_name = %s"
                params.append(project_id)

            # if sample_type:
            #     sql_query += " AND description LIKE %s"
            #     params.append(f"%{sample_type}%")

            # if analysis_type:
            #     sql_query += " AND description LIKE %s"
            #     params.append(f"%{analysis_type}%")

            with connection.cursor() as cursor:
                cursor.execute(sql_query, params)
                samples = cursor.fetchall()

            # Format results as a list of dictionaries
            sample_data = [{
                'sample_name': sample[0],
                'description': sample[1],
                'analyst': sample[2],
                'harvest_date': sample[3],
            } for sample in samples]

            return JsonResponse(sample_data, safe=False)

    # Render the initial page when the user accesses the URL
    return render(request, 'analytics_report.html')


def handle_submit(request):
    if request.method == 'POST':
        report_name = request.POST.get('report_name')
        project_id = request.POST.get('project_id')
        sample_type = request.POST.get('sample_type')
        analysis_type = request.POST.get('analysis_type')
        selected_samples = request.POST.get('selected_samples')

        sql = """
        INSERT INTO report (report_name, project_id, sample_type, analysis_type, selected_samples)
        VALUES (%s, %s, %s, %s, %s)
        """

        with connection.cursor() as cursor:
            try:
                cursor.execute(sql, [report_name, project_id, sample_type, analysis_type, selected_samples])
                return JsonResponse({'status': 'success', 'message': 'Report successfully saved.'})
            except Error as e:
                return JsonResponse({'status': 'fail', 'message': 'Could not save the report due to a database error.'})
    else:
        return JsonResponse({'status': 'fail', 'message': 'Invalid request.'})