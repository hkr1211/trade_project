"""
自定义存储后端配置
用于在 Vercel serverless 环境中处理文件上传
"""
from storages.backends.s3boto3 import S3Boto3Storage


class MediaStorage(S3Boto3Storage):
    """
    用于用户上传的媒体文件（询单附件、订单附件等）
    """
    location = 'media'
    file_overwrite = False
    default_acl = 'private'
