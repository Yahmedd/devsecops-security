"""Application configuration settings."""
import json
import os

import boto3


class Config:
    """Base configuration."""

    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:////app/instance/cybertek.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = None

    DEBUG = False
    TESTING = False
    HOST = "0.0.0.0"
    PORT = 8000

    @staticmethod
    def get_secret_key():
        """Load the Flask secret from the environment or AWS Secrets Manager."""
        env_secret = os.getenv("SECRET_KEY")
        if env_secret:
            return env_secret

        secret_id = os.getenv("AWS_SECRET_ID", "flask/session-key")
        region = os.getenv("AWS_REGION", "us-west-2")

        try:
            client = boto3.client("secretsmanager", region_name=region)
            response = client.get_secret_value(SecretId=secret_id)
            secret_json = json.loads(response["SecretString"])
            return secret_json["flask_session_key"]
        except Exception as exc:
            raise RuntimeError(
                "No Flask SECRET_KEY configured. Set SECRET_KEY or configure AWS Secrets Manager."
            ) from exc


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False


class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SECRET_KEY = "test-only-secret-key"


config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig,
}
