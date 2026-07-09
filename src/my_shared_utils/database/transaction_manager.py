#!/usr/bin/env python3
"""
Database transaction script
"""

from datetime import datetime
from typing import List, Dict, Any, Optional, Union
import sys


class DatabaseTransactionManager:
    def __init__(self, connector_factory, table: str):
        """Initialize database connection"""
        self.connector_factory = connector_factory
        self.table = table
        self.conn = None
        self.cursor = None
        self._native_dict_cursor = False
        self._return_dict = False

    def __enter__(self):
        """Context manager entry"""
        try:
            self.conn = self.connector_factory()
            self.cursor = self.conn.cursor()
            return self
        except Exception as e:
            raise DTMError(f"Database connection failed: {e}")

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

    def returnrow(self, returnrow: Union[str, bool] = 'id'):
        self.run()
        rows = '*' if returnrow == True else returnrow
        return self.select(rows).where(f"id=(SELECT LAST_INSERT_ID())")

    def select(self, columns='*', return_dict=False):
        """Start building a SELECT query"""
        if isinstance(columns, list):
            columns = ", ".join(columns)

        self._native_dict_cursor = False
        self._return_dict = return_dict

        if return_dict:
            try:
                self.cursor = self.conn.cursor(dictionary=True)
                self._native_dict_cursor = True
            except TypeError:
                # fallback for drivers without dict cursor
                self.cursor = self.conn.cursor()
        else:
            self.cursor = self.conn.cursor()

        self.sql = f"SELECT {columns} FROM {self.table}"
        self.params = []
        return self

    def update(self, data: List[Dict[str, Any]]):
        """Start building an UPDATE query

        Args:
            data: List of dictionaries
        """
        # Doesn't work for update where in(), use custom_query() for that
        if not data:
            raise ValueError("No data provided for update")

        self.params = data
        set_clauses = [f"{column} = %s" for column in data[0].keys()]

        self.sql = f"UPDATE {self.table} SET {', '.join(set_clauses)}"
        return self

    def delete(self):
        """Start building a DELETE query"""
        self.sql = f"DELETE FROM {self.table}"
        self.params = []
        return self

    def where(self, condition: str, params: Union[list, tuple, List[Dict[str, Any]]] = None):
        """Add WHERE clause to current query"""
        if 'WHERE' in self.sql:
            self.sql += f" AND {condition}"
        else:
            self.sql += f" WHERE {condition}"

        if self.sql.startswith('UPDATE'):
            if not params:
                print("Update queries require where parameters")
                sys.exit()

            # params have to be list of dict just like update()
            if not isinstance(params[0], dict):
                print("params should be in the format List[Dict[str, Any]]")
                sys.exit()

            all_rows = []
            for index, row in enumerate(self.params):
                row_params = (*row.values(), *params[index].values())
                all_rows.append(row_params)
            self.params = all_rows
        else:
            self.params.extend(params or [])
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
                results = self.cursor.fetchall()
                if self._return_dict and not self._native_dict_cursor:
                    columns = [desc[0] for desc in self.cursor.description]
                    results = [dict(zip(columns, row)) for row in results]
                return results
            return self.cursor
        elif self.sql.startswith(('INSERT', 'UPDATE')):
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


class DTMError(Exception):
    pass
