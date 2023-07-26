import os
import logging
import boto3
import json

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize the DynamoDB client
dynamodb = boto3.resource('dynamodb', region_name=os.environ['AWS_REGION'])
table_name = os.environ['TABLE_NAME']
table = dynamodb.Table(table_name)

def handler(event, context):
    order = json.loads(event['body'])
    order_id = order['OrderID']

    logger.info(f"[{order_id}] - received new order")

    # Persist the order data. Set order status to new.
    order['OrderStatus'] = 'New'

    try:
        save_order(order)
    except Exception as e:
        logger.error(f"[{order_id}] - error! {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

    # Testing scenario
    if order_id.startswith('1'):
        return {
            'statusCode': 400,
            'body': json.dumps({'error': f'Unable to process order {order_id}'})
        }

    logger.info(f"[{order_id}] - order status set to new")

    return {
        'statusCode': 200,
        'body': json.dumps(order)
    }

def save_order(order):
    response = table.put_item(Item=order)
    if response['ResponseMetadata']['HTTPStatusCode'] != 200:
        raise Exception('Failed to put record to DynamoDB')

# For testing locally
if __name__ == '__main__':
    event = {
        'body': '{"OrderID": "123", "OrderData": "example data"}'
    }
    context = None
    response = handler(event, context)
    print(response)
