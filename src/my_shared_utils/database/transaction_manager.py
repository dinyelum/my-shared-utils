#!/usr/bin/env python3
"""
Database transaction script
"""

from . import config
import MySQLdb
from datetime import datetime
from typing import List, Dict, Any, Optional, Union


class DatabaseTransactionManager:
    def __init__(self, table: str):
        """Initialize database connection"""
        self.table = table
        self.conn = None
        self.cursor = None

    def __enter__(self):
        """Context manager entry"""
        try:
            self.conn = MySQLdb.connect(
                host=config.DB_HOST,
                user=config.DB_USER,
                password=config.DB_PASS,
                database=config.DB_NAME
            )

            self.cursor = self.conn.cursor()
            return self

        except MySQLdb.Error as e:
            print(f"MYSQL ERROR in __enter__: {type(e).__name__}: {e}")
            print(
                f"Error details: errno={getattr(e, 'errno', 'N/A')}, sqlstate={getattr(e, 'sqlstate', 'N/A')}")
            raise

        except Exception as e:
            print(f"GENERAL ERROR in __enter__: {type(e).__name__}: {e}")
            raise

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - commit and close connection"""
        if exc_type is None:
            self.conn.commit()
        else:
            self.conn.rollback()
        self.conn.close()

    def insert(self, data, columns=None, ignore=False, returnself=False):
        """
        Insert data into records table.

        Args:
            data: List of dictionaries or list of tuples/values
            columns: Column names (required if data is list of tuples)
        """
        if not data:
            print("No data")
            return

        # Handle different input formats
        if isinstance(data, dict):
            # Single dictionary
            columns = list(data.keys())
            values = [tuple(data.values())]
        elif isinstance(data[0], dict):
            # List of dictionaries
            columns = list(data[0].keys())
            values = [tuple(row.values()) for row in data]
        else:
            # List of tuples/list, columns must be provided
            if not columns:
                raise ValueError(
                    "columns parameter required when data is not a dictionary")
            values = data

        placeholders = ", ".join(["%s"] * len(columns))
        column_list = ", ".join(columns)

        self.sql = f"INSERT {'ignore' if ignore == True else ''} INTO {self.table} ({column_list}) VALUES ({placeholders})"
        self.params = values

        if returnself == True:
            return self

        return self.run()

    def on_duplicate_key(self, query, params=None):
        self.sql += f" ON DUPLICATE KEY {query} "
        if params:
            self.params.append(params)
        return self

    def returnrow(self, returnrow: Union['id', list] = 'id'):
        id = self.cursor.lastrowid
        if returnrow == True:
            return self.select(', '.join(returnrow)).where(f"id={id}")
        self.run()
        return self.cursor.lastrowid

    def select(self, columns='*', returncolumns=False):
        """Start building a SELECT query"""
        if isinstance(columns, list):
            columns = ", ".join(columns)

        if returncolumns == True:
            self.cursor = self.conn.cursor(MySQLdb.cursors.DictCursor)

        self.sql = f"SELECT {columns} FROM {self.table}"
        self.params = []
        return self

    def update(self, data: Dict[str, Any]):
        """Start building an UPDATE query"""
        if not data:
            raise ValueError("No data provided for update")

        set_clauses = []
        self.params = []

        for column, value in data.items():
            set_clauses.append(f"{column} = %s")
            self.params.append(value)

        self.sql = f"UPDATE {self.table} SET {', '.join(set_clauses)}"
        return self

    def delete(self):
        """Start building a DELETE query"""
        self.sql = f"DELETE FROM {self.table}"
        self.params = []
        return self

    def where(self, condition: str, *params):
        """Add WHERE clause to current query"""
        if 'WHERE' in self.sql:
            self.sql += f" AND {condition}"
        else:
            self.sql += f" WHERE {condition}"

        self.params.extend(params)
        return self.run()

    def run(self, fetch_all: bool = True):
        """Execute the built query

        Args:
            fetch_all: Override the fetch preference. If None, uses self.fetch_all

        Returns:
            If fetch_all=True: List of all results
            If fetch_all=False: Cursor object for streaming
        """
        if self.sql.startswith('SELECT'):
            self.cursor.execute(self.sql, self.params)
            if fetch_all == True:
                return self.cursor.fetchall()
            return self.cursor
        elif self.sql.startswith('INSERT'):
            if len(self.params) == 1:
                self.cursor.execute(self.sql, self.params[0])
            else:
                self.cursor.executemany(self.sql, self.params)
        else:
            self.cursor.execute(self.sql, self.params)
            return self.cursor.rowcount

    def custom_query(self, query, queryvalues: list):
        queryvalues = queryvalues or []
        self.sql = query
        self.params = queryvalues
        return self.run()


class DTMError(MySQLdb.Error):
    pass
