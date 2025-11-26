"""
Factor evaluation platform utilities.

This package hosts the lightweight factor registry, job planner, and the API
layer used by ``starquant_factor_pipeline``.  Keeping the code in a dedicated
module allows reuse from both the Airflow DAG and standalone CLIs / services.
"""

from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent

__all__ = ["WORKSPACE_ROOT"]
