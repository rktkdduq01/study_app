#!/usr/bin/env python3
"""
Simple HTTP server for testing - no external dependencies required
Version 2 with better error handling and logging
"""

import http.server
import json
import urllib.parse
import uuid
import traceback
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
        try:
            parsed_path = urllib.parse.urlparse(self.path)
            path = parsed_path.path
            normalized_path = self.normalize_path(path)
            
            print(f"\n[GET] Original: {path}, Normalized: {normalized_path}")
            
            # Route to appropriate handler
            routes = {
                '/': self.handle_root,
                '/health': self.handle_health,
                '/users': self.handle_get_users,
                '/users/me': self.handle_get_current_user,
                '/products': self.handle_get_products,
                '/orders': self.handle_get_orders,
                '/characters': self.handle_get_characters,
                '/characters/me': self.handle_get_my_character,
            }
            
            # Check for specific routes first
            if normalized_path in routes:
                routes[normalized_path]()
                return
            
            # Check for ID-based routes
            if normalized_path.startswith('/users/') and len(normalized_path.split('/')) == 3:
                self.handle_get_user(normalized_path.split('/')[2])
            elif normalized_path.startswith('/characters/') and len(normalized_path.split('/')) == 3:
                self.handle_get_character(normalized_path.split('/')[2])
            elif normalized_path.startswith('/products/') and len(normalized_path.split('/')) == 3:
                self.handle_get_product(normalized_path.split('/')[2])
            elif normalized_path.startswith('/orders/') and len(normalized_path.split('/')) == 3:
                self.handle_get_order(normalized_path.split('/')[2])
            else:
                self.handle_not_found()
        except Exception as e:
            print(f"[ERROR] GET {self.path}: {str(e)}")
            traceback.print_exc()
            self.send_json_response({"detail": f"Server error: {str(e)}"}, 500)
    
    def do_POST(self):
        """Handle POST requests"""
        try:
            parsed_path = urllib.parse.urlparse(self.path)
            path = parsed_path.path
            normalized_path = self.normalize_path(path)
            
            # Handle trailing slash
            if normalized_path.endswith('/') and normalized_path != '/':
                normalized_path = normalized_path[:-1]
            
            print(f"\n[POST] Original: {path}, Normalized: {normalized_path}")
            
            # Read body
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length) if content_length > 0 else b'{}'
            
            print(f"[POST] Body length: {len(body)} bytes")
            
            # Route to appropriate handler
            routes = {
                '/users': lambda: self.handle_create_user(body),
                '/users/register': lambda: self.handle_register_user(body),
                '/auth/token': lambda: self.handle_login(body),
                '/products': lambda: self.handle_create_product(body),
                '/orders': lambda: self.handle_create_order(body),
                '/characters': lambda: self.handle_create_character(body),
            }
            
            handler = routes.get(normalized_path)
            if handler:
                handler()
            else:
                print(f"[404] No handler for POST {normalized_path}")
                self.handle_not_found()
        except Exception as e:
            print(f"[ERROR] POST {self.path}: {str(e)}")
            traceback.print_exc()
            self.send_json_response({"detail": f"Server error: {str(e)}"}, 500)
    
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
        response_body = json.dumps(data, default=str).encode()
        self.wfile.write(response_body)
        print(f"[RESPONSE] Status: {status}, Body: {response_body[:200].decode('utf-8', errors='ignore')}...")
    
    def handle_root(self):
        """Handle root endpoint"""
        data = {
            "message": "Welcome to EduRPG Simple API Server",
            "version": "2.0.0",
            "endpoints": {
                "users": "/users",
                "characters": "/characters",
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
            "timestamp": datetime.now().isoformat(),
            "stats": {
                "users": len(users_db),
                "characters": len(characters_db),
                "products": len(products_db),
                "orders": len(orders_db)
            }
        }
        self.send_json_response(data)
    
    def handle_get_users(self):
        """Get all users"""
        users = list(users_db.values())
        # Remove passwords from response
        safe_users = [{k: v for k, v in user.items() if k != "password"} for user in users]
        self.send_json_response(safe_users)
    
    def handle_get_user(self, user_id: str):
        """Get specific user"""
        user = users_db.get(user_id)
        if user:
            safe_user = {k: v for k, v in user.items() if k != "password"}
            self.send_json_response(safe_user)
        else:
            self.send_json_response({"detail": "User not found"}, 404)
    
    def handle_get_current_user(self):
        """Get current user from token"""
        try:
            # Get Authorization header
            auth_header = self.headers.get('Authorization', '')
            print(f"[AUTH] Authorization header: {auth_header[:50]}...")
            
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
            print(f"[ERROR] Get current user: {str(e)}")
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
            print(f"[ERROR] Create user: {str(e)}")
            self.send_json_response({"detail": str(e)}, 400)
    
    def handle_register_user(self, body: bytes):
        """Handle user registration"""
        try:
            data = json.loads(body.decode())
            print(f"[REGISTER] Request data: {json.dumps(data, indent=2)}")
            
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
            
            print(f"[REGISTER] Created user: {user['username']} (ID: {user_id})")
            
            # Return user without password
            response_user = {k: v for k, v in user.items() if k != "password"}
            self.send_json_response(response_user, 201)
            
        except json.JSONDecodeError:
            self.send_json_response({"detail": "Invalid JSON format"}, 400)
        except Exception as e:
            print(f"[ERROR] Registration: {str(e)}")
            traceback.print_exc()
            self.send_json_response({"detail": str(e)}, 400)
    
    def handle_login(self, body: bytes):
        """Handle user login"""
        try:
            # Parse form data (application/x-www-form-urlencoded)
            body_str = body.decode('utf-8')
            params = urllib.parse.parse_qs(body_str)
            
            username = params.get('username', [''])[0]
            password = params.get('password', [''])[0]
            
            print(f"[LOGIN] Attempt for username: {username}")
            
            # Find user by username
            user = None
            for u in users_db.values():
                if u.get("username") == username:
                    user = u
                    break
            
            if not user:
                print(f"[LOGIN] User not found: {username}")
                self.send_json_response({"detail": "Invalid username or password"}, 401)
                return
            
            # Check password (in production, use proper password hashing)
            if user.get("password") != password:
                print(f"[LOGIN] Invalid password for: {username}")
                self.send_json_response({"detail": "Invalid username or password"}, 401)
                return
            
            # Generate token (in production, use proper JWT)
            token = f"fake-jwt-token-{user['id']}-{uuid.uuid4()}"
            
            print(f"[LOGIN] Success for: {username}, Token: {token[:50]}...")
            
            # Return login response
            response = {
                "access_token": token,
                "token_type": "bearer",
                "user": {k: v for k, v in user.items() if k != "password"}
            }
            self.send_json_response(response)
            
        except Exception as e:
            print(f"[ERROR] Login: {str(e)}")
            traceback.print_exc()
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
            self.send_json_response({"detail": "Product not found"}, 404)
    
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
            self.send_json_response({"detail": str(e)}, 400)
    
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
            self.send_json_response({"detail": "Order not found"}, 404)
    
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
            self.send_json_response({"detail": str(e)}, 400)
    
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
            
            print(f"[CHARACTER] Looking for character with user_id: {user_id}")
            
            # Find character for this user
            for character in characters_db.values():
                if character.get("user_id") == user_id:
                    self.send_json_response(character)
                    return
            
            # No character found
            print(f"[CHARACTER] No character found for user: {user_id}")
            self.send_json_response({"detail": "Character not found"}, 404)
            
        except Exception as e:
            print(f"[ERROR] Get my character: {str(e)}")
            self.send_json_response({"detail": str(e)}, 400)
    
    def handle_create_character(self, body: bytes):
        """Create new character"""
        try:
            data = json.loads(body.decode())
            print(f"[CHARACTER] Create request: {json.dumps(data, indent=2)}")
            
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
                print("[CHARACTER] No authentication token found")
                self.send_json_response({"detail": "Authentication required"}, 401)
                return
            
            print(f"[CHARACTER] Creating for user: {user_id}")
            
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
                "avatar_url": data.get("avatar_url", "/avatars/default.png"),
                "total_level": 1,
                "total_experience": 0,
                "coins": 100,
                "gems": 10,
                "streak_days": 0,
                "last_active_date": datetime.now().isoformat(),
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            characters_db[character_id] = character
            print(f"[CHARACTER] Created: {character['name']} (ID: {character_id})")
            self.send_json_response(character, 201)
            
        except json.JSONDecodeError:
            self.send_json_response({"detail": "Invalid JSON format"}, 400)
        except Exception as e:
            print(f"[ERROR] Character creation: {str(e)}")
            traceback.print_exc()
            self.send_json_response({"detail": str(e)}, 400)
    
    def handle_not_found(self):
        """Handle 404"""
        print(f"[404] Not Found: {self.path}")
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
        "password": "password123",  # In production, hash this
        "role": "student",
        "is_active": True,
        "is_verified": True,
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
    
    print(f"\n{'='*50}")
    print(f"EduRPG Simple API Server v2.0")
    print(f"{'='*50}")
    print(f"Server running on http://localhost:{port}")
    print(f"\nAPI endpoints:")
    print(f"  Authentication:")
    print(f"    POST /auth/token              - Login")
    print(f"    POST /users/register          - Register new user")
    print(f"    GET  /users/me                - Get current user")
    print(f"  Characters:")
    print(f"    POST /characters              - Create character")
    print(f"    GET  /characters/me           - Get my character")
    print(f"    GET  /characters              - List all characters")
    print(f"  Other:")
    print(f"    GET  /                        - Server info")
    print(f"    GET  /health                  - Health check")
    print(f"\nAll endpoints support /api/v1 prefix")
    print(f"{'='*50}")
    print(f"\nPress Ctrl+C to stop the server\n")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\nServer stopped.")

if __name__ == "__main__":
    run_server()