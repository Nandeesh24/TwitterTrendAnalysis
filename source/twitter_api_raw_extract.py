import os
import tweepy
import json
import time
import boto3
from datetime import datetime
from io import StringIO
from botocore.exceptions import ClientError


def get_list_of_locations(api):
    """Get list of locations to be extracted."""
    try:
        s3 = boto3.client('s3')
        response = s3.get_object(Bucket=os.environ['BUCKET_NAME'],
                                 Key=os.environ['LOCATION_CODES_FILE'])
        list_of_locations = json.loads(response['Body'].read().decode('utf-8'))
    except ClientError as client_exp:
        error_code = client_exp.response['Error']['Code']
        print(f"Error! Exception when extracting locations {error_code}")
        list_of_locations = api.trends_available()
        output_str = StringIO()
        output_str.write(json.dumps(list_of_locations))
        s3.put_object(Bucket=os.environ['BUCKET_NAME'],
                      Key=os.environ['LOCATION_CODES_FILE'],
                      Body=output_str.getvalue())

    return list_of_locations


def get_countries(list_of_locations):
    """Get list of countries from the list of locations."""
    list_of_countries = [1]
    for loc_data in list_of_locations:
        name = loc_data.get('name')
        country = loc_data.get('country')
        woeid = loc_data.get('woeid')
        if name == country:
            list_of_countries.append(woeid)
    return list_of_countries


def get_api_keys():
    """Get API Keys from Secrets Manager."""
    secrets_dict = {}
    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(service_name='secretsmanager',
                            region_name=os.environ['REGION_NAME'])
    try:
        api_response = client.get_secret_value(SecretId=os.environ['SECRET_ARN'])
        if 'SecretString' in api_response:
            secrets_dict = json.loads(api_response['SecretString'])

    except ClientError as client_exp:
        err_code = client_exp.response['Error']['Code']
        print(f"Error! Exception when extracting key from API {err_code}")
        raise client_exp
    except KeyError as key_exp:
        print(f"Error! Exception when extracting key {key_exp}")
        raise key_exp
    return secrets_dict


def get_latest_trends(api, countries):
    current_time = datetime.now().strftime("%Y%m%d%H%M%S")
    output_file = ''
    try:
        output_list = []
        for loc_id in countries:
            trends = api.trends_place(loc_id)
            trends.append(loc_id)
            trends.append(current_time)
            output_list.append(trends)

        output_str = StringIO()
        for trend in output_list:
            output_str.write(json.dumps(trend) + "\n")

        s3 = boto3.client('s3')
        output_file = os.path.join(os.environ['RAW_FOLDER'],
                                   current_time[:8], f"trends_{current_time}.json")
        s3.put_object(Bucket=os.environ['BUCKET_NAME'],
                      Key=output_file, Body=output_str.getvalue())
        return output_file
    except tweepy.error.RateLimitError:
        print(f"Error! RateLimitError exception at {current_time}")


def write_to_sqs(message):
    """Write the message to SQS."""
    sqs_client = boto3.client('sqs')
    print(f"Info! Sending filename {message} to SQS")
    sqs_client.send_message(QueueUrl=os.environ['QUEUE_URL'], MessageBody=message)


def lambda_handler(event, context):
    secrets_dict = get_api_keys()
    auth = tweepy.OAuthHandler(secrets_dict['CLIENT_API_KEY'],
                               secrets_dict['CLIENT_API_KEY_SECRET'])
    auth.set_access_token(secrets_dict['ACCESS_TOKEN'],
                          secrets_dict['ACCESS_TOKEN_SECRET'])

    api = tweepy.API(auth)
    list_of_locations = get_list_of_locations(api)
    countries = get_countries(list_of_locations)
    output_file = get_latest_trends(api, countries)
    if output_file:
        write_to_sqs(output_file)
    return {
        'statusCode': 200,
        'body': json.dumps('OK')
    }
