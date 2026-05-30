import asyncio
import json
import logging
from typing import Dict, Any, Optional, Callable, Awaitable
from datetime import datetime

import aio_pika

from app.core.queue.connection import RabbitMQConnection
from app.core.config import settings
from app.services.email_service import EmailService
from app.core.cache import cache_service

logger = logging.getLogger(__name__)


class EventConsumer:
    """Потребляет события из очередей RabbitMQ"""
    
    def __init__(self):
        self._connection = RabbitMQConnection()
        self._email_service = EmailService()
        self._running = False
        self._handlers: Dict[str, Callable] = {}
        
        self._handlers["user.registered"] = self._handle_user_registered
    
    async def start(self) -> None:
        """Запускает потребление сообщений"""
        if self._running:
            logger.warning("Consumer already running")
            return
        
        self._running = True
        
        try:
            await self._connection.declare_exchanges_and_queues()
            
            channel = await self._connection.get_channel()
            
            await channel.set_qos(prefetch_count=1)
            
            queue = await channel.get_queue(settings.RMQ_QUEUE_USER_REGISTERED)
            
            logger.info(f"[QUEUE] '{queue.name}' has {queue.declaration_result.message_count} messages")
            logger.info(f"[QUEUE] Consumers: {queue.declaration_result.consumer_count}")
            
            await queue.consume(self._process_message)
            
            logger.info("[CONSUMER] Event consumer started, waiting for messages...")
            
            while self._running:
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error(f"[ERROR] Consumer error: {e}")
            import traceback
            traceback.print_exc()
            self._running = False
            raise
    
    async def stop(self) -> None:
        """Останавливает потребление"""
        self._running = False
        logger.info("[CONSUMER] Event consumer stopped")
    
    async def _process_message(self, message: aio_pika.IncomingMessage) -> None:
        ##########################################################################################################################
        await asyncio.sleep(120)
        """Обрабатывает входящее сообщение"""
        async with message.process():
            try:
                body = json.loads(message.body.decode())
                event_type = body.get("eventType")
                event_id = body.get("eventId")
                
                logger.info(f"[RECEIVED] Event: {event_type} | id={event_id}")
                
                if await self._is_event_processed(event_id):
                    logger.info(f"[SKIP] Event {event_id} already processed")
                    return
                
                handler = self._handlers.get(event_type)
                if not handler:
                    logger.warning(f"[WARN] No handler for event type: {event_type}")
                    return
                
                success = await self._process_with_retry(handler, body)
                
                if success:
                    await self._mark_event_processed(event_id)
                    logger.info(f"[OK] Event {event_id} processed successfully")
                else:
                    metadata = body.get("metadata", {})
                    attempt = metadata.get("attempt", 1)
                    
                    if attempt >= 3:
                        logger.error(f"[ERROR] Event {event_id} failed after {attempt} attempts, moving to DLQ")
                        await message.nack(requeue=False)
                        return
                    
                    body["metadata"]["attempt"] = attempt + 1
                    body["metadata"]["lastError"] = "Processing failed"
                    
                    logger.warning(f"[RETRY] Retry {attempt + 1}/3 for event {event_id}")
                    
                    await self._republish_with_retry(body, message.routing_key)
                    
            except Exception as e:
                logger.error(f"[ERROR] Error processing message: {e}")
                await message.nack(requeue=False)
    
    async def _process_with_retry(
        self,
        handler: Callable[[Dict[str, Any]], Awaitable[bool]],
        message: Dict[str, Any]
    ) -> bool:
        """Обрабатывает сообщение с логикой повторных попыток"""
        max_retries = 3
        retry_delays = [1, 5, 15]
        
        for attempt in range(max_retries):
            try:
                return await handler(message)
            except Exception as e:
                logger.warning(f"[WARN] Handler attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delays[attempt])
                else:
                    raise
        return False
    
    async def _republish_with_retry(self, message: Dict[str, Any], routing_key: str) -> None:
        """Перепубликовывает сообщение с обновленным счетчиком попыток"""
        try:
            channel = await self._connection.get_channel()
            
            message_body = json.dumps(message, ensure_ascii=False).encode()
            
            rmq_message = aio_pika.Message(
                message_body,
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                content_type="application/json",
                message_id=message["eventId"],
                timestamp=datetime.utcnow()
            )
            
            await channel.default_exchange.publish(
                rmq_message,
                routing_key=routing_key
            )
        except Exception as e:
            logger.error(f"[ERROR] Failed to republish message: {e}")
    
    async def _is_event_processed(self, event_id: str) -> bool:
        """Проверяет, было ли событие уже обработано (идемпотентность)"""
        if not event_id:
            return False
        
        try:
            key = f"processed_event:{event_id}"
            return cache_service.get("events", key) is not None
        except Exception as e:
            logger.warning(f"[WARN] Idempotency check failed: {e}")
            return False
    
    async def _mark_event_processed(self, event_id: str) -> None:
        """Отмечает событие как обработанное"""
        if not event_id:
            return
        
        try:
            key = f"processed_event:{event_id}"
            cache_service.set("events", "true", 86400, key)
        except Exception as e:
            logger.warning(f"[WARN] Failed to mark event as processed: {e}")
    
    async def _handle_user_registered(self, message: Dict[str, Any]) -> bool:
        """Обрабатывает событие user.registered - отправляет приветственное письмо"""
        payload = message.get("payload", {})
        user_id = payload.get("userId")
        email = payload.get("email")
        display_name = payload.get("displayName", "User")
        
        if not email:
            logger.error("[ERROR] No email in user.registered payload")
            return False
        
        logger.info(f"[EMAIL] Sending welcome email to {email}")
        
        try:
            await self._email_service.send_welcome_email(
                to_email=email,
                display_name=display_name,
                user_id=user_id
            )
            logger.info(f"[EMAIL] Welcome email sent to {email}")
            return True
        except Exception as e:
            logger.error(f"[ERROR] Failed to send welcome email: {e}")
            raise