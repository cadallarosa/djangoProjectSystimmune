from django import forms


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
