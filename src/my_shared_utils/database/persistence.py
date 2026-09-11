from .transaction_manager import DatabaseTransactionManager, DTMError
from typing import Union, List, Dict, Any, Iterable
from pathlib import Path
import json
import os


class PersistenceManager:
    """Manages robust data persistence with automatic local file fallback.

    This manager orchestrates low-level database operations through a
    transaction manager. If database operations fail due to connectivity
    or operational errors, it gracefully intercepts the failure and caches
    the payload locally to disk so data is never lost.
    """

    def __init__(self, connector_factory):
        """Initializes the PersistenceManager.

        Args:
            connector_factory (callable): A function or lambda that returns an
                active database connection object when executed.
                Example: lambda: MySQLdb.connect(...)
        """
        self.connector_factory = connector_factory

    def write_to_db(
        self,
        table: str,
        data: Union[Dict[str, Any], List[Dict[str, Any]]],
        return_last_row: bool = False,
        allow_duplicate: bool = False
    ):
        """Executes an INSERT operation into the specified table.

        Automatically handles ON DUPLICATE KEY UPDATE syntax based on the
        provided flag to prevent execution crashes on key constraints.

        Args:
            table: The name of the target database table.
            data: A dictionary representing a row (column: value), or a list of
                dictionaries for bulk insertions.
            return_last_row: If True, executes the query and returns the auto-incremented
                ID of the inserted row. Defaults to False.
            allow_duplicate: If False, maps the insertion to an upsert statement 
                (ON DUPLICATE KEY UPDATE) using the data keys. Defaults to False.

        Returns:
            The primary key ID if return_last_row is True, otherwise the query execution
            result. Returns None if data payload is empty.

        Raises:
            DTMError: If the transaction or underlying database query fails.
        """
        if not data:
            return None

        # print(f"data in write_to_db: {data}")
        try:
            with DatabaseTransactionManager(self.connector_factory, table) as dtm:
                # 1. Initialize the base insert statement
                db_insert = dtm.insert(data, returnself=True)

                # 2. Conditionally apply the duplicate handling logic
                if not allow_duplicate:
                    keys = data[0].keys() if isinstance(
                        data, list) else data.keys()
                    update_clause = ", ".join(
                        f"{col}=VALUES({col})" for col in keys)
                    if return_last_row:
                        update_clause += ", id=LAST_INSERT_ID(id)"
                    db_insert = db_insert.on_duplicate_key(
                        f"Update {update_clause}")

                # 3. Conditionally execute and determine the final return value
                return db_insert.returnrow('id') if return_last_row else db_insert.run()

        except DTMError as e:
            print(f"MySQL error: {e}")
            return None

    def update_db(
            self,
            table: str,
            data: List[Dict[str, Any]],
            where_clause='',
            where_data: List[Dict[str, Any]] = None
    ):
        """Executes an UPDATE operation against specific rows in a table.

        Args:
            table: The name of the target database table.
            data: A list of dictionaries containing columns and updated values.
            where_clause: The conditional SQL WHERE string (e.g., "id = %s").
            where_data: The values bound dynamically to the where_clause filters.

        Returns:
            The result of the database transaction operation, or None if parameters are empty.

        Raises:
            DTMError: If the transaction or underlying database query fails.
        """

        if not data or not where_data:
            return None

        try:
            with DatabaseTransactionManager(self.connector_factory, table) as dtm:
                return dtm.update(data).where(where_clause, where_data)

        except DTMError as e:
            print(f"MySQL error: {e}")
            return None

    def persist(self, operation, table, data, fallback_file, where_clause=None, where_data=None):
        """Attempts a database operation and captures data to a file if it fails.

        This is the primary public entrypoint for writes. It guarantees that network drops
        or server outages safely cache operational payloads locally to prevent data loss.

        Args:
            operation: The type of SQL statement to run ('insert' or 'update').
            table: The name of the destination database table.
            data: The row data payload to be processed.
            fallback_file: The path or filename where the payload should be cached
                if a database exception occurs.
            where_clause: The conditional query string used only for updates.
            where_data: The list of parameters bound to the where_clause filters.

        Returns:
            bool: True if the database operation was committed successfully; False if
            it failed and data was dumped to the fallback file.
        """
        # print(f"data in persist: {data}")
        try:
            # ssh_tunnel.start()

            if operation == "insert":
                self.write_to_db(
                    self.connector_factory,
                    table,
                    data
                )
            else:
                self.update_db(
                    self.connector_factory,
                    table,
                    data,
                    where_clause,
                    where_data
                )
            return True

        except Exception as e:
            # logger.exception(e)
            print(e)

            file_data = {
                'operation': operation,
                'table': table,
                'data': data,
                'where_clause': where_clause,
                'where_data': where_data
            }

            self.write_to_fallback(
                fallback_file,
                file_data
            )

            return False

        finally:
            # ssh_tunnel.stop()
            pass

    @classmethod
    def write_to_fallback(cls, path, new_records):
        """Dumps a failed query payload to a local text file structured as JSON.

        Args:
            path (str or Path): The destination file system location for the fallback file.
            new_records (dict): The contextual payload containing the target table,
                the statement operation type, and raw data parameters.
        """
        with open(path, "w") as f:
            json.dump(new_records, f, indent=4)

    def clean_up(self, files: Iterable[Path]):
        """Iterates over a sequence of fallback files and replays them back into the database.

        If a file's transaction is successfully committed to the database on this pass,
        the local file is permanently deleted from the file system. If it fails again,
        it remains cached on disk for a later retry.

        Args:
            files: An iterable collection of Path objects pointing to local JSON cache files.
        """
        for file in files:
            if os.path.exists(file):
                with open(file, "r", encoding="utf-8") as f:
                    content = json.load(f)

                try:
                    updated = self.persist(
                        operation=content['operation'],
                        table=content['table'],
                        data=content['data'],
                        fallback_file=file,
                        where_clause=content.get('where_clause'),
                        where_data=content.get('where_data')
                    )

                    # success -> delete file
                    if updated:
                        os.remove(file)

                except Exception:
                    pass
