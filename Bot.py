
# Bot1- Don't delete this code.
'''
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import mysql.connector
import re
import os
from dotenv import load_dotenv
from collections import defaultdict

# Load environment variables
load_dotenv()

# Create Flask app and user lock mapping
app = Flask(__name__)
user_locks = defaultdict(lambda: False)


# MySQL connection setup
def get_db_connection():
    try:
        conn = mysql.connector.connect(
            host="127.0.0.1",
            user="root",  # Update with your MySQL username
            password="Gx7!pQz@92Lm$Vt",  # Update with your MySQL password
            database="dummydb"  # Update with your database name
        )
        print("✅ Successfully connected to the MySQL database.")
        return conn
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        raise e


# Clean text response for Twilio
def clean_text(text):
    return re.sub(r'[^\x09\x0A\x0D\x20-\x7E]', '', str(text))


# Match user message to templates in the database
def match_question_template(user_question):
    print("🔍 Matching user question with templates...")
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Fetch templates from the database
        cursor.execute("SELECT * FROM standard_questions")
        templates = cursor.fetchall()

        cursor.close()
        conn.close()
        print(f"✅ Retrieved {len(templates)} templates from the database.")

        # Match user question against the templates
        for template in templates:
            pattern = re.escape(template["question_template"]).replace(r'\{product_name\}', r'(.+)')
            print(f"🔍 Testing pattern: {pattern}")
            match = re.search(pattern, user_question, re.IGNORECASE)
            if match:
                product_name = match.group(1).strip()
                print(f"✅ Match found: Category: {template['category']}, Product Name: {product_name}")
                return template["category"], product_name
    except Exception as e:
        print(f"❌ Error in match_question_template: {e}")
    return None, None


# Category-to-query mapping
CATEGORY_QUERIES = {
    "Product Info": "SELECT title, description FROM full_product_data WHERE title = %s OR title LIKE %s",
    "Reviews": "SELECT title, review_comment FROM full_product_data WHERE title = %s OR title LIKE %s",
    "Ratings": "SELECT title, review_rating FROM full_product_data WHERE title = %s OR title LIKE %s",
    "Availability": "SELECT title, availabilityStatus FROM full_product_data WHERE title = %s OR title LIKE %s",
    "Pricing": "SELECT title, price FROM full_product_data WHERE title = %s OR title LIKE %s",
    "Brand Info": "SELECT title, brand FROM full_product_data WHERE title = %s OR title LIKE %s",
    "Tags": "SELECT title, tag FROM full_product_data WHERE title = %s OR title LIKE %s",
    "Images": "SELECT title, image_url FROM full_product_data WHERE title = %s OR title LIKE %s",
    "Warranty": "SELECT title, warrantyInformation FROM full_product_data WHERE title = %s OR title LIKE %s",
    "Shipping": "SELECT title, shippingInformation FROM full_product_data WHERE title = %s OR title LIKE %s"
}

# Column-to-response formatting
COLUMN_RESPONSE = {
    "description": lambda p: f"{p['title']} — {p['description']}",
    "review_comment": lambda p: f"{p['review_comment']}",
    "review_rating": lambda p: f"{p['title']} has a rating of {p['review_rating']}/5.",
    "availabilityStatus": lambda p: f"{p['title']} is currently {p['availabilityStatus']}.",
    "price": lambda p: f"The price of {p['title']} is ₹{p['price']}.",
    "brand": lambda p: f"{p['title']} is manufactured by {p['brand']}.",
    "tag": lambda p: f"Tags for {p['title']}: {p['tag']}.",
    "image_url": lambda p: f"Here’s an image of {p['title']}: {p['image_url']}",
    "warrantyInformation": lambda p: p.get("warrantyInformation", "Warranty info not available."),
    "shippingInformation": lambda p: p.get("shippingInformation", "Shipping info not available.")
}


# Fetch data for a given category
def get_category_data(category, product_name):
    print(f"🔍 Fetching data for Category: {category}, Product: {product_name}")
    query = CATEGORY_QUERIES.get(category)  # Retrieve query based on category
    if not query:
        print(f"❌ No query found for category: {category}")
        return None, None

    try:
        conn = get_db_connection()  # Connect to database
        cursor = conn.cursor(dictionary=True)

        # Debugging: log the exact query and parameters
        print(f"Executing Query: {query}")
        print(f"With Parameters: ({product_name}, {f'%{product_name}%'}))")

        # Execute the query
        cursor.execute(query, (product_name, f"%{product_name}%"))

        # Fetch one result and clear any unread results
        result = cursor.fetchone()
        cursor.fetchall()  # Ensure remaining results are cleared from cursor

        cursor.close()
        conn.close()

        # Debugging: log the query result
        print(f"✅ Query Result: {result}")

        # Determine the column name for response formatting (if data exists)
        column_name = query_column(query) if result else None
        return result, column_name
    except mysql.connector.Error as e:
        print(f"❌ Database query error: {e}")
        return None, None



# Extract queried column name from SQL
def query_column(query):
    try:
        fields = query.split("SELECT")[1].split("FROM")[0].strip().split(",")
        column = fields[1].strip()
        print(f"✅ Extracted column name: {column}")
        return column
    except Exception as e:
        print(f"❌ Error extracting column from query: {e}")
        return None


# Main bot endpoint
@app.route("/", methods=["POST"])
def bot():
    """
    This is the entry point for the bot backend. It logs incoming requests
    and tracks whether they make it to the backend.
    """
    print("\n🔗 Backend endpoint '/' has been called!")  # Debug log to confirm backend hit
    try:
        print("🔗 RAW Request Data:", request.data)  # Raw HTTP request content
        print(f"🔗 Request Values: {request.values}")  # Parsed values (form data)

        user_msg = request.values.get('Body', '').strip()
        user_number = request.values.get('From', '').strip()

        print("✅ Question Asked:", user_msg)  # User's question
        print("✅ User Number:", user_number)  # User's phone number

        response = MessagingResponse()

        # Lock user if already processing
        if user_locks[user_number]:
            print(f"⏳ User {user_number} is locked.")
            response.message("⏳ Please wait, your previous question is still being answered.")
            return str(response)

        user_locks[user_number] = True

        # Match question with a category and product
        category, product_name = match_question_template(user_msg)

        if not category or not product_name:
            print(f"❌ No valid match for question: '{user_msg}'")
            response.message("❌ Sorry, I cannot answer this question.")
        else:
            # Fetch data based on category and product
            product_data, col = get_category_data(category, product_name)

            if not product_data:
                print(f"❌ Product '{product_name}' not found in the database.")
                response.message("❌ Product not found in database.")
            else:
                # Respond with formatted output
                final_msg = COLUMN_RESPONSE[col](product_data)
                print(f"✅ Sending Response: {final_msg}")
                response.message(clean_text(final_msg))

        user_locks[user_number] = False
        return str(response)

    except Exception as e:
        print(f"❌ Backend Error: {e}")
        return "An error occurred.", 500  # Return 500 if something fails


# Start the Flask server
if __name__ == "__main__":
    print("🚀 Starting Flask server...")
    app.run(debug=True)
'''




# Bot 2- Don't delete this code.

from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import mysql.connector
import re
import os
from dotenv import load_dotenv
from collections import defaultdict

# Load environment variables
load_dotenv()

# Create Flask app and user lock mapping
app = Flask(__name__)
user_locks = defaultdict(lambda: False)


# MySQL connection setup
def get_db_connection():
    try:
        conn = mysql.connector.connect(
            host="127.0.0.1",
            user="root",  # Update with your MySQL username
            password="Gx7!pQz@92Lm$Vt",  # Update with your MySQL password
            database="dummydb"  # Update with your database name
        )
        print("✅ Successfully connected to the MySQL database.")
        return conn
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        raise e


# Clean text response for Twilio
def clean_text(text):
    return re.sub(r'[^\x09\x0A\x0D\x20-\x7E]', '', str(text))


# Match user message to templates in the database
def match_question_template(user_question):
    print("🔍 Matching user question with templates...")
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Fetch templates from the database
        cursor.execute("SELECT * FROM standard_questions")
        templates = cursor.fetchall()

        cursor.close()
        conn.close()
        print(f"✅ Retrieved {len(templates)} templates from the database.")

        # Match user question against the templates
        for template in templates:
            pattern = re.escape(template["question_template"]).replace(r'\{product_name\}', r'(.+)')
            print(f"🔍 Testing pattern: {pattern}")
            match = re.search(pattern, user_question, re.IGNORECASE)
            if match:
                product_name = match.group(1).strip()
                print(f"✅ Match found: Category: {template['category']}, Product Name: {product_name}")
                return template["category"], product_name
    except Exception as e:
        print(f"❌ Error in match_question_template: {e}")
    return None, None


# Category-to-query mapping
CATEGORY_QUERIES = {
    "Product Info": "SELECT title, description FROM full_product_data WHERE title = %s OR title LIKE %s",
    "Reviews": "SELECT title, review_comment FROM full_product_data WHERE title = %s OR title LIKE %s",
    "Ratings": "SELECT title, review_rating FROM full_product_data WHERE title = %s OR title LIKE %s",
    "Availability": "SELECT title, availabilityStatus FROM full_product_data WHERE title = %s OR title LIKE %s",
    "Pricing": "SELECT title, price FROM full_product_data WHERE title = %s OR title LIKE %s",
    "Brand Info": "SELECT title, brand FROM full_product_data WHERE title = %s OR title LIKE %s",
    "Tags": "SELECT title, tag FROM full_product_data WHERE title = %s OR title LIKE %s",
    "Images": "SELECT title, image_url FROM full_product_data WHERE title = %s OR title LIKE %s",
    "Warranty": "SELECT title, warrantyInformation FROM full_product_data WHERE title = %s OR title LIKE %s",
    "Shipping": "SELECT title, shippingInformation FROM full_product_data WHERE title = %s OR title LIKE %s"
}

# Column-to-response formatting
COLUMN_RESPONSE = {
    "description": lambda p: f"{p['title']} — {p['description']}",
    "review_comment": lambda p: f"{p['review_comment']}",
    "review_rating": lambda p: f"{p['title']} has a rating of {p['review_rating']}/5.",
    "availabilityStatus": lambda p: f"{p['title']} is currently {p['availabilityStatus']}.",
    "price": lambda p: f"The price of {p['title']} is ₹{p['price']}.",
    "brand": lambda p: f"{p['title']} is manufactured by {p['brand']}.",
    "tag": lambda p: f"Tags for {p['title']}: {p['tag']}.",
    "image_url": lambda p: f"Here’s an image of {p['title']}: {p['image_url']}",
    "warrantyInformation": lambda p: p.get("warrantyInformation", "Warranty info not available."),
    "shippingInformation": lambda p: p.get("shippingInformation", "Shipping info not available.")
}


# Fetch data for a given category
def get_category_data(category, product_name):
    print(f"🔍 Fetching data for Category: {category}, Product: {product_name}")
    query = CATEGORY_QUERIES.get(category)  # Retrieve query based on category
    if not query:
        print(f"❌ No query found for category: {category}")
        return None, None

    try:
        conn = get_db_connection()  # Connect to database
        cursor = conn.cursor(dictionary=True)

        # Debugging: log the exact query and parameters
        print(f"Executing Query: {query}")
        print(f"With Parameters: ({product_name}, {f'%{product_name}%'}))")

        # Execute the query
        cursor.execute(query, (product_name, f"%{product_name}%"))

        # Fetch one result and clear any unread results
        result = cursor.fetchone()
        cursor.fetchall()  # Ensure remaining results are cleared from cursor

        cursor.close()
        conn.close()

        # Debugging: log the query result
        print(f"✅ Query Result: {result}")

        # Determine the column name for response formatting (if data exists)
        column_name = query_column(query) if result else None
        return result, column_name
    except mysql.connector.Error as e:
        print(f"❌ Database query error: {e}")
        return None, None



# Extract queried column name from SQL
def query_column(query):
    try:
        fields = query.split("SELECT")[1].split("FROM")[0].strip().split(",")
        column = fields[1].strip()
        print(f"✅ Extracted column name: {column}")
        return column
    except Exception as e:
        print(f"❌ Error extracting column from query: {e}")
        return None


# Main bot endpoint
@app.route("/", methods=["POST"])
def bot():
    """
    This is the entry point for the bot backend. It logs incoming requests
    and tracks whether they make it to the backend.
    """
    print("\n🔗 Backend endpoint '/' has been called!")  # Debug log to confirm backend hit
    try:
        print("🔗 RAW Request Data:", request.data)  # Raw HTTP request content
        print(f"🔗 Request Values: {request.values}")  # Parsed values (form data)

        user_msg = request.values.get('Body', '').strip()
        user_msg = re.sub(r'\s+', ' ', user_msg)  # Clean up extra spaces
        print("✅ Cleaned User Message:", user_msg)

        user_number = request.values.get('From', '').strip()

        print("✅ Question Asked:", user_msg)  # User's question
        print("✅ User Number:", user_number)  # User's phone number

        response = MessagingResponse()

        # Lock user if already processing
        if user_locks[user_number]:
            print(f"⏳ User {user_number} is locked.")
            response.message("⏳ Please wait, your previous question is still being answered.")
            return str(response)

        user_locks[user_number] = True

        # Match question with a category and product
        category, product_name = match_question_template(user_msg)

        if not category or not product_name:
            print(f"❌ No valid match for question: '{user_msg}'")
            response.message("❌ Sorry, I cannot answer this question.")
        else:
            # Fetch data based on category and product
            product_data, col = get_category_data(category, product_name)

            if not product_data:
                print(f"❌ Product '{product_name}' not found in the database.")
                response.message("❌ Product not found in database.")
            else:
                # Respond with formatted output
                final_msg = COLUMN_RESPONSE[col](product_data)
                print(f"✅ Sending Response: {final_msg}")
                response.message(clean_text(final_msg))

        user_locks[user_number] = False
        return str(response)

    except Exception as e:
        print(f"❌ Backend Error: {e}")
        return "An error occurred.", 500  # Return 500 if something fails


# Start the Flask server
if __name__ == "__main__":
    print("🚀 Starting Flask server...")
    app.run(debug=True)





