from rest_framework import serializers
from .models import Location,Pdfdata,AvailableSlot,TimeAvailability ,HomeURL

class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = '__all__'

class PdfdataSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pdfdata
        fields = '__all__'


class AvailableSlotSerializer(serializers.ModelSerializer):
    date = serializers.DateField(format="%d %B")  

    class Meta:
        model = AvailableSlot
        fields = ['date']




# class TimeAvailabilitySerializer(serializers.ModelSerializer):
#     formatted_time_range = serializers.SerializerMethodField()

#     class Meta:
#         model = TimeAvailability
#         fields = ['formatted_time_range']

#     def get_formatted_time_range(self, obj):
#         start_time = obj.start_time.strftime("%-I:%M %p")  # Use %-I for hour without leading zero
#         end_time = obj.end_time.strftime("%-I:%M %p")  # Use %-I for hour without leading zero
#         return f"{start_time} to {end_time}"
    
class TimeAvailabilitySerializer(serializers.ModelSerializer):
    formatted_time_range = serializers.SerializerMethodField()

    class Meta:
        model = TimeAvailability
        fields = ['formatted_time_range']

    def get_formatted_time_range(self, obj):
        start_time = obj.start_time.strftime("%I:%M %p").lstrip('0')  
        end_time = obj.end_time.strftime("%I:%M %p").lstrip('0')  
        return f"{start_time} to {end_time}"

    
    
class HomeURLSerializer(serializers.ModelSerializer):
    class Meta:
        model = HomeURL
        fields = '__all__'