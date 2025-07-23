import requests
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone, timedelta
from urllib.parse import quote

class NavisworksAPI:
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url
        self.endpoints = {
            'create_task': '/api/timeliner/task',
            'update_task': '/api/timeliner/task/update',
            'delete_task': '/api/timeliner/task/delete',
            'auth_token': '/api/auth/token',
            'auth_status': '/api/auth/status'
        }
        self.headers = {'Content-Type': 'application/json'}
        self.access_token = None
        self.token_expiry = None

    def authenticate(self, client_id: str, client_secret: str) -> bool:
        """Authenticate with the Navisworks API using APS credentials"""
        try:
            payload = {
                'clientId': client_id,
                'clientSecret': client_secret
            }
            response = requests.post(
                f"{self.base_url}{self.endpoints['auth_token']}",
                json=payload,
                headers=self.headers
            )
            response.raise_for_status()
            auth_data = response.json()
            
            if auth_data.get('success'):
                self.access_token = auth_data.get('token')
                # Handle the ISO format date string more robustly
                expiry_str = auth_data.get('expiresAt')
                try:
                    # Try to parse using fromisoformat with potential adjustment
                    if 'Z' in expiry_str:
                        expiry_str = expiry_str.replace('Z', '+00:00')
                    
                    # Handle microsecond precision if needed
                    if '.' in expiry_str:
                        parts = expiry_str.split('.')
                        microseconds = parts[1].split('+')[0]
                        if len(microseconds) > 6:
                            # Truncate to 6 digits for microseconds
                            microseconds = microseconds[:6]
                            expiry_str = parts[0] + '.' + microseconds + '+00:00'
                    
                    self.token_expiry = datetime.fromisoformat(expiry_str)
                except ValueError:
                    # Fallback: use a more flexible approach with strptime
                    import re
                    import pytz
                    
                    # Extract date and time part
                    match = re.match(r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})(\.\d+)?([+-]\d{2}:\d{2}|Z)?', expiry_str)
                    if match:
                        date_part = match.group(1)
                        self.token_expiry = datetime.strptime(date_part, "%Y-%m-%dT%H:%M:%S")
                        self.token_expiry = self.token_expiry.replace(tzinfo=pytz.UTC)
                    else:
                        # Last resort: set expiry to 1 hour from now
                        self.token_expiry = datetime.now(timezone.utc) + timedelta(hours=1)
                        logging.warning(f"Could not parse token expiry date: {expiry_str}. Using default 1 hour expiry.")
                
                # Add token to headers for future requests
                self.headers['Authorization'] = f"Bearer {self.access_token}"
                logging.info(f"Authentication successful. Token expires at {self.token_expiry}")
                return True
            else:
                logging.error("Authentication failed: No success indicator in response")
                return False
        except Exception as e:
            logging.error(f"Authentication error: {str(e)}")
            return False

    def check_auth_status(self) -> Dict[str, Any]:
        """Check the current authentication status"""
        try:
            response = requests.get(
                f"{self.base_url}{self.endpoints['auth_status']}",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logging.error(f"Error checking authentication status: {str(e)}")
            return {"authenticated": False, "error": str(e)}

    def is_token_valid(self) -> bool:
        """Check if the current token is valid and not expired"""
        if not self.access_token or not self.token_expiry:
            return False
        
        # Add a 5-minute buffer to avoid using a token that's about to expire
        now = datetime.now(timezone.utc)
        return now < self.token_expiry

    def ensure_authenticated(self, client_id: str = None, client_secret: str = None) -> bool:
        """Ensure we have a valid authentication token"""
        if self.is_token_valid():
            return True
            
        if client_id and client_secret:
            return self.authenticate(client_id, client_secret)
        else:
            logging.error("Token expired and no credentials provided for re-authentication")
            return False

    def create_task(self, task_name: str, task_type: str, start_date: datetime, end_date: datetime, 
                   client_id: str = None, client_secret: str = None) -> Dict[str, Any]:
        """Create a new task in Navisworks Timeliner"""
        # Ensure we're authenticated before making the request
        if not self.ensure_authenticated(client_id, client_secret):
            return {"success": False, "error": "Not authenticated"}
            
        try:
            payload = {
                'taskName': task_name,
                'taskType': task_type,
                'plannedStartDate': start_date.strftime("%Y-%m-%d"),
                'plannedEndDate': end_date.strftime("%Y-%m-%d")
            }
            response = requests.post(
                f"{self.base_url}{self.endpoints['create_task']}", 
                json=payload,
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logging.error(f"Error creating Navisworks task: {str(e)}")
            return {"success": False, "error": str(e)}

    def update_task(self, task_name: str, updates: Dict[str, Any], 
                    client_id: str = None, client_secret: str = None) -> Dict[str, Any]:
        """Update an existing task in Navisworks Timeliner"""
        # Ensure we're authenticated before making the request
        if not self.ensure_authenticated(client_id, client_secret):
            return {"success": False, "error": "Not authenticated"}
            
        try:
            # Format date strings if datetime objects are provided
            start_date = updates.get('start_date')
            if start_date and isinstance(start_date, datetime):
                start_date = start_date.strftime("%Y-%m-%d")
                
            end_date = updates.get('end_date')
            if end_date and isinstance(end_date, datetime):
                end_date = end_date.strftime("%Y-%m-%d")
                
            payload = {
                'TaskName': task_name,
                'Updates': {
                    'NewName': updates.get('name'),
                    'NewStartDate': start_date,
                    'NewEndDate': end_date,
                    'NewStatus': updates.get('status')
                }
            }
            response = requests.put(
                f"{self.base_url}{self.endpoints['update_task']}", 
                json=payload,
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logging.error(f"Error updating Navisworks task: {str(e)}")
            return {"success": False, "error": str(e)}

    def delete_task(self, task_name: str, client_id: str = None, client_secret: str = None) -> Dict[str, Any]:
        """Delete a task from Navisworks Timeliner"""
        # Ensure we're authenticated before making the request
        if not self.ensure_authenticated(client_id, client_secret):
            return {"success": False, "error": "Not authenticated"}
            
        try:
            encoded_task_name = quote(task_name)
            response = requests.delete(
                f"{self.base_url}{self.endpoints['delete_task']}/{encoded_task_name}",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logging.error(f"Error deleting Navisworks task: {str(e)}")
            return {"success": False, "error": str(e)}

    def map_vis4d_status_to_navisworks(self, vis4d_status: str) -> str:
        """Map VIS4D status to Navisworks status"""
        status_mapping = {
            'complete': 'Completed',
            'in progress': 'In Progress',
            'on hold': 'On Hold',
            'not started': 'Not Started',
            'suspended': 'Suspended'
        }
        return status_mapping.get(vis4d_status.lower(), 'Not Started')
