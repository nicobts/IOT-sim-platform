"""
Unit tests for SIM service.
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.sim import SIM
from app.schemas.sim import SIMCreate, SIMUpdate
from app.services.sim_service import SIMService
from tests.mocks.mock_once_client import MockOnceClient


class TestGetSimByICCID:
    """Tests for get_sim_by_iccid method."""

    @pytest.mark.asyncio
    async def test_get_sim_success(self, db_session: AsyncSession):
        """Test getting SIM by ICCID when it exists."""
        # Create a SIM
        sim = SIM(
            iccid="8991101200003204514",
            imsi="310150123456789",
            msisdn="+1234567890",
            status="active",
        )
        db_session.add(sim)
        await db_session.commit()

        # Get SIM
        result = await SIMService.get_sim_by_iccid(db_session, "8991101200003204514")

        assert result is not None
        assert result.iccid == "8991101200003204514"
        assert result.imsi == "310150123456789"

    @pytest.mark.asyncio
    async def test_get_sim_not_found(self, db_session: AsyncSession):
        """Test getting SIM by ICCID when it doesn't exist."""
        result = await SIMService.get_sim_by_iccid(db_session, "9999999999999999999")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_sim_invalid_iccid(self, db_session: AsyncSession):
        """Test getting SIM with invalid ICCID format."""
        with pytest.raises(ValueError, match="Invalid ICCID format"):
            await SIMService.get_sim_by_iccid(db_session, "invalid")


class TestGetSIMs:
    """Tests for get_sims method."""

    @pytest.mark.asyncio
    async def test_get_sims_empty(self, db_session: AsyncSession):
        """Test getting SIMs when none exist."""
        sims, total = await SIMService.get_sims(db_session)

        assert sims == []
        assert total == 0

    @pytest.mark.asyncio
    async def test_get_sims_with_data(self, db_session: AsyncSession):
        """Test getting SIMs with data."""
        # Create SIMs
        for i in range(5):
            sim = SIM(
                iccid=f"899110120000320451{i}",
                imsi=f"31015012345678{i}",
                status="active",
            )
            db_session.add(sim)
        await db_session.commit()

        # Get SIMs
        sims, total = await SIMService.get_sims(db_session)

        assert len(sims) == 5
        assert total == 5

    @pytest.mark.asyncio
    async def test_get_sims_pagination(self, db_session: AsyncSession):
        """Test SIM pagination."""
        # Create 10 SIMs
        for i in range(10):
            sim = SIM(
                iccid=f"899110120000320451{i}",
                imsi=f"31015012345678{i}",
                status="active",
            )
            db_session.add(sim)
        await db_session.commit()

        # Get first page
        sims_page1, total = await SIMService.get_sims(db_session, page=1, page_size=5)
        assert len(sims_page1) == 5
        assert total == 10

        # Get second page
        sims_page2, total = await SIMService.get_sims(db_session, page=2, page_size=5)
        assert len(sims_page2) == 5
        assert total == 10

        # Verify different SIMs
        page1_iccids = {s.iccid for s in sims_page1}
        page2_iccids = {s.iccid for s in sims_page2}
        assert page1_iccids.isdisjoint(page2_iccids)

    @pytest.mark.asyncio
    async def test_get_sims_filter_by_status(self, db_session: AsyncSession):
        """Test filtering SIMs by status."""
        # Create SIMs with different statuses
        active_sim = SIM(iccid="8991101200003204514", status="active")
        disabled_sim = SIM(iccid="8991101200003204515", status="disabled")
        db_session.add(active_sim)
        db_session.add(disabled_sim)
        await db_session.commit()

        # Get active SIMs
        sims, total = await SIMService.get_sims(db_session, status="active")

        assert len(sims) == 1
        assert total == 1
        assert sims[0].status == "active"


class TestCreateSIM:
    """Tests for create_sim method."""

    @pytest.mark.asyncio
    async def test_create_sim_success(self, db_session: AsyncSession):
        """Test creating a new SIM."""
        sim_create = SIMCreate(
            iccid="8991101200003204514",
            imsi="310150123456789",
            msisdn="+1234567890",
            label="Test SIM",
        )

        sim = await SIMService.create_sim(db_session, sim_create)

        assert sim.id is not None
        assert sim.iccid == "8991101200003204514"
        assert sim.imsi == "310150123456789"
        assert sim.label == "Test SIM"

    @pytest.mark.asyncio
    async def test_create_sim_duplicate_iccid(self, db_session: AsyncSession):
        """Test creating SIM with duplicate ICCID."""
        sim_create = SIMCreate(
            iccid="8991101200003204514",
            imsi="310150123456789",
        )

        # Create first SIM
        await SIMService.create_sim(db_session, sim_create)

        # Try to create duplicate
        with pytest.raises(ValueError, match="already exists"):
            await SIMService.create_sim(db_session, sim_create)

    @pytest.mark.asyncio
    async def test_create_sim_invalid_iccid(self, db_session: AsyncSession):
        """Test creating SIM with invalid ICCID."""
        sim_create = SIMCreate(
            iccid="invalid",
            imsi="310150123456789",
        )

        with pytest.raises(ValueError, match="Invalid ICCID format"):
            await SIMService.create_sim(db_session, sim_create)


class TestUpdateSIM:
    """Tests for update_sim method."""

    @pytest.mark.asyncio
    async def test_update_sim_success(self, db_session: AsyncSession):
        """Test updating SIM."""
        # Create SIM
        sim = SIM(iccid="8991101200003204514", label="Old Label")
        db_session.add(sim)
        await db_session.commit()

        # Update SIM
        sim_update = SIMUpdate(label="New Label")
        updated_sim = await SIMService.update_sim(
            db_session, "8991101200003204514", sim_update
        )

        assert updated_sim is not None
        assert updated_sim.label == "New Label"

    @pytest.mark.asyncio
    async def test_update_sim_not_found(self, db_session: AsyncSession):
        """Test updating non-existent SIM."""
        sim_update = SIMUpdate(label="New Label")
        result = await SIMService.update_sim(
            db_session, "9999999999999999999", sim_update
        )

        assert result is None


class TestSyncSIMFromOnce:
    """Tests for sync_sim_from_once method."""

    @pytest.mark.asyncio
    async def test_sync_new_sim(
        self, db_session: AsyncSession, mock_once_client: MockOnceClient
    ):
        """Test syncing a new SIM from 1NCE."""
        result = await SIMService.sync_sim_from_once(
            db_session, mock_once_client, "8991101200003204514"
        )

        assert result is not None
        assert result.iccid == "8991101200003204514"
        assert result.imsi == "310150123456789"
        assert result.status == "active"

    @pytest.mark.asyncio
    async def test_sync_existing_sim(
        self, db_session: AsyncSession, mock_once_client: MockOnceClient
    ):
        """Test syncing an existing SIM updates data."""
        # Create SIM with old data
        sim = SIM(iccid="8991101200003204514", status="unknown")
        db_session.add(sim)
        await db_session.commit()

        # Sync from 1NCE
        result = await SIMService.sync_sim_from_once(
            db_session, mock_once_client, "8991101200003204514"
        )

        assert result is not None
        assert result.status == "active"  # Updated from mock
        assert result.last_synced_at is not None

    @pytest.mark.asyncio
    async def test_sync_sim_not_found_in_once(
        self, db_session: AsyncSession, mock_once_client: MockOnceClient
    ):
        """Test syncing SIM that doesn't exist in 1NCE."""
        result = await SIMService.sync_sim_from_once(
            db_session, mock_once_client, "9999999999999999999"
        )

        assert result is None


class TestSyncAllSIMsFromOnce:
    """Tests for sync_all_sims_from_once method."""

    @pytest.mark.asyncio
    async def test_sync_all_sims(
        self, db_session: AsyncSession, mock_once_client: MockOnceClient
    ):
        """Test syncing all SIMs from 1NCE."""
        count = await SIMService.sync_all_sims_from_once(db_session, mock_once_client)

        assert count == 2  # Mock client has 2 SIMs

        # Verify SIMs were created
        sims, total = await SIMService.get_sims(db_session)
        assert total == 2


class TestSyncSIMUsageFromOnce:
    """Tests for sync_sim_usage_from_once method."""

    @pytest.mark.asyncio
    async def test_sync_usage_success(
        self, db_session: AsyncSession, mock_once_client: MockOnceClient
    ):
        """Test syncing SIM usage from 1NCE."""
        # Create SIM first
        sim = SIM(iccid="8991101200003204514")
        db_session.add(sim)
        await db_session.commit()

        # Sync usage
        usage_records = await SIMService.sync_sim_usage_from_once(
            db_session, mock_once_client, "8991101200003204514"
        )

        assert len(usage_records) == 1
        assert usage_records[0].iccid == "8991101200003204514"
        assert usage_records[0].volume_rx == 1024000

    @pytest.mark.asyncio
    async def test_sync_usage_sim_not_found(
        self, db_session: AsyncSession, mock_once_client: MockOnceClient
    ):
        """Test syncing usage for non-existent SIM."""
        usage_records = await SIMService.sync_sim_usage_from_once(
            db_session, mock_once_client, "9999999999999999999"
        )

        assert usage_records == []


class TestTopupSIMQuota:
    """Tests for topup_sim_quota method."""

    @pytest.mark.asyncio
    async def test_topup_success(
        self, db_session: AsyncSession, mock_once_client: MockOnceClient
    ):
        """Test topping up SIM quota."""
        result = await SIMService.topup_sim_quota(
            db_session, mock_once_client, "8991101200003204514", "data", 1000000
        )

        assert result is True
        assert len(mock_once_client.topup_history) == 1
        assert mock_once_client.topup_history[0]["volume"] == 1000000


class TestSendSMS:
    """Tests for send_sms method."""

    @pytest.mark.asyncio
    async def test_send_sms_success(
        self, db_session: AsyncSession, mock_once_client: MockOnceClient
    ):
        """Test sending SMS."""
        # Create SIM first
        sim = SIM(iccid="8991101200003204514")
        db_session.add(sim)
        await db_session.commit()

        # Send SMS
        result = await SIMService.send_sms(
            db_session, mock_once_client, "8991101200003204514", "Test message"
        )

        assert result is True
        assert len(mock_once_client.sent_sms) == 1
        assert mock_once_client.sent_sms[0]["message"] == "Test message"
