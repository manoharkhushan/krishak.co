# Krishak - Agricultural Expense Tracker
## Complete Setup Guide

---

## 🌾 Project Overview

**Krishak** is a comprehensive agricultural expense tracking system designed for Indian farmers. It provides:
- User registration and authentication
- Expense tracking by categories (Seeds, Fertilizers, Labor, etc.)
- Dashboard with visual summaries
- Government schemes information
- Bilingual interface (English and Hindi)

---

## 📋 Prerequisites

Before installation, ensure you have:

1. **Python 3.8+** installed
2. **MySQL Server** (8.0 or higher)
3. **pip** (Python package manager)
4. Basic knowledge of command line

---

## 🚀 Installation Steps

### Step 1: Install MySQL Server

#### For Windows:
1. Download MySQL Installer from: https://dev.mysql.com/downloads/installer/
2. Run the installer
3. Choose "Custom" installation
4. Select "MySQL Server" and "MySQL Workbench"
5. Set root password during installation (remember this!)

#### For macOS:
```bash
brew install mysql
brew services start mysql
mysql_secure_installation
```

#### For Linux (Ubuntu/Debian):
```bash
sudo apt update
sudo apt install mysql-server
sudo systemctl start mysql
sudo mysql_secure_installation
```

---

### Step 2: Create Database

1. Open MySQL command line or MySQL Workbench

2. Login to MySQL:
```bash
mysql -u root -p
```

3. Create the database and import schema:
```sql
SOURCE /path/to/krishak_project/database/schema.sql;
```

Or manually run:
```sql
CREATE DATABASE krishak_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE krishak_db;
```

Then execute all the SQL commands from `database/schema.sql`

---

### Step 3: Install Python Dependencies

Navigate to the project directory:

```bash
cd krishak_project
```

Install required packages:

```bash
pip install -r requirements.txt
```

**If you face issues with mysqlclient:**

For Windows:
```bash
pip install mysqlclient-1.4.6-cp310-cp310-win_amd64.whl
# Download the wheel file from: https://www.lfd.uci.edu/~gohlke/pythonlibs/#mysqlclient
```

For macOS:
```bash
brew install mysql-client
export PATH="/usr/local/opt/mysql-client/bin:$PATH"
pip install mysqlclient
```

For Linux:
```bash
sudo apt-get install python3-dev default-libmysqlclient-dev build-essential
pip install mysqlclient
```

---

### Step 4: Configure Database Connection

Edit `app.py` and update the MySQL configuration:

```python
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'          # Your MySQL username
app.config['MYSQL_PASSWORD'] = 'your_password'  # Your MySQL password
app.config['MYSQL_DB'] = 'krishak_db'
```

---

### Step 5: Run the Application

Start the Flask server:

```bash
python app.py
```

You should see output like:
```
 * Running on http://0.0.0.0:5000
 * Running on http://127.0.0.1:5000
```

---

### Step 6: Access the Application

Open your web browser and navigate to:
```
http://localhost:5000
```

---

## 📁 Project Structure

```
krishak_project/
│
├── app.py                      # Main Flask application
├── requirements.txt            # Python dependencies
│
├── database/
│   └── schema.sql             # Database schema
│
├── templates/
│   ├── login.html             # Login page
│   ├── signup.html            # Registration page
│   ├── dashboard.html         # Main dashboard
│   └── schemes.html           # Government schemes
│
└── static/
    ├── css/
    │   ├── style.css          # Login/Signup styles
    │   └── dashboard.css      # Dashboard styles
    └── images/
        ├── krishak_logo.png
        └── krishak_background.jpeg
```

---

## 🎯 Features

### 1. User Management
- Secure user registration with password hashing
- Login authentication
- Session management

### 2. Expense Tracking
- Add expenses with date, category, amount, and remarks
- View expense history in organized table
- Filter and search expenses
- Delete expenses

### 3. Analytics
- Total expenses summary
- Category-wise breakdown
- Monthly expense tracking
- Visual cards for quick overview

### 4. Government Schemes
- Information about PM-KISAN
- Kisan Credit Card details
- Fasal Bima Yojana
- Application links

---

## 📊 Database Schema

### Tables:
1. **users** - User accounts and profiles
2. **expense_categories** - Predefined expense categories
3. **expenses** - Individual expense records
4. **crops** - Crop information (for future use)
5. **government_schemes** - Available schemes

---

## 🔐 Security Features

- Password hashing using Werkzeug
- SQL injection prevention with parameterized queries
- Session-based authentication
- Login required decorators for protected routes

---

## 🌐 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Redirect to dashboard or login |
| `/signup` | GET, POST | User registration |
| `/login` | GET, POST | User authentication |
| `/logout` | GET | Logout user |
| `/dashboard` | GET | Main dashboard (protected) |
| `/api/expenses` | POST | Add new expense |
| `/api/expenses` | DELETE | Delete expense |
| `/api/analytics` | GET | Get analytics data |
| `/schemes` | GET | View government schemes |

---

## 🐛 Troubleshooting

### Issue: Can't connect to MySQL
**Solution:** 
- Check if MySQL service is running
- Verify username and password in app.py
- Ensure database exists

### Issue: mysqlclient installation fails
**Solution:**
- Install development tools and MySQL client libraries
- Use appropriate wheel file for Windows
- Check Python version compatibility

### Issue: Port 5000 already in use
**Solution:**
Change port in app.py:
```python
app.run(debug=True, host='0.0.0.0', port=5001)
```

### Issue: Images not loading
**Solution:**
- Ensure images are in `static/images/` folder
- Clear browser cache
- Check file paths in templates

---

## 🔄 Future Enhancements

- [ ] Crop management module
- [ ] Weather integration
- [ ] Market price tracking
- [ ] Expense export to PDF/Excel
- [ ] Mobile responsive improvements
- [ ] SMS/Email notifications
- [ ] Multi-language support
- [ ] Data visualization charts
- [ ] Expense predictions using ML

---

## 📞 Support

For issues or questions:
- Email: support@krishak.in
- Government Helpline: 1800-180-1551

---

## 📄 License

This project is open-source and available for educational purposes.

---

## 👨‍💻 Development

To run in development mode:
```bash
export FLASK_ENV=development
export FLASK_DEBUG=1
python app.py
```

To run in production:
```bash
export FLASK_ENV=production
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

---

## 🙏 Credits

Developed for empowering Indian farmers with digital tools.

**Jai Kisan! Jai Jawan! Jai Vigyan!** 🇮🇳
