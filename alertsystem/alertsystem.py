from confluent_kafka import Consumer, Producer
import json
from datetime import datetime
import mysql.connector
from CQRS import QueryHandler,CommandHandler

CQRS_port='mysql'
# Kafka configuration for consumer and producer
consumer_config = {
#    'bootstrap.servers': 'localhost:19092,localhost:29092,localhost:39092',  # List of Kafka brokers
    'bootstrap.servers': 'kafka:9092',  # List of Kafka brokers
    'group.id': 'receivestock-consumer-group',  # Consumer group ID
    'auto.offset.reset': 'earliest',  # Start reading from the earliest offset if no committed offset is available
    'enable.auto.commit': False  # Enable automatic offset commits
#    'enable.auto.commit': True,  # Enable automatic offset commits
#    'auto.commit.interval.ms': 5000  # Commit offsets every 5000ms (5 seconds)
}

#producer_config = {
#    'bootstrap.servers': 'localhost:19092,localhost:29092,localhost:39092',  # List of Kafka brokers
#    'acks': 'all',  # Ensure all in-sync replicas acknowledge the message
#    'max.in.flight.requests.per.connection': 1,  # Ensure ordering of messages
#    'batch.size': 500,  # Maximum size of a batch in bytes
#    'retries': 3  # Number of retries for failed messages
#}
#producer_config = {'bootstrap.servers': 'localhost:29092'}  # Producer configur>
producer_config = {'bootstrap.servers': 'kafka:9092'}  # Producer configur>


consumer = Consumer(consumer_config)
producer = Producer(producer_config)

toalesys = 'to-alert-system'# Source topic for input messages
tonotif = 'to-notifier'  # Destination topic for sender message

# List to hold values for calculating statistics

consumer.subscribe([toalesys])  # Subscribe to TOPIC1

def produce_sync(producer, topic, value):
    """
    Synchronous producer function that blocks until the message is delivered.
    :param producer: Kafka producer instance
    :param topic: Kafka topic to send the message to
    :param value: Message value (string)
    """
    try:
        # Produce the message synchronously
        producer.produce(topic, value)
        producer.flush()  # Block until all outstanding messages are delivered
        print(f"Synchronously produced message to {topic}: {value}")
    except Exception as e:
        print(f"Failed to produce message: {e}")

while True:
    # Poll for new messages from TOPIC1
    msg = consumer.poll(1.0)
    if msg is None:
        continue  # No message received, continue polling
    if msg.error():
        print(f"Consumer error: {msg.error()}")  # Log any consumer errors
        continue

    # Parse the received message
    data = json.loads(msg.value().decode('utf-8'))
    email=data['email']
    ticker=data['ticker']
    value=data['last_price']
    timestamp=data['timestamp']
    print(data)
    query_handler = QueryHandler(CQRS_port)
    users = query_handler.get_user_by_email(email)
    query_handler.close()
    for user in users:
        print(user)
        email=user['email']
        ticker=user['ticker']
        id = user['telegramid'] 
        high_value=user['high_value']
        low_value=user['low_value']
        send=False
        if (value>high_value):
            alarm='High'
            send=True
        if(value<=low_value):
            alarm='Low'
            send=True
    # Produce the statistics to TOPIC2 synchronously
        if(send==True):
            message = {'email':email,
                       'ticker':ticker,
                       'alarm': alarm,
                       'id': id }
            print(f"Produced: {message}")
            produce_sync(producer, tonotif, json.dumps(message))
