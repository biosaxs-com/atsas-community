
import sqlite3


def connect(dbfile):
  """Create database connection to sqlite database file 'dbfile'."""
  conn = None

  try:
    conn = sqlite3.connect(dbfile)
  except Error as e:
    print(e)

  return conn


def query(db, sql):
  """Requires an open database connect 'db', returns the retrieved rows (a list of tuples)."""
  # print(f"current query: {sql}")
  cur = db.cursor();
  cur.execute(sql);
  return cur.fetchall()
