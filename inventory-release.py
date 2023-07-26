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

    logger.info(f"[{order_id}] - processing inventory release")

    # Find inventory transaction
    inventory, err = get_transaction(order_id)
    if err is not None:
        logger.error(f"[{order_id}] - error! {str(err)}")
        return {
            'statusCode': 500,
            'body': 'Error releasing inventory'
        }

    # Release the items to the inventory
    inventory['Status'] = 'Released'

    # Save the inventory transaction
    try:
        save_transaction(inventory)
    except Exception as e:
        logger.error(f"[{order_id}] - error! {str(e)}")
        return {
            'statusCode': 500,
            'body': 'Error saving inventory transaction'
        }

    order['Inventory'] = inventory

    # Testing scenario
    if order_id.startswith('33'):
        return {
            'statusCode': 400,
            'body': 'Unable to release inventory for order ' + order_id
        }

    logger.info(f"[{order_id}] - reservation processed")

    return {
        'statusCode': 200,
        'body': order
    }

def get_transaction(order_id):
    response = table.query(
        KeyConditionExpression="order_id = :v1 AND transaction_type = :v2",
        ExpressionAttributeValues={
            ":v1": order_id,
            ":v2": "Reserve"
        },
        IndexName="orderIDIndex"
    )

    if 'Items' not in response or len(response['Items']) == 0:
        return None, 'Transaction not found'

    return response['Items'][0], None

def save_transaction(inventory):
    response = table.put_item(Item=inventory)
    if response['ResponseMetadata']['HTTPStatusCode'] != 200:
        raise Exception('Failed to put record to DynamoDB')

# For testing locally
if __name__ == '__main__':
    event = {
        'Order': {
            'OrderID': '123',
            'OrderData': 'example data'
        }
    }
    context = None
    response = handler(event, context)
    print(response)
