def upload_to_s3(file_path, s3_key):
    """
    Uploads a file to the specified S3 bucket and ensures the folder exists.
    """
    try:
        logger.info(f"Uploading {file_path} to S3 with key {s3_key}")

        
        folder_prefix = "/".join(s3_key.split("/")[:-1])  # Extract only the folder path
        
        if not folder_prefix.endswith("/"):
            folder_prefix += "/"

        
        placeholder = f"{folder_prefix}placeholder.txt"
        
        
        try:
            s3_client.head_object(Bucket=S3_BUCKET_NAME, Key=placeholder)
            logger.info(f"Folder {folder_prefix} already exists.")
        except:
            logger.info(f"Creating folder {folder_prefix} in S3 by adding placeholder.txt.")
            s3_client.put_object(Bucket=S3_BUCKET_NAME, Key=placeholder, Body="Placeholder file to create folder.")

        
        s3_client.upload_file(file_path, S3_BUCKET_NAME, s3_key)
        logger.info(f"Uploaded {file_path} to S3 bucket {S3_BUCKET_NAME} with key {s3_key}")

    except Exception as e:
        logger.error(f"Error uploading to S3: {e}")
