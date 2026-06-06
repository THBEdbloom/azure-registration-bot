import os
import pyodbc
from dotenv import load_dotenv
from keyvault_service import get_secret

load_dotenv()

USE_KEY_VAULT = os.getenv("USE_KEY_VAULT", "false").lower() == "true"

if USE_KEY_VAULT:
    DB_SERVER = get_secret("db-server")
    DB_NAME = get_secret("db-name")
    DB_USER = get_secret("db-user")
    DB_PASSWORD = get_secret("db-password")
else:
    DB_SERVER = os.getenv("DB_SERVER")
    DB_NAME = os.getenv("DB_NAME")
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")


def get_connection():
    connection_string = (
        "DRIVER={ODBC Driver 17 for SQL Server};"
        f"SERVER={DB_SERVER};"
        f"DATABASE={DB_NAME};"
        f"UID={DB_USER};"
        f"PWD={DB_PASSWORD};"
        "Encrypt=yes;"
        "TrustServerCertificate=no;"
        "Connection Timeout=30;"
    )
    return pyodbc.connect(connection_string)


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        IF NOT EXISTS (
            SELECT * FROM sysobjects 
            WHERE name='Users' AND xtype='U'
        )
        CREATE TABLE Users (
            Id INT IDENTITY(1,1) PRIMARY KEY,
            FirstName NVARCHAR(100) NOT NULL,
            LastName NVARCHAR(100) NOT NULL,
            BirthDate NVARCHAR(20) NOT NULL,
            Email NVARCHAR(255) NOT NULL,
            Phone NVARCHAR(50) NOT NULL,
            Street NVARCHAR(255) NOT NULL,
            HouseNumber NVARCHAR(20) NOT NULL,
            PostalCode NVARCHAR(20) NOT NULL,
            City NVARCHAR(100) NOT NULL,
            Country NVARCHAR(100) NOT NULL,
            CreatedAt DATETIME DEFAULT GETDATE()
        )
    """)

    conn.commit()
    conn.close()


def save_user(user_data):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO Users (
            FirstName, LastName, BirthDate, Email, Phone,
            Street, HouseNumber, PostalCode, City, Country
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        user_data.get("first_name"),
        user_data.get("last_name"),
        user_data.get("birth_date"),
        user_data.get("email"),
        user_data.get("phone"),
        user_data.get("street"),
        user_data.get("house_number"),
        user_data.get("postal_code"),
        user_data.get("city"),
        user_data.get("country")
    ))

    conn.commit()
    conn.close()


def get_all_users():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            Id, FirstName, LastName, BirthDate, Email, Phone,
            Street, HouseNumber, PostalCode, City, Country, CreatedAt
        FROM Users
        ORDER BY CreatedAt DESC
    """)

    users = cursor.fetchall()
    conn.close()
    return users


def search_users(search_term):
    conn = get_connection()
    cursor = conn.cursor()

    query = f"%{search_term}%"

    cursor.execute("""
        SELECT 
            Id, FirstName, LastName, BirthDate, Email, Phone,
            Street, HouseNumber, PostalCode, City, Country, CreatedAt
        FROM Users
        WHERE 
            FirstName LIKE ?
            OR LastName LIKE ?
            OR Email LIKE ?
            OR City LIKE ?
            OR PostalCode LIKE ?
        ORDER BY CreatedAt DESC
    """, (query, query, query, query, query))

    users = cursor.fetchall()
    conn.close()
    return users


def get_statistics():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM Users")
    total_users = cursor.fetchone()[0]

    cursor.execute("""
        SELECT Country, COUNT(*) 
        FROM Users 
        GROUP BY Country 
        ORDER BY COUNT(*) DESC
    """)
    users_by_country = cursor.fetchall()

    cursor.execute("""
        SELECT City, COUNT(*) 
        FROM Users 
        GROUP BY City 
        ORDER BY COUNT(*) DESC
    """)
    users_by_city = cursor.fetchall()

    conn.close()

    return {
        "total_users": total_users,
        "users_by_country": users_by_country,
        "users_by_city": users_by_city
    }