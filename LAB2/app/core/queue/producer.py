import json
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
import logging

import aio_pika

from app.core.queue.connection import RabbitMQConnection
from app.core.config import settings

logger = logging.getLogger(__name__)


class EventProducer:
    """Производит события в RabbitMQ"""
    
    def __init__(self):
        self._connection = RabbitMQConnection()
    
    async def publish(
        self,
        event_type: str,
        payload: Dict[str, Any],
        routing_key: str,
        exchange: str = None,
        event_id: Optional[str] = None
    ) -> bool:
        """Публикует событие в обменник RabbitMQ"""
        exchange_name = exchange or settings.RMQ_EXCHANGE_EVENTS
        
        message_data = {
            "eventId": event_id or str(uuid.uuid4()),
            "eventType": event_type,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "payload": payload,
            "metadata": {
                "attempt": 1,
                "sourceService": "smart-home-api",
                "version": "1.0"
            }
        }
        
        message_body = json.dumps(message_data, ensure_ascii=False).encode()
        
        try:
            channel = await self._connection.get_channel()
            
            message = aio_pika.Message(
                message_body,
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                content_type="application/json",
                message_id=message_data["eventId"],
                timestamp=datetime.utcnow()
            )
            
            exchange_obj = await channel.get_exchange(exchange_name)
            await exchange_obj.publish(
                message,
                routing_key=routing_key
            )
            
            logger.info(f"[PUBLISH] {event_type} | routing_key={routing_key} | event_id={message_data['eventId']}")
            return True
            
        except Exception as e:
            logger.error(f"[ERROR] Failed to publish event: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def publish_user_registered(
        self,
        user_id: str,
        email: str,
        full_name: Optional[str] = None
    ) -> bool:
        """Публикует событие user.registered"""
        payload = {
            "userId": user_id,
            "email": email,
            "displayName": full_name or email.split("@")[0],
            "registeredAt": datetime.utcnow().isoformat() + "Z"
        }
        
        return await self.publish(
            event_type="user.registered",
            payload=payload,
            routing_key=settings.RMQ_ROUTING_KEY_USER_REGISTERED
        )