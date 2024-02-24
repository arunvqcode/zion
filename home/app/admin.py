from django.contrib import admin
from app.models import Location,Pdfdata,AvailableSlot,TimeAvailability,HomeURL

# Register your models here.

admin.site.register(Location)
admin.site.register(Pdfdata)
admin.site.register(AvailableSlot)
admin.site.register(TimeAvailability)
admin.site.register(HomeURL)