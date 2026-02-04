
import unittest
import time
import os
import shutil
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.retry_handler import RetryHandler
from src.workers.task_queue import TaskQueue

# --- Mock for Retry Logic ---
class MockAPI:
    def __init__(self):
        self.attempts = 0
    
    @RetryHandler.with_retry(max_retries=3, base_delay=0.1, jitter=False)
    def flaky_method(self, fail_times=3):
        self.attempts += 1
        if self.attempts <= fail_times:
            print(f"MockAPI: Attempt {self.attempts} failed!")
            raise ConnectionError("Mock Connection Exception")
        print(f"MockAPI: Attempt {self.attempts} succeeded!")
        return "Success"

# --- Mock for Task Queue ---
def dummy_worker_task(msg):
    # This function needs to be importable or picklable. 
    # Since we use cloudpickle, it handles lambda/local functions well usually, 
    # but for stability in test, top level is best.
    print(f"WORKER EXECUTING: {msg}")
    return f"Processed {msg}"

class TestRobustness(unittest.TestCase):
    
    def test_retry_logic(self):
        print("\n--- Testing Retry Logic ---")
        api = MockAPI()
        # Should fail 3 times then succeed on 4th attempt
        # Retry logic: max_retries=3 means 1 initial + 3 retries = 4 total attempts max.
        # Wait, max_retries=3 usually means we try 1 time, then retry 3 times. 
        # Let's verify the implementation: "attempt <= max_retries" loop starts at 0. 
        # attempt 0 -> run (fail). attempt 1 -> run (fail). attempt 2 -> run (fail). attempt 3 -> run (success). 
        # Total attempts = 4. 
        
        result = api.flaky_method(fail_times=2) 
        self.assertEqual(result, "Success")
        self.assertEqual(api.attempts, 3) # 1 initial + 2 retries
        
    def test_task_queue(self):
        print("\n--- Testing Task Queue ---")
        db_path = "test_tasks.db"
        if os.path.exists(db_path):
            try:
                os.remove(db_path)
            except OSError:
                pass
            
        queue = TaskQueue(db_path=db_path)
        
        try:
            # Add task
            task_id = queue.add_task(dummy_worker_task, "Hello World")
            print(f"Added task {task_id}")
            
            # Verify pending
            import sqlite3
            with sqlite3.connect(db_path) as conn:
                row = conn.execute("SELECT status FROM tasks WHERE id = ?", (task_id,)).fetchone()
                self.assertEqual(row[0], 'pending')
                
            # Process
            queue.process_pending_tasks()
            
            # Verify completed
            with sqlite3.connect(db_path) as conn:
                row = conn.execute("SELECT status FROM tasks WHERE id = ?", (task_id,)).fetchone()
                self.assertEqual(row[0], 'completed')
                
        finally:
            # Cleanup
            del queue # Ensure object is deleted
            import gc
            gc.collect() # Force garbage collection
            time.sleep(0.5) # Wait for file lock release
            if os.path.exists(db_path):
                try:
                    os.remove(db_path)
                except OSError as e:
                    print(f"Warning: Could not remove test db: {e}")

if __name__ == '__main__':
    unittest.main()
