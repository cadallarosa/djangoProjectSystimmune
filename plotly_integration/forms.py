from django import forms
from .models import Report

class ReportSelectionForm(forms.Form):
    report_name = forms.ChoiceField(
        choices=[],
        label="Select Report Name",
        required=True,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['report_name'].choices = [
            (report.report_name, report.report_name) for report in Report.objects.all()
        ]
