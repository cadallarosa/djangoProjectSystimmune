from django.shortcuts import render
from .forms import ReportSelectionForm
from .models import Report, SampleMetadata, TimeSeriesData
import plotly.graph_objects as go
import pandas as pd

def plot_time_series(request):
    project_id = None
    sample_list = []
    plot_html = ""

    if request.method == "POST":
        form = ReportSelectionForm(request.POST)
        if form.is_valid():
            report_name = form.cleaned_data['report_name']
            # Get the Report object
            report = Report.objects.filter(report_name=report_name).first()
            if report:
                project_id = report.project_id
                selected_samples = report.selected_samples
                sample_list = selected_samples.split(",")
    else:
        form = ReportSelectionForm()

    # Proceed with the plotting logic if sample_list is populated
    if sample_list:
        sample_names = sample_list
        selected_channels = ['channel_1']  # Modify as needed
        filtered_samples = SampleMetadata.objects.filter(sample_name__in=sample_names)

        # Initialize the figure
        fig = go.Figure()

        # Loop over samples and add traces
        for sample in filtered_samples:
            time_series = TimeSeriesData.objects.filter(result_id=sample.result_id)
            df = pd.DataFrame(list(time_series.values()))

            # Add traces for each selected channel
            for channel in selected_channels:
                if channel in df.columns:
                    fig.add_trace(go.Scatter(
                        x=df['time'],
                        y=df[channel],
                        mode='lines',
                        name=f"{sample.sample_name} - {channel}"
                    ))

        # Update layout
        fig.update_layout(
            title='Time Series Data',
            xaxis_title='Time (seconds)',
            yaxis_title='Intensity',
            template='plotly_white'
        )

        # Convert the plot to HTML
        plot_html = fig.to_html(full_html=False)

    return render(request, 'time_series.html', {
        'form': form,
        'project_id': project_id,
        'plot_html': plot_html,
        'sample_names': sample_list,  # Pass the sample names to the template
    })


from django.shortcuts import render

def home(request):
    return render(request, 'dashboard.html')

def dashboard(request):
    return render(request, 'dashboard.html')