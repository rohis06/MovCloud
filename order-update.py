import os
import logging
import boto3

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize the DynamoDB client
dynamodb = boto3.resource('dynamodb', region_name=os.environ['AWS_REGION'])
table_name = os.environ['TABLE_NAME']
table = dynamodb.Table(table_name)

def handler(event, context):
    order = event['Order']
    order_id = order['OrderID']

    logger.info(f"[{order_id}] - received request to update order status")

    # Retrieve the order from DynamoDB
    try:
        existing_order = get_order(order_id)
    except Exception as e:
        logger.error(f"[{order_id}] - error! {str(e)}")
        return {
            'statusCode': 500,
            'body': 'Error retrieving order from DynamoDB'
        }

    # Set order status to "Pending"
    existing_order['OrderStatus'] = 'Pending'

    # Save the updated order
    try:
        save_order(existing_order)
    except Exception as e:
        logger.error(f"[{order_id}] - error! {str(e)}")
        return {
            'statusCode': 500,
            'body': 'Error saving order to DynamoDB'
        }

    # Testing scenario
    if order_id.startswith('11'):
        return {
            'statusCode': 400,
            'body': 'Unable to update order status for ' + order_id
        }

    logger.info(f"[{order_id}] - order status updated to pending")

    return {
        'statusCode': 200,
        'body': order
    }

def get_order(order_id):
    response = table.get_item(Key={'order_id': order_id})
    if 'Item' not in response:
        raise Exception('Order not found in DynamoDB')
    return response['Item']

def save_order(order):
    response = table.put_item(Item=order)
    if response['ResponseMetadata']['HTTPStatusCode'] != 200:
        raise Exception('Failed to put record to DynamoDB')

# For testing locally
if __name__ == '__main__':
    event = {
        'Order': {
            'OrderID': '123',
            'OrderData': 'example data',
            'OrderStatus': 'New'
        }
    }
    context = None
    response = handler(event, context)
    print(response)
