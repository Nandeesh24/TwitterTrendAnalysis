import os
import csv
import json
import boto3
from datetime import datetime
from io import StringIO
from collections import namedtuple

OUTPUT_FIELD_NAMES = ['DATETIME', 'LOCATION', 'TREND_NAME', 'TREND_NUMBER', 'TWEET_VOLUME']
CSV_EXT = ".csv"

def write_out(s3_client, file_name, output_list):
    """write out the transformed data."""
    output_str = StringIO()
    writer = csv.DictWriter(output_str, fieldnames=OUTPUT_FIELD_NAMES)
    for output in output_list:
        writer.writerow(output)
    base_name = os.path.splitext(os.path.basename(file_name))[0]
    file_dt = file_name.split("/")[-2]
    output_file = os.path.join(os.environ['TRANSFORM_FOLDER'], file_dt, base_name + CSV_EXT)
    print(f"Writing file {output_file} to S3")
    s3_client.put_object(Bucket=os.environ['BUCKET_NAME'],
                         Key=output_file, Body=output_str.getvalue())


def process_data(data):
    """Process file data."""
    output_list = []
    for inp_data in data.split("\n"):
        if not inp_data:
            continue
        trend_data = dict(DateTime='', Location='', TrendName='', TrendNum='', TrendVolume='')
        json_doc = json.loads(inp_data)
        curr_trends = json_doc[0].get('trends')
        tr_loc = json_doc[0].get('locations')[0].get('name')
        tr_dt = datetime.strptime(json_doc[2], "%Y%m%d%H%M%S").strftime("%Y-%m-%dT%H:%M:%SZ")
        trend_pos = 1
        for json_dict in curr_trends:
            trend_data = dict(DATETIME='', LOCATION='', TREND_NAME='', TREND_NUMBER='', TWEET_VOLUME='')
            trend_data['LOCATION'] = tr_loc
            trend_data['DATETIME'] = tr_dt
            trend_data['TREND_NAME'] = json_dict.get('name').lstrip("#")
            trend_data['TREND_NUMBER'] = trend_pos
            trend_data['TWEET_VOLUME'] = json_dict.get('tweet_volume')
            trend_data['TWEET_VOLUME'] = trend_data['TWEET_VOLUME'] if trend_data['TWEET_VOLUME'] else 20000
            trend_pos += 1
            output_list.append(trend_data)

    return output_list


def lambda_handler(event, context):
    """main function to analyze the trends"""
    s3_client = boto3.client('s3')
    for record in event.get('Records'):
        file_name = record['body']
        print(f"Processing raw file {file_name}")
        response = s3_client.get_object(Bucket=os.environ['BUCKET_NAME'], Key=file_name)
        data = response['Body'].read().decode('utf-8')
        output_list = process_data(data)
        write_out(s3_client, file_name, output_list)

    return {
        'statusCode': 200,
        'body': json.dumps('OK')
    }
