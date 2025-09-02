#Fill with your Twilio credentials
import os
from dotenv import load_dotenv
load_dotenv()
TWILIO_SID =os.getenv("TWILIO_SID")
TWILIO_AUTH_TOKEN =os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE= os.getenv("TWILIO_PHONE") # Your Twilio phone number
TO_NUMBER =os.getenv ("TO_NUMBER ") # Farmer/your mobile number
WEATHER_API_KEY=os.getenv("WEATHER_API_KEY")


