#!/bin/bash

# Credenziali MySQL
#MYSQL_HOST="mysql"
MYSQL_HOST="localhost"
MYSQL_USER="root"
MYSQL_PASS="root"
MYSQL_DB="usermanagement"

# Comandi SQL per creare le tabelle
SQL="
CREATE DATABASE IF NOT EXISTS usermanagement;

CREATE USER IF NOT EXISTS 'Admin'@'%' IDENTIFIED BY '1234';

USE usermanagement;


CREATE TABLE IF NOT EXISTS utenti(
    email VARCHAR(255) PRIMARY KEY,
    high_value DOUBLE DEFAULT NULL,
    low_value DOUBLE DEFAULT NULL,
    telegramid BIGINT   DEFAULT NULL,
    ticker VARCHAR(10) NOT NULL);

CREATE TABLE IF NOT EXISTS stock_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255),
    ticker VARCHAR(10),
    value DOUBLE NOT NULL,
    timestamp DATETIME NOT NULL,
    FOREIGN KEY (email) REFERENCES utenti(email));
FLUSH PRIVILEGES;

GRANT ALL PRIVILEGES ON usermanagement.* TO 'Admin'@'%' WITH GRANT OPTION;
"

# Esegui i comandi SQL
echo "Creazione delle tabelle nel database $MYSQL_DB..."
mysql -h $MYSQL_HOST -u $MYSQL_USER -p$MYSQL_PASS $MYSQL_DB -e "$SQL"

if [ $? -eq 0 ]; then
    echo "Tabelle create con successo!"
else
    echo "Errore durante la creazione delle tabelle."
fi
