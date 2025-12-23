"""
Bite Me Buddy - Live PostgreSQL Database Viewer
Fixed Version - No Log File Issues
"""

from flask import Flask, render_template, jsonify, request
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from datetime import datetime
import logging

app = Flask(__name__)

# Simple logging to console only - NO FILE LOGGING
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Your Database URL
DATABASE_URL = "postgresql://bite_me_buddy_user:6Mb7axQ89EkOQTQnqw6shT5CaO2lFY1Z@dpg-d536f8khg0os738kuhm0-a/bite_me_buddy"

def get_db_connection():
    """Create database connection"""
    try:
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        print("✅ Database connection successful")
        return conn
    except Exception as e:
        print(f"❌ Database connection failed: {str(e)}")
        raise

@app.route('/')
def home():
    """Home page - show HTML interface"""
    print("📄 Home page accessed")
    return render_template('index.html')

@app.route('/api/health')
def health_check():
    """Check if database is connected"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT 1')
        cur.close()
        conn.close()
        
        print("✅ Health check: Database connected")
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        print(f"❌ Health check failed: {str(e)}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500

@app.route('/api/tables')
def get_tables():
    """Get list of all tables"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        
        tables = [row[0] for row in cur.fetchall()]
        cur.close()
        conn.close()
        
        print(f"✅ Retrieved {len(tables)} tables")
        return jsonify({
            'success': True,
            'tables': tables,
            'count': len(tables)
        })
    except Exception as e:
        print(f"❌ Error fetching tables: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/data/<table_name>')
def get_table_data(table_name):
    """Get data from specific table"""
    try:
        limit = request.args.get('limit', default=100, type=int)
        
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get column names
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = %s
            ORDER BY ordinal_position;
        """, (table_name,))
        
        columns = [row['column_name'] for row in cur.fetchall()]
        
        # Get data
        data = []
        if columns:
            columns_str = ', '.join([f'"{col}"' for col in columns])
            query = f'SELECT {columns_str} FROM "{table_name}" LIMIT %s'
            cur.execute(query, (limit,))
            data = cur.fetchall()
        
        cur.close()
        conn.close()
        
        print(f"✅ Retrieved {len(data)} rows from table '{table_name}'")
        
        return jsonify({
            'success': True,
            'table_name': table_name,
            'columns': columns,
            'data': data,
            'count': len(data)
        })
    except Exception as e:
        print(f"❌ Error fetching data from table {table_name}: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/all-data')
def get_all_data():
    """Get data from all tables"""
    try:
        limit = request.args.get('limit', default=50, type=int)
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Get all tables
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        
        tables = [row[0] for row in cur.fetchall()][:5]  # First 5 tables only
        cur.close()
        conn.close()
        
        result = {}
        
        for table in tables:
            try:
                conn = get_db_connection()
                cur = conn.cursor(cursor_factory=RealDictCursor)
                
                # Get columns for this table
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
                    columns_str = ', '.join([f'"{col}"' for col in columns])
                    query = f'SELECT {columns_str} FROM "{table}" LIMIT %s'
                    cur.execute(query, (limit,))
                    data = cur.fetchall()
                
                cur.close()
                conn.close()
                
                result[table] = {
                    'columns': columns,
                    'data': data,
                    'count': len(data)
                }
                
                print(f"✅ Loaded table '{table}' with {len(data)} rows")
                
            except Exception as e:
                result[table] = {
                    'error': str(e),
                    'columns': [],
                    'data': [],
                    'count': 0
                }
                print(f"⚠️ Could not load table '{table}': {str(e)}")
        
        print(f"✅ Successfully loaded data from {len(result)} tables")
        
        return jsonify({
            'success': True,
            'data': result,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"❌ Error in get_all_data: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.errorhandler(404)
def not_found(e):
    """Handle 404 errors"""
    print(f"❌ 404 Error: {request.url}")
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def server_error(e):
    """Handle 500 errors"""
    print(f"❌ 500 Error: {str(e)}")
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 Starting Bite Me Buddy Live Viewer on port {port}")
    print(f"🔗 Database: bite_me_buddy")
    print(f"🐍 Python version: 3.9.18")
    app.run(host='0.0.0.0', port=port)