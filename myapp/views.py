import os
import json
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException
from datetime import datetime
import pytz

BITRIX24_APP_TOKEN = "ijtf0dz352qh5t0ganhowoqy66miijxj"
GOOGLE_ADS_CREDENTIALS_FILE = os.getenv('GOOGLE_ADS_CREDENTIALS_PATH', 'D:/form1/client_secret.json')
TIMEZONE = pytz.timezone("Europe/London")

@csrf_exempt
def bitrix24_handler(request):
    if request.method != 'POST':
        return JsonResponse({"error": "Method Not Allowed"}, status=405)
    
    if request.content_type == 'application/x-www-form-urlencoded':
        data = request.POST.dict()
    elif request.content_type == 'application/json':
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)
    else:
        return JsonResponse({"error": "Unsupported Media Type"}, status=415)

    token = data.get('auth', {}).get('application_token', '') or request.POST.get('auth[application_token]', '')
    if token != BITRIX24_APP_TOKEN:
        return JsonResponse({"error": "Unauthorized"}, status=403)

    event = data.get('event', '')
    details = data.get('data', {})
    print(f"Received event: {event}")
    print(f"Data: {details}")

    gclid = details.get('GCLID', None)  
    if not gclid:
        print("GCLID not found in the payload.")
        return JsonResponse({"error": "GCLID not found"}, status=400)

    if event in ["ONCRMLEADADD", "ONCRMLEADUPDATE"]:
        lead_id = details.get('FIELDS', {}).get('ID')
        lead_name = details.get('FIELDS', {}).get('TITLE', '')
        lead_status = details.get('FIELDS', {}).get('STATUS', '')
        lead_email = details.get('FIELDS', {}).get('EMAIL', [{}])[0].get('VALUE', '')
        lead_phone = details.get('FIELDS', {}).get('PHONE', [{}])[0].get('VALUE', '')
        lead_currency = details.get('FIELDS', {}).get('CURRENCY', 'USD')
        lead_value = details.get('FIELDS', {}).get('AMOUNT', 100.0)  

        created_time = details.get('FIELDS', {}).get('DATE_CREATE', '')
        if created_time:
            lead_created_time = datetime.strptime(created_time, "%Y-%m-%d %H:%M:%S")
            lead_created_time = lead_created_time.replace(tzinfo=TIMEZONE)
        else:
            lead_created_time = None

        if lead_id and lead_name:
        
            conversion_name = "Qualified Lead" if lead_status != "DEAL_WON" else "Converted Lead"
            send_to_google_ads(
                entity_type="lead",
                entity_id=lead_id,
                entity_name=lead_name,
                entity_status=lead_status,
                gclid=gclid,
                conversion_name=conversion_name,
                conversion_value=lead_value,
                currency_code=lead_currency,
                email=lead_email,
                phone=lead_phone,
                created_time=lead_created_time
            )
        else:
            print("Incomplete lead data received.")

    elif event in ["ONCRMDEALADD", "ONCRMDEALUPDATE"]:
        deal_id = details.get('FIELDS', {}).get('ID')
        deal_name = details.get('FIELDS', {}).get('TITLE', '')
        deal_status = details.get('FIELDS', {}).get('STAGE_ID', '')
        deal_value = details.get('FIELDS', {}).get('AMOUNT', 100.0)  
        deal_currency = details.get('FIELDS', {}).get('CURRENCY', 'USD')

        if deal_id and deal_name:
        
            conversion_name = "Converted Lead" if deal_status == "DEAL_WON" else "Qualified Lead"
            send_to_google_ads(
                entity_type="deal",
                entity_id=deal_id,
                entity_name=deal_name,
                entity_status=deal_status,
                gclid=gclid,
                conversion_name=conversion_name,
                conversion_value=deal_value,
                currency_code=deal_currency
            )
        else:
            print("Incomplete deal data received.")

    elif event in ["ONCRMLEADDELETE"]:
        lead_id = details.get('FIELDS', {}).get('ID')
        if lead_id:
            delete_from_google_ads(
                entity_type="lead",
                entity_id=lead_id,
                gclid=gclid
            )
        else:
            print("Lead ID missing in deletion request.")

    elif event in ["ONCRMDEALDELETE"]:
        deal_id = details.get('FIELDS', {}).get('ID')
        if deal_id:
            delete_from_google_ads(
                entity_type="deal",
                entity_id=deal_id,
                gclid=gclid
            )
        else:
            print("Deal ID missing in deletion request.")

    return JsonResponse({"status": "success"})


def send_to_google_ads(entity_type, entity_id, entity_name, entity_status=None, gclid=None, 
                       conversion_name=None, conversion_value=None, currency_code=None, 
                       email=None, phone=None, created_time=None):
    client = GoogleAdsClient.load_from_storage(GOOGLE_ADS_CREDENTIALS_FILE)
    customer_id = '583-209-9938'
    
    conversion_action_id = '963778520' if conversion_name == "Converted Lead" else 'QUALIFIED_LEAD_CONVERSION_ID'
    
    try:
        conversion = client.get_type('ClickConversion')
        conversion.conversion_action = client.get_service('GoogleAdsService').conversion_action_path(customer_id, conversion_action_id)
        conversion.gclid = gclid
        conversion.conversion_value = conversion_value
        conversion.currency_code = currency_code
        conversion.email = email
        conversion.phone_number = phone
        conversion.created_at = created_time

        conversion_upload_service = client.get_service('ConversionUploadService')
        response = conversion_upload_service.upload_click_conversions(
            customer_id=customer_id,
            conversions=[conversion],
            partial_failure=True,
        )

        if response.partial_failure_error:
            print(f"Partial failure: {response.partial_failure_error.message}")
        else:
            print(f"Conversion successfully uploaded for {entity_type}: {entity_name} (ID: {entity_id})")

    except GoogleAdsException as ex:
        print(f"Google Ads API Error: {ex}")
    except Exception as e:
        print(f"Unexpected error: {e}")


def delete_from_google_ads(entity_type, entity_id, gclid=None):
    client = GoogleAdsClient.load_from_storage(GOOGLE_ADS_CREDENTIALS_FILE)
    customer_id = '583-209-9938'
    conversion_action_id = '963778520'

    try:
        conversion = client.get_type('ClickConversion')
        conversion.conversion_action = client.get_service('GoogleAdsService').conversion_action_path(customer_id, conversion_action_id)
        conversion.gclid = gclid
        conversion.conversion_value = 0.0  
        conversion.currency_code = 'USD'

        conversion_upload_service = client.get_service('ConversionUploadService')
        response = conversion_upload_service.upload_click_conversions(
            customer_id=customer_id,
            conversions=[conversion],
            partial_failure=True,
        )

        if response.partial_failure_error:
            print(f"Partial failure: {response.partial_failure_error.message}")
        else:
            print(f"Conversion deletion successfully uploaded for {entity_type}: ID {entity_id}")

    except GoogleAdsException as ex:
        print(f"Google Ads API Error: {ex}")
    except Exception as e:
        print(f"Unexpected error: {e}")
