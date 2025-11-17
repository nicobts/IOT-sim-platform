"""
SIM service for managing SIM cards and synchronization with 1NCE.
"""

from datetime import datetime
from typing import Dict, List, Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.clients.once_client import OnceClient
from app.core.logging import get_logger
from app.models.sim import (
    SIM,
    SIMConnectivity,
    SIMEvent,
    SIMQuota,
    SIMSMS,
    SIMUsage,
)
from app.schemas.sim import SIMCreate, SIMResponse, SIMUpdate
from app.utils.validators import parse_page_params, validate_iccid

logger = get_logger(__name__)


class SIMService:
    """Service for SIM card operations"""

    @staticmethod
    async def get_sim_by_iccid(
        db: AsyncSession, iccid: str
    ) -> Optional[SIM]:
        """
        Get SIM by ICCID.

        Args:
            db: Database session
            iccid: SIM ICCID

        Returns:
            SIM if found, None otherwise
        """
        if not validate_iccid(iccid):
            raise ValueError(f"Invalid ICCID format: {iccid}")

        result = await db.execute(select(SIM).where(SIM.iccid == iccid))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_sims(
        db: AsyncSession,
        page: int = 1,
        page_size: int = 100,
        status: Optional[str] = None,
    ) -> Tuple[List[SIM], int]:
        """
        Get paginated list of SIMs.

        Args:
            db: Database session
            page: Page number (1-indexed)
            page_size: Items per page
            status: Optional status filter

        Returns:
            Tuple of (list of SIMs, total count)
        """
        page, page_size = parse_page_params(page, page_size)

        # Build query
        query = select(SIM)
        if status:
            query = query.where(SIM.status == status)

        query = query.order_by(SIM.created_at.desc())

        # Get total count
        count_query = select(func.count()).select_from(SIM)
        if status:
            count_query = count_query.where(SIM.status == status)

        total = await db.scalar(count_query)

        # Get paginated results
        query = query.limit(page_size).offset((page - 1) * page_size)
        result = await db.execute(query)
        sims = list(result.scalars().all())

        return sims, total or 0

    @staticmethod
    async def create_sim(db: AsyncSession, sim_create: SIMCreate) -> SIM:
        """
        Create a new SIM record.

        Args:
            db: Database session
            sim_create: SIM creation data

        Returns:
            Created SIM

        Raises:
            ValueError: If ICCID already exists
        """
        if not validate_iccid(sim_create.iccid):
            raise ValueError(f"Invalid ICCID format: {sim_create.iccid}")

        # Check if SIM already exists
        existing = await SIMService.get_sim_by_iccid(db, sim_create.iccid)
        if existing:
            raise ValueError(f"SIM with ICCID {sim_create.iccid} already exists")

        # Create SIM
        sim = SIM(
            iccid=sim_create.iccid,
            imsi=sim_create.imsi,
            msisdn=sim_create.msisdn,
            label=sim_create.label,
            organization_id=sim_create.organization_id,
            metadata=sim_create.metadata,
        )

        db.add(sim)
        await db.commit()
        await db.refresh(sim)

        logger.info("sim_created", sim_id=sim.id, iccid=sim.iccid)
        return sim

    @staticmethod
    async def update_sim(
        db: AsyncSession, iccid: str, sim_update: SIMUpdate
    ) -> Optional[SIM]:
        """
        Update SIM information.

        Args:
            db: Database session
            iccid: SIM ICCID
            sim_update: Update data

        Returns:
            Updated SIM if found, None otherwise
        """
        sim = await SIMService.get_sim_by_iccid(db, iccid)
        if not sim:
            return None

        # Update fields
        if sim_update.label is not None:
            sim.label = sim_update.label
        if sim_update.metadata is not None:
            sim.metadata = sim_update.metadata

        await db.commit()
        await db.refresh(sim)

        logger.info("sim_updated", sim_id=sim.id, iccid=sim.iccid)
        return sim

    @staticmethod
    async def sync_sim_from_once(
        db: AsyncSession, once_client: OnceClient, iccid: str
    ) -> Optional[SIM]:
        """
        Sync single SIM from 1NCE API.

        Args:
            db: Database session
            once_client: 1NCE API client
            iccid: SIM ICCID

        Returns:
            Synced SIM if found, None otherwise
        """
        try:
            # Get SIM data from 1NCE
            sim_data = await once_client.get_sim(iccid)

            # Get or create SIM
            sim = await SIMService.get_sim_by_iccid(db, iccid)
            if not sim:
                sim = SIM(iccid=iccid)
                db.add(sim)

            # Update SIM data
            sim.imsi = sim_data.get("imsi")
            sim.msisdn = sim_data.get("msisdn")
            sim.status = sim_data.get("status")
            sim.ip_address = sim_data.get("ip_address")
            sim.imei = sim_data.get("imei")
            sim.last_synced_at = datetime.utcnow()

            await db.commit()
            await db.refresh(sim)

            logger.info("sim_synced_from_once", sim_id=sim.id, iccid=iccid)
            return sim

        except Exception as e:
            logger.error("sim_sync_failed", iccid=iccid, error=str(e))
            return None

    @staticmethod
    async def sync_all_sims_from_once(
        db: AsyncSession, once_client: OnceClient
    ) -> int:
        """
        Sync all SIMs from 1NCE API.

        Args:
            db: Database session
            once_client: 1NCE API client

        Returns:
            Number of SIMs synced
        """
        try:
            # Get all SIMs from 1NCE (paginated)
            page = 1
            synced_count = 0

            while True:
                response = await once_client.get_sims(page=page, page_size=100)
                sims_data = response.get("sims", [])

                if not sims_data:
                    break

                # Sync each SIM
                for sim_data in sims_data:
                    iccid = sim_data.get("iccid")
                    if not iccid:
                        continue

                    sim = await SIMService.get_sim_by_iccid(db, iccid)
                    if not sim:
                        sim = SIM(iccid=iccid)
                        db.add(sim)

                    # Update data
                    sim.imsi = sim_data.get("imsi")
                    sim.msisdn = sim_data.get("msisdn")
                    sim.status = sim_data.get("status")
                    sim.ip_address = sim_data.get("ip_address")
                    sim.imei = sim_data.get("imei")
                    sim.last_synced_at = datetime.utcnow()

                    synced_count += 1

                # Check if there are more pages
                if len(sims_data) < 100:
                    break

                page += 1

            await db.commit()

            logger.info("all_sims_synced", count=synced_count)
            return synced_count

        except Exception as e:
            logger.error("all_sims_sync_failed", error=str(e))
            raise

    @staticmethod
    async def get_sim_usage(
        db: AsyncSession,
        iccid: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[SIMUsage]:
        """
        Get SIM usage data.

        Args:
            db: Database session
            iccid: SIM ICCID
            start_date: Optional start date filter
            end_date: Optional end date filter

        Returns:
            List of usage records
        """
        query = select(SIMUsage).where(SIMUsage.iccid == iccid)

        if start_date:
            query = query.where(SIMUsage.timestamp >= start_date)
        if end_date:
            query = query.where(SIMUsage.timestamp <= end_date)

        query = query.order_by(SIMUsage.timestamp.desc())

        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def sync_sim_usage_from_once(
        db: AsyncSession, once_client: OnceClient, iccid: str
    ) -> List[SIMUsage]:
        """
        Sync SIM usage data from 1NCE.

        Args:
            db: Database session
            once_client: 1NCE API client
            iccid: SIM ICCID

        Returns:
            List of synced usage records
        """
        try:
            # Get usage data from 1NCE
            usage_data = await once_client.get_sim_usage(iccid)

            # Get SIM
            sim = await SIMService.get_sim_by_iccid(db, iccid)
            if not sim:
                logger.warning("sim_not_found_for_usage_sync", iccid=iccid)
                return []

            usage_records = []
            for usage in usage_data.get("usage", []):
                # Create or update usage record
                timestamp = datetime.fromisoformat(usage.get("timestamp"))

                # Check if record exists
                result = await db.execute(
                    select(SIMUsage).where(
                        SIMUsage.iccid == iccid, SIMUsage.timestamp == timestamp
                    )
                )
                usage_record = result.scalar_one_or_none()

                if not usage_record:
                    usage_record = SIMUsage(
                        sim_id=sim.id,
                        iccid=iccid,
                        timestamp=timestamp,
                    )
                    db.add(usage_record)

                # Update data
                usage_record.volume_rx = usage.get("volume_rx", 0)
                usage_record.volume_tx = usage.get("volume_tx", 0)
                usage_record.total_volume = usage.get("total_volume", 0)
                usage_record.sms_mo = usage.get("sms_mo", 0)
                usage_record.sms_mt = usage.get("sms_mt", 0)

                usage_records.append(usage_record)

            await db.commit()

            logger.info(
                "sim_usage_synced", iccid=iccid, records=len(usage_records)
            )
            return usage_records

        except Exception as e:
            logger.error("sim_usage_sync_failed", iccid=iccid, error=str(e))
            return []

    @staticmethod
    async def get_sim_quota(
        db: AsyncSession, iccid: str, quota_type: str
    ) -> Optional[SIMQuota]:
        """
        Get SIM quota (data or SMS).

        Args:
            db: Database session
            iccid: SIM ICCID
            quota_type: 'data' or 'sms'

        Returns:
            Quota if found, None otherwise
        """
        result = await db.execute(
            select(SIMQuota).where(
                SIMQuota.iccid == iccid, SIMQuota.quota_type == quota_type
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def topup_sim_quota(
        db: AsyncSession,
        once_client: OnceClient,
        iccid: str,
        quota_type: str,
        volume: int,
    ) -> bool:
        """
        Top-up SIM quota.

        Args:
            db: Database session
            once_client: 1NCE API client
            iccid: SIM ICCID
            quota_type: 'data' or 'sms'
            volume: Volume to add

        Returns:
            True if successful, False otherwise
        """
        try:
            # Call 1NCE API to top-up
            await once_client.topup_sim(iccid, quota_type, volume)

            # Update quota in database
            quota = await SIMService.get_sim_quota(db, iccid, quota_type)
            if quota:
                quota.last_volume_added = volume
                quota.last_status_change_date = datetime.utcnow()
                await db.commit()

            logger.info(
                "sim_quota_topup",
                iccid=iccid,
                quota_type=quota_type,
                volume=volume,
            )
            return True

        except Exception as e:
            logger.error(
                "sim_quota_topup_failed",
                iccid=iccid,
                quota_type=quota_type,
                error=str(e),
            )
            return False

    @staticmethod
    async def send_sms(
        db: AsyncSession,
        once_client: OnceClient,
        iccid: str,
        message: str,
        destination: Optional[str] = None,
    ) -> bool:
        """
        Send SMS to SIM.

        Args:
            db: Database session
            once_client: 1NCE API client
            iccid: SIM ICCID
            message: SMS message
            destination: Optional destination number

        Returns:
            True if successful, False otherwise
        """
        try:
            # Send SMS via 1NCE API
            result = await once_client.send_sms(iccid, message, destination)

            # Get SIM
            sim = await SIMService.get_sim_by_iccid(db, iccid)
            if sim:
                # Create SMS record
                sms_record = SIMSMS(
                    sim_id=sim.id,
                    iccid=iccid,
                    direction="MT",
                    message=message,
                    destination_address=destination,
                    status="sent",
                    submit_date=datetime.utcnow(),
                )
                db.add(sms_record)
                await db.commit()

            logger.info("sms_sent", iccid=iccid, length=len(message))
            return True

        except Exception as e:
            logger.error("sms_send_failed", iccid=iccid, error=str(e))
            return False
