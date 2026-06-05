import os
import pyodbc
from dotenv import load_dotenv

load_dotenv()

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