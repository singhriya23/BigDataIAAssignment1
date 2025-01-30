import boto3

def upload_to_s3(file_path: str, s3_key: str):
    # Initialize the S3 client
    s3 = boto3.client('s3', region_name='us-east-2')
    
    try:
        # Upload the file to S3
        s3.upload_file(Filename=file_path, Bucket='document-parsed-files', Key=s3_key)
        s3_url = f"s3://document-parsed-files/{s3_key}"
        return s3_url
    except Exception as e:
        raise Exception(f"Error uploading file to S3: {e}")
