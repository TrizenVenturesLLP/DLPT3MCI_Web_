
import os
from dotenv import load_dotenv
from twilio.rest import Client

load_dotenv()

# Twilio configuration
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER')

class SMSSender:
    def __init__(self):
        self.client = None
        if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN and TWILIO_PHONE_NUMBER:
            self.client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
            self.from_number = TWILIO_PHONE_NUMBER
        else:
            print("Warning: Twilio credentials not found. SMS functionality disabled.")

    def format_phone_number(self, phone_number):
        """Format phone number to E.164 format for Twilio"""
        # Strip any non-digit characters
        digits_only = ''.join(filter(str.isdigit, phone_number))
        
        # If the number already has a plus sign, it might be in international format
        if phone_number.startswith('+'):
            return phone_number
        
        # Handle Indian numbers (10 digits)
        if len(digits_only) == 10:
            # For India, the country code is +91
            return f"+91{digits_only}"
        
        # For US/Canada numbers (10 digits)
        if len(digits_only) == 10:
            return f"+1{digits_only}"
            
        # If it's already a full international number without the plus
        if len(digits_only) > 10:
            # Check if it starts with country code
            if digits_only.startswith('91') and len(digits_only) == 12:  # India
                return f"+{digits_only}"
            if digits_only.startswith('1') and len(digits_only) == 11:   # US/Canada
                return f"+{digits_only}"
            
        # If we can't determine the format, return with a plus sign
        # hoping it's already in international format without the plus
        return f"+{digits_only}"

    def send_message(self, to_number, message):
        """Send an SMS message using Twilio"""
        if not self.client:
            print("SMS sending disabled: Twilio not configured.")
            return False
        
        try:
            # Format the phone number properly for Twilio
            formatted_number = self.format_phone_number(to_number)
            print(f"Sending SMS to formatted number: {formatted_number}")
                
            message = self.client.messages.create(
                body=message,
                from_=self.from_number,
                to=formatted_number
            )
            print(f"SMS sent successfully. SID: {message.sid}")
            return True
        except Exception as e:
            print(f"Error sending SMS: {e}")
            return False

    def send_child_found_notification(self, parent_phone, child_name, location, reporter_name, reporter_phone):
        """Send notification to parent that their child has been found"""
        if not parent_phone:
            print("Cannot send SMS: No parent phone number provided")
            return False
            
        message = (
            f"URGENT: Your child {child_name} has been found! "
            f"Current location: {location}. "
            f"Found by: {reporter_name}. "
            f"Contact finder at: {reporter_phone}. "
            f"Please contact authorities immediately."
        )
        
        return self.send_message(parent_phone, message)
