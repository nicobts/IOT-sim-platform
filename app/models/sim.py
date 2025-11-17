"""
SIM card and related database models.
Includes usage, connectivity, events, quotas, SMS, orders, and products.
"""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import INET, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class SIM(Base, TimestampMixin):
    """
    SIM card master data.
    Stores information about each SIM card managed by the system.
    """

    __tablename__ = "sims"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    iccid: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    imsi: Mapped[Optional[str]] = mapped_column(String(15), index=True)
    msisdn: Mapped[Optional[str]] = mapped_column(String(15), index=True)
    status: Mapped[Optional[str]] = mapped_column(String(20), index=True)
    label: Mapped[Optional[str]] = mapped_column(String(255))
    ip_address: Mapped[Optional[str]] = mapped_column(INET)
    imei: Mapped[Optional[str]] = mapped_column(String(15))
    organization_id: Mapped[Optional[int]] = mapped_column(Integer)
    last_synced_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    metadata: Mapped[Optional[dict]] = mapped_column(JSONB)

    # Relationships
    usage_records: Mapped[List["SIMUsage"]] = relationship(
        "SIMUsage", back_populates="sim", cascade="all, delete-orphan"
    )
    connectivity_records: Mapped[List["SIMConnectivity"]] = relationship(
        "SIMConnectivity", back_populates="sim", cascade="all, delete-orphan"
    )
    events: Mapped[List["SIMEvent"]] = relationship(
        "SIMEvent", back_populates="sim", cascade="all, delete-orphan"
    )
    quotas: Mapped[List["SIMQuota"]] = relationship(
        "SIMQuota", back_populates="sim", cascade="all, delete-orphan"
    )
    sms_messages: Mapped[List["SIMSMS"]] = relationship(
        "SIMSMS", back_populates="sim", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<SIM(id={self.id}, iccid='{self.iccid}', status='{self.status}')>"


class SIMUsage(Base, TimestampMixin):
    """
    SIM usage data - TimescaleDB hypertable for time-series data.
    Tracks data usage over time for each SIM.
    """

    __tablename__ = "sim_usage"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    sim_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("sims.id", ondelete="CASCADE"), nullable=False, index=True
    )
    iccid: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    volume_rx: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    volume_tx: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    total_volume: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    sms_mo: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    sms_mt: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Relationships
    sim: Mapped["SIM"] = relationship("SIM", back_populates="usage_records")

    def __repr__(self) -> str:
        return f"<SIMUsage(id={self.id}, iccid='{self.iccid}', timestamp='{self.timestamp}')>"


class SIMConnectivity(Base, TimestampMixin):
    """
    SIM connectivity information - TimescaleDB hypertable.
    Tracks connection status and network information.
    """

    __tablename__ = "sim_connectivity"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    sim_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("sims.id", ondelete="CASCADE"), nullable=False, index=True
    )
    iccid: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    connected: Mapped[Optional[bool]] = mapped_column(Boolean)
    cell_id: Mapped[Optional[str]] = mapped_column(String(50))
    signal_strength: Mapped[Optional[int]] = mapped_column(Integer)
    rat: Mapped[Optional[str]] = mapped_column(String(10))  # Radio Access Technology
    country_code: Mapped[Optional[str]] = mapped_column(String(3))
    operator_name: Mapped[Optional[str]] = mapped_column(String(100))

    # Relationships
    sim: Mapped["SIM"] = relationship("SIM", back_populates="connectivity_records")

    def __repr__(self) -> str:
        return f"<SIMConnectivity(id={self.id}, iccid='{self.iccid}', connected={self.connected})>"


class SIMEvent(Base, TimestampMixin):
    """
    SIM events - TimescaleDB hypertable.
    Logs all events related to SIM cards.
    """

    __tablename__ = "sim_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    sim_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("sims.id", ondelete="CASCADE"), nullable=False, index=True
    )
    iccid: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    event_data: Mapped[Optional[dict]] = mapped_column(JSONB)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)

    # Relationships
    sim: Mapped["SIM"] = relationship("SIM", back_populates="events")

    def __repr__(self) -> str:
        return f"<SIMEvent(id={self.id}, iccid='{self.iccid}', event_type='{self.event_type}')>"


class SIMQuota(Base, TimestampMixin):
    """
    SIM quotas (data and SMS).
    Tracks quota information and thresholds.
    """

    __tablename__ = "sim_quotas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    sim_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("sims.id", ondelete="CASCADE"), nullable=False, index=True
    )
    iccid: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    quota_type: Mapped[str] = mapped_column(String(10), nullable=False)  # 'data' or 'sms'
    volume: Mapped[Optional[int]] = mapped_column(BigInteger)
    last_volume_added: Mapped[Optional[int]] = mapped_column(BigInteger)
    last_status_change_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    status: Mapped[Optional[str]] = mapped_column(String(20))
    threshold_percentage: Mapped[Optional[int]] = mapped_column(Integer)
    threshold_volume: Mapped[Optional[int]] = mapped_column(BigInteger)
    auto_reload: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    sim: Mapped["SIM"] = relationship("SIM", back_populates="quotas")

    def __repr__(self) -> str:
        return f"<SIMQuota(id={self.id}, iccid='{self.iccid}', type='{self.quota_type}')>"


class SIMSMS(Base, TimestampMixin):
    """
    SIM SMS messages.
    Stores sent and received SMS messages.
    """

    __tablename__ = "sim_sms"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    sim_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("sims.id", ondelete="CASCADE"), nullable=False, index=True
    )
    iccid: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    direction: Mapped[str] = mapped_column(String(10), nullable=False)  # 'MO' or 'MT'
    message: Mapped[str] = mapped_column(Text, nullable=False)
    source_address: Mapped[Optional[str]] = mapped_column(String(20))
    destination_address: Mapped[Optional[str]] = mapped_column(String(20))
    status: Mapped[Optional[str]] = mapped_column(String(20))
    submit_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    delivery_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Relationships
    sim: Mapped["SIM"] = relationship("SIM", back_populates="sms_messages")

    def __repr__(self) -> str:
        return f"<SIMSMS(id={self.id}, iccid='{self.iccid}', direction='{self.direction}')>"


class Order(Base, TimestampMixin):
    """
    Orders for SIM cards and products.
    """

    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    order_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    customer_id: Mapped[Optional[int]] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    total_amount: Mapped[Optional[float]] = mapped_column(Float)
    currency: Mapped[Optional[str]] = mapped_column(String(3))
    order_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    delivery_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    metadata: Mapped[Optional[dict]] = mapped_column(JSONB)

    # Relationships
    items: Mapped[List["OrderItem"]] = relationship(
        "OrderItem", back_populates="order", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Order(id={self.id}, order_number='{self.order_number}', status='{self.status}')>"


class OrderItem(Base, TimestampMixin):
    """
    Line items within an order.
    """

    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    order_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True
    )
    product_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("products.id", ondelete="SET NULL")
    )
    product_name: Mapped[str] = mapped_column(String(255), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[Optional[float]] = mapped_column(Float)
    total_price: Mapped[Optional[float]] = mapped_column(Float)

    # Relationships
    order: Mapped["Order"] = relationship("Order", back_populates="items")
    product: Mapped[Optional["Product"]] = relationship("Product")

    def __repr__(self) -> str:
        return f"<OrderItem(id={self.id}, product='{self.product_name}', quantity={self.quantity})>"


class Product(Base, TimestampMixin):
    """
    Product catalog.
    """

    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    product_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    category: Mapped[Optional[str]] = mapped_column(String(50))
    price: Mapped[Optional[float]] = mapped_column(Float)
    currency: Mapped[Optional[str]] = mapped_column(String(3))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    metadata: Mapped[Optional[dict]] = mapped_column(JSONB)

    def __repr__(self) -> str:
        return f"<Product(id={self.id}, code='{self.product_code}', name='{self.name}')>"


class SupportTicket(Base, TimestampMixin):
    """
    Support tickets.
    """

    __tablename__ = "support_tickets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    ticket_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    priority: Mapped[Optional[str]] = mapped_column(String(20))
    category: Mapped[Optional[str]] = mapped_column(String(50))
    user_id: Mapped[Optional[int]] = mapped_column(Integer)
    assigned_to: Mapped[Optional[int]] = mapped_column(Integer)
    resolution: Mapped[Optional[str]] = mapped_column(Text)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    def __repr__(self) -> str:
        return f"<SupportTicket(id={self.id}, ticket='{self.ticket_number}', status='{self.status}')>"
