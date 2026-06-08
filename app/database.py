import sqlite3 
from datetime import datetime

db_path = "./shopease.db"

def get_connection():
    conn= sqlite3.connect(db_path)
    return conn

def init_db():
    conn=get_connection()
    conn.execute("CREATE TABLE IF NOT EXISTS messages (id INTEGER PRIMARY KEY AUTOINCREMENT, session_id TEXT, role TEXT, content TEXT, timestamp DATETIME)")
    conn.commit()
    conn.close()

def save_message(session_id, role, content):
  conn=get_connection()
  timestamp=datetime.utcnow()
  conn.execute("INSERT INTO messages VALUES (NULL, ?, ?, ?, ?)", (session_id, role, content, timestamp))
  conn.commit()
  conn.close()

def get_history(session_id):
  conn=get_connection()
  cursor=conn.execute("SELECT role,content FROM messages WHERE session_id=?", (session_id,))
  rows=cursor.fetchall()
  conn.close()
  dicts=[]
  for role,content in rows:
    dicts.append({'role': role, 'content': content})
  return dicts

def clear_history(session_id):
  conn=get_connection()
  conn.execute("DELETE FROM messages WHERE session_id=?",(session_id,))
  conn.commit()
  conn.close()

# orders
def init_orders_db():
  conn=get_connection()
  conn.execute("CREATE TABLE IF NOT EXISTS orders(order_id TEXT PRIMARY KEY,customer_name TEXT,status TEXT,address TEXT,item TEXT,created_at TEXT)")
  sample_orders = [
    ("ORD-1001", "Raj Kumar", "processing", "123 MG Road, Mumbai", "Blue Sneakers","2026-01-15"),
    ("ORD-1002", "Priya Singh", "shipped", "45 Park Street, Delhi", "Wireless Headphones","2026-03-16"),
    ("ORD-1003", "Amit Shah", "delivered", "78 Brigade Road, Bangalore", "Cotton T-Shirt","2026-07-19"),
  ]
  conn.executemany("INSERT OR IGNORE INTO orders VALUES (?,?,?,?,?,?)", sample_orders)   #IGNORE skips the insert if a row with that primary key already exists — safe to run multiple times.
  conn.commit()
  conn.close()

def get_order(order_id):
  conn=get_connection()
  cursor=conn.execute("SELECT * FROM orders WHERE order_id=?", (order_id,))
  row=cursor.fetchone()
  conn.close()
  if row:
      return {
          'order_id': row[0],
          'customer_name': row[1],
          'status': row[2],
          'address': row[3],
          'item': row[4],
          'created_at': row[5]
      }
  return None

def update_order_address(order_id, new_address):
  conn=get_connection()
  cursor=conn.execute("UPDATE orders SET address=? WHERE order_id=?",(new_address,order_id))
  conn.commit()
  conn.close()
  if cursor.rowcount > 0:
      return True
  return False

def update_order_status(order_id, new_status):
  conn=get_connection()
  cursor=conn.execute("UPDATE orders SET status=? WHERE order_id=?",(new_status,order_id))
  conn.commit()
  conn.close()
  if cursor.rowcount > 0:
      return True
  return False