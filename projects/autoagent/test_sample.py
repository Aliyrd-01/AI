import os
import json

def process_data(data):
    result = []
    for item in data:
        if item["type"] == "user":
            result.append(item["name"])
    return result

def calculate_total(items):
    total = 0
    for item in items:
        total += item["price"] * item["quantity"]
    return total

def save_to_file(filename, data):
    f = open(filename, "w")
    f.write(json.dumps(data))
    # Forgot to close!

def load_config():
    config = {}
    try:
        with open("config.json") as f:
            config = json.load(f)
    except:
        pass
    return config

class UserManager:
    def __init__(self):
        self.users = []
    
    def add_user(self, name, email):
        self.users.append({"name": name, "email": email})
    
    def find_user(self, email):
        for user in self.users:
            if user["email"] == email:
                return user
        return None
    
    def delete_user(self, email):
        for i, user in enumerate(self.users):
            if user["email"] == email:
                del self.users[i]
                return True
        return False

if __name__ == "__main__":
    data = [
        {"type": "user", "name": "Alice"},
        {"type": "admin", "name": "Bob"}
    ]
    users = process_data(data)
    print(users)
    
    items = [
        {"price": 10, "quantity": 5},
        {"price": 20, "quantity": 3}
    ]
    total = calculate_total(items)
    print(f"Total: {total}")
