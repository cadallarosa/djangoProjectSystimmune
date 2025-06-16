from django.contrib import admin
from .models import (
     AktaColumnsCharacteristics, AktaMethodInformation,
     AktaScoutingList,
     # LimsPDSamples,
     # DnAssignment
)

# admin.site.register(AktaResult)
admin.site.register(AktaColumnsCharacteristics)
admin.site.register(AktaMethodInformation)
admin.site.register(AktaScoutingList)
# admin.site.register(LimsPDSamples)
# admin.site.register(DnAssignment)