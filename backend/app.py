from flask import Flask, request, jsonify, send_from_directory
import sqlite3
from flask_cors import CORS

import os
app = Flask(__name__)
FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../frontend'))

# Serve frontend
@app.route('/')
def serve_index():
    return send_from_directory(FRONTEND_DIR, 'index.html')

# Serve static files (if any)
@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory(FRONTEND_DIR, path)
CORS(app)

# Database setup
DB_NAME = 'mess.db'

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS meals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        student_name TEXT NOT NULL,
        meal_type TEXT NOT NULL,
        quantity INTEGER NOT NULL
    )''')
    conn.commit()
    conn.close()

@app.route('/add_meal', methods=['POST'])
def add_meal():
    data = request.json
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('INSERT INTO meals (date, student_name, meal_type, quantity) VALUES (?, ?, ?, ?)',
              (data['date'], data['student_name'], data['meal_type'], data['quantity']))
    conn.commit()
    conn.close()
    return jsonify({'status': 'success'})


@app.route('/meals', methods=['GET'])
def get_meals():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT * FROM meals')
    rows = c.fetchall()
    conn.close()
    meals = [
        {'id': row[0], 'date': row[1], 'student_name': row[2], 'meal_type': row[3], 'quantity': row[4]}
        for row in rows
    ]
    return jsonify(meals)

# Delete meal by id
@app.route('/delete_meal/<int:meal_id>', methods=['DELETE'])
def delete_meal(meal_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('DELETE FROM meals WHERE id = ?', (meal_id,))
    conn.commit()
    conn.close()
    return jsonify({'status': 'deleted'})

# Download meals as CSV
@app.route('/download/csv', methods=['GET'])
def download_csv():
    import csv
    from io import StringIO
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT * FROM meals')
    rows = c.fetchall()
    conn.close()
    si = StringIO()
    cw = csv.writer(si)
    cw.writerow(['id', 'date', 'student_name', 'meal_type', 'quantity'])
    cw.writerows(rows)
    output = si.getvalue()
    return app.response_class(
        output,
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment;filename=meals.csv'}
    )

# Download meals as Excel
@app.route('/download/excel', methods=['GET'])
def download_excel():
    import pandas as pd
    import io
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query('SELECT * FROM meals', conn)
    conn.close()
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Meals')
    output.seek(0)
    return app.response_class(
        output.read(),
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={'Content-Disposition': 'attachment;filename=meals.xlsx'}
    )

@app.route('/analytics', methods=['GET'])
def analytics():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT meal_type, SUM(quantity) FROM meals GROUP BY meal_type')
    data = c.fetchall()
    conn.close()
    return jsonify({row[0]: row[1] for row in data})

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
