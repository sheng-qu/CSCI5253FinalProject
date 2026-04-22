"""Pydantic schemas for the REST API contract."""

from pydantic import BaseModel, ConfigDict, Field
from typing import Any, Optional


class TransactionIn(BaseModel):
    """
    Raw transaction payload.
    """
    model_config = ConfigDict(extra="allow")

    # --- required core ---
    TransactionID: int = Field(..., description="Unique transaction identifier")
    TransactionDT: int = Field(..., description="Seconds from reference datetime")
    TransactionAmt: float = Field(..., description="Payment amount in USD")
    ProductCD: str = Field(..., description="Product code")

    # --- commonly present, optional ---
    card1: Optional[int] = None
    card2: Optional[float] = None
    card3: Optional[float] = None
    card4: Optional[str] = None
    card5: Optional[float] = None
    card6: Optional[str] = None
    addr1: Optional[float] = None
    addr2: Optional[float] = None
    P_emaildomain: Optional[str] = None
    R_emaildomain: Optional[str] = None
    D1: Optional[float] = None
    DeviceInfo: Optional[str] = None
    id_31: Optional[str] = None


class ScoreResponse(BaseModel):
    """Returned by POST /score (async mode)."""
    job_id: str
    transaction_id: int
    status: str = "queued"


class SyncScoreResponse(BaseModel):
    """Returned by POST /score/sync."""
    transaction_id: int
    fraud_proba: float
    top_signals: list[dict[str, Any]]


class ResultResponse(BaseModel):
    """Returned by GET /results/{transaction_id}."""
    transaction_id: int
    job_id: str
    created_at: str
    fraud_proba: float
    top_signals: list[dict[str, Any]]
