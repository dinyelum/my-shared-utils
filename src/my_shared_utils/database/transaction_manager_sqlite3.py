#!/usr/bin/env python3
"""
Database transaction script with JSON export and Git push
"""

import json
import sqlite3
import subprocess
import os
from datetime import datetime
from typing import List, Dict, Any


class DatabaseTransactionManager:
    def __init__(self, db_path: str = 'data.db'):
        """Initialize database connection"""
        self.db_path = db_path
        self.conn = None
        self.cursor = None

    def __enter__(self):
        """Context manager entry"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        self.cursor = self.conn.cursor()
        self._create_table_if_not_exists()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - commit and close connection"""
        if exc_type is None:
            self.conn.commit()
        else:
            self.conn.rollback()
        self.conn.close()

    def _create_table_if_not_exists(self):
        """Create sample table if it doesn't exist"""
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        self.cursor.execute(create_table_sql)

    def insert_sample_data(self):
        """Insert sample data into the database"""
        sample_data = [
            ('John Doe', 'john@example.com'),
            ('Jane Smith', 'jane@example.com'),
            ('Bob Johnson', 'bob@example.com')
        ]

        insert_sql = "INSERT INTO records (name, email) VALUES (?, ?)"

        print("Inserting sample data...")
        for name, email in sample_data:
            self.cursor.execute(insert_sql, (name, email))
            print(f"  Inserted: {name}, {email}")

        return len(sample_data)

    def insert_custom_data(self, name: str, email: str):
        """Insert custom data into the database"""
        insert_sql = "INSERT INTO records (name, email) VALUES (?, ?)"
        self.cursor.execute(insert_sql, (name, email))
        print(f"Inserted custom record: {name}, {email}")

    def select_all_rows(self) -> List[Dict[str, Any]]:
        """Select all rows from the database"""
        select_sql = "SELECT * FROM records ORDER BY created_at DESC"
        self.cursor.execute(select_sql)

        rows = []
        for row in self.cursor.fetchall():
            # Convert sqlite3.Row to dictionary
            row_dict = dict(row)
            # Convert datetime to string for JSON serialization
            if 'created_at' in row_dict and isinstance(row_dict['created_at'], str):
                row_dict['created_at'] = row_dict['created_at']
            rows.append(row_dict)

        print(f"Retrieved {len(rows)} records from database")
        return rows

    def save_to_json(self, data: List[Dict[str, Any]],
                     json_file: str = 'database_export.json'):
        """Save data to JSON file"""
        # Add metadata
        export_data = {
            'export_timestamp': datetime.now().isoformat(),
            'database': self.db_path,
            'record_count': len(data),
            'records': data
        }

        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)

        print(f"Data saved to {json_file}")
        return json_file

    def print_to_console(self, data: List[Dict[str, Any]]):
        """Pretty print data to console"""
        print("\n" + "="*50)
        print("DATABASE RECORDS:")
        print("="*50)
        for record in data:
            print(f"ID: {record['id']}")
            print(f"  Name: {record['name']}")
            print(f"  Email: {record['email']}")
            print(f"  Created: {record['created_at']}")
            print("-" * 30)


class GitManager:
    @staticmethod
    def git_add(file_path: str):
        """Stage file for git commit"""
        try:
            subprocess.run(['git', 'add', file_path],
                           check=True, capture_output=True)
            print(f"Git: Staged {file_path}")
        except subprocess.CalledProcessError as e:
            print(f"Git add failed: {e.stderr.decode()}")

    @staticmethod
    def git_commit(message: str):
        """Commit changes to git"""
        try:
            subprocess.run(['git', 'commit', '-m', message],
                           check=True, capture_output=True)
            print(f"Git: Committed with message '{message}'")
        except subprocess.CalledProcessError as e:
            print(f"Git commit failed: {e.stderr.decode()}")

    @staticmethod
    def git_push():
        """Push changes to remote repository"""
        try:
            result = subprocess.run(['git', 'push'],
                                    check=True, capture_output=True, text=True)
            print("Git: Successfully pushed to remote repository")
            print(result.stdout)
        except subprocess.CalledProcessError as e:
            print(f"Git push failed: {e.stderr.decode()}")

    @staticmethod
    def git_status():
        """Check git status"""
        try:
            result = subprocess.run(['git', 'status'],
                                    capture_output=True, text=True)
            print("Git Status:")
            print(result.stdout)
        except Exception as e:
            print(f"Git status failed: {e}")


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
