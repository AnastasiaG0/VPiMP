import asyncio
import logging
from typing import Optional
from contextlib import asynccontextmanager

import aio_pika
from aio_pika import connect_robust, Connection, Channel, Message

from app.core.config import settings

logger = logging.getLogger(__name__)


class RabbitMQConnection:
    """Управляет подключением и каналом RabbitMQ"""
    
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
        """Устанавливает соединение с RabbitMQ"""
        if self.is_connected:
            logger.info("RabbitMQ уже подключен")
            return
        
        try:
            amqp_url = f"amqp://{settings.RABBITMQ_USER}:{settings.RABBITMQ_PASS}@{settings.RABBITMQ_HOST}:{settings.RABBITMQ_PORT}/"
            self._connection = await connect_robust(amqp_url)
            self._channel = await self._connection.channel()
            logger.info(f"[OK] Connected to RabbitMQ at {settings.RABBITMQ_HOST}:{settings.RABBITMQ_PORT}")
        except Exception as e:
            logger.error(f"[ERROR] Failed to connect to RabbitMQ: {e}")
            raise
    
    async def disconnect(self) -> None:
        """Закрывает соединение с RabbitMQ"""
        if self._connection and not self._connection.is_closed:
            await self._connection.close()
            logger.info("[OK] Disconnected from RabbitMQ")
    
    async def get_channel(self) -> Channel:
        """Возвращает канал (ленивая инициализация)"""
        if not self.is_connected:
            await self.connect()
        return self._channel
    
    async def declare_exchanges_and_queues(self) -> None:
        """Объявляет обменники, очереди и привязки"""
        channel = await self.get_channel()
        
        await channel.declare_exchange(
            settings.RMQ_EXCHANGE_EVENTS,
            aio_pika.ExchangeType.DIRECT,
            durable=True
        )
        
        await channel.declare_exchange(
            settings.RMQ_DLX_EXCHANGE,
            aio_pika.ExchangeType.DIRECT,
            durable=True
        )
        
        queue = await channel.declare_queue(
            settings.RMQ_QUEUE_USER_REGISTERED,
            durable=True,
            arguments={
                "x-dead-letter-exchange": settings.RMQ_DLX_EXCHANGE,
                "x-dead-letter-routing-key": settings.RMQ_ROUTING_KEY_USER_REGISTERED
            }
        )
        
        await queue.bind(
            settings.RMQ_EXCHANGE_EVENTS,
            routing_key=settings.RMQ_ROUTING_KEY_USER_REGISTERED
        )
        
        dlq = await channel.declare_queue(
            settings.RMQ_DLQ_USER_REGISTERED,
            durable=True
        )
        
        await dlq.bind(
            settings.RMQ_DLX_EXCHANGE,
            routing_key=settings.RMQ_ROUTING_KEY_USER_REGISTERED
        )
        
        logger.info("[OK] Declared exchanges and queues")