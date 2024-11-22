from flask import Flask, jsonify, request
import os
from bson import ObjectId
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

# Initialize Flask app
app = Flask(__name__)

# Load environment variables from .env file
load_dotenv()

# MongoDB connection
MONGO_URI = os.getenv('MONGO_URI') 
print(MONGO_URI)
try:
    # Connect to MongoDB
    client = MongoClient(MONGO_URI)
    client.admin.command('ping')  # Verify connection
    print("Database connected successfully.")
    db = client["FoodDeliveryApp"]
    users = db["user"]
    menus = db["menu"]
    orders = db["order"]
except ConnectionFailure:
    print("Failed to connect to the database.")


###################### User Section #######################
# Root route to display a welcome message
@app.route('/', methods=['GET'])
def welcome():
    return jsonify({"msg": "Welcome to the Food Delivery App"}), 200

# Route to register a new user
@app.route('/register', methods=['POST'])
def register_user():
    # Get form data (for form submission)
    data = request.get_json()

    print(data)
    
    # Check if role is valid
    if data.get('role') not in ["customer", "restaurant_owner", "delivery_personnel", "admin"]:
        return jsonify({"msg": "Invalid role"}), 400

    # Ensure essential fields are provided
    if not data.get('name') or not data.get('email') or not data.get('password'):
        return jsonify({"msg": "Missing required fields"}), 400

    # Check if a user with the same email already exists
    if users.find_one({"email": data.get('email')}):
        return jsonify({"msg": "User with this email already exists"}), 400

    try:
        # Insert the user data into MongoDB
        user_id = users.insert_one(data).inserted_id

        # Fetch the saved user from the database by ID (to get the auto-generated _id)
        saved_user = users.find_one({"_id": ObjectId(user_id)})

        # Convert ObjectId to string
        saved_user['_id'] = str(saved_user['_id'])

        return jsonify({"msg": "User registered successfully", "user_data": saved_user}), 201
    except Exception as e:
        return jsonify({"msg": "Error registering user", "error": str(e)}), 500

# Update user profile
@app.route('/users/<user_id>', methods=['PUT'])
def update_user(user_id):
    # Get the data to update from the request body
    data = request.get_json()
    try:
        # Update only the fields that are provided in the request
        result = users.update_one(
            {"_id": ObjectId(user_id)}, 
            {"$set": data}  # Use $set to update fields
        )

        if result.modified_count > 0:
            # Fetch the updated user data to return
            updated_user = users.find_one({"_id": ObjectId(user_id)})
            # Convert ObjectId to string
            updated_user['_id'] = str(updated_user['_id'])
            return jsonify({"msg": "User updated successfully", "user_data": updated_user}), 200
        else:
            return jsonify({"msg": "No changes made to the user"}), 400

    except Exception as e:
        return jsonify({"msg": "Error updating user", "error": str(e)}), 500

# Get order Track or history
@app.route('/restaurant/orders/<restaurant_id>', methods=['GET'])
def get_restaurant_orders(restaurant_id):
    try:
        # Find all orders associated with the restaurant
        restaurant_orders = list(orders.find({"restaurant_id": ObjectId(restaurant_id)}))

        if not restaurant_orders:
            return jsonify({"msg": "No orders found for this restaurant"}), 404

        # Convert ObjectId fields to strings for each order
        formatted_orders = []
        for order in restaurant_orders:
            order["_id"] = str(order["_id"])
            order["user_id"] = str(order["user_id"])
            order["restaurant_id"] = str(order["restaurant_id"])
            order["delivery_person_id"] = str(order["delivery_person_id"])
            formatted_orders.append(order)

        return jsonify({"msg": "Orders retrieved successfully", "orders": formatted_orders}), 200

    except Exception as e:
        return jsonify({"msg": "Error retrieving orders", "error": str(e)}), 500



# Route to retrieve all users
@app.route('/users', methods=['GET'])
def get_all_users():
    try:
        # Fetch all users from MongoDB
        all_users = list(users.find({}))  # Exclude passwords from response for security

        # Convert MongoDB documents to JSON serializable format
        user_list = []
        for user in all_users:
            user['_id'] = str(user['_id'])  # Convert ObjectId to string
            user_list.append(user)
        
        return jsonify({"msg": "Users retrieved successfully", "users": user_list}), 200
    except Exception as e:
        return jsonify({"msg": "Error fetching users", "error": str(e)}), 500
    
# Route to delete a user by ID
@app.route('/users/<user_id>', methods=['DELETE'])
def delete_user(user_id):
    try:
        # Attempt to delete the user with the specified ID
        result = users.delete_one({"_id": ObjectId(user_id)})

        # Check if a document was deleted
        if result.deleted_count > 0:
            return jsonify({"msg": "User deleted successfully", "user_id": user_id}), 200
        else:
            return jsonify({"msg": "User not found", "user_id": user_id}), 404
    except Exception as e:
        return jsonify({"msg": "Error deleting user", "error": str(e)}), 500

# Route to login (basic authentication simulation)
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = users.find_one({"email": data.get("email"), "password": data.get("password")})
    if user:
        return jsonify({"msg": "Login successful", "user_id": str(user["_id"]), "role": user["role"]})
    return jsonify({"msg": "Invalid credentials"}), 401

# Get restaurant order
@app.route('/restaurant_specific/orders/<restaurant_id>', methods=['GET'])
def get_specific_restaurant_orders(restaurant_id):
    try:
        # Find all orders associated with the restaurant
        restaurant_orders = list(orders.find({"restaurant_id": ObjectId(restaurant_id)}))

        if not restaurant_orders:
            return jsonify({"msg": "No orders found for this restaurant"}), 404

        # Convert ObjectId fields to strings for each order
        formatted_orders = []
        for order in restaurant_orders:
            order["_id"] = str(order["_id"])
            order["user_id"] = str(order["user_id"])
            order["restaurant_id"] = str(order["restaurant_id"])
            order["delivery_person_id"] = str(order["delivery_person_id"])
            formatted_orders.append(order)

        return jsonify({"msg": "Orders retrieved successfully", "orders": formatted_orders}), 200

    except Exception as e:
        return jsonify({"msg": "Error retrieving orders", "error": str(e)}), 500


# Get Delivery Person Order
@app.route('/delivery_person/orders/<delivery_person_id>', methods=['GET'])
def get_delivery_person_orders(delivery_person_id):
    try:
        # Query the database for orders associated with the given delivery_person_id
        order_cursor = orders.find({"delivery_person_id": ObjectId(delivery_person_id)})
        
        # Convert the cursor to a list of orders
        orders_list = list(order_cursor)

        # If no orders are found, return a message
        if not orders_list:
            return jsonify({'message': 'No orders found for this delivery person.'}), 404
        
        # Format the orders list by converting ObjectId to string for each field
        formatted_orders = []
        for order in orders_list:
            order["_id"] = str(order["_id"])
            order["user_id"] = str(order["user_id"])
            order["restaurant_id"] = str(order["restaurant_id"])
            order["delivery_person_id"] = str(order["delivery_person_id"])
            
            # Include menu details
            order["menu_detail"] = order.get("menu_detail", [])

            formatted_orders.append(order)

        # Return the formatted orders list in the response
        return jsonify({'orders': formatted_orders}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

############### Order Section #################################

# Add a new order
@app.route('/order/<user_id>/<restaurant_id>', methods=['POST'])
def add_order(user_id, restaurant_id):
    try:
        # Get data from request body
        data = request.get_json()

        # Validate required fields
        required_fields = ["status", "menu_detail", "total_price", "delivery_person_id"]
        for field in required_fields:
            if field not in data:
                return jsonify({"msg": f"Missing required field: {field}"}), 400

        # Prepare the order document
        order_data = {
            "user_id": ObjectId(user_id),
            "restaurant_id": ObjectId(restaurant_id),
            "status": data["status"],
            "menu_detail": data["menu_detail"],  # Assume this is a list or detailed object
            "total_price": data["total_price"],
            "delivery_person_id": ObjectId(data["delivery_person_id"])
        }

        # Insert the order into the database
        order_id = orders.insert_one(order_data).inserted_id

        # Fetch the inserted order to include all fields
        inserted_order = orders.find_one({"_id": order_id})

        # Convert ObjectId fields to strings for the response
        inserted_order["_id"] = str(inserted_order["_id"])
        inserted_order["user_id"] = str(inserted_order["user_id"])
        inserted_order["restaurant_id"] = str(inserted_order["restaurant_id"])
        inserted_order["delivery_person_id"] = str(inserted_order["delivery_person_id"])

        return jsonify({"msg": "Order added successfully", "order_data": inserted_order}), 201

    except Exception as e:
        return jsonify({"msg": "Error adding order", "error": str(e)}), 500    
# Start the Flask app
if __name__ == "__main__":
    print("Starting the server...")
    app.run(host="0.0.0.0", port=8081, debug=True)