from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import *
from .serializers import *
from rest_framework.views import APIView
import re
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework import generics
from rest_framework import serializers
from django.http import JsonResponse, HttpRequest
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import os
from datetime import datetime,timedelta




SCOPES = ["https://www.googleapis.com/auth/calendar"]

def get_credentials():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json')
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'zion.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds

def create_event(service, start_datetime_str, end_datetime_str, full_name, email, mobile_number):
    try:
        start_datetime = datetime.strptime(start_datetime_str, "%Y-%m-%d %H:%M:%S")
        end_datetime = datetime.strptime(end_datetime_str, "%Y-%m-%d %H:%M:%S")

        event = {
            'summary': 'Appointments',
            'start': {
                'dateTime': start_datetime.isoformat(),
                'timeZone': 'UTC',
            },
            'end': {
                'dateTime': end_datetime.isoformat(),
                'timeZone': 'UTC',
            },
            'description': f'Booked by: {full_name}\nEmail: {email}\nMobile: {mobile_number}',
        }

        event = service.events().insert(calendarId='primary', body=event).execute()
        print(f'Event created: {event.get("htmlLink")}')
    except Exception as e:
        print(f"Error creating event: {e}")
        raise


@csrf_exempt
def create_google_calendar_event(request: HttpRequest):
    if request.method == 'POST':
        try:
            
            date = request.POST.get('date')
            time = request.POST.get('time')
            full_name = request.POST.get('full_name')
            email = request.POST.get('email')
            mobile_number = request.POST.get('mobile_number')
            start_datetime_str = f"{date} {time}"
            end_datetime_str = (datetime.strptime(start_datetime_str, "%Y-%m-%d %H:%M:%S") + timedelta(minutes=15)).strftime("%Y-%m-%d %H:%M:%S")

            creds = get_credentials()
            service = build('calendar', 'v3', credentials=creds)
            create_event(service, start_datetime_str, end_datetime_str, full_name, email, mobile_number)

            return JsonResponse({"message": "Event created successfully"}, status=200)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)



class AvailableSlotListAPIView(generics.ListAPIView):
    serializer_class = AvailableSlotSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serialized_dates = [slot.date.strftime("%d %B") for slot in queryset]
        return Response(serialized_dates)

    def get_queryset(self):
    
        return AvailableSlot.objects.all()



class AvailableTimeView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = AvailableSlotSerializer(data=request.data)
        
        try:
            serializer.is_valid(raise_exception=True)
        except serializers.ValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        date = serializer.validated_data['date']
        available_slot = self.get_available_slot(date)
        if not available_slot:
            return Response({'error': 'No available slot for the given date'}, status=status.HTTP_404_NOT_FOUND)
        first_time_availability = TimeAvailability.objects.filter(available_slot=available_slot).first()

        if not first_time_availability:
            return Response({'error': 'No time availabilities found for the given date'}, status=status.HTTP_404_NOT_FOUND)

        serialized_data = TimeAvailabilitySerializer(first_time_availability).data
        return Response(serialized_data, status=status.HTTP_200_OK)

    def get_available_slot(self, date):
        try:
            return AvailableSlot.objects.get(date=date)
        except AvailableSlot.DoesNotExist:
            return None
        
class TimeValidationAPIView(APIView):
    def post(self, request):
        time_input = request.data.get('time')
        
        # Updated regular expression pattern to match time formats like "1pm", "1:00am", "5:00 pm", "1 am"
        pattern = r'^(1[0-2]|0?[1-9])(:[0-5][0-9])?\s?(am|pm)$|^(1[0-2]|0?[1-9])(am|pm)$'
        
        
        if re.match(pattern, time_input.lower()):
            # Add a space between time and am/pm if it doesn't exist to standardize the format
            if len(time_input.split()) == 1:
                # Insert a colon between hour and minute if it's missing
                if len(time_input) == 3:
                    time_input = time_input[:1] + ':00' + time_input[1:]
                time_input = time_input[:-2] + ' ' + time_input[-2:]
            
            try:
                time_obj = datetime.strptime(time_input, "%I:%M %p")
                formatted_time = time_obj.strftime("%H:%M:%S")
                return Response({"message": "Valid time format!", "formatted_time": formatted_time}, status=status.HTTP_200_OK)
            except ValueError:
                return Response({"message": "Invalid time format. Please provide a valid time."}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"message": "Invalid time format. Please provide the time in the format '1 pm' or '12 am'."}, status=status.HTTP_400_BAD_REQUEST)


class CheckTimeAvailabilityAPI(APIView):
    def post(self, request):
        date_str = request.data.get('date')
        time_str = request.data.get('time')
        if not date_str or not time_str:
            return Response({'error': 'Please provide a date and time'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
            time = datetime.strptime(time_str, '%H:%M:%S').time()
        except ValueError:
            return Response({'error': 'Invalid date or time format. Please provide date in YYYY-MM-DD format and time in HH:MM:SS format'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            available_slot = AvailableSlot.objects.get(date=date)
        except AvailableSlot.DoesNotExist:
            return Response({'error': 'No available slot for the given date'}, status=status.HTTP_404_NOT_FOUND)
        
        time_availability = TimeAvailability.objects.filter(available_slot=available_slot, start_time__lte=time, end_time__gte=time).first()
        if time_availability:
            return Response({'message': 'Time is available'}, status=status.HTTP_200_OK)
        else:
            return Response({'message': 'Time is not available'}, status=status.HTTP_400_BAD_REQUEST)




class LocationListCreateView(APIView):
    def get(self, request):
        
        locations = Location.objects.all()
        serializer = LocationSerializer(locations, many=True)
        addresses = [location["address"] for location in serializer.data]
        return Response(addresses)

    def post(self, request):
        serializer = LocationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



@api_view(['GET'])
def get_pdfdata(request):
    data = Pdfdata.objects.all()
    serializer = PdfdataSerializer(data, many=True)
    return Response(serializer.data)






class GetUrlByLocation(APIView):
    def post(self, request):
        
        serializer = LocationSerializer(data=request.data)
        if serializer.is_valid():
            address = serializer.validated_data.get('address')

            
            try:
                home_url = HomeURL.objects.get(location__address__iexact=address)
                home_url_serializer = HomeURLSerializer(home_url)
                return Response(home_url_serializer.data, status=status.HTTP_200_OK)
            except HomeURL.DoesNotExist:
                return Response({"detail": "URL not found for the given location."},
                                status=status.HTTP_404_NOT_FOUND)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class GetPdfByLocation(APIView):
    def post(self, request):
        # Deserialize the incoming data to get the location
        serializer = LocationSerializer(data=request.data)
        if serializer.is_valid():
            location = serializer.validated_data['address']

            # Retrieve the Pdfdata instance associated with the provided location
            try:
                pdf_data = Pdfdata.objects.get(location__address=location)
                pdf_serializer = PdfdataSerializer(pdf_data)
                return Response(pdf_serializer.data, status=status.HTTP_200_OK)
            except Pdfdata.DoesNotExist:
                return Response({"detail": "PDF not found for the given location."},
                                status=status.HTTP_404_NOT_FOUND)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)




# Function to validate the International Phone Numbers
def is_valid_phone_number(phone_number):
    pattern = r"^[+]{1}(?:[0-9\\-\\(\\)\\/""\\.]\\s?){11,13}[0-9]{1}$"
    if not phone_number:
        return False
    return bool(re.match(pattern, phone_number))

@csrf_exempt
def validate_phone(request):
    if request.method == 'POST':
        phone_number = request.POST.get('phone_number')
        is_valid = is_valid_phone_number(phone_number)

        if not is_valid:
            return JsonResponse({'error': 'Not a valid phone number'}, status=400)

        response = {
            'phone_number': phone_number,
            'is_valid': is_valid,
            'message': 'Valid phone number'
        }

        return JsonResponse(response)




@api_view(['POST'])
def validate_email(request):
    email = request.data.get('email')
    if not email:
        return Response({'error': 'Email address is required'}, status=400)

    pattern = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
    match = pattern.search(email)
    if match:
        return Response({'message': 'Valid email address'}, status=200)
    else:
        return Response({'error': 'Invalid email address'}, status=400)


