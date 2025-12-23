from flask import Flask, render_template, jsonify
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from datetime import datetime

app = Flask(__name__)

# Database configuration
DATABASE_URL = "postgresql://bite_me_buddy_user:6Mb7axQ89EkOQTQnqw6shT5CaO2lFY1Z@dpg-d536f8khg0os738kuhm0-a/bite_me_buddy"

def get_db_connection():
    """Create and return a database connection"""
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    return conn

def get_table_names():
    """Get all table names from the database"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        tables = cursor.fetchall()
        cursor.close()
        conn.close()
        return [table[0] for table in tables]
    except Exception as e:
        print(f"Error getting table names: {e}")
        return []

def get_table_data(table_name, limit=100):
    """Get data from a specific table"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get column names first
        cursor.execute(f"""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = '{table_name}'
            ORDER BY ordinal_position;
        """)
        columns = [row['column_name'] for row in cursor.fetchall()]
        
        # Get data with dynamic column selection
        if columns:
            columns_str = ', '.join([f'"{col}"' for col in columns])
            query = f'SELECT {columns_str} FROM "{table_name}" LIMIT {limit}'
            cursor.execute(query)
            data = cursor.fetchall()
        else:
            data = []
        
        cursor.close()
        conn.close()
        
        return {
            'table_name': table_name,
            'columns': columns,
            'data': data,
            'count': len(data),
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        print(f"Error getting table data: {e}")
        return {'error': str(e)}

def get_all_tables_data(limit=50):
    """Get data from all tables (limited rows per table)"""
    tables = get_table_names()
    all_data = {}
    
    for table in tables[:5]:  # Limit to first 5 tables to avoid too much data
        table_data = get_table_data(table, limit)
        all_data[table] = table_data
    
    return all_data

@app.route('/')
def index():
    """Render the main page"""
    return render_template('index.html')

@app.route('/api/tables')
def get_tables():
    """API endpoint to get all table names"""
    try:
        tables = get_table_names()
        return jsonify({
            'success': True,
            'tables': tables,
            'count': len(tables)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/data/<table_name>')
def get_data(table_name):
    """API endpoint to get data from a specific table"""
    try:
        limit = request.args.get('limit', default=100, type=int)
        data = get_table_data(table_name, limit)
        
        if 'error' in data:
            return jsonify({
                'success': False,
                'error': data['error']
            }), 500
            
        return jsonify({
            'success': True,
            **data
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/all-data')
def get_all_data():
    """API endpoint to get data from all tables"""
    try:
        limit = request.args.get('limit', default=50, type=int)
        all_data = get_all_tables_data(limit)
        
        return jsonify({
            'success': True,
            'data': all_data,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT 1')
        cursor.close()
        conn.close()
        
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'database': 'disconnected',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
