import asyncio
import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
import sys

from loguru import logger
from livef1.adapters import RealF1Client
from broker import KafkaMessageProducer

class F1DataCollector:
    def __init__(self, topics: Optional[List[str]] = None):
        logger.info("Initializing F1DataCollector")
        
        # Get default topic configurations
        default_topic_configs = self._get_default_topics()
        self.topic_key_mapping = {config["topic"]: config for config in default_topic_configs}
        
        # Use default topics if none provided
        if topics is None:
            logger.debug("No topics provided, using default topics")
            topics = [config["topic"] for config in default_topic_configs]
        else:
            logger.debug(f"Using provided topics: {topics}")
        
        # Initialize client with topics to subscribe
        logger.info(f"Initializing RealF1Client with {len(topics)} topics")
        self.client = RealF1Client(
            topics=topics,
            log_file_name='./sample_data/telemetry.json'
        )

        # Initialize Kafka producer
        logger.info("Initializing Kafka producer")
        self.kafka_producer = KafkaMessageProducer()
        
        # Register callback for incoming data
        @self.client.callback("telemetry_handler")
        async def handle_data(records: Dict[str, List[Dict[str, Any]]]) -> None:
            """Process incoming F1 data records.
            
            According to the documentation, records are organized by topic.
            """
            total_records = sum(len(topic_records) for topic_records in records.values())
            
            # Process each topic's records
            for topic, topic_records in records.items():
                logger.debug(f"Processing {len(topic_records)} records for topic: {topic}")
                
                for record in topic_records:
                    try:                        
                        # Send to Kafka with the F1 topic as the Kafka topic
                        kafka_topic = f"f1-{topic.split('.')[0].lower() if '.' in topic else topic.lower()}"
                        
                        # Generate a key based on the topic configuration
                        key = self._generate_key_for_topic(topic, record)
                        
                        # Send to Kafka
                        self.kafka_producer.send_message_with_key(
                            topic=kafka_topic,
                            message=record,
                            key=key
                        )
                    except Exception as e:
                        logger.error(f"Error processing record: {e}")
                        logger.debug(f"Problematic record: {str(record)[:200]}")
    
    def _generate_key_for_topic(self, topic: str, payload: Dict[str, Any]) -> str:
        """Generate an appropriate key for the Kafka message based on the topic configuration."""
        # Get topic configuration
        topic_config = self.topic_key_mapping.get(topic)
        
        # If we don't have a configuration for this topic, use a default approach
        if not topic_config:
            topic_key = topic.split('.')[0].lower() if '.' in topic else topic.lower()
            return f"f1-{topic_key}"
        
        # If the configuration has a static key, use it
        if "key" in topic_config:
            return topic_config["key"]
        
        # If the configuration specifies a key field, extract it from the payload
        if "key_field" in topic_config:
            # Handle string payloads
            if isinstance(payload, str):
                return topic_config.get("fallback", "generic")
            
            # Extract the key field from the payload
            key_value = payload.get(topic_config["key_field"])
            if key_value:
                return str(key_value)
            
            # Use fallback if key field not found
            return topic_config.get("fallback", "unknown")
        
        # Default fallback
        return f"f1-{topic.lower()}"
    
    def _get_default_topics(self) -> List[Dict[str, str]]:
        """Return a comprehensive list of default topics with their corresponding key strategies."""
        return [
            # Core telemetry and position data
            {"topic": "CarData.z", "key_field": "DriverNo", "fallback": "car-unknown"},  # Car telemetry data
            {"topic": "Position.z", "key_field": "DriverNo", "fallback": "car-unknown"},  # Position data
            
            # Timing information
            {"topic": "TimingData.z", "key_field": "DriverNo", "fallback": "driver-unknown"},  # General timing data
            {"topic": "TimingDataF1", "key_field": "DriverNo", "fallback": "driver-unknown"},  # F1-specific timing
            {"topic": "TimingStats", "key_field": "DriverNo", "fallback": "driver-unknown"},  # Statistical timing
            {"topic": "TimingAppData", "key_field": "DriverNo", "fallback": "driver-unknown"},  # Timing app data
            
            # Session information
            {"topic": "SessionInfo", "key": "session-info"},  # Session details
            {"topic": "SessionStatus", "key": "session-status"},  # Current session status
            {"topic": "TrackStatus", "key": "track-status"},  # Current track status
            {"topic": "ExtrapolatedClock", "key": "session-clock"},  # Session clock information
            
            # Weather and conditions
            {"topic": "WeatherData", "key": "weather-current"},  # Current weather conditions
            {"topic": "WeatherDataSeries", "key": "weather-series"},  # Weather data over time
            
            # Driver and team information
            {"topic": "DriverList", "key_field": "DriverNo", "fallback": "driver-unknown"},  # List of drivers
            {"topic": "TeamRadio", "key_field": "DriverNo", "fallback": "team-radio"},  # Team radio communications
            {"topic": "RaceControlMessages", "key": "race-control"},  # Messages from race control
            
            # Tire and pit information
            {"topic": "TyreStintSeries", "key_field": "DriverNo", "fallback": "tyre-stint"},  # Tire stint data
            {"topic": "CurrentTyres", "key_field": "DriverNo", "fallback": "current-tyres"},  # Current tire compounds
            {"topic": "PitStopSeries", "key_field": "DriverNo", "fallback": "pit-stop"},  # Pit stop data
            {"topic": "PitLaneTimeCollection", "key_field": "DriverNo", "fallback": "pit-lane"},  # Pit lane timing
            
            # Race analysis
            {"topic": "LapSeries", "key_field": "DriverNo", "fallback": "lap-series"},  # Lap time data
            {"topic": "LapCount", "key": "lap-count"},  # Lap counting
            {"topic": "OvertakeSeries", "key_field": "DriverNo", "fallback": "overtake"},  # Overtake information
        ]
    
    async def run(self) -> None:
        """Start collecting F1 data asynchronously."""
        logger.info(f"Subscribed to {len(self.client.topics)} topics")
        try:
            logger.info("Starting F1 client")
            # According to the documentation, we can just call run() directly
            # The client handles the connection and data streaming
            await asyncio.to_thread(self.client.run)
        except Exception as e:
            logger.error(f"Error in F1 client: {e}")
        finally:
            # Ensure Kafka producer is closed properly
            logger.info("Closing Kafka producer")
            self.kafka_producer.close()

if __name__ == "__main__":
    logger.info("F1 Live Timing application starting")
    collector = F1DataCollector()
    
    # Create and run the event loop
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(collector.run())
    except KeyboardInterrupt:
        logger.info("Application stopped by user")
    finally:
        loop.close()
