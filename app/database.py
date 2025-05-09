import os
import pyodbc
from dotenv import load_dotenv

def get_db_connection():
    load_dotenv()  # Load environment variables from .env file
    server = os.getenv("DB_SERVER", "localhost")
    database = os.getenv("DB_NAME", "WeatherDB")
    username = os.getenv("DB_USER", "sa")
    password = os.getenv("DB_PASSWORD", "your_password_here")  # Replace with your actual password
    driver = "{ODBC Driver 17 for SQL Server}"

    connection_string = f'DRIVER={driver};SERVER={server};DATABASE={database};UID={username};PWD={password}'
    conn = pyodbc.connect(connection_string)
    return conn
 
