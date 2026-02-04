
import sqlite3
import json
import logging
import time
import pickle
import cloudpickle
from datetime import datetime
from typing import Callable, Any, Dict, Optional, List

logger = logging.getLogger(__name__)

class TaskQueue:
    """
    A persistent, lightweight task queue backed by SQLite.
    Allows for asynchronous processing of heavy tasks (emails, tracking updates).
    """
    
    def __init__(self, db_path: str = "tasks.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initialize the tasks table."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_type TEXT NOT NULL,
                    payload BLOB NOT NULL,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    attempts INTEGER DEFAULT 0,
                    last_error TEXT
                )
            """)
            
    def add_task(self, func: Callable, *args, **kwargs) -> int:
        """
        Add a function call to the queue.
        Uses cloudpickle to serialize the function and arguments.
        """
        task_data = {
            'func': func,
            'args': args,
            'kwargs': kwargs
        }
        serialized_payload = cloudpickle.dumps(task_data)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO tasks (task_type, payload) VALUES (?, ?)",
                (func.__name__, serialized_payload)
            )
            task_id = cursor.lastrowid
            logger.info(f"Task {task_id} added: {func.__name__}")
            return task_id

    def process_pending_tasks(self, limit: int = 10):
        """
        Fetch and execute pending tasks.
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Fetch pending tasks
            cursor.execute("""
                SELECT id, payload, attempts FROM tasks 
                WHERE status = 'pending' 
                ORDER BY created_at ASC 
                LIMIT ?
            """, (limit,))
            
            tasks = cursor.fetchall()
            
            if not tasks:
                return
            
            logger.info(f"Processing {len(tasks)} pending tasks...")
            
            for task in tasks:
                self._execute_task(task['id'], task['payload'], task['attempts'])

    def _execute_task(self, task_id: int, payload: bytes, attempts: int):
        """Execute a single task and update its status."""
        try:
            # Mark as processing
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("UPDATE tasks SET status = 'processing' WHERE id = ?", (task_id,))
            
            # Deserialize and run
            task_data = pickle.loads(payload)
            func = task_data['func']
            args = task_data['args']
            kwargs = task_data['kwargs']
            
            logger.info(f"Executing task {task_id}: {func.__name__}")
            func(*args, **kwargs)
            
            # Mark as completed
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("UPDATE tasks SET status = 'completed' WHERE id = ?", (task_id,))
            logger.info(f"Task {task_id} completed successfully")
            
        except Exception as e:
            logger.error(f"Task {task_id} failed: {e}")
            with sqlite3.connect(self.db_path) as conn:
                status = 'failed' if attempts >= 3 else 'pending'
                conn.execute("""
                    UPDATE tasks 
                    SET status = ?, 
                        attempts = attempts + 1, 
                        last_error = ? 
                    WHERE id = ?
                """, (status, str(e), task_id))
