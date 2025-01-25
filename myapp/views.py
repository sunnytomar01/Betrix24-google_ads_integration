import os
import json
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException

BITRIX24_APP_TOKEN = "ijtf0dz352qh5t0ganhowoqy66miijxj"
GOOGLE_ADS_CREDENTIALS_FILE = os.getenv('GOOGLE_ADS_CREDENTIALS_PATH', 'D:/form1/client_secret.json')


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

    # gclid = details.get('GCLID', None)  
    # if not gclid:
    #     print("GCLID not found in the payload.")
    #     return JsonResponse({"error": "GCLID not found"}, status=400)

    if event in ["ONCRMLEADADD", "ONCRMLEADUPDATE"]:
    
        lead_id = details.get('FIELDS', {}).get('ID')
        lead_name = details.get('FIELDS', {}).get('TITLE', '')
        lead_status = details.get('FIELDS', {}).get('STATUS', '')

        if lead_id and lead_name:
            send_to_google_ads(
                entity_type="lead",
                entity_id=lead_id,
                entity_name=lead_name,
                entity_status=lead_status,
                gclid=gclid
            )
        else:
            print("Incomplete lead data received.")

    elif event in ["ONCRMDEALADD", "ONCRMDEALUPDATE"]:
        
        deal_id = details.get('FIELDS', {}).get('ID')
        deal_name = details.get('FIELDS', {}).get('TITLE', '')
        deal_status = details.get('FIELDS', {}).get('STAGE_ID', '')

        if deal_id and deal_name:
            send_to_google_ads(
                entity_type="deal",
                entity_id=deal_id,
                entity_name=deal_name,
                entity_status=deal_status,
                gclid=gclid
            )
        else:
            print("Incomplete deal data received.")

    return JsonResponse({"status": "success"})


def send_to_google_ads(entity_type, entity_id, entity_name, entity_status=None, gclid=None):

    client = GoogleAdsClient.load_from_storage(GOOGLE_ADS_CREDENTIALS_FILE)
    customer_id = '583-209-9938'
    conversion_action_id = '963778520' 

    try:
        conversion = client.get_type('ClickConversion')
        conversion.conversion_action = client.get_service('GoogleAdsService').conversion_action_path(customer_id, conversion_action_id)
        # conversion.gclid = gclid
        # conversion.conversion_date_time = details.get('TIMESTAMP', '')  #
        # conversion.conversion_value = 100.0  
        # conversion.currency_code = 'USD'

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
