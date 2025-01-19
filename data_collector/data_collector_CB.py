import json
import time
from CQRS import QueryHandler,CommandHandler

import yfinance as yf
from confluent_kafka import Producer

from circuit_breaker import CircuitBreaker, CircuitBreakerOpenException
from prometheus_client import start_http_server, Counter, Gauge, Summary
import time

port='mysql'

producer_config = {
#    'bootstrap.servers': 'localhost:19092,localhost:29092,localhost:39092',  # List of Kafka brokers
    'bootstrap.servers': 'kafka:9092',  # List of Kafka brokers
    'acks': 'all',  # Ensure all in-sync replicas acknowledge the message
    'max.in.flight.requests.per.connection': 1,  # Ensure ordering of messages
    'batch.size': 500,  # Maximum size of a batch in bytes
    'retries': 3  # Number of retries for failed messages
}
producer = Producer(producer_config)
topic1 = 'to-alert-system'  # Topic to produce messages to
datacollector_request_counter=Counter('datacollector_request_total','Total dataColl requests')
datacollector_request_time=Gauge('datacollector_time_total','Total time datacollector')
def delivery_report(err, msg):
    """Callback to report the result of message delivery."""
    if err:
        print(f"Delivery failed: {err}")
    else:
        print(f"Message delivered to {msg.topic()} [{msg.partition()}] at offset {msg.offset()}")

@datacollector_request_time.time()
def fetch_stock_data():
    datacollector_request_counter.inc()
    query_handler = QueryHandler(port)
    users = query_handler.get_email_ticker()
    query_handler.close()
    for user in users:
        try:
            email=user['email']
            ticker=user['ticker']
            print(ticker)
            stock_info = yf.Ticker(ticker).history(period="1d")
            if not stock_info.empty:
                last_price = stock_info["Close"].iloc[-1]
                last_timestamp=stock_info.index[-1]
                datatime=last_timestamp.strftime("%Y-%m-%d %H:%M:%S")
                last_price_fl=float(last_price)
                print(email,ticker,last_price,last_price_fl)
                command_handler = CommandHandler(port)
                command_handler.add_value(email,ticker,last_price_fl)
                command_handler.close()
                message = {'email':email,'ticker':ticker, 'last_price':last_price_fl,'timestamp': datatime}
                print(f"Produced: {message}")
                producer.produce(topic1, json.dumps(message), callback=delivery_report)
                producer.flush()  # Ensure the message is sent
        except Exception as e:
                print(f"Error fetching data for {ticker}: {e}")

if __name__ == "__main__":
    circuit_breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=5)

    while True:
        try:
          result = circuit_breaker.call(fetch_stock_data)
          print(f"Call : {result}")
        except CircuitBreakerOpenException:
          # Handle the case where the circuit is open
          print(f"Call : Circuit is open. Skipping call.Modificato")
        except Exception as e:
        # Handle other exceptions (e.g., service failures)
          print(f"Call : Exception occurred - {e}")
        time.sleep(1)  # Wait for a second before the next call
