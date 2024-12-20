from django.shortcuts import render
from .forms import PlotValuesForm
import matplotlib.pyplot as plt
from django.http import HttpResponse


def new_page(request):
    return render(request, 'data_view.html')


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


from .forms import DatabaseSampleForm

# Add this where you have your other imports
import os
import io
import urllib
import base64
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from .utils import main_workflow

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


# from .forms import ProjectForm
# from django.http import HttpResponseRedirect
#
#
# def analytics(request):
#     if request.method == 'POST':
#         form = AnalyticsForm(request.POST)
#         if form.is_valid():
#             # Process the form data
#
#             # If needed, save the data to the database
#             # Redirect to a new URL:
#             return HttpResponseRedirect('/analytics/')
#     else:
#         form = AnalyticsForm()
#
#     return render(request, 'analytics.html', {'form': form})
#
# from django.shortcuts import render
# from .forms import ProjectForm, SampleForm  # Adjust the import statement to match your project structure
# from .models import Sample  # Adjust the import statement to match your project structure
#
#
# def view(request):
#     project_form = ProjectForm()
#     sample_form = SampleForm()
#     if request.method == "POST":
#         if 'update_samples' in request.POST:
#             project_form = ProjectForm(request.POST)
#             if project_form.is_valid():
#                 project_id = project_form.cleaned_data['project_id']
#                 sample_choices = [(name, name) for name in Sample.get_sample_names_by_project(
#                     db_name='C:/Users/cdallarosa/DataAlchemy/Database Management/Database Management/Empower.db',
#                     project_name=project_id)]
#                 sample_form = SampleForm()
#                 sample_form.fields['sample_selection'].choices = sample_choices
#         elif 'submit_form' in request.POST:
#             sample_form = SampleForm(request.POST)
#             if sample_form.is_valid():
#                 pass
#     return render(request, 'analytics.html', {'project_form': project_form, 'sample_form': sample_form})


from django.shortcuts import render
from django.http import JsonResponse
from django.db import connection
import re


def analytics_page(request):
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
    return render(request, 'analytics_test.html')
