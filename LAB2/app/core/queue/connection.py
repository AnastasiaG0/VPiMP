import asyncio
import logging
from typing import Optional
from contextlib import asynccontextmanager

import aio_pika
from aio_pika import connect_robust, Connection, Channel, Message

from app.core.config import settings

logger = logging.getLogger(__name__)


class RabbitMQConnection:
    """Manages RabbitMQ connection and channel"""
    
    _instance: Optional["RabbitMQConnection"] = None
    _connection: Optional[Connection] = None
    _channel: Optional[Channel] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @property
    def is_connected(self) -> bool:
        return self._connection is not None and not self._connection.is_closed
    
    async def connect(self) -> None:
        """Establish connection to RabbitMQ"""
        if self.is_connected:
            logger.info("RabbitMQ already connected")
            return
        
        try:
            amqp_url = f"amqp://{settings.RABBITMQ_USER}:{settings.RABBITMQ_PASS}@{settings.RABBITMQ_HOST}:{settings.RABBITMQ_PORT}/"
            self._connection = await connect_robust(amqp_url)
            self._channel = await self._connection.channel()
            logger.info(f"✅ Connected to RabbitMQ at {settings.RABBITMQ_HOST}:{settings.RABBITMQ_PORT}")
        except Exception as e:
            logger.error(f"❌ Failed to connect to RabbitMQ: {e}")
            raise
    
    async def disconnect(self) -> None:
        """Close RabbitMQ connection"""
        if self._connection and not self._connection.is_closed:
            await self._connection.close()
            logger.info("✅ Disconnected from RabbitMQ")
    
    async def get_channel(self) -> Channel:
        """Get channel (lazy initialization)"""
        if not self.is_connected:
            await self.connect()
        return self._channel
    
    async def declare_exchanges_and_queues(self) -> None:
        """Declare exchanges, queues and bindings"""
        channel = await self.get_channel()
        
        # Declare main exchange
        await channel.declare_exchange(
            settings.RMQ_EXCHANGE_EVENTS,
            aio_pika.ExchangeType.DIRECT,
            durable=True
        )
        
        # Declare Dead Letter Exchange
        await channel.declare_exchange(
            settings.RMQ_DLX_EXCHANGE,
            aio_pika.ExchangeType.DIRECT,
            durable=True
        )
        
        # Declare main queue with DLX configuration
        queue = await channel.declare_queue(
            settings.RMQ_QUEUE_USER_REGISTERED,
            durable=True,
            arguments={
                "x-dead-letter-exchange": settings.RMQ_DLX_EXCHANGE,
                "x-dead-letter-routing-key": settings.RMQ_ROUTING_KEY_USER_REGISTERED,
                "x-max-retries": 3
            }
        )
        
        # Bind queue to exchange
        await queue.bind(
            settings.RMQ_EXCHANGE_EVENTS,
            routing_key=settings.RMQ_ROUTING_KEY_USER_REGISTERED
        )
        
        # Declare Dead Letter Queue
        dlq = await channel.declare_queue(
            settings.RMQ_DLQ_USER_REGISTERED,
            durable=True
        )
        
        # Bind DLQ to DLX
        await dlq.bind(
            settings.RMQ_DLX_EXCHANGE,
            routing_key=settings.RMQ_ROUTING_KEY_USER_REGISTERED
        )
        
        logger.info(f"✅ Declared exchanges and queues")