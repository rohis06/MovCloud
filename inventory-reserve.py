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

    logger.info(f"[{order_id}] - processing inventory reservation")

    new_inv_trans = {
        'OrderID': order_id,
        'OrderItems': order['ItemIds'](),
        'Status': 'Reserved'
    }

    # Save the reservation
    try:
        save_inventory(new_inv_trans)
    except Exception as e:
        logger.error(f"[{order_id}] - error! {str(e)}")
        return {
            'statusCode': 500,
            'body': 'Error saving inventory reservation'
        }

    # Annotate saga with inventory transaction id
    order['Inventory'] = new_inv_trans

    # Testing scenario
    if order_id.startswith('3'):
        return {
            'statusCode': 400,
            'body': 'Unable to update newInvTrans for order ' + order_id
        }

    logger.info(f"[{order_id}] - reservation processed")

    return {
        'statusCode': 200,
        'body': order
    }

def save_inventory(new_inv_trans):
    response = table.put_item(Item=new_inv_trans)
    if response['ResponseMetadata']['HTTPStatusCode'] != 200:
        raise Exception('Failed to put record to DynamoDB')

# For testing locally
if __name__ == '__main__':
    event = {
        'Order': {
            'OrderID': '123',
            'OrderData': 'example data',
            'ItemIds': lambda: ['item1', 'item2']
        }
    }
    context = None
    response = handler(event, context)
    print(response)
