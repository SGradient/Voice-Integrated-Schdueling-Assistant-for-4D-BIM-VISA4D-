import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

# Import the NavisworksAPI class
from navisworks_api import NavisworksAPI

class TaskManager:
    def __init__(self, client_id: str = None, client_secret: str = None):
        self.task_statuses = {}
        self.task_dates = {}
        self.task_mapping = self._load_task_mapping()
        
        # Initialize the NavisworksAPI client
        self.api = NavisworksAPI()
        
        # Store credentials for token refresh if provided
        self.client_id = client_id
        self.client_secret = client_secret
        
        # Attempt initial authentication if credentials are provided
        if client_id and client_secret:
            self.authenticate(client_id, client_secret)
            
        # Load saved task state if available
        self._load_task_state()

    def authenticate(self, client_id: str, client_secret: str) -> bool:
        """Authenticate with the Navisworks API"""
        try:
            success = self.api.authenticate(client_id, client_secret)
            if success:
                # Store credentials for future use
                self.client_id = client_id
                self.client_secret = client_secret
                logging.info("Authentication successful")
            else:
                logging.error("Authentication failed")
            return success
        except Exception as e:
            logging.error(f"Authentication error: {e}")
            return False

    def _load_task_mapping(self) -> Dict[str, str]:
        try:
            with open('task_mapping.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            default_mapping = {
                "flooring": "Flooring Installation",
                "roofing": "Roofing",
                "concrete": "Concrete Pouring",
                "painting": "Painting and Decorating",
                "plumbing": "Plumbing Installation",
                "electrical": "Electrical Wiring",
                "hvac": "HVAC Installation",
                "drywall": "Drywall Installation"
            }
            self._save_task_mapping(default_mapping)
            return default_mapping
    
    def _load_task_state(self):
        """Load task state from a JSON file if it exists"""
        try:
            if Path('task_state.json').exists():
                with open('task_state.json', 'r') as f:
                    state = json.load(f)
                    self.task_statuses = state.get('statuses', {})
                    self.task_dates = state.get('dates', {})
                    logging.info("Task state loaded successfully")
        except Exception as e:
            logging.error(f"Error loading task state: {e}")
    
    def _save_task_state(self):
        """Save current task state to a JSON file"""
        try:
            state = {
                'statuses': self.task_statuses,
                'dates': self.task_dates
            }
            with open('task_state.json', 'w') as f:
                json.dump(state, f, indent=4)
        except Exception as e:
            logging.error(f"Error saving task state: {e}")
            
    def _save_task_mapping(self, mapping: Dict[str, str]):
        try:
            with open('task_mapping.json', 'w') as f:
                json.dump(mapping, f, indent=4)
        except Exception as e:
            logging.error(f"Error saving task mapping: {e}")

    def update_task_status(self, task_name: str, status: str) -> bool:
        try:
            # Update local state
            self.task_statuses[task_name] = status
            self._save_task_state()

            # Map status to Navisworks format
            navisworks_status = self.api.map_vis4d_status_to_navisworks(status)
            
            # Use NavisworksAPI to update the task
            result = self.api.update_task(
                task_name=task_name,
                updates={'status': navisworks_status},
                client_id=self.client_id,
                client_secret=self.client_secret
            )
            
            if result.get('success', False):
                logging.info(f"Successfully updated status of '{task_name}' to '{status}'")
                return True
            else:
                logging.error(f"Failed to update task status: {result.get('error')}")
                return False
                
        except Exception as e:
            logging.error(f"Error updating task status: {e}")
            return False

    def update_task_date(self, task_name: str, date: str) -> bool:
        try:
            # Update local state
            self.task_dates[task_name] = date
            self._save_task_state()

            # Parse and format the date
            date_obj = datetime.strptime(date, "%B %d, %Y")
            
            # Use NavisworksAPI to update the task
            result = self.api.update_task(
                task_name=task_name,
                updates={'start_date': date_obj},
                client_id=self.client_id,
                client_secret=self.client_secret
            )
            
            if result.get('success', False):
                logging.info(f"Successfully updated date of '{task_name}' to '{date}'")
                return True
            else:
                logging.error(f"Failed to update task date: {result.get('error')}")
                return False
                
        except Exception as e:
            logging.error(f"Error updating task date: {e}")
            return False

    def create_task(self, task_name: str, start_date: datetime, end_date: datetime) -> bool:
        try:
            # Use NavisworksAPI to create the task
            result = self.api.create_task(
                task_name=task_name,
                task_type="Construct",  # Default task type
                start_date=start_date,
                end_date=end_date,
                client_id=self.client_id,
                client_secret=self.client_secret
            )
            
            if result.get('success', False):
                # Update local state
                self.task_dates[task_name] = start_date.strftime("%B %d, %Y")
                self.task_statuses[task_name] = "not started"
                self._save_task_state()
                
                logging.info(f"Successfully created task '{task_name}'")
                return True
            else:
                logging.error(f"Failed to create task: {result.get('error')}")
                return False
                
        except Exception as e:
            logging.error(f"Error creating task: {e}")
            return False

    def delete_task(self, task_name: str) -> bool:
        try:
            # Delete from local state
            self.task_statuses.pop(task_name, None)
            self.task_dates.pop(task_name, None)
            self._save_task_state()

            # Use NavisworksAPI to delete the task
            result = self.api.delete_task(
                task_name=task_name,
                client_id=self.client_id,
                client_secret=self.client_secret
            )
            
            if result.get('success', False):
                logging.info(f"Successfully deleted task '{task_name}'")
                return True
            else:
                logging.error(f"Failed to delete task: {result.get('error')}")
                return False
                
        except Exception as e:
            logging.error(f"Error deleting task: {e}")
            return False