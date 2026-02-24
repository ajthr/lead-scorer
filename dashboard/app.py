import streamlit as st
import pandas as pd
import psycopg2
import boto3
import redis
import requests
from core.config_manager import get_settings

# Page Configuration
st.set_page_config(
    page_title="ALS | Management Dashboard",
    page_icon="shield",
    layout="wide"
)

settings = get_settings()

# --- Health Check Logic ---
def check_postgres():
    try:
        conn = psycopg2.connect(settings.DATABASE_URL)
        conn.close()
        return True, "Connected"
    except Exception as e:
        return False, str(e)

def check_minio():
    try:
        s3 = boto3.client(
            "s3",
            endpoint_url=f"http://{settings.MINIO_ENDPOINT}",
            aws_access_key_id=settings.MINIO_ROOT_USER,
            aws_secret_access_key=settings.MINIO_ROOT_PASSWORD
        )
        s3.list_buckets()
        return True, "Connected"
    except Exception as e:
        return False, str(e)

def check_redis():
    try:
        r = redis.from_url(settings.REDIS_URL)
        r.ping()
        return True, "Connected"
    except Exception as e:
        return False, str(e)

def check_mlflow():
    try:
        # Note: MLflow tracking URI doesn't always have a simple /health
        # We'll just try to reach the root
        response = requests.get(settings.MLFLOW_TRACKING_URI, timeout=5)
        if response.status_code == 200:
            return True, "Connected"
        return False, f"Status: {response.status_code}"
    except Exception as e:
        return False, str(e)

def check_loki():
    try:
        loki_url = f"http://{'loki' if settings.DOCKER_MODE else 'localhost'}:3100/ready"
        response = requests.get(loki_url, timeout=5)
        if response.status_code == 200:
            return True, "Connected"
        return False, f"Status: {response.status_code}"
    except Exception as e:
        return False, str(e)

def check_prometheus():
    try:
        prom_url = f"http://{'prometheus' if settings.DOCKER_MODE else 'localhost'}:9090/-/ready"
        response = requests.get(prom_url, timeout=5)
        if response.status_code == 200:
            return True, "Connected"
        return False, f"Status: {response.status_code}"
    except Exception as e:
        return False, str(e)

# --- UI Layout ---
st.title("Lead Scorer Management Dashboard")

# Tabs for different views
tab1, tab2 = st.tabs(["System Health", "Development Status"])

with tab1:
    st.markdown("### Infrastructure Pulse")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        status, msg = check_postgres()
        st.metric("PostgreSQL (pgvector)", "Online" if status else "Offline", delta=msg if not status else None, delta_color="inverse")

    with col2:
        status, msg = check_minio()
        st.metric("MinIO (S3)", "Online" if status else "Offline", delta=msg if not status else None, delta_color="inverse")

    with col3:
        status, msg = check_redis()
        st.metric("Redis (Celery)", "Online" if status else "Offline", delta=msg if not status else None, delta_color="inverse")

    with col4:
        status, msg = check_mlflow()
        st.metric("MLflow Registry", "Online" if status else "Offline", delta=msg if not status else None, delta_color="inverse")

    col5, col6, col7, col8 = st.columns(4)
    with col5:
        status, msg = check_loki()
        st.metric("Loki (Logs)", "Online" if status else "Offline", delta=msg if not status else None, delta_color="inverse")
    
    with col6:
        status, msg = check_prometheus()
        st.metric("Prometheus (Metrics)", "Online" if status else "Offline", delta=msg if not status else None, delta_color="inverse")

    st.divider()
    st.subheader("Org Registry and Pipeline Status")
    st.info("No organizations registered yet. Connect a Salesforce Org to begin.")

with tab2:
    st.markdown("### Development Insights (Read-Only)")
    
    col_dev1, col_dev2 = st.columns([2, 1])
    
    with col_dev1:
        st.write("**Active Phase:** Phase 1 - Infrastructure and Foundation")
        st.write("**Current Sprint:** Sprint 1 - The Foundation (Baseline)")
        st.write("**Sprint Goal:** Establish multi-tenant core and RFR logic.")
        
        st.markdown("""
        #### Current Focus:
        - [x] ALS-S1-T1: Dockerized Infrastructure Scaffolding
        - [x] ALS-S1-T2: Core Orchestrator and Config Manager
        - [x] ALS-S1-T3: System Management Dashboard v1
        """)
        
    with col_dev2:
        st.info("External Resources")
        st.link_button("Master Backlog Board", "https://github.com/users/ajthr/projects/PVT_kwHOAcU2mM4BQZdR")
        st.link_button("Current Sprint Board", "https://github.com/users/ajthr/projects/PVT_kwHOAcU2mM4BQZdS")
        st.link_button("Architecture Plan", "https://github.com/ajthr/lead-scorer/blob/main/docs/architecture_plan.md")

    st.divider()
    st.markdown("#### Development Analysis")
    st.write("""
    The system is currently in the **Post-Infrastructure Baseline** state. 
    The core RFR (Recursive Fallback and Recovery) handler is active at Level 1 
    (Retries). Multi-org isolation is enforced at the BaseWorkflow level.
    """)

# Sidebar for controls
with st.sidebar:
    st.header("Admin Controls")
    if st.button("Refresh Dashboard"):
        st.rerun()
    
    st.divider()
    st.write(f"**Environment:** {settings.ENVIRONMENT}")
    st.write(f"**Log Level:** {settings.LOG_LEVEL}")
    st.write(f"**Docker Mode:** {'Enabled' if settings.DOCKER_MODE else 'Disabled'}")
