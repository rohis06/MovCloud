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

    logger.info(f"[{order_id}] - processing refund")

    # Find payment transaction for this order
    try:
        payment = get_transaction(order_id)
    except Exception as e:
        logger.error(f"[{order_id}] - error! {str(e)}")
        return {
            'statusCode': 500,
            'body': 'Error processing refund'
        }

    # Process the refund for the order
    payment['Status'] = 'Refunded'

    # Write to database
    try:
        save_transaction(payment)
    except Exception as e:
        logger.error(f"[{order_id}] - error! {str(e)}")
        return {
            'statusCode': 500,
            'body': 'Error saving payment transaction'
        }

    # Save state
    order['Payment'] = payment

    # Testing scenario
    if order_id.startswith('22'):
        return {
            'statusCode': 400,
            'body': 'Unable to process refund for order ' + order_id
        }

    logger.info(f"[{order_id}] - refund processed")

    return {
        'statusCode': 200,
        'body': order
    }

def get_transaction(order_id):
    response = table.query(
        KeyConditionExpression="order_id = :v1 AND payment_type = :v2",
        ExpressionAttributeValues={
            ":v1": order_id,
            ":v2": "Debit"
        },
        IndexName="orderIDIndex"
    )

    if 'Items' not in response or len(response['Items']) == 0:
        raise Exception('Payment transaction not found in DynamoDB')

    return response['Items'][0]

def save_transaction(payment):
    response = table.put_item(Item=payment)
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
