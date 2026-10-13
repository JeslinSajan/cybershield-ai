"""
AI Security Assistant router — Phase 19 full implementation.

Permission matrix (user-roles.md):
- Administrator, Security Analyst: Full access (get_current_analyst_or_admin)
- Viewer: Explicitly excluded (403 FORBIDDEN)

Endpoints:
- POST /ai/explain-alert: Detailed triage breakdown of an alert
- POST /ai/explain-vulnerability: Remediation and CVSS analysis of a vulnerability
- POST /ai/explain-risk: Quantified factor breakdown of a device's risk score
- POST /ai/chat: Interactive dialogue persisting AIConversation and AIMessages
- GET  /ai/conversations: List user's AI explanation conversations
- GET  /ai/conversations/{id}: Retrieve conversation history
"""

import uuid
from datetime import datetime
from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_analyst_or_admin
from app.models.ai import AIConversation, AIMessage
from app.models.user import User
from app.services.ai_service import ai_engine

router = APIRouter()


# ---------------------------------------------------------------------------
# Pydantic Schemas
# ---------------------------------------------------------------------------

class ExplainAlertRequest(BaseModel):
    alert_id: uuid.UUID = Field(..., description="UUID of the alert to explain")


class ExplainVulnerabilityRequest(BaseModel):
    vulnerability_id: uuid.UUID = Field(..., description="UUID of the vulnerability to explain")


class ExplainRiskRequest(BaseModel):
    device_id: uuid.UUID = Field(..., description="UUID of the device whose risk score should be explained")


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="Question or prompt from security analyst")
    context_type: str = Field(..., description="Type of context: 'alert', 'vulnerability', 'risk', or 'device'")
    context_id: uuid.UUID = Field(..., description="Target entity UUID")


class ExplanationResponse(BaseModel):
    target_id: uuid.UUID
    target_type: str
    explanation: str
    provider: str = Field(default="local_rule_ai", description="Local Security Explanation Engine")


class MessageResponse(BaseModel):
    id: uuid.UUID
    role: str
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ConversationResponse(BaseModel):
    id: uuid.UUID
    subject_type: str
    subject_id: uuid.UUID
    provider_type: str
    created_at: datetime
    updated_at: datetime
    messages: Optional[List[MessageResponse]] = None

    model_config = {"from_attributes": True}


class ChatResponse(BaseModel):
    conversation_id: uuid.UUID
    response: str
    context_type: str
    context_id: uuid.UUID
    provider: str = "local_rule_ai"


# ---------------------------------------------------------------------------
# Endpoints (Admin & Security Analyst ONLY)
# ---------------------------------------------------------------------------

@router.post("/explain-alert", response_model=ExplanationResponse, summary="Explain security alert")
async def explain_alert(
    body: ExplainAlertRequest,
    current_user: Annotated[User, Depends(get_current_analyst_or_admin)],
    db: Annotated[Session, Depends(get_db)],
):
    """Generate detailed SOC explanation and triage playbook for an alert."""
    explanation = ai_engine.explain_alert(
        db=db,
        alert_id=body.alert_id,
        org_id=current_user.organization_id,
    )
    return ExplanationResponse(
        target_id=body.alert_id,
        target_type="alert",
        explanation=explanation,
        provider=ai_engine.PROVIDER_NAME,
    )


@router.post("/explain-vulnerability", response_model=ExplanationResponse, summary="Explain vulnerability")
async def explain_vulnerability(
    body: ExplainVulnerabilityRequest,
    current_user: Annotated[User, Depends(get_current_analyst_or_admin)],
    db: Annotated[Session, Depends(get_db)],
):
    """Generate CVE technical analysis, attack vector notes, and remediation guidance."""
    explanation = ai_engine.explain_vulnerability(
        db=db,
        vuln_id=body.vulnerability_id,
        org_id=current_user.organization_id,
    )
    return ExplanationResponse(
        target_id=body.vulnerability_id,
        target_type="vulnerability",
        explanation=explanation,
        provider=ai_engine.PROVIDER_NAME,
    )


@router.post("/explain-risk", response_model=ExplanationResponse, summary="Explain device risk score")
async def explain_risk(
    body: ExplainRiskRequest,
    current_user: Annotated[User, Depends(get_current_analyst_or_admin)],
    db: Annotated[Session, Depends(get_db)],
):
    """Generate factor-by-factor breakdown and score reduction playbook for a device."""
    explanation = ai_engine.explain_risk_score(
        db=db,
        device_id=body.device_id,
        org_id=current_user.organization_id,
    )
    return ExplanationResponse(
        target_id=body.device_id,
        target_type="device_risk",
        explanation=explanation,
        provider=ai_engine.PROVIDER_NAME,
    )


@router.post("/chat", response_model=ChatResponse, summary="AI Security Assistant Chat")
async def chat(
    body: ChatRequest,
    current_user: Annotated[User, Depends(get_current_analyst_or_admin)],
    db: Annotated[Session, Depends(get_db)],
):
    """
    Interactive dialogue with the Local Security Explanation Engine.
    Maps inquiries to contextual rules and stores conversation history.
    """
    conversation, response_text = ai_engine.chat(
        db=db,
        org_id=current_user.organization_id,
        user_id=current_user.id,
        message=body.message,
        context_type=body.context_type,
        context_id=body.context_id,
    )
    return ChatResponse(
        conversation_id=conversation.id,
        response=response_text,
        context_type=body.context_type,
        context_id=body.context_id,
        provider=ai_engine.PROVIDER_NAME,
    )


@router.get("/conversations", response_model=List[ConversationResponse], summary="List AI conversations")
async def list_conversations(
    current_user: Annotated[User, Depends(get_current_analyst_or_admin)],
    db: Annotated[Session, Depends(get_db)],
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    """List historical AI Assistant conversation threads for the user's organization."""
    convs = (
        db.query(AIConversation)
        .filter(
            AIConversation.organization_id == current_user.organization_id,
            AIConversation.user_id == current_user.id,
        )
        .order_by(AIConversation.updated_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return convs


@router.get("/conversations/{conversation_id}", response_model=ConversationResponse, summary="Get conversation messages")
async def get_conversation(
    conversation_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_analyst_or_admin)],
    db: Annotated[Session, Depends(get_db)],
):
    """Retrieve an AI conversation along with its full transcript messages."""
    conv = (
        db.query(AIConversation)
        .filter(
            AIConversation.id == conversation_id,
            AIConversation.organization_id == current_user.organization_id,
        )
        .first()
    )
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "NOT_FOUND", "message": f"Conversation '{conversation_id}' was not found.", "details": []}},
        )

    messages = (
        db.query(AIMessage)
        .filter(AIMessage.conversation_id == conv.id)
        .order_by(AIMessage.created_at.asc())
        .all()
    )

    result = ConversationResponse(
        id=conv.id,
        subject_type=conv.subject_type,
        subject_id=conv.subject_id,
        provider_type=conv.provider_type,
        created_at=conv.created_at,
        updated_at=conv.updated_at,
        messages=messages,
    )
    return result
