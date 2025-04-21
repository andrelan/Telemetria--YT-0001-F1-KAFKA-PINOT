from typing import Any
from kafka import KafkaProducer
from loguru import logger
import json
import logging


class KafkaMessageProducer:
    """A class to handle Kafka message production for F1 realtime data."""
    
    def __init__(self, bootstrap_servers: list[str] = ['localhost:29092']) -> None:
        """Initialize the Kafka producer with the given bootstrap servers."""
        self.bootstrap_servers = bootstrap_servers
        self.topic_name = 'f1-realtime-data'
        self.producer = self._create_producer()

    def _create_producer(self) -> KafkaProducer:
        """Create and return a Kafka producer instance."""
        logger.info("Creating Kafka producer...")
        try:
            producer = KafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8')
            )
            logger.info("Kafka producer created successfully")
            return producer
        except Exception as e:
            logger.error(f"Failed to create Kafka producer: {e}")
            raise

    def send_message(self, message: Any) -> None:
        """Send a message to the F1 realtime data Kafka topic."""
        try:
            logger.debug(f"Sending message to topic '{self.topic_name}': {message}")
            future = self.producer.send(self.topic_name, message)
            future.get(timeout=10)  # Wait for message to be sent
            logger.info(f"Message sent successfully to topic '{self.topic_name}'")
        except Exception as e:
            logger.error(f"Error sending message to Kafka: {e}")
            raise

    def send_message_with_key(self, topic: str, message: Any, key: str) -> None:
        """Send a message to a specific Kafka topic with a key."""
        try:
            # Convert key to bytes
            key_bytes = key.encode('utf-8') if key else None
            future = self.producer.send(topic, key=key_bytes, value=message)
            future.get(timeout=10)
            logger.debug(f"Message sent successfully to topic '{topic}' with key '{key}'")
        except Exception as e:
            logger.error(f"Error sending message to Kafka: {e}")
            raise

    def close(self) -> None:
        """Close the Kafka producer connection."""
        self.producer.close()
        logger.info("Kafka producer closed")

def main():    
    try:
        producer = KafkaMessageProducer()
        # Example message
        message = {"event": "race_start", "timestamp": "2024-03-20T10:00:00Z"}
        producer.send_message(message)
    except Exception as e:
        logger.error(f"Main execution failed: {e}")
        raise
    finally:
        producer.close()

if __name__ == "__main__":
    main()
