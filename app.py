"""
Bite Me Buddy - Live Database Viewer
Simplest Working Version
"""

from flask import Flask, render_template, jsonify, request
import psycopg2
from psycopg2.extras import RealDictCursor
import os

app = Flask(__name__)

# Database URL
DATABASE_URL = "postgresql://bite_me_buddy_user:6Mb7axQ89EkOQTQnqw6shT5CaO2lFY1Z@dpg-d536f8khg0os738kuhm0-a/bite_me_buddy"

def get_db():
    """Get database connection"""
    return psycopg2.connect(DATABASE_URL)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/health')
def health():
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute('SELECT 1')
        cur.close()
        conn.close()
        return jsonify({'status': 'ok', 'db': 'connected'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/tables')
def tables():
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")
        tables = [row[0] for row in cur.fetchall()]
        cur.close()
        conn.close()
        return jsonify({'success': True, 'tables': tables})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/data/<table>')
def table_data(table):
    try:
        limit = request.args.get('limit', 100, type=int)
        conn = get_db()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get columns
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name=%s", (table,))
        columns = [row['column_name'] for row in cur.fetchall()]
        
        # Get data
        data = []
        if columns:
            cols = ', '.join([f'"{c}"' for c in columns])
            cur.execute(f'SELECT {cols} FROM "{table}" LIMIT %s', (limit,))
            data = cur.fetchall()
        
        cur.close()
        conn.close()
        return jsonify({'success': True, 'table': table, 'columns': columns, 'data': data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/all')
def all_data():
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")
        tables = [row[0] for row in cur.fetchall()][:5]
        cur.close()
        conn.close()
        
        result = {}
        for table in tables:
            try:
                conn = get_db()
                cur = conn.cursor(cursor_factory=RealDictCursor)
                
                cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name=%s", (table,))
                columns = [row['column_name'] for row in cur.fetchall()]
                
                data = []
                if columns:
                    cols = ', '.join([f'"{c}"' for c in columns])
                    cur.execute(f'SELECT {cols} FROM "{table}" LIMIT 50')
                    data = cur.fetchall()
                
                cur.close()
                conn.close()
                result[table] = {'columns': columns, 'data': data, 'count': len(data)}
            except:
                result[table] = {'error': 'Failed to load', 'data': []}
        
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)