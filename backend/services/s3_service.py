"""
S3 Service

Handle file uploads and downloads to/from AWS S3.
"""

import boto3
from botocore.exceptions import ClientError
from typing import Optional
import uuid
from datetime import datetime

from config.settings import settings


class S3Service:
    """AWS S3 service for file management"""

    def __init__(self):
        """Initialize S3 client"""
        self.s3_client = boto3.client(
            's3',
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID if settings.AWS_ACCESS_KEY_ID else None,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY if settings.AWS_SECRET_ACCESS_KEY else None
        )
        self.bucket = settings.S3_BUCKET

    def generate_presigned_upload_url(
        self,
        file_key: str,
        content_type: str = "image/jpeg",
        expires_in: int = 900
    ) -> Optional[str]:
        """
        Generate presigned URL for uploading files to S3

        Args:
            file_key: S3 object key (path)
            content_type: MIME type of the file
            expires_in: URL expiration time in seconds (default 15 min)

        Returns:
            Presigned URL string or None if error
        """
        try:
            presigned_url = self.s3_client.generate_presigned_url(
                'put_object',
                Params={
                    'Bucket': self.bucket,
                    'Key': file_key,
                    'ContentType': content_type
                },
                ExpiresIn=expires_in
            )
            return presigned_url
        except ClientError as e:
            print(f"Error generating presigned URL: {e}")
            return None

    def generate_presigned_download_url(
        self,
        file_key: str,
        expires_in: int = 3600
    ) -> Optional[str]:
        """
        Generate presigned URL for downloading files from S3

        Args:
            file_key: S3 object key (path)
            expires_in: URL expiration time in seconds (default 1 hour)

        Returns:
            Presigned URL string or None if error
        """
        try:
            presigned_url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket,
                    'Key': file_key
                },
                ExpiresIn=expires_in
            )
            return presigned_url
        except ClientError as e:
            print(f"Error generating presigned download URL: {e}")
            return None

    def generate_answer_sheet_key(
        self,
        exam_instance_id: str,
        question_id: str,
        page_number: int,
        file_extension: str = "jpg"
    ) -> str:
        """
        Generate S3 key for answer sheet upload

        Format: answer-sheets/{exam_id}/{question_id}/page_{page_num}_{uuid}.{ext}

        Args:
            exam_instance_id: Exam instance UUID
            question_id: Question UUID
            page_number: Page number of the answer
            file_extension: File extension (jpg, png, pdf)

        Returns:
            S3 object key string
        """
        unique_id = str(uuid.uuid4())[:8]
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")

        return f"{settings.S3_ANSWER_SHEETS_PREFIX}{exam_instance_id}/{question_id}/page_{page_number}_{timestamp}_{unique_id}.{file_extension}"

    def generate_question_image_key(
        self,
        question_id: str,
        file_extension: str = "jpg"
    ) -> str:
        """
        Generate S3 key for question image

        Format: question-images/{question_id}_{uuid}.{ext}

        Args:
            question_id: Question UUID
            file_extension: File extension

        Returns:
            S3 object key string
        """
        unique_id = str(uuid.uuid4())[:8]
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")

        return f"{settings.S3_QUESTION_IMAGES_PREFIX}{question_id}_{timestamp}_{unique_id}.{file_extension}"

    def delete_file(self, file_key: str) -> bool:
        """
        Delete a file from S3

        Args:
            file_key: S3 object key

        Returns:
            True if successful, False otherwise
        """
        try:
            self.s3_client.delete_object(Bucket=self.bucket, Key=file_key)
            return True
        except ClientError as e:
            print(f"Error deleting file: {e}")
            return False

    def file_exists(self, file_key: str) -> bool:
        """
        Check if a file exists in S3

        Args:
            file_key: S3 object key

        Returns:
            True if exists, False otherwise
        """
        try:
            self.s3_client.head_object(Bucket=self.bucket, Key=file_key)
            return True
        except ClientError:
            return False


# Global S3 service instance
s3_service = S3Service()
