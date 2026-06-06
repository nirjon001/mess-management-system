CREATE DATABASE IF NOT EXISTS mess_management_new;
USE mess_management_new;

CREATE TABLE users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('admin', 'member') NOT NULL DEFAULT 'member',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE members (
    member_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    member_name VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    occupation VARCHAR(100),
    district VARCHAR(100),
    reg_date DATE,
    status ENUM('active', 'inactive') DEFAULT 'active',
    gender ENUM('male', 'female') DEFAULT 'male',
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE TABLE room_types (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    capacity INT NOT NULL,
    rent DECIMAL(10,2) NOT NULL
);

CREATE TABLE rooms (
    room_id INT AUTO_INCREMENT PRIMARY KEY,
    room_no INT NOT NULL,
    floor INT NOT NULL,
    building VARCHAR(50) NOT NULL,
    type_id INT NOT NULL,
    is_available BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (type_id) REFERENCES room_types(id) ON DELETE CASCADE
);

CREATE TABLE assignments (
    assign_id INT AUTO_INCREMENT PRIMARY KEY,
    member_id INT NOT NULL,
    room_id INT NOT NULL,
    check_in DATE NOT NULL,
    monthly_rent DECIMAL(10,2) NOT NULL,
    active BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (member_id) REFERENCES members(member_id) ON DELETE CASCADE,
    FOREIGN KEY (room_id) REFERENCES rooms(room_id) ON DELETE CASCADE
);

CREATE TABLE food_menu (
    menu_id INT AUTO_INCREMENT PRIMARY KEY,
    menu_date DATE NOT NULL,
    item VARCHAR(255) NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    meal_type ENUM('breakfast', 'lunch', 'dinner') NOT NULL,
    available BOOLEAN DEFAULT TRUE
);

CREATE TABLE meal_orders (
    order_id INT AUTO_INCREMENT PRIMARY KEY,
    member_id INT NOT NULL,
    menu_id INT NOT NULL,
    quantity INT NOT NULL DEFAULT 1,
    order_date DATE NOT NULL,
    total DECIMAL(10,2) NOT NULL,
    status ENUM('confirmed', 'pending', 'cancelled') DEFAULT 'confirmed',
    FOREIGN KEY (member_id) REFERENCES members(member_id) ON DELETE CASCADE,
    FOREIGN KEY (menu_id) REFERENCES food_menu(menu_id) ON DELETE CASCADE
);

CREATE TABLE utility_bills (
    bill_id INT AUTO_INCREMENT PRIMARY KEY,
    bill_month VARCHAR(7) NOT NULL,
    due_date DATE NOT NULL,
    bill_type ENUM('electricity', 'water', 'gas', 'internet', 'other') NOT NULL,
    amount DECIMAL(10,2) DEFAULT 0,
    status ENUM('unpaid', 'paid') DEFAULT 'unpaid',
    room_id INT NOT NULL,
    FOREIGN KEY (room_id) REFERENCES rooms(room_id) ON DELETE CASCADE
);

CREATE TABLE payments (
    payment_id INT AUTO_INCREMENT PRIMARY KEY,
    payment_date DATE NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    payment_method VARCHAR(50) NOT NULL,
    payment_type ENUM('rent', 'utility', 'food', 'other') NOT NULL,
    status ENUM('completed', 'pending') DEFAULT 'completed',
    assignment_id INT,
    member_id INT,
    bill_id INT DEFAULT NULL,
    FOREIGN KEY (assignment_id) REFERENCES assignments(assign_id) ON DELETE SET NULL,
    FOREIGN KEY (member_id) REFERENCES members(member_id) ON DELETE CASCADE
);

-- Default users (admin/admin123, member/member123) are auto-created by app.py on first run
-- Run the app first, then register, or let it auto-create defaults.

-- Sample data (uncomment after first run if needed):
-- INSERT INTO members (user_id, member_name, phone, occupation, district, reg_date, status, gender) VALUES
-- (2, 'Rahim Uddin', '01711223344', 'Student', 'Dhaka', '2024-01-10', 'active', 'male');

-- INSERT INTO room_types (name, capacity, rent) VALUES
-- ('Single', 1, 3500),
-- ('Double', 2, 2500),
-- ('Triple', 3, 2000);

-- INSERT INTO rooms (room_no, floor, building, type_id, is_available) VALUES
-- (101, 1, 'Block A', 1, FALSE),
-- (102, 1, 'Block A', 2, TRUE),
-- (201, 2, 'Block B', 1, TRUE);

-- INSERT INTO assignments (member_id, room_id, check_in, monthly_rent, active) VALUES
-- (1, 1, '2024-01-10', 3500, TRUE);
