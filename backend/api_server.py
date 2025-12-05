# first run "python backend/api_server.py"
import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import requests
import pyodbc
from urllib.parse import quote_plus

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configure Gemini API
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    raise RuntimeError("Missing required environment variable: GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

# SQL Server connection details
DB_SERVER = os.getenv('DB_SERVER')
DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')

missing_db_vars = [
    var_name for var_name, value in [
        ('DB_SERVER', DB_SERVER),
        ('DB_NAME', DB_NAME),
        ('DB_USER', DB_USER),
        ('DB_PASSWORD', DB_PASSWORD),
    ] if not value
]
if missing_db_vars:
    raise RuntimeError(f"Missing required database environment variables: {', '.join(missing_db_vars)}")

# Build connection string
password_encoded = quote_plus(DB_PASSWORD)
db_connection_string = f'mssql+pyodbc://{DB_USER}:{password_encoded}@{DB_SERVER}/{DB_NAME}?driver=ODBC+Driver+17+for+SQL+Server'

# Create engine
engine = None
database_connected = False

try:
    engine = create_engine(db_connection_string)
    
    # Test the connection
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    database_connected = True
    print("Successfully connected to SQL Server using SQLAlchemy with pyodbc")
    print(f"Connected to SQL Server at {DB_SERVER} with database {DB_NAME}")
except Exception as e:
    print(f"Failed to connect to SQL Server using SQLAlchemy with pyodbc: {e}")
    print(f"Attempted to connect to SQL Server at {DB_SERVER} with database {DB_NAME}")
    print("Please verify:")
    print("1. The SQL Server is running and accessible")
    print("2. The IP address and port are correct")
    print("3. The ODBC Driver 17 for SQL Server is installed")
    print("4. The firewall allows connections to the SQL Server")
    print("5. SQL Server is configured to allow remote connections")
    # We'll continue without database connection but will return an error for search requests
    database_connected = False
    engine = None

# Database structure
db_structure = """
Tables:
- Properties (property_id, unparsed_address, list_price, bedrooms, bathrooms, square_footage, property_type, year_built, description, latitude, longitude)
- Amenities (amenity_id, property_id, amenity_type, title, address, distance_km)
"""

# Prompt for Gemini LLM
prompt = """
You are an expert in converting natural language questions to SQL queries and ddon't make mistake in SQL query.
Given the database structure below, generate a SQL query for the user's question.
- Alwaays display the Properties use  P.*
- For properties with a pool, check the 'description' field for the word 'pool'.
- For amenities, only use the following key words values for 'amenity_type': Transit, Malls, Pharmacies, Hospitals, Schools, Restaurants, Groceries, ATMs, Parks.
- Use DISTINCT to avoid duplicate rows.
- Use LIKE for case-insensitive searches, not ILIKE.
- Use <= for less than or equal to comparisons.
- Use the correct spelling for locations (e.g., 'South Carolina').
Only return the SQL query, nothing else.
"""

# RealtyFeed API Configuration (only used for fetching images)
REALTY_API_URL = "https://api.realtyfeed.com/reso/odata/Property?&$orderby=RFModificationTimestamp desc&$top=200&$count=true"
REALTY_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI2NTM1ZDVmZjdkYTQ0OWI4ODU2NDFlOTA3YTYyMmYxMyIsInRva2VuX3VzZSI6ImFjY2VzcyIsInNjb3BlIjoiYXBpL3JlYWQiLCJleHAiOjE3NjQ5NTM4NTUsImp0aSI6IjA5YWZmN2QxLTU1YzktNDdmYi04YmUyLTc0YzMzOWUyZjBmMCIsImNsaWVudF9pZCI6IjY1MzVkNWZmN2RhNDQ5Yjg4NTY0MWU5MDdhNjIyZjEzIn0.A7VpN3U1yZ-exs1g8KrLSZgzWHZKtsSub-IclHL4qpU"

def fetch_realty_properties():
    """Fetch properties from RealtyFeed API for image matching"""
    try:
        headers = {
            'Authorization': f'Bearer {REALTY_TOKEN}',
            'Accept': 'application/json'
        }
        response = requests.get(REALTY_API_URL, headers=headers, timeout=10)
        
        if response.ok:
            data = response.json()
            properties = data.get('value', [])
            print(f"Fetched {len(properties)} properties from RealtyFeed API for image matching")
            return properties
        else:
            print(f"Failed to fetch from RealtyFeed API: {response.status_code}")
            return []
    except Exception as e:
        print(f"Error fetching RealtyFeed properties: {str(e)}")
        return []

def find_property_images(address, realty_properties):
    """Find property images from RealtyFeed properties by matching address"""
    if not address or not realty_properties:
        return []
    
    # Normalize address for comparison
    normalized_address = address.lower().strip()
    
    # Try to find matching property
    for prop in realty_properties:
        prop_address = prop.get('UnparsedAddress', '')
        if not prop_address:
            # Construct address from parts
            parts = [
                prop.get('StreetNumber'),
                prop.get('StreetName'),
                prop.get('City'),
                prop.get('StateOrProvince')
            ]
            prop_address = ' '.join([str(p) for p in parts if p])
        
        if prop_address and normalized_address in prop_address.lower():
            media = prop.get('Media', [])
            if media and isinstance(media, list):
                return media
    
    return []

def generate_sql_query(user_query, db_structure, prompt):
    model = genai.GenerativeModel('gemini-2.5-flash')
    response = model.generate_content(
        f"{prompt}\nDatabase Structure:\n{db_structure}\nUser Query:\n{user_query}"
    )
    return response.text.strip()

def execute_sql_query(sql_query):
    """Execute SQL query and return results as list of dictionaries"""
    if not database_connected or engine is None:
        raise Exception("Database connection not available. Please check your database configuration.")
    
    try:
        with engine.connect() as connection:
            result = connection.execute(text(sql_query))
            df = pd.DataFrame(result.fetchall(), columns=result.keys())
            return df.to_dict('records')
    except Exception as e:
        raise Exception(f"Error executing SQL query: {str(e)}")

def transform_sql_results_to_properties(sql_results, realty_properties=None):
    """Transform SQL query results directly to Property format matching frontend interface"""
    transformed_properties = []
    
    # Fetch RealtyFeed properties once if not provided (for image matching)
    if realty_properties is None:
        realty_properties = fetch_realty_properties()
    
    for prop in sql_results:
        # Get column values (handle different possible column name formats)
        def get_value(key_variants, default=None):
            for key in key_variants:
                value = prop.get(key) or prop.get(key.upper()) or prop.get(key.lower())
                if value is not None:
                    return value
            return default
        
        # Create a transformed property object matching the frontend interface
        transformed = {
            'ListingKey': str(get_value(['property_id', 'PROPERTY_ID'], '')),
            'ListingId': str(get_value(['property_id', 'PROPERTY_ID'], '')),
            'ListPrice': float(get_value(['list_price', 'LIST_PRICE'], 0)) if get_value(['list_price', 'LIST_PRICE']) else 0,
            'UnparsedAddress': str(get_value(['unparsed_address', 'UNPARSED_ADDRESS'], '')),
            'StreetNumber': '',
            'StreetName': '',
            'City': '',
            'BedroomsTotal': int(get_value(['bedrooms', 'BEDROOMS'], 0)) if get_value(['bedrooms', 'BEDROOMS']) else 0,
            'BathroomsTotalInteger': int(get_value(['bathrooms', 'BATHROOMS'], 0)) if get_value(['bathrooms', 'BATHROOMS']) else 0,
            'LivingArea': float(get_value(['square_footage', 'SQUARE_FOOTAGE'], 0)) if get_value(['square_footage', 'SQUARE_FOOTAGE']) else 0,
            'Media': [],
            'Latitude': float(get_value(['latitude', 'LATITUDE'], 0)) if get_value(['latitude', 'LATITUDE']) else None,
            'Longitude': float(get_value(['longitude', 'LONGITUDE'], 0)) if get_value(['longitude', 'LONGITUDE']) else None,
            'PublicRemarks': str(get_value(['description', 'DESCRIPTION'], '')),
            'YearBuilt': int(get_value(['year_built', 'YEAR_BUILT'], 0)) if get_value(['year_built', 'YEAR_BUILT']) else None,
            'PropertyType': str(get_value(['property_type', 'PROPERTY_TYPE'], '')),
        }
        
        # Parse address if available
        unparsed_address = transformed['UnparsedAddress']
        if unparsed_address:
            address_parts = unparsed_address.split(',')
            if len(address_parts) >= 1:
                street_parts = address_parts[0].strip().split(' ', 1)
                if len(street_parts) >= 2:
                    transformed['StreetNumber'] = street_parts[0]
                    transformed['StreetName'] = street_parts[1]
            if len(address_parts) >= 2:
                transformed['City'] = address_parts[1].strip()
        
        # Find images from RealtyFeed API by matching address
        unparsed_address = transformed['UnparsedAddress']
        if unparsed_address:
            images = find_property_images(unparsed_address, realty_properties)
            if images:
                transformed['Media'] = images
            else:
                # Fallback to placeholder if no images found
                transformed['Media'] = [{
                    'MediaURL': f'https://via.placeholder.com/400x300?text=No+Image+Available'
                }]
        else:
            # Add placeholder image if no address available
            transformed['Media'] = [{
                'MediaURL': f'https://via.placeholder.com/400x300?text=No+Image+Available'
            }]
        
        transformed_properties.append(transformed)
    
    return transformed_properties


@app.route('/api/search', methods=['POST'])
def search():
    """Handle natural language search requests"""
    try:
        data = request.get_json()
        
        if not data or 'query' not in data:
            return jsonify({'error': 'Missing query parameter'}), 400
        
        user_query = data['query'].strip()
        
        if not user_query:
            return jsonify({'error': 'Query cannot be empty'}), 400
        
        # Check if database is connected
        if not database_connected or engine is None:
            return jsonify({
                'success': False,
                'error': 'Database connection not available. Please check your database configuration.'
            }), 500
        
        # Generate SQL query using Gemini
        sql_query = generate_sql_query(user_query, db_structure, prompt)
        
        # Clean the SQL query (remove markdown code blocks if present)
        cleaned_sql_query = sql_query.replace("```sql", "").replace("```", "").strip()
        
        # Execute SQL query to get results from database
        sql_results = execute_sql_query(cleaned_sql_query)
        
        # Fetch RealtyFeed properties once for image matching
        realty_properties = fetch_realty_properties()
        
        # Transform SQL results directly to Property format (properties are already listed in database)
        # Pass realty_properties to avoid fetching multiple times
        transformed_properties = transform_sql_results_to_properties(sql_results, realty_properties)
        
        count = len(transformed_properties)
        
        message = ""
        lower_query = user_query.lower()
        if lower_query.startswith('show me '):
            rest_of_query = user_query[len('show me '):]
            message = f"Showing {count} {rest_of_query}"
        else:
            message = f"Showing {count} results for: {user_query}"

        return jsonify({
            'success': True,
            'query': user_query,
            'sql': cleaned_sql_query,
            'results': transformed_properties,
            'count': count,
            'message': message
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy', 
        'service': 'Real Estate Search API', 
        'database_connected': database_connected,
        'database_server': DB_SERVER,
        'database_name': DB_NAME
    })

if __name__ == '__main__':
    print("Starting Real Estate Search API server...")
    print("Server running on http://localhost:5000")
    app.run(debug=True, port=5000)
