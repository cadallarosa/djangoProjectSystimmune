from django.contrib import admin
from .models import (
     AktaColumnsCharacteristics, AktaMethodInformation,
     AktaScoutingList, PDSamples, DnAssignment
)

# admin.site.register(AktaResult)
admin.site.register(AktaColumnsCharacteristics)
admin.site.register(AktaMethodInformation)
admin.site.register(AktaScoutingList)
admin.site.register(PDSamples)
admin.site.register(DnAssignment)