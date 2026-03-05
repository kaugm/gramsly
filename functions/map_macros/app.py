import os
import json
import boto3
from botocore.exceptions import ClientError
from decimal import Decimal

# Instantiate AWS Resources
s3 = boto3.client("s3")
dynamodb = boto3.resource('dynamodb')

# Read in Environment Variables
BUCKET = os.environ['BUCKET']
Table = dynamodb.Table(os.environ["TABLE_NAME"])

# Cache for JSON Object pulled from S3
_cached_data = None


def get_data_object_from_s3():
    '''
    Caches object from S3.
    '''
    global _cached_data

    if _cached_data is None:
        # Get food macro data
        try:
            # print("[1] Getting JSON object from S3..")
            response_s3 = s3.get_object(Bucket=BUCKET, Key="food-data.json")
            content = response_s3["Body"].read().decode("utf-8")
            # data = json.loads(content)
            _cached_data = json.loads(content)
            # print(f"[2] Success! Object found: {data}")

        except Exception as e:
            print(f"S3 get_object() error: {e}")
            raise

    return _cached_data

def log(id, timestamp, amount):
    '''
    Add an item to DynamoDB.
    
    :param id: Day in format YYYYMMDD
    :param timestamp: Unix Timestamp to avoid collisions
    :param amount: Amount consumed in grams
    '''
    try:
        Table.put_item(Item={
            'id':    id,               # Partition Key - Day in format YYYYMMDD
            'timestamp':  timestamp,   # Sort Key - Unix Timestamp
            'amount': amount,
        })
    except ClientError as e:
        print(f"DynamoDB put_item() error: {e}")
        raise # Log as Error in CloudWatch Logs

def update(id, timestamp, cost, fiber, fat, carbohydrates, protein, ingredient, date_time):
    '''
    Added attributes to item in DynamoDB. Attributes are enriched data created from macro calculations.
    
    :param id: Day in format YYYYMMDD
    :param timestamp: Unix Timestamp to avoid collisions
    :param cost: Cost per amount consumed
    :param fiber: Fiber per amount consumed
    :param fat: Fat per amount consumed
    :param carbohydrates: Carbohydrates per amount consumed
    :param protein: Protein per amount consumed
    :param ingredient: Human readable name for ingredient
    :param date_time: Human readable date_time
    '''
    try:
        Table.update_item(
            Key={
                'id': id,                       # Hash key
                'timestamp': timestamp,         # Sort key
            },
            UpdateExpression='SET cost = :cost, fiber = :fiber, fat = :fat, protein = :protein, carbohydrates = :carbohydrates, ingredient = :ingredient, date_time = :date_time',
            ExpressionAttributeValues={
                ':cost': str(round(cost, 2)),
                ':fiber': str(round(fiber, 2)),
                ':fat': str(round(fat, 2)),
                ':protein': str(round(protein, 2)),
                ':carbohydrates': str(round(carbohydrates, 2)),
                ':ingredient': ingredient,
                ':date_time': date_time
            }
        )
    except ClientError as e:
        print(f"DynamoDB update_item() error: {e}")
        raise # Log as Error in CloudWatch Logs


def lambda_handler(event, context):
    # Get S3 Object
    get_data_object_from_s3()

    # Read Event Data
    try:
        body = json.loads(event.get('body', '{}'))
    except json.JSONDecodeError:
        return {'statusCode': 400, 'body': json.dumps({'message': 'Invalid JSON body'})}
    
    # Parse Body
    id = body.get('DAY')
    ingredient = body.get('INGREDIENT')
    amount = Decimal(body.get('AMOUNT'))

    if not all([id, ingredient, amount]):
        return {'statusCode': 400, 'body': json.dumps({'message': 'Missing required fields: DAY, INGREDIENT, AMOUNT'})}
    
    # Parse Event Context
    timestamp = event['requestContext']['requestTimeEpoch']
    date_time = event['requestContext']['requestTime']
    
    # 1. Put (Add) Item to DynamoDB
    log(
        id,
        timestamp,
        Decimal(str(amount))
    )

    # 2. Calculate Macros
    data = _cached_data # Pull from cache

    # Use serving_size instead of '100', as some ingredients have a unit size of 1 (Eggs), not 100g
    serving_size = data[ingredient]["unit_size"]
    ratio = amount / Decimal(str(serving_size))

    try:
        data[ingredient]["friendly_name"]
    except KeyError:
        return {
            "statusCode": 200,
            "body": json.dumps({"message": f"Error: {data[ingredient]} not found in database!"})
        }

    #3. Update item in DynamoDB
    update(
        id,
        timestamp,
        Decimal(str(data[ingredient]["cost"])) * ratio,
        Decimal(str(data[ingredient]["fiber"])) * ratio,
        Decimal(str(data[ingredient]["fats"])) * ratio,
        Decimal(str(data[ingredient]["carbs"])) * ratio,
        Decimal(str(data[ingredient]["protein"])) * ratio,
        data[ingredient]["friendly_name"],
        date_time
    )
    print(f"{data[ingredient]["friendly_name"]} logged!")
    return {
        "statusCode": 200,
        "body": json.dumps({"message": f"Error: {data[ingredient]} logged!"})
    }

