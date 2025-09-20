# shared/utils.py

import os
from google.cloud import secretmanager, firestore, aiplatform

# Load configuration from environment or defaults
GCP_PROJECT = os.environ.get("GCP_PROJECT", "aspira")
REGION = os.environ.get("REGION", "asia-south1")


def get_secret(secret_id: str) -> str:
    """
    Fetch the latest version of a secret from Secret Manager.
    Args:
        secret_id: The name of the secret in GCP Secret Manager.
    Returns:
        The decoded secret payload as a string.
    """
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{GCP_PROJECT}/secrets/{secret_id}/versions/latest"
    response = client.access_secret_version(name=name)
    return response.payload.data.decode("utf-8")


def init_firestore():
    """
    Initialize and return a Firestore client for the project.
    """
    return firestore.Client(project=GCP_PROJECT)


def init_vertex():
    """
    Initialize Vertex AI with the project and region.
    Returns the aiplatform module for further use.
    """
    aiplatform.init(project=GCP_PROJECT, location=REGION)
    return aiplatform
