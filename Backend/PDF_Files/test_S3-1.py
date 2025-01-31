import boto3
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def upload_to_s3(file_path: str, s3_key: str):
    # Initialize the S3 client using environment variables
    s3 = boto3.client(
        's3',
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
        region_name=os.getenv('AWS_REGION')
    )
    
    try:
        # Upload the file to S3
        s3.upload_file(
            Filename=file_path,
            Bucket=os.getenv('S3_BUCKET_NAME'),
            Key=s3_key
        )
        s3_url = f"s3://{os.getenv('S3_BUCKET_NAME')}/{s3_key}"
        return s3_url
    except Exception as e:
        raise Exception(f"Error uploading file to S3: {e}")

# Example usage
if __name__ == "__main__":
    file_path = "path/to/your/file.txt"
    s3_key = "your/s3/key/file.txt"
    s3_url = upload_to_s3(file_path, s3_key)
    print(f"File uploaded to: {s3_url}")
