from concurrent import futures
import grpc
import mysql.connector
import yfinance as yf
from CQRS import QueryHandler, CommandHandler
from user_management_pb2 import *
from user_management_pb2_grpc import UserManagementServicer, add_UserManagementServicer_to_server
from threading import Lock
from prometheus_client import start_http_server, Counter, Histogram,Summary
import time

request_cache={}
values={}
cache_lock=Lock()
mysqllocation='mysql'
request_counter = Counter('grpc_requests_total', 'Total gRPC requests')
REQUEST_TIME = Summary('grpc_request_processing_seconds', 'Time spent processing request')



class UserService(UserManagementServicer):
    def __init__(self):
        query = QueryHandler(mysqllocation)
        users=query.get_users()
        query.close()
        with cache_lock:
             for user in users:
                 values={"ticker":user.get("ticker"),
                          "highvalue":user.get("high_value"),
                          "lowvalue":user.get("low_value"),
                          "telegramid":user.get("telegramid")}
                 request_cache[user.get("email")]=values
        print(request_cache)

    def UserCache(self, request, context):
        email = request.email
        values={"ticker":request.ticker,
                "highvalue":request.highvalue,
                "lowvalue":request.lowvalue,
                "telegramid":request.telegramid}

        print(f"Message received - Userid:{email},values:{values}")

        with cache_lock:
           print("Cache context:\n")
           for entry in  request_cache:
               print(entry)
               if email in entry:
                    print(f"Return for request {email} exist in cache")
                    return request_cache[email],True
        with cache_lock:
           request_cache[email]=values

        return request_cache[email],False

    @REQUEST_TIME.time()
    def RegisterUser(self, request, context):
#        print(type(request),type(context),context)
        email, ticker, highvalue, lowvalue ,telegramid = request.email, request.ticker, request.highvalue,request.lowvalue,request.telegramid
        value, stato=self.UserCache(request, context)
        print(value,stato)
        if (stato==False):
           try:
               stock = yf.Ticker(ticker)
               info=stock.info
               if 'shortName' not in info:
#                raise ValueError(f"Nessun dato valido trovato per il simbolo: {symbol}")
                   return UserResponse(success=False, message="ticker does'n exists.")
               DB_request_counter.inc()  # Incrementa il contatore
               query=CommandHandler(mysqllocation)
               query.add_user(email, ticker,highvalue,lowvalue,telegramid)
               query.close()
               return UserResponse(success=True, message="User registered successfully.")
           except mysql.connector.IntegrityError:
               return UserResponse(success=False, message="User already exists.")

    def UpdateUser(self, request, context):
        email, ticker , highvalue ,lowvalue,telegraid = request.email, request.ticker, request.highvalue, request.lowvalue,request.telegramid
        value, stato=self.UserCache(request, context)
        print(value,stato)
        if (stato==True):
	        with cache_lock:
                   values={"ticker":request.ticker,
                           "highvalue":request.highvalue,
                           "lowvalue":request.lowvalue,
                           "telegramid":request.telegramid}
                   request_cache[email]=values
                   DB_request_counter.inc()  # Incrementa il contatore
                   query=CommandHandler(mysqllocation)
                   query.update_user(email, ticker,highvalue,lowvalue,telegramid)
                   query.close()
        	return UserResponse(success=True, message="User updated successfully.")
        return UserResponse(success=False, message="User not {email} updated, not in queue.")


    def DeleteUser(self, request, context):
        email = request.email
        query=CommandHandler(mysqllocation)
        numrows=query.remove_user(email)
        query.close()
        if(numrows>0):
          DB_request_counter.inc()  # Incrementa il contatore
          del request_cache[email] 
          print (request_cache)
          return DeleteResponse(success=True, message="User deleted successfully.")
        return DeleteResponse(success=False, message="User deleted unsuccessfully.")


    def GetLatestStockValue(self, request, context):
        email = request.email
        query = QueryHandler(mysqllocation)
        user=query.get_user_by_email(email)
        query.close()
        print((user[0])['ticker'],len(user))
        if len(user)>0:
             ticker = user[0]['ticker']
             stock = yf.Ticker(ticker)
             price = stock.history(period="1d")['Close'].iloc[-1]
             return StockValueResponse(ticker=ticker, value=price, timestamp=str(stock.history(period="1d").index[-1]))
        return StockValueResponse()

    def GetAverageStockValue(self, request, context):
        email, count = request.email, request.count
        DB_request_counter.inc()  # Incrementa il contatore
        query = QueryHandler(mysqllocation)
        rows=query.get_average_value(email,count)
        query.close()
        values = [row[0] for row in rows]
        if values:
            return AverageValueResponse(average=sum(values) / len(values))
        return AverageValueResponse(average=0.0)

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    add_UserManagementServicer_to_server(UserService(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    server.wait_for_termination()

if __name__ == "__main__":
    # Avvio server Prometheus
    start_http_server(8001)
    print("Server is started")
    serve()

