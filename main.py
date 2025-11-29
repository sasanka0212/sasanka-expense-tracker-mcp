from fastmcp import FastMCP
import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(__file__), "expense.db")
CATEGORIES_PATH = os.path.join(os.path.dirname(__file__), "categories.json")

mcp = FastMCP(name="ExpenseTracker")

def init_db():
    with sqlite3.connect(DB_PATH) as cursor:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS expense(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                amount NUMBER NOT NULL,
                category TEXT NOT NULL,
                subcategory TEXT DEFAULT '',
                note TEXT DEFAULT ''
            )
            """
        )

init_db()

@mcp.tool
def add_expense(date, amount, category, subcategory='', note=''):
    '''add a new expense entry to database'''
    with sqlite3.connect(DB_PATH) as cursor:
        res = cursor.execute(
            "INSERT INTO expense(date, amount, category, subcategory, note) values(?, ?, ?, ?, ?)",
            (date, amount, category, subcategory, note)
        )
        return {
            'status': 'ok',
            'id': res.lastrowid
        }

@mcp.tool
def list_expenses(start_date, end_date):
    '''List expences within the given range'''
    with sqlite3.connect(DB_PATH) as cursor:
        res = cursor.execute(
            '''
            SELECT id, date, amount, category, subcategory, note
            FROM expense
            WHERE date BETWEEN ? AND ?
            ORDER BY id ASC
            ''',(start_date, end_date)
        )
        cols = [d[0] for d in res.description]
        return [dict(zip(cols, r)) for r in res.fetchall()]
    
@mcp.tool
def summerize(start_date, end_date, category=None):
    '''Summerize expense according to inclusive given range within the category'''
    with sqlite3.connect(DB_PATH) as cursor:
        query = """
            SELECT category, SUM(amount) as total_amount
            FROM expense
            WHERE date BETWEEN ? AND ?
        """
        params = [start_date, end_date]
        if category:
            query += " AND category = ?"
            params.append(category)

        query += "GROUP BY category ORDER BY category ASC"
        res = cursor.execute(query, params)
        cols = [d[0] for d in res.description]
        return [dict(zip(cols, r)) for r in res.fetchall()]
    
@mcp.resource("expense://categories", mime_type="application/json")
def categories():
    with open(CATEGORIES_PATH, mode="r", encoding="utf-8") as file:
        return file.read()

if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", PORT=8000)