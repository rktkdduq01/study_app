#!/usr/bin/env python3
"""
Simple HTTP server for testing - no external dependencies required
"""

import http.server
import json
import urllib.parse
import uuid
from datetime import datetime
from typing import Dict, List, Any

# In-memory storage
users_db: Dict[str, Dict[str, Any]] = {}
products_db: Dict[str, Dict[str, Any]] = {}
orders_db: Dict[str, Dict[str, Any]] = {}
characters_db: Dict[str, Dict[str, Any]] = {}

class APIHandler(http.server.BaseHTTPRequestHandler):
    def normalize_path(self, path):
        """Normalize path by removing /api/v1 prefix if present"""
        if path.startswith('/api/v1'):
            return path[7:]  # Remove '/api/v1' prefix
        return path
    
    def do_GET(self):
        """Handle GET requests"""
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path
        normalized_path = self.normalize_path(path)
        
        # Route to appropriate handler
        routes = {
            '/': self.handle_root,
            '/health': self.handle_health,
            '/users': self.handle_get_users,
            '/users/me': self.handle_get_current_user,
            '/products': self.handle_get_products,
            '/orders': self.handle_get_orders,
            '/characters': self.handle_get_characters,
        }
        
        # Check for ID-based routes
        if normalized_path == '/users/me':
            self.handle_get_current_user()
            return
        elif normalized_path == '/characters/me':
            self.handle_get_my_character()
            return
        elif normalized_path.startswith('/users/') and len(normalized_path.split('/')) == 3:
            self.handle_get_user(normalized_path.split('/')[2])
            return
        elif normalized_path.startswith('/characters/') and len(normalized_path.split('/')) == 3:
            self.handle_get_character(normalized_path.split('/')[2])
            return
        elif normalized_path.startswith('/products/') and len(normalized_path.split('/')) == 3:
            self.handle_get_product(normalized_path.split('/')[2])
            return
        elif normalized_path.startswith('/orders/') and len(normalized_path.split('/')) == 3:
            self.handle_get_order(normalized_path.split('/')[2])
            return
        
        # Use route handler or 404
        handler = routes.get(normalized_path, self.handle_not_found)
        handler()
    
    def do_POST(self):
        """Handle POST requests"""
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path
        normalized_path = self.normalize_path(path)
        
        print(f"POST request - Original path: {path}, Normalized: {normalized_path}")
        
        # Read body
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)
        
        # Route to appropriate handler
        routes = {
            '/users': lambda: self.handle_create_user(body),
            '/users/register': lambda: self.handle_register_user(body),
            '/auth/token': lambda: self.handle_login(body),
            '/products': lambda: self.handle_create_product(body),
            '/orders': lambda: self.handle_create_order(body),
            '/characters': lambda: self.handle_create_character(body),
            '/characters/': lambda: self.handle_create_character(body),
        }
        
        handler = routes.get(normalized_path, self.handle_not_found)
        if handler:
            handler()
        else:
            print(f"No handler found for path: {normalized_path}")
            self.handle_not_found()
    
    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self.send_response(200)
        self.send_cors_headers()
        self.end_headers()
    
    def send_cors_headers(self):
        """Send CORS headers"""
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
    
    def send_json_response(self, data: Any, status: int = 200):
        """Send JSON response"""
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_cors_headers()
        self.end_headers()
        self.wfile.write(json.dumps(data, default=str).encode())
    
    def handle_root(self):
        """Handle root endpoint"""
        data = {
            "message": "Welcome to EduRPG Simple API Server",
            "version": "1.0.0",
            "endpoints": {
                "users": "/users",
                "products": "/products", 
                "orders": "/orders",
                "health": "/health"
            }
        }
        self.send_json_response(data)
    
    def handle_health(self):
        """Handle health check"""
        data = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat()
        }
        self.send_json_response(data)
    
    def handle_get_users(self):
        """Get all users"""
        users = list(users_db.values())
        self.send_json_response(users)
    
    def handle_get_user(self, user_id: str):
        """Get specific user"""
        user = users_db.get(user_id)
        if user:
            self.send_json_response(user)
        else:
            self.send_json_response({"error": "User not found"}, 404)
    
    def handle_get_current_user(self):
        """Get current user from token"""
        try:
            # Get Authorization header
            auth_header = self.headers.get('Authorization', '')
            if not auth_header.startswith('Bearer '):
                self.send_json_response({"detail": "Not authenticated"}, 401)
                return
            
            token = auth_header.replace('Bearer ', '')
            
            # Extract user ID from token (in production, verify JWT properly)
            if token.startswith('fake-jwt-token-'):
                parts = token.split('-')
                if len(parts) >= 5:
                    user_id = parts[3]
                    user = users_db.get(user_id)
                    if user:
                        # Return user without password
                        response_user = {k: v for k, v in user.items() if k != "password"}
                        self.send_json_response(response_user)
                        return
            
            self.send_json_response({"detail": "Invalid token"}, 401)
        except Exception as e:
            print(f"Get current user error: {str(e)}")
            self.send_json_response({"detail": str(e)}, 400)
    
    def handle_create_user(self, body: bytes):
        """Create new user"""
        try:
            data = json.loads(body.decode())
            user_id = str(uuid.uuid4())
            user = {
                "id": user_id,
                "username": data.get("username"),
                "email": data.get("email"),
                "full_name": data.get("full_name"),
                "created_at": datetime.now().isoformat()
            }
            users_db[user_id] = user
            self.send_json_response(user, 201)
        except Exception as e:
            self.send_json_response({"error": str(e)}, 400)
    
    def handle_register_user(self, body: bytes):
        """Handle user registration"""
        try:
            data = json.loads(body.decode())
            print(f"Registration request: {data}")
            
            # Validate required fields
            required_fields = ["username", "email", "password", "full_name"]
            for field in required_fields:
                if not data.get(field):
                    self.send_json_response({"detail": f"{field} is required"}, 400)
                    return
            
            # Check if username already exists
            for user in users_db.values():
                if user.get("username") == data.get("username"):
                    self.send_json_response({"detail": "Username already exists"}, 400)
                    return
            
            # Check if email already exists
            for user in users_db.values():
                if user.get("email") == data.get("email"):
                    self.send_json_response({"detail": "Email already registered"}, 400)
                    return
            
            # Create new user
            user_id = str(uuid.uuid4())
            user = {
                "id": user_id,
                "username": data.get("username"),
                "email": data.get("email"),
                "full_name": data.get("full_name"),
                "role": data.get("role", "student"),
                "password": data.get("password"),  # In production, this should be hashed
                "is_active": True,
                "is_verified": False,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            users_db[user_id] = user
            
            # Return user without password
            response_user = {k: v for k, v in user.items() if k != "password"}
            self.send_json_response(response_user, 201)
            
        except json.JSONDecodeError:
            self.send_json_response({"detail": "Invalid JSON format"}, 400)
        except Exception as e:
            print(f"Registration error: {str(e)}")
            self.send_json_response({"detail": str(e)}, 400)
    
    def handle_login(self, body: bytes):
        """Handle user login"""
        try:
            # Parse form data (application/x-www-form-urlencoded)
            body_str = body.decode('utf-8')
            params = urllib.parse.parse_qs(body_str)
            
            username = params.get('username', [''])[0]
            password = params.get('password', [''])[0]
            
            print(f"Login attempt for username: {username}")
            
            # Find user by username
            user = None
            for u in users_db.values():
                if u.get("username") == username:
                    user = u
                    break
            
            if not user:
                self.send_json_response({"detail": "Invalid username or password"}, 401)
                return
            
            # Check password (in production, use proper password hashing)
            if user.get("password") != password:
                self.send_json_response({"detail": "Invalid username or password"}, 401)
                return
            
            # Generate token (in production, use proper JWT)
            token = f"fake-jwt-token-{user['id']}-{uuid.uuid4()}"
            
            # Return login response
            response = {
                "access_token": token,
                "token_type": "bearer",
                "user": {k: v for k, v in user.items() if k != "password"}
            }
            self.send_json_response(response)
            
        except Exception as e:
            print(f"Login error: {str(e)}")
            self.send_json_response({"detail": str(e)}, 400)
    
    def handle_get_products(self):
        """Get all products"""
        products = list(products_db.values())
        self.send_json_response(products)
    
    def handle_get_product(self, product_id: str):
        """Get specific product"""
        product = products_db.get(product_id)
        if product:
            self.send_json_response(product)
        else:
            self.send_json_response({"error": "Product not found"}, 404)
    
    def handle_create_product(self, body: bytes):
        """Create new product"""
        try:
            data = json.loads(body.decode())
            product_id = str(uuid.uuid4())
            product = {
                "id": product_id,
                "name": data.get("name"),
                "description": data.get("description"),
                "price": data.get("price", 0),
                "stock": data.get("stock", 0),
                "created_at": datetime.now().isoformat()
            }
            products_db[product_id] = product
            self.send_json_response(product, 201)
        except Exception as e:
            self.send_json_response({"error": str(e)}, 400)
    
    def handle_get_orders(self):
        """Get all orders"""
        orders = list(orders_db.values())
        self.send_json_response(orders)
    
    def handle_get_order(self, order_id: str):
        """Get specific order"""
        order = orders_db.get(order_id)
        if order:
            self.send_json_response(order)
        else:
            self.send_json_response({"error": "Order not found"}, 404)
    
    def handle_create_order(self, body: bytes):
        """Create new order"""
        try:
            data = json.loads(body.decode())
            order_id = str(uuid.uuid4())
            order = {
                "id": order_id,
                "user_id": data.get("user_id"),
                "products": data.get("products", []),
                "total": data.get("total", 0),
                "status": data.get("status", "pending"),
                "created_at": datetime.now().isoformat()
            }
            orders_db[order_id] = order
            self.send_json_response(order, 201)
        except Exception as e:
            self.send_json_response({"error": str(e)}, 400)
    
    def handle_get_characters(self):
        """Get all characters"""
        characters = list(characters_db.values())
        self.send_json_response(characters)
    
    def handle_get_character(self, character_id: str):
        """Get specific character"""
        character = characters_db.get(character_id)
        if character:
            self.send_json_response(character)
        else:
            self.send_json_response({"detail": "Character not found"}, 404)
    
    def handle_get_my_character(self):
        """Get current user's character"""
        try:
            # Get current user from token
            auth_header = self.headers.get('Authorization', '')
            user_id = None
            
            if auth_header.startswith('Bearer '):
                token = auth_header.replace('Bearer ', '')
                if token.startswith('fake-jwt-token-'):
                    parts = token.split('-')
                    if len(parts) >= 5:
                        user_id = parts[3]
            
            if not user_id:
                self.send_json_response({"detail": "Not authenticated"}, 401)
                return
            
            # Find character for this user
            for character in characters_db.values():
                if character.get("user_id") == user_id:
                    self.send_json_response(character)
                    return
            
            # No character found
            self.send_json_response({"detail": "Character not found"}, 404)
            
        except Exception as e:
            print(f"Get my character error: {str(e)}")
            self.send_json_response({"detail": str(e)}, 400)
    
    def handle_create_character(self, body: bytes):
        """Create new character"""
        try:
            data = json.loads(body.decode())
            print(f"Character creation request: {data}")
            
            # Get current user from token
            auth_header = self.headers.get('Authorization', '')
            user_id = None
            
            if auth_header.startswith('Bearer '):
                token = auth_header.replace('Bearer ', '')
                if token.startswith('fake-jwt-token-'):
                    parts = token.split('-')
                    if len(parts) >= 5:
                        user_id = parts[3]
            
            if not user_id:
                self.send_json_response({"detail": "Authentication required"}, 401)
                return
            
            # Create character
            character_id = str(uuid.uuid4())
            character = {
                "id": character_id,
                "user_id": user_id,
                "name": data.get("name", "Hero"),
                "class": data.get("class", "warrior"),
                "level": 1,
                "experience": 0,
                "health": 100,
                "max_health": 100,
                "mana": 50,
                "max_mana": 50,
                "strength": data.get("strength", 10),
                "intelligence": data.get("intelligence", 10),
                "agility": data.get("agility", 10),
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            characters_db[character_id] = character
            self.send_json_response(character, 201)
            
        except json.JSONDecodeError:
            self.send_json_response({"detail": "Invalid JSON format"}, 400)
        except Exception as e:
            print(f"Character creation error: {str(e)}")
            self.send_json_response({"detail": str(e)}, 400)
    
    def handle_not_found(self):
        """Handle 404"""
        print(f"404 Not Found: {self.path}")
        self.send_json_response({"detail": f"Not found: {self.path}"}, 404)
    
    def log_message(self, format, *args):
        """Custom logging"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {self.address_string()} - {format % args}")

def initialize_sample_data():
    """Add sample data"""
    # Sample user
    user_id = "1"
    users_db[user_id] = {
        "id": user_id,
        "username": "john_doe",
        "email": "john@example.com",
        "full_name": "John Doe",
        "created_at": datetime.now().isoformat()
    }
    
    # Sample products
    products = [
        {"id": "1", "name": "Quest Book", "description": "Learn programming through quests", "price": 29.99, "stock": 100},
        {"id": "2", "name": "Code Sword", "description": "Debug your code with style", "price": 49.99, "stock": 50},
        {"id": "3", "name": "Algorithm Shield", "description": "Master data structures", "price": 39.99, "stock": 75}
    ]
    
    for product in products:
        product["created_at"] = datetime.now().isoformat()
        products_db[product["id"]] = product

def run_server(port=8000):
    """Run the HTTP server"""
    initialize_sample_data()
    
    server_address = ('', port)
    httpd = http.server.HTTPServer(server_address, APIHandler)
    
    print(f"=== EduRPG Simple API Server ===")
    print(f"Server running on http://localhost:{port}")
    print(f"\nAPI endpoints:")
    print(f"  - http://localhost:{port}/                    (Server info)")
    print(f"  - http://localhost:{port}/health              (Health check)")
    print(f"  - http://localhost:{port}/users               (Get all users)")
    print(f"  - http://localhost:{port}/users/register      (Register new user)")
    print(f"  - http://localhost:{port}/users/me            (Get current user)")
    print(f"  - http://localhost:{port}/auth/token          (Login)")
    print(f"  - http://localhost:{port}/characters          (Character management)")
    print(f"  - http://localhost:{port}/products            (Product management)")
    print(f"  - http://localhost:{port}/orders              (Order management)")
    print(f"\nAPI with /api/v1 prefix also supported")
    print(f"\nPress Ctrl+C to stop the server")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")

if __name__ == "__main__":
    run_server()