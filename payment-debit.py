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

    logger.info(f"[{order_id}] - processing payment")

    payment = {
        'OrderID': order_id,
        'MerchantID': 'merch1',
        'PaymentAmount': order['Total'](),
        'Status': 'Paid'
    }

    # Save payment
    try:
        save_payment(payment)
    except Exception as e:
        logger.error(f"[{order_id}] - error! {str(e)}")
        return {
            'statusCode': 500,
            'body': 'Error saving payment'
        }

    # Save state
    order['Payment'] = payment

    # Testing scenario
    if order_id.startswith('2'):
        return {
            'statusCode': 400,
            'body': 'Unable to process payment for order ' + order_id
        }

    logger.info(f"[{order_id}] - payment processed")

    return {
        'statusCode': 200,
        'body': order
    }

def save_payment(payment):
    response = table.put_item(Item=payment)
    if response['ResponseMetadata']['HTTPStatusCode'] != 200:
        raise Exception('Failed to put record to DynamoDB')

# For testing locally
if __name__ == '__main__':
    event = {
        'Order': {
            'OrderID': '123',
            'OrderData': 'example data',
            'Total': lambda: 100.0
        }
    }
    context = None
    response = handler(event, context)
    print(response)
