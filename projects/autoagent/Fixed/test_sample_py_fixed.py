import os
import json

def process_data(data: Optional[List[Dict[str, Any]]]) -> List[str]:
    """Process a list of dictionaries and return names of users.

    Args:
        data: A list of dictionaries, each containing user information.

    Returns:
        A list of user names where the type is "user".
    """
    if not isinstance(data, list):
        return []
    result = []
    for item in data:
        if not isinstance(item, dict):
            continue
        if item.get("type") == "user" and isinstance(item.get("name"), str):
            result.append(item["name"])
    return result

def calculate_total(items: Optional[List[Dict[str, Any]]]) -> float:
    """Calculate the total cost of items.

    Args:
        items: A list of dictionaries, each containing 'price' and 'quantity'.

    Returns:
        The total cost as a float. Returns 0 if items is None or empty.
    """
    if not items:
        return 0.0
    total = 0.0
    for item in items:
        if not isinstance(item, dict):
            continue
        price = item.get("price")
        quantity = item.get("quantity")
        if isinstance(price, (int, float)) and isinstance(quantity, (int, float)):
            total += float(price) * float(quantity)
    return total

def save_to_file(filename: str, data: Any) -> bool:
    """Save data to a file.

    Args:
        filename: Path to the file.
        data: Data to be saved.

    Returns:
        True if successful, False otherwise.
    """
    try:
        normalized_path = os.path.abspath(filename)
        if not os.path.exists(os.path.dirname(normalized_path)):
            os.makedirs(os.path.dirname(normalized_path), exist_ok=True)
        with open(normalized_path, "w") as f:
            json.dump(data, f)
        return True
    except (IOError, OSError) as e:
        print(f"Error saving file: {e}")
        return False

def load_config(filename: str) -> Dict[str, Any]:
    """Load configuration from a JSON file.

    Args:
        filename: Path to the configuration file.

    Returns:
        A dictionary containing the configuration. Returns empty dict on error.
    """
    try:
        normalized_path = os.path.abspath(filename)
        with open(normalized_path, "r") as f:
            config = json.load(f)
            if not isinstance(config, dict):
                print("Config file does not contain a valid JSON object.")
                return {}
            return config
    except FileNotFoundError:
        print(f"Config file {filename} not found.")
        return {}
    except json.JSONDecodeError:
        print(f"Config file {filename} contains invalid JSON.")
        return {}

class UserManager:
    """Manage a list of users."""

    def __init__(self) -> None:
        self.users: List[Dict[str, str]] = []

    def add_user(self, name: str, email: str) -> bool:
        """Add a new user.

        Args:
            name: User's name.
            email: User's email.

        Returns:
            True if user was added, False if user with email already exists or data is invalid.
        """
        if not name or not isinstance(name, str) or not email or not isinstance(email, str):
            raise ValueError("Name and email must be non-empty strings.")
        if self.find_user(email) is not None:
            return False
        self.users.append({"name": name, "email": email})
        return True

    def find_user(self, email: str) -> Optional[Dict[str, str]]:
        """Find a user by email.

        Args:
            email: Email to search for.

        Returns:
            The user dictionary if found, None otherwise.
        """
        if not email or not isinstance(email, str):
            return None
        for user in self.users:
            if user.get("email") == email:
                return user
        return None

    def delete_user(self, email: str) -> bool:
        """Delete a user by email.

        Args:
            email: Email of the user to delete.

        Returns:
            True if user was deleted, False otherwise.
        """
        if not email or not isinstance(email, str):
            return False
        new_users = [user for user in self.users if user.get("email") != email]
        if len(new_users) == len(self.users):
            return False
        self.users = new_users
        return True