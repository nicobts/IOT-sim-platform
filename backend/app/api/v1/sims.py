"""
SIM Management API endpoints.
Handles SIM CRUD operations, usage tracking, quota management, and SMS.
"""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_active_user, get_once_client_dep
from app.clients.once_client import OnceClient
from app.core.logging import get_logger
from app.db.session import get_db
from app.models.user import User
from app.schemas.sim import (
    QuotaResponse,
    SIMCreate,
    SIMListResponse,
    SIMResponse,
    SIMUpdate,
    SMSResponse,
    SMSSendRequest,
    TopUpRequest,
    UsageResponse,
)
from app.services.sim_service import SIMService

logger = get_logger(__name__)

router = APIRouter()


@router.get("", response_model=SIMListResponse, summary="List all SIMs")
async def list_sims(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(100, ge=1, le=1000, description="Items per page"),
    status: Optional[str] = Query(None, description="Filter by status"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get paginated list of SIM cards.

    - **page**: Page number (1-indexed)
    - **page_size**: Items per page (1-1000)
    - **status**: Optional status filter

    Returns paginated list of SIMs with total count.
    """
    sims, total = await SIMService.get_sims(db, page, page_size, status)

    total_pages = (total + page_size - 1) // page_size

    return SIMListResponse(
        items=[SIMResponse.model_validate(sim) for sim in sims],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.post(
    "",
    response_model=SIMResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create SIM",
)
async def create_sim(
    sim_create: SIMCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Create a new SIM record.

    - **iccid**: SIM ICCID (19-20 digits, required)
    - **imsi**: IMSI (14-15 digits, optional)
    - **msisdn**: Phone number (optional)
    - **label**: Custom label (optional)

    Returns created SIM.
    """
    try:
        sim = await SIMService.create_sim(db, sim_create)
        return SIMResponse.model_validate(sim)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/{iccid}", response_model=SIMResponse, summary="Get SIM by ICCID")
async def get_sim(
    iccid: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get SIM card details by ICCID.

    - **iccid**: SIM ICCID

    Returns SIM details.
    """
    sim = await SIMService.get_sim_by_iccid(db, iccid)

    if not sim:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"SIM with ICCID {iccid} not found",
        )

    return SIMResponse.model_validate(sim)


@router.patch("/{iccid}", response_model=SIMResponse, summary="Update SIM")
async def update_sim(
    iccid: str,
    sim_update: SIMUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Update SIM information.

    - **iccid**: SIM ICCID
    - **label**: New label (optional)
    - **metadata**: New metadata (optional)

    Returns updated SIM.
    """
    sim = await SIMService.update_sim(db, iccid, sim_update)

    if not sim:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"SIM with ICCID {iccid} not found",
        )

    return SIMResponse.model_validate(sim)


@router.post(
    "/{iccid}/sync",
    response_model=SIMResponse,
    summary="Sync SIM from 1NCE",
)
async def sync_sim(
    iccid: str,
    db: AsyncSession = Depends(get_db),
    once_client: OnceClient = Depends(get_once_client_dep),
    current_user: User = Depends(get_current_active_user),
):
    """
    Synchronize SIM data from 1NCE API.

    - **iccid**: SIM ICCID

    Fetches latest data from 1NCE and updates local database.
    Returns updated SIM.
    """
    sim = await SIMService.sync_sim_from_once(db, once_client, iccid)

    if not sim:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"SIM with ICCID {iccid} not found in 1NCE",
        )

    return SIMResponse.model_validate(sim)


@router.post("/sync-all", summary="Sync all SIMs from 1NCE")
async def sync_all_sims(
    db: AsyncSession = Depends(get_db),
    once_client: OnceClient = Depends(get_once_client_dep),
    current_user: User = Depends(get_current_active_user),
):
    """
    Synchronize all SIMs from 1NCE API.

    Fetches all SIMs from 1NCE and updates/creates records in local database.
    This may take a while for large numbers of SIMs.

    Returns count of synced SIMs.
    """
    try:
        count = await SIMService.sync_all_sims_from_once(db, once_client)
        return {"synced_count": count, "message": f"Successfully synced {count} SIMs"}
    except Exception as e:
        logger.error("sync_all_sims_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to sync SIMs from 1NCE",
        )


@router.get(
    "/{iccid}/usage",
    response_model=List[UsageResponse],
    summary="Get SIM usage data",
)
async def get_sim_usage(
    iccid: str,
    start_date: Optional[datetime] = Query(None, description="Start date"),
    end_date: Optional[datetime] = Query(None, description="End date"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get SIM usage data with optional date filtering.

    - **iccid**: SIM ICCID
    - **start_date**: Optional start date (ISO format)
    - **end_date**: Optional end date (ISO format)

    Returns list of usage records.
    """
    usage_records = await SIMService.get_sim_usage(db, iccid, start_date, end_date)

    return [UsageResponse.model_validate(record) for record in usage_records]


@router.post(
    "/{iccid}/usage/sync",
    response_model=List[UsageResponse],
    summary="Sync SIM usage from 1NCE",
)
async def sync_sim_usage(
    iccid: str,
    db: AsyncSession = Depends(get_db),
    once_client: OnceClient = Depends(get_once_client_dep),
    current_user: User = Depends(get_current_active_user),
):
    """
    Synchronize SIM usage data from 1NCE API.

    - **iccid**: SIM ICCID

    Fetches usage data from 1NCE and updates local database.
    Returns synced usage records.
    """
    usage_records = await SIMService.sync_sim_usage_from_once(db, once_client, iccid)

    return [UsageResponse.model_validate(record) for record in usage_records]


@router.get(
    "/{iccid}/quota/{quota_type}",
    response_model=QuotaResponse,
    summary="Get SIM quota",
)
async def get_sim_quota(
    iccid: str,
    quota_type: str = Query(..., pattern="^(data|sms)$", description="Quota type"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get SIM quota information (data or SMS).

    - **iccid**: SIM ICCID
    - **quota_type**: 'data' or 'sms'

    Returns quota details.
    """
    quota = await SIMService.get_sim_quota(db, iccid, quota_type)

    if not quota:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Quota not found for SIM {iccid}",
        )

    return QuotaResponse.model_validate(quota)


@router.post("/{iccid}/topup", summary="Top-up SIM quota")
async def topup_sim(
    iccid: str,
    topup_request: TopUpRequest,
    db: AsyncSession = Depends(get_db),
    once_client: OnceClient = Depends(get_once_client_dep),
    current_user: User = Depends(get_current_active_user),
):
    """
    Top-up SIM quota (data or SMS).

    - **iccid**: SIM ICCID
    - **quota_type**: 'data' or 'sms'
    - **volume**: Volume to add

    Returns success message.
    """
    success = await SIMService.topup_sim_quota(
        db,
        once_client,
        iccid,
        topup_request.quota_type,
        topup_request.volume,
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to top-up quota",
        )

    return {
        "message": f"Successfully topped up {topup_request.volume} {topup_request.quota_type} for SIM {iccid}"
    }


@router.post("/{iccid}/sms", summary="Send SMS")
async def send_sms(
    iccid: str,
    sms_request: SMSSendRequest,
    db: AsyncSession = Depends(get_db),
    once_client: OnceClient = Depends(get_once_client_dep),
    current_user: User = Depends(get_current_active_user),
):
    """
    Send SMS to SIM.

    - **iccid**: SIM ICCID
    - **message**: SMS message (max 160 characters)
    - **destination_address**: Optional destination number

    Returns success message.
    """
    success = await SIMService.send_sms(
        db,
        once_client,
        iccid,
        sms_request.message,
        sms_request.destination_address,
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send SMS",
        )

    return {"message": f"SMS sent successfully to SIM {iccid}"}


@router.get("/{iccid}/connectivity", summary="Get SIM connectivity status")
async def get_sim_connectivity(
    iccid: str,
    once_client: OnceClient = Depends(get_once_client_dep),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get SIM connectivity status from 1NCE.

    - **iccid**: SIM ICCID

    Returns current connectivity information.
    """
    try:
        connectivity = await once_client.get_sim_connectivity(iccid)
        return connectivity
    except Exception as e:
        logger.error("get_connectivity_failed", iccid=iccid, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get connectivity status",
        )


@router.post("/{iccid}/connectivity/reset", summary="Reset SIM connectivity")
async def reset_sim_connectivity(
    iccid: str,
    once_client: OnceClient = Depends(get_once_client_dep),
    current_user: User = Depends(get_current_active_user),
):
    """
    Reset SIM connectivity.

    - **iccid**: SIM ICCID

    Resets the SIM's connectivity via 1NCE API.
    Returns success message.
    """
    try:
        await once_client.reset_sim_connectivity(iccid)
        return {"message": f"Connectivity reset successful for SIM {iccid}"}
    except Exception as e:
        logger.error("reset_connectivity_failed", iccid=iccid, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset connectivity",
        )


@router.get("/{iccid}/events", summary="Get SIM events")
async def get_sim_events(
    iccid: str,
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    once_client: OnceClient = Depends(get_once_client_dep),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get SIM events from 1NCE.

    - **iccid**: SIM ICCID
    - **event_type**: Optional event type filter

    Returns list of events.
    """
    try:
        events = await once_client.get_sim_events(iccid, event_type)
        return events
    except Exception as e:
        logger.error("get_events_failed", iccid=iccid, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get events",
        )
