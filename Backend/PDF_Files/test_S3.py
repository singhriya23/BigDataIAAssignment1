def upload_to_s3(file_path, s3_key):
    """
    Uploads a file to the specified S3 bucket and ensures the folder exists.
    """
    try:
        logger.info(f"Uploading {file_path} to S3 with key {s3_key}")

        # ✅ Extract folder path from s3_key
        folder_prefix = "/".join(s3_key.split("/")[:-1])  # Extract only the folder path
        
        if not folder_prefix.endswith("/"):
            folder_prefix += "/"

        # ✅ Ensure the folder exists by uploading a placeholder file
        placeholder_key = f"{folder_prefix}placeholder.txt"
        
        # ✅ Upload a placeholder file if the folder is new
        try:
            s3_client.head_object(Bucket=S3_BUCKET_NAME, Key=placeholder_key)
            logger.info(f"Folder {folder_prefix} already exists.")
        except:
            logger.info(f"Creating folder {folder_prefix} in S3 by adding placeholder.txt.")
            s3_client.put_object(Bucket=S3_BUCKET_NAME, Key=placeholder_key, Body="Placeholder file to create folder.")

        # ✅ Upload the actual file
        s3_client.upload_file(file_path, S3_BUCKET_NAME, s3_key)
        logger.info(f"Uploaded {file_path} to S3 bucket {S3_BUCKET_NAME} with key {s3_key}")

    except Exception as e:
        logger.error(f"Error uploading to S3: {e}")
