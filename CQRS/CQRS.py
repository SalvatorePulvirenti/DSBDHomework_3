
import mysql.connector
from datetime import datetime

# Configurazione della connessione al database
DB_CONFIG ={
    'host': 'mysql',
#    'host': 'localhost',
    'user':'Admin',
    'password': '1234',
    'database': 'usermanagement'
}

# Classe per i comandi (scrittura nel database)
class CommandHandler:
    def __init__(self,host='mysql'):
        DB_CONFIG['host']=host
        self.conn = mysql.connector.connect(**DB_CONFIG)
        self.cursor = self.conn.cursor()

    def add_user(self, email, ticker, high_value,low_value,telegramid):
        query = "INSERT INTO utenti (email, ticker, high_value, low_value,telegramid ) VALUES (%s, %s, %s, %s,%s)"
        self.cursor.execute(query, (email, ticker, high_value,low_value,telegramid))
        self.conn.commit()

    def add_value(self, email, ticker, valore):
        query = """
        INSERT INTO stock_data (email, ticker, value,timestamp) VALUES (%s, %s, %s,%s)
        """
        self.cursor.execute(query, (email, ticker, valore, datetime.now()))
        self.conn.commit()

    def update_user(self, email,ticker, high_value,low_value,telegramid):
        query = "UPDATE utenti SET ticker=%s, high_value=%s, low_value=%s telegramid=%s WHERE email=%s"
        self.cursor.execute(query,(ticker,high_value,low_value, telegramid, email))
        self.conn.commit()
#         pass
    def remove_user(self,email):
        query= "DELETE FROM utenti WHERE email=%s"
        self.cursor.execute(query, (email,))
        value=self.cursor.rowcount
        print(value)
        self.conn.commit()
        return value

    def close(self):
        self.cursor.close()
        self.conn.close()

# Classe per le query (lettura dal database)
class QueryHandler:
    def __init__(self,host='mysql'):
        DB_CONFIG['host']=host
        self.conn = mysql.connector.connect(**DB_CONFIG)
        self.cursor = self.conn.cursor(dictionary=True)

    def get_users(self):
        query = "SELECT * FROM utenti"
        self.cursor.execute(query)
        return self.cursor.fetchall()

    def get_user_by_email(self, email):
        query = "SELECT * FROM utenti WHERE email = %s"
        self.cursor.execute(query, (email,))
        return self.cursor.fetchall()

    def get_values_by_user(self, email):
        query = "SELECT * FROM stock_data WHERE email = %s"
        self.cursor.execute(query, (email,))
        return self.cursor.fetchall()

    def get_average_value(self,email,count):
        query = "SELECT value FROM stock_data WHERE email = %s ORDER BY timestamp DESC LIMIT %s"
        self.cursor.execute(query, (email,count))
        return self.cursor.fetchall()

    def get_email_ticker(self):
        query = "SELECT email,ticker FROM utenti"
        self.cursor.execute(query)
        return self.cursor.fetchall()

        
    def close(self):
        self.cursor.close()
        self.conn.close()

# Esempio di utilizzo del sistema
if __name__ == "__main__":
    # Command Handler per scrittura
    command_handler = CommandHandler()
    command_handler.add_user("user1@example.com", "AAPL")
    command_handler.add_value("user1@example.com", "AAPL", 150.0)
    command_handler.close()

    # Query Handler per lettura
    query_handler = QueryHandler()
    users = query_handler.get_users()
    print("Utenti:", users)

    user_values = query_handler.get_values_by_user("user1@example.com")
    print("Valori per user1@example.com:", user_values)
    query_handler.close()
