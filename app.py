"""
Updated Main Flask Application for Bite Me Buddy Live Database Viewer
Compatible with Python 3.13
"""

from flask import Flask, render_template, jsonify, request
import psycopg
from psycopg.rows import dict_row
import os
from datetime import datetime
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Flask App
app = Flask(__name__)

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = os.environ.get('DATABASE_URL', 
    'postgresql://bite_me_buddy_user:6Mb7axQ89EkOQTQnqw6shT5CaO2lFY1Z@dpg-d536f8khg0os738kuhm0-a/bite_me_buddy')

def get_db_connection():
    """Create and return a database connection using psycopg"""
    try:
        conn = psycopg.connect(DATABASE_URL, row_factory=dict_row)
        logger.debug("Database connection established")
        return conn
    except Exception as e:
        logger.error(f"Database connection failed: {str(e)}")
        raise

@app.route('/')
def index():
    """Render main dashboard page"""
    logger.info("Home page accessed")
    return render_template('index.html')

@app.route('/api/health')
def health_check():
    """Check database connection health"""
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute('SELECT 1')
        conn.close()
        
        logger.info("Health check: Database connected")
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'timestamp': datetime.now().isoformat(),
            'service': 'Bite Me Buddy Live Viewer',
            'python_version': os.environ.get('PYTHON_VERSION', 'Unknown')
        })
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            'status': 'unhealthy',
            'database': 'disconnected',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/tables')
def get_tables():
    """Get list of all tables in database"""
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """)
            
            tables = [row['table_name'] for row in cur.fetchall()]
        
        conn.close()
        
        logger.info(f"Retrieved {len(tables)} tables")
        return jsonify({
            'success': True,
            'tables': tables,
            'count': len(tables)
        })
    except Exception as e:
        logger.error(f"Error fetching tables: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/data/<table_name>')
def get_table_data(table_name):
    """Get data from specific table"""
    try:
        # Get limit from query parameters
        limit = request.args.get('limit', default=100, type=int)
        
        conn = get_db_connection()
        
        # Get column information
        with conn.cursor() as cur:
            cur.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = %s
                ORDER BY ordinal_position;
            """, (table_name,))
            
            columns_info = cur.fetchall()
            columns = [col['column_name'] for col in columns_info]
        
        # Get table data
        data = []
        if columns:
            with conn.cursor() as cur:
                columns_str = ', '.join([f'"{col}"' for col in columns])
                query = f'SELECT {columns_str} FROM "{table_name}" LIMIT %s'
                cur.execute(query, (limit,))
                data = cur.fetchall()
        
        conn.close()
        
        logger.info(f"Retrieved {len(data)} rows from table '{table_name}'")
        
        return jsonify({
            'success': True,
            'table_name': table_name,
            'columns': columns,
            'data': data,
            'count': len(data),
            'limit': limit,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error fetching data from table {table_name}: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/all-data')
def get_all_data():
    """Get data from all tables (limited rows per table)"""
    try:
        limit_per_table = request.args.get('limit', default=50, type=int)
        
        # Get all tables
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """)
            
            tables = [row['table_name'] for row in cur.fetchall()][:10]  # Limit to first 10 tables
        conn.close()
        
        all_data = {}
        
        for table in tables:
            try:
                # Fetch data for each table
                conn = get_db_connection()
                
                # Get columns
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT column_name 
                        FROM information_schema.columns 
                        WHERE table_name = %s
                        ORDER BY ordinal_position;
                    """, (table,))
                    
                    columns = [row['column_name'] for row in cur.fetchall()]
                
                # Get data
                data = []
                if columns:
                    with conn.cursor() as cur:
                        columns_str = ', '.join([f'"{col}"' for col in columns])
                        query = f'SELECT {columns_str} FROM "{table}" LIMIT %s'
                        cur.execute(query, (limit_per_table,))
                        data = cur.fetchall()
                
                conn.close()
                
                all_data[table] = {
                    'columns': columns,
                    'data': data,
                    'count': len(data)
                }
                
            except Exception as e:
                logger.warning(f"Could not fetch data from table {table}: {str(e)}")
                all_data[table] = {
                    'error': str(e),
                    'columns': [],
                    'data': [],
                    'count': 0
                }
        
        logger.info(f"Retrieved data from {len(all_data)} tables")
        
        return jsonify({
            'success': True,
            'data': all_data,
            'total_tables': len(tables),
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error fetching all data: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.errorhandler(404)
def page_not_found(e):
    """Handle 404 errors"""
    logger.warning(f"404 error: {request.url}")
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    """Handle 500 errors"""
    logger.error(f"500 error: {str(e)}")
    return render_template('500.html'), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    logger.info(f"Starting Bite Me Buddy Live Viewer on port {port}")
    logger.info(f"Python version: {os.sys.version}")
    app.run(host='0.0.0.0', port=port, debug=debug)