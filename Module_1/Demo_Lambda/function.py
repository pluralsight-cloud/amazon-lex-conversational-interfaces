import boto3
import os

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['TABLE_NAME'])

def lambda_handler(event, context):
    order_id = event['sessionState']['intent']['slots']['OrderId']['value']['interpretedValue']

    try:
        response = table.get_item(Key={'OrderId': order_id})
        item = response.get('Item')

        if item:
            message = f"Order {order_id} is currently: {item['Status']}"
        else:
            message = f"Sorry, I couldn't find order {order_id}"

        return {
            "sessionState": {
                "dialogAction": { "type": "Close" },
                "intent": {
                    "name": "CheckOrderStatus",
                    "state": "Fulfilled"
                }
            },
            "messages": [
                {
                    "contentType": "PlainText",
                    "content": message
                }
            ]
        }

    except Exception as e:
        print(f"Error: {e}")
        return {
            "sessionState": {
                "dialogAction": { "type": "Close" },
                "intent": {
                    "name": "CheckOrderStatus",
                    "state": "Failed"
                }
            },
            "messages": [
                {
                    "contentType": "PlainText",
                    "content": "There was an error looking up your order."
                }
            ]
        }
