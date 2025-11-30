import os
import json
import aiosqlite
from fastmcp import FastMCP

DB_PATH = os.path.join(os.path.dirname(__file__), "expense.db")
CATEGORIES_PATH = os.path.join(os.path.dirname(__file__), "categories.json")

mcp = FastMCP(name="ExpenseTracker")

# Always open DB in read-write-create mode
def db_uri():
    return f"file:{DB_PATH}?mode=rwc"

async def init_db():
    async with aiosqlite.connect(db_uri(), uri=True) as db:
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS expense(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                subcategory TEXT DEFAULT '',
                note TEXT DEFAULT ''
            )
            """
        )
        await db.commit()

@mcp.tool
async def add_expense(date, amount, category, subcategory='', note=''):
    """Add a new expense entry to database"""
    async with aiosqlite.connect(db_uri(), uri=True) as db:
        cursor = await db.execute(
            "INSERT INTO expense(date, amount, category, subcategory, note) VALUES (?, ?, ?, ?, ?)",
            (date, amount, category, subcategory, note)
        )
        await db.commit()
        return {"status": "ok", "id": cursor.lastrowid}

@mcp.tool
async def list_expenses(start_date, end_date):
    """List expenses within the given range"""
    async with aiosqlite.connect(db_uri(), uri=True) as db:
        cursor = await db.execute(
            """
            SELECT id, date, amount, category, subcategory, note
            FROM expense
            WHERE date BETWEEN ? AND ?
            ORDER BY id ASC
            """,
            (start_date, end_date)
        )
        rows = await cursor.fetchall()
        cols = [d[0] for d in cursor.description]
        return [dict(zip(cols, r)) for r in rows]

@mcp.tool
async def summerize(start_date, end_date, category=None):
    """Summarize expense within the date range (optionally filtered by category)"""
    async with aiosqlite.connect(db_uri(), uri=True) as db:
        query = """
            SELECT category, SUM(amount) as total_amount
            FROM expense
            WHERE date BETWEEN ? AND ?
        """
    params = [start_date, end_date]

    if category:
        query += " AND category = ?"
        params.append(category)

    query += " GROUP BY category ORDER BY category ASC"

    cursor = await db.execute(query, params)
    rows = await cursor.fetchall()
    cols = [d[0] for d in cursor.description]
    return [dict(zip(cols, r)) for r in rows]

@mcp.resource("expense://categories", mime_type="application/json")
def categories():
    with open(CATEGORIES_PATH, "r", encoding="utf-8") as file:
        return file.read()

if __name__ == "__main__":
    import asyncio
    asyncio.run(init_db())
    mcp.run(transport="http", host="0.0.0.0", port=8000)