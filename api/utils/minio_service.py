from datetime import timedelta
import json
from minio import Minio
from minio.error import S3Error

from api.utils.settings import settings


class MinioService:

    def __init__(self):
        self.minio_client = Minio(
            endpoint='91.229.239.118:9000',
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=False
        )

    
    def __make_public(self, bucket_name: str):
        """This function makes a bucket public"""

        policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"AWS": ["*"]},
                    "Action": ["s3:GetObject"],
                    "Resource": [f"arn:aws:s3:::{bucket_name}/*"]
                }
            ]
        }
        
        # Set bucket policy
        self.minio_client.set_bucket_policy(bucket_name, json.dumps(policy))

    
    def upload_to_minio(self, bucket_name: str, source_file: str, destination_file: str, content_type: str):
        """This function saves a file to a minio bucket

        Args:
            bucket_name (str): Name of the bucket to save the file to
            source_file (str): File path to the file to be save to minio bucket
            destination_file (str): Path to where the file should be saved in minio bucket
        """

        try:
            if not self.minio_client.bucket_exists(bucket_name):
                self.minio_client.make_bucket(bucket_name)
            
            self.__make_public(bucket_name)

            # Upload file
            self.minio_client.fput_object(
                bucket_name=bucket_name,
                object_name=destination_file,
                file_path=source_file,
                content_type=content_type
            )

            preview_url = self.minio_client.presigned_get_object(
                bucket_name=bucket_name,
                object_name=destination_file,
            ).split('?')[0]

            download_url = self.download_from_minio(bucket_name, destination_file)

            return preview_url, download_url

        except S3Error as s3_error:
            print(f'An error occured: {s3_error}')
    

    def download_from_minio(self, bucket_name: str, destination_file: str):
        """This function gets an object from minio and downloads it

        Args:
            bucket_name (str): Name of bucket to get the object from
            source_file (str): _description_
            destination_file (str): _description_
        """

        try:
            if not self.minio_client.bucket_exists(bucket_name):
                self.minio_client.make_bucket(bucket_name)
            
            self.__make_public(bucket_name)

            # Upload file
            url = self.minio_client.presigned_get_object(
                bucket_name=bucket_name,
                object_name=destination_file,
            ).split('?')[0]

            return url

        except S3Error as s3_error:
            print(f'An error occured: {s3_error}')


minio_service = MinioService()