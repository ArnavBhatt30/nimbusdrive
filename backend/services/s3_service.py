import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv
import os

load_dotenv()

s3_client = boto3.client(
    's3',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    region_name=os.getenv('AWS_REGION')
)

BUCKET_NAME = os.getenv('S3_BUCKET_NAME')

def upload_file(file_bytes, filename, content_type):
    try:
        s3_client.put_object(
            Bucket=BUCKET_NAME, Key=filename,
            Body=file_bytes, ContentType=content_type
        )
        return {"success": True, "filename": filename}
    except ClientError as e:
        return {"success": False, "error": str(e)}

def list_files(prefix: str = ""):
    try:
        kwargs = {"Bucket": BUCKET_NAME}
        if prefix:
            kwargs["Prefix"] = prefix
        response = s3_client.list_objects_v2(**kwargs)
        files = []
        if 'Contents' in response:
            for obj in response['Contents']:
                # Skip folder entries
                if obj['Key'].endswith('/'):
                    continue
                files.append({
                    "filename": obj['Key'],
                    "size": obj['Size'],
                    "last_modified": str(obj['LastModified'])
                })
        return {"success": True, "files": files}
    except ClientError as e:
        return {"success": False, "error": str(e)}

def delete_file(filename):
    try:
        s3_client.delete_object(Bucket=BUCKET_NAME, Key=filename)
        return {"success": True, "filename": filename}
    except ClientError as e:
        return {"success": False, "error": str(e)}

def get_download_url(filename):
    try:
        url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': BUCKET_NAME, 'Key': filename},
            ExpiresIn=3600
        )
        return {"success": True, "url": url}
    except ClientError as e:
        return {"success": False, "error": str(e)}
