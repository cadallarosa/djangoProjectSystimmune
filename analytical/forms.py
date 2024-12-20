from django import forms
from .models import Project, Sample


class PlotValuesForm(forms.Form):
    x_values = forms.CharField(label='X values', max_length=200)
    y_values = forms.CharField(label='Y values', max_length=200)
    z_values = forms.CharField(label='Z values', max_length=200)


class DatabaseSampleForm(forms.Form):
    sample_name = forms.CharField(label='Sample Name', max_length=200)
    channels = forms.MultipleChoiceField(widget=forms.CheckboxSelectMultiple,
                                         choices=[
                                             ("Channel 1", "Channel 1"),
                                             ("Channel 2", "Channel 2"),
                                             ("Channel 3", "Channel 3")
                                         ]
                                         )


# I'm assuming you have these options in your current setup
SAMPLE_TYPES = [
    ('UP', 'UP'),
    ('FB', 'FB'),
    ('PD', 'PD'),
]


class ProjectForm(forms.Form):
    report_name = forms.CharField(label='Report Name', max_length=100)
    project_id = forms.ChoiceField(
        choices=[(name, name) for name in Project.get_unique_names(
            db_name='C:/Users/cdallarosa/DataAlchemy/Database Management/Database Management/Empower.db',
            table_name='project_id', column_name="project_name")]
    )
    sample_type = forms.ChoiceField(choices=SAMPLE_TYPES)


class SampleForm(forms.Form):
    sample_selection = forms.MultipleChoiceField(
        widget=forms.CheckboxSelectMultiple,
        choices=[]
    )