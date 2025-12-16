#!/usr/bin/env python3
"""
Database transaction script
"""

import config
import mysql.connector as mysqlconn
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
        self.conn = mysqlconn.connect(
            host=config.DB_HOST, user=config.DB_USER, password=config.DB_PASS, database=config.DB_NAME)
        # self.conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        self.cursor = self.conn.cursor()
        # self._create_table_if_not_exists()
        return self

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

        self.sql = f"INSERT {'ignore' if ignore == True else ''} INTO records ({column_list}) VALUES ({placeholders})"
        self.params = values

        if returnself == True:
            return self

        return self.run()

    def on_duplicate_key(self, query, params=None):
        if params is None:
            params = []
        self.sql += f" ON DUPLICATE KEY {query} "
        self.params.append(params)
        return self.run()

    def returnrow(self, returnrow: Union['id', list] = 'id'):
        id = self.cursor.lastrowid
        if returnrow == True:
            return self.select(', '.join(returnrow)).where(f"id={id}")
        return id

    def select(self, columns='*'):
        """Start building a SELECT query"""
        if isinstance(columns, list):
            columns_str = ", ".join(columns)

        self.sql = f"SELECT {columns_str} FROM {self.table}"
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


def main():
    """Main execution function"""
    # Configuration
    DB_FILE = 'sample.db'
    JSON_FILE = 'database_export.json'
    GIT_COMMIT_MESSAGE = f"Database export {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

    print("Starting database transaction process...")
    print("-" * 50)

    # Step 1: Database operations
    try:
        with DatabaseTransactionManager(DB_FILE) as db:
            # Insert sample data
            inserted_count = db.insert_sample_data()

            # Insert additional custom data
            db.insert_custom_data("Alice Brown", "alice@example.com")

            # Select all rows
            all_data = db.select_all_rows()

            # Print to console
            db.print_to_console(all_data)

            # Save to JSON
            json_path = db.save_to_json(all_data, JSON_FILE)

    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return

    print("\n" + "="*50)
    print("Git Operations:")
    print("="*50)

    # Step 2: Git operations
    git = GitManager()

    # Check git status first
    git.git_status()

    # Stage the JSON file
    git.git_add(JSON_FILE)

    # Commit changes
    git.git_commit(GIT_COMMIT_MESSAGE)

    # Push to remote (uncomment when ready)
    # git.git_push()

    print("\n" + "="*50)
    print("Process completed successfully!")
    print(f"Database: {DB_FILE}")
    print(f"JSON Export: {JSON_FILE}")
    print("="*50)


if __name__ == "__main__":
    main()
