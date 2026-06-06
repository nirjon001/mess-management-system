# Mess Management System

A web-based mess/hostel management system built with Python Flask, MySQL, and Bootstrap. Provides separate admin and member panels for managing rooms, assignments, food menu, utility bills, and payments.

## Features

### Admin Panel
- Dashboard with overview stats
- Member management (add/edit/delete)
- Room & room type management (add/edit/delete)
- Room assignment & rent tracking
- Food menu management (daily items by meal type)
- Utility bill generation & tracking
- Payment monitoring with rent/utility/food breakdown
- Reports & data export

### Member Panel
- Dashboard with rent summary (monthly rent, paid, due)
- View utility bills with outstanding amounts
- Make payments (rent, utility, food) with partial payment support
- Book food from daily menu
- View personal expense history

## Tech Stack

- **Backend:** Python Flask 3.0
- **Database:** MySQL with mysql-connector-python
- **Frontend:** HTML5, CSS3, Bootstrap 5.3, vanilla JavaScript
- **Auth:** Werkzeug password hashing, session-based auth

## Requirements

- Python 3.8+
- MySQL 5.7+ / MariaDB 10.3+
- XAMPP (recommended) or standalone MySQL server

## Installation

### 1. Clone the repository
```bash
git clone <repo-url>
cd mess_management_system
```

### 2. Create the database
Open phpMyAdmin or MySQL CLI and run:
```sql
CREATE DATABASE IF NOT EXISTS mess_management_new;
```
Then import the schema:
```bash
mysql -u root -p mess_management_new < schema.sql
```

Or simply run the app — it auto-creates the database and tables on first startup.

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure database (optional)
Edit `config.py` to change database credentials:
```python
DB_HOST = 'localhost'
DB_USER = 'root'
DB_PASS = ''
DB_NAME = 'mess_management_new'
```

### 5. Run the application
```bash
python app.py
```

The app starts on `http://localhost:5000`.

### 6. Access the system

| Role | Username | Password |
|------|----------|----------|
| Admin | admin | admin123 |
| Member | rahim | member123 |
| Member | karim | member123 |
| Member | sumon | member123 |

> Default users are auto-created on first startup.

### 7. Seed sample data (optional)
Visit these endpoints after login:
- `/api/seed-data` — creates rooms, room types, and a default member assignment
- `/api/seed-historical-data` — creates 6 months of utility bills, 30 days food menu, meal orders, and payment history

## Project Structure

```
mess_system_new/
├── app.py                 # Main Flask application
├── config.py              # Database & app configuration
├── db.py                  # Database connection & query helpers
├── requirements.txt       # Python dependencies
├── schema.sql            # MySQL schema
├── static/
│   ├── css/
│   │   └── style.css     # Custom styles
│   └── js/
│       ├── admin.js       # Admin panel JavaScript
│       └── member.js      # Member panel JavaScript
├── templates/
│   ├── base.html          # Base template with collapsible sidebar
│   ├── login.html         # Login page
│   ├── register.html      # Registration page
│   ├── admin/             # Admin templates
│   │   ├── dashboard.html
│   │   ├── members.html
│   │   ├── rooms.html
│   │   ├── assignments.html
│   │   ├── food_menu.html
│   │   ├── utility_bills.html
│   │   ├── payments.html
│   │   └── reports.html
│   └── member/            # Member templates
│       ├── dashboard.html
│       ├── bills.html
│       ├── payments.html
│       ├── food_booking.html
│       └── expenses.html
├── README.md
├── LICENSE
└── .gitignore
```

## API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/login` | Login page |
| POST | `/login` | Authenticate user |
| GET | `/register` | Registration page |
| POST | `/register` | Create new account |
| GET | `/logout` | Logout |

### Admin API
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/admin/dashboard` | Admin dashboard stats |
| GET/POST | `/api/admin/members` | List / Create members |
| PUT/DELETE | `/api/admin/members/<id>` | Update / Delete member |
| GET/POST | `/api/admin/rooms` | List / Create rooms |
| PUT/DELETE | `/api/admin/rooms/<id>` | Update / Delete room |
| GET/POST | `/api/admin/room-types` | List / Create room types |
| PUT/DELETE | `/api/admin/room-types/<id>` | Update / Delete room type |
| GET/POST | `/api/admin/assignments` | List / Create assignments |
| PUT/DELETE | `/api/admin/assignments/<id>` | Update / Delete assignment |
| GET/POST | `/api/admin/food-menu` | List / Create food menu items |
| PUT/DELETE | `/api/admin/food-menu/<id>` | Update / Delete food menu item |
| GET/POST | `/api/admin/utility-bills` | List / Create bills |
| PUT/DELETE | `/api/admin/utility-bills/<id>` | Update / Delete bill |
| GET/POST | `/api/admin/payments` | List / Create payments |
| GET | `/api/admin/reports` | Reports data |

### Member API
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/member/dashboard` | Member dashboard (rent summary) |
| GET | `/api/member/bills` | Utility bills for member's room |
| GET/POST | `/api/member/payments` | List / Submit payments |
| GET | `/api/member/food-menu` | Daily food menu |
| POST | `/api/member/order-food` | Order food |
| GET | `/api/member/orders` | Member's food orders |
| GET | `/api/member/expenses` | Expense history |

### Seed Data
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/seed-data` | Create rooms, types, and initial assignment |
| GET | `/api/seed-historical-data` | Create 6 months of sample data |

## License

MIT

## Author

Developed as part of a mess management system project.
