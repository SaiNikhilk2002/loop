from dotenv import load_dotenv
from os import getenv
from pymongo import MongoClient
import boto3

load_dotenv()
s3_client = boto3.client("s3",aws_access_key_id=getenv("AWS_ACCESS_KEY"), 
                      aws_secret_access_key=getenv("AWS_SECRET_ACCESS_KEY"), 
                      region_name=getenv("region_name"))
bucket_name = getenv("S3_BUCKET_NAME")
client = MongoClient(getenv("MONGO_URI"))
database=getenv("DATABASE")
db_client = client[database]
