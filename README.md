# 💬 WhatsApp Chatbot with Twilio & MySQL

This project is a **WhatsApp chatbot** built using **Flask**, **Twilio API**, and **MySQL**.  
The bot can handle **natural product-related queries** such as product info, reviews, ratings, availability, pricing, brand info, shipping, warranty, and more.  
It fetches answers in real time from a MySQL database and replies directly to the user on WhatsApp.

---

## 📌 Features
- WhatsApp integration using **Twilio Messaging API**.
- Matches user messages against **stored templates** in the database.
- Extracts product details like:
  - Product Info
  - Reviews & Ratings
  - Availability
  - Pricing
  - Brand Information
  - Tags
  - Images
  - Warranty
  - Shipping
- Uses **MySQL database** as backend knowledge store.
- Implements **user lock mechanism** to avoid duplicate responses.
- Clean and structured responses formatted for WhatsApp.

---

## 🛠️ Tech Stack
- **Python 3**
- **Flask** – Web framework for API backend
- **Twilio API** – Messaging service for WhatsApp
- **MySQL** – Data storage and retrieval
- **dotenv** – For managing environment variables
- **Regex (re)** – For pattern matching and message parsing

---

## 📂 Project Structure
📁 whatsapp-chatbot
┣ 📄 app.py # Main chatbot backend (Flask + Twilio + MySQL)
┣ 📄 .env # Environment variables (Twilio credentials, DB configs)
┣ 📄 requirements.txt # Python dependencies
┣ 📄 README.md # Project documentation
┗ 📄 db/ # (Optional) SQL schema & sample data
