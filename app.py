"""
Bite Me Buddy - Live PostgreSQL Database Viewer
Compatible with Python 3.13
"""

from flask import Flask, render_template, jsonify, request
import psycopg
from psycopg.rows import dict_row
import os
from datetime import datetime

app = Flask(__name__)

# Your Database URL
DATABASE_URL = "postgresql://bite_me_buddy_user:6Mb7axQ89EkOQTQnqw6shT5CaO2lFY1Z@dpg-d536f8khg0os738kuhm0-a/bite_me_buddy"

def get_db_connection():
    """Create database connection using psycopg (not psycopg2)"""
    try:
        conn = psycopg.connect(DATABASE_URL, row_factory=dict_row)
        print("✅ Database connection successful")
        return conn
    except Exception as e:
        print(f"❌ Database connection failed: {str(e)}")
        raise

@app.route('/')
def home():
    """Home page"""
    print("📄 Home page accessed")
    return render_template('index.html')

@app.route('/api/health')
def health_check():
    """Check database connection"""
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute('SELECT 1')
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
    """Get all table names"""
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
        
        # Get column names
        with conn.cursor() as cur:
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
            with conn.cursor() as cur:
                columns_str = ', '.join([f'"{col}"' for col in columns])
                query = f'SELECT {columns_str} FROM "{table_name}" LIMIT %s'
                cur.execute(query, (limit,))
                data = cur.fetchall()
        
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
        
        # Get all tables
        with conn.cursor() as cur:
            cur.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """)
            
            tables = [row['table_name'] for row in cur.fetchall()][:5]  # First 5 tables
        
        conn.close()
        
        result = {}
        
        for table in tables:
            try:
                conn = get_db_connection()
                
                # Get columns for this table
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
                        cur.execute(query, (limit,))
                        data = cur.fetchall()
                
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

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 Starting Bite Me Buddy Live Viewer on port {port}")
    print(f"🔗 Database: bite_me_buddy")
    print(f"🐍 Using psycopg[c] for Python 3.13 compatibility")
    app.run(host='0.0.0.0', port=port)