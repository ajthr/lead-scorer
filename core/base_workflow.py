import logging
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Callable
from functools import wraps

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def retry_with_backoff(
    retries: int = 3, 
    backoff_in_seconds: int = 1, 
    exceptions: tuple[type[Exception], ...] = (Exception,)
) -> Callable:
    """
    RFR Level 1: Retry transient failures with exponential backoff.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            x = 0
            while True:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if x == retries:
                        logger.error(f"RFR Level 1 failed for {func.__name__} after {retries} retries.")
                        raise e
                    
                    sleep = (backoff_in_seconds * 2 ** x)
                    logger.warning(
                        f"Retrying {func.__name__} in {sleep}s (Attempt {x+1}/{retries}) due to {str(e)}"
                    )
                    time.sleep(sleep)
                    x += 1
        return wrapper
    return decorator


class BaseWorkflow(ABC):
    """
    Abstract Orchestrator that enforces multi-org context and RFR handlers.
    All pipelines (Ingestion, FE, Training, Inference) must inherit from this.
    """
    
    def __init__(self, org_id: str):
        if not org_id or not isinstance(org_id, str):
            raise ValueError("A valid 'org_id' must be provided to initialize a workflow.")
        
        self.org_id = org_id
        self.logger = logging.getLogger(f"{self.__class__.__name__}[{org_id}]")
        self.logger.info(f"Initialized workflow for Org: {org_id}")

    @abstractmethod
    def execute(self, payload: Dict[str, Any]) -> Any:
        """
        The main execution method for the workflow.
        Must be implemented by child classes.
        """
        pass

    def rfr_level_4_alert(self, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        """
        RFR Level 4: Log critical failure and alert the system dashboard.
        Should never let the main process halt.
        """
        error_context = context or {}
        self.logger.critical(
            f"RFR-L4 ALERT | Org: {self.org_id} | Message: {message} | Context: {error_context}"
        )
        # TODO: Implement push notification to Streamlit/Grafana/Slack here.

    def log_partial_success(self, step_name: str, details: str) -> None:
        """Helper to log intermediate progress for multi-org audibility."""
        self.logger.info(f"Step '{step_name}' completed: {details}")
