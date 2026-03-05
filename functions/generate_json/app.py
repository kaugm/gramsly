'''
Every time an item is added of modified in DynamoDB, scan the table and create a JSON file that is stored in S3. Another Lambda function will reference this file in order to calculate daily macros.
'''

import boto3
import json
import os

TABLE = os.environ['FOOD_DATA_TABLE_NAME']
BUCKET = os.environ['FOOD_DATA_BUCKET']

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE)

s3 = boto3.client("s3")


def lambda_handler(event, context):

    # Get all items from DynamoDB
    items = []
    response = table.scan()

    items.extend(response.get("Items", []))

    while "LastEvaluatedKey" in response:
        response = table.scan(
            ExclusiveStartKey=response["LastEvaluatedKey"]
        )
        items.extend(response.get("Items", []))

    print(f"[1] Found {len(items)} items!")
    for i,j in enumerate(items, start=2):
        print(f"[{i}] {j}")

    # Create JSON object
    data = {item["id"]: item for item in items}
    json_blob = json.dumps(data, default=str, indent=2)

    print(f"[N] {json_blob}")

    # Save to S3
    s3.put_object(
        Bucket=BUCKET,
        Key="food-data.json",
        Body=json_blob,
        ContentType="application/json"
    )
    print("Saved to S3!")

    return {
        "statusCode": 200,
        "body": f"GENERATED JSON: \n{json_blob}"
    }
