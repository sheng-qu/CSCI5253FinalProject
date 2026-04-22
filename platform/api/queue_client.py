"""Thin RabbitMQ publisher wrapper.
"""

import json
import os
import threading

import pika

_QUEUE_NAME = os.environ.get("QUEUE_NAME", "fraud_scoring")
_RABBITMQ_URL = os.environ["RABBITMQ_URL"]

_lock = threading.Lock()
_conn: pika.BlockingConnection | None = None
_channel: pika.adapters.blocking_connection.BlockingChannel | None = None


def _connect():
    global _conn, _channel
    _conn = pika.BlockingConnection(pika.URLParameters(_RABBITMQ_URL))
    _channel = _conn.channel()
    _channel.queue_declare(queue=_QUEUE_NAME, durable=True)


def publish(msg: dict) -> None:
    """Publish a JSON-serializable dict onto the queue with persistence."""
    global _conn, _channel
    with _lock:
        if _channel is None or _conn is None or _conn.is_closed:
            _connect()
        assert _channel is not None
        _channel.basic_publish(
            exchange="",
            routing_key=_QUEUE_NAME,
            body=json.dumps(msg, default=str).encode(),
            properties=pika.BasicProperties(delivery_mode=2),
        )
