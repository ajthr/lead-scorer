import pytest
import psycopg2
import boto3
import redis
import requests
import time
from core.config_manager import get_settings
from core.base_workflow import BaseWorkflow, retry_with_backoff

settings = get_settings()

# --- Infrastructure Tests ---

def test_postgres_connectivity():
    """Verify Postgres is reachable and pgvector extension is installed."""
    try:
        conn = psycopg2.connect(settings.DATABASE_URL)
        cur = conn.cursor()
        cur.execute("SELECT 1;")
        cur.execute("SELECT * FROM pg_extension WHERE extname = 'vector';")
        extension = cur.fetchone()
        conn.close()
        assert extension is not None, "pgvector extension not found in Postgres"
    except Exception as e:
        pytest.fail(f"Postgres connectivity failed: {e}")

def test_minio_connectivity():
    """Verify MinIO S3 is reachable and credentials work."""
    try:
        s3 = boto3.client(
            "s3",
            endpoint_url=f"http://{settings.MINIO_ENDPOINT}",
            aws_access_key_id=settings.MINIO_ROOT_USER,
            aws_secret_access_key=settings.MINIO_ROOT_PASSWORD
        )
        s3.list_buckets()
    except Exception as e:
        pytest.fail(f"MinIO connectivity failed: {e}")

def test_redis_connectivity():
    """Verify Redis is reachable."""
    try:
        r = redis.from_url(settings.REDIS_URL)
        assert r.ping() is True
    except Exception as e:
        pytest.fail(f"Redis connectivity failed: {e}")

def test_mlflow_connectivity():
    """Verify MLflow server is reachable and healthy."""
    try:
        response = requests.get(f"{settings.MLFLOW_TRACKING_URI}/health")
        assert response.status_code == 200
    except Exception as e:
        pytest.fail(f"MLflow connectivity failed: {e}")

# --- Workflow Logic Tests ---

class MockWorkflow(BaseWorkflow):
    """Concrete implementation for testing BaseWorkflow logic."""
    def execute(self, payload: dict) -> str:
        return f"Success for {self.org_id}"

    @retry_with_backoff(retries=2, backoff_in_seconds=0.1)
    def failing_method(self):
        raise ValueError("Simulated Transient Failure")

def test_base_workflow_org_isolation():
    """Verify BaseWorkflow enforces org_id context."""
    with pytest.raises(ValueError):
        MockWorkflow(org_id="") # Should fail with empty org_id
    
    wf = MockWorkflow(org_id="org_test_123")
    assert wf.org_id == "org_test_123"
    assert wf.execute({}) == "Success for org_test_123"

def test_rfr_level_1_retry():
    """Verify the RFR Level 1 decorator handles retries correctly."""
    wf = MockWorkflow(org_id="org_retry_test")
    
    start_time = time.time()
    with pytest.raises(ValueError):
        wf.failing_method()
    end_time = time.time()
    
    # We expect 2 retries with 0.1s backoff (0.1 + 0.2 = ~0.3s)
    assert (end_time - start_time) >= 0.3
