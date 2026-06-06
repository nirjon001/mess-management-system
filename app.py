from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from config import SECRET_KEY
from db import query, query_row

app = Flask(__name__)
app.secret_key = SECRET_KEY

def init_default_users():
    try:
        count = query_row("SELECT COUNT(*) as count FROM users")
        if count and count['count'] == 0:
            admin_hash = generate_password_hash('admin123')
            member_hash = generate_password_hash('member123')
            query("INSERT INTO users (username, email, password_hash, role) VALUES (%s,%s,%s,%s)", ('admin', 'admin@mess.com', admin_hash, 'admin'), fetch=False)
            query("INSERT INTO users (username, email, password_hash, role) VALUES (%s,%s,%s,%s)", ('rahim', 'rahim@mess.com', member_hash, 'member'), fetch=False)
            print("Default users created (admin: admin123, member: member123)")

        # Add bill_id column if missing
        try:
            query("ALTER TABLE payments ADD COLUMN bill_id INT DEFAULT NULL", fetch=False)
        except:
            pass  # column already exists
    except Exception as e:
        print(f"Note: Could not init users (DB may not be ready yet): {e}")

init_default_users()

# ===================== DECORATORS =====================

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        if session.get('role') != 'admin':
            return redirect(url_for('member_dashboard'))
        return f(*args, **kwargs)
    return decorated

def member_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        if session.get('role') != 'member':
            return redirect(url_for('admin_dashboard'))
        return f(*args, **kwargs)
    return decorated

# ===================== AUTH ROUTES =====================

@app.route('/')
def index():
    if 'user_id' in session:
        if session['role'] == 'admin':
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('member_dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        username = data.get('username', '').strip()
        password = data.get('password', '')

        user = query_row("SELECT * FROM users WHERE username = %s OR email = %s", (username, username))
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['user_id']
            session['username'] = user['username']
            session['role'] = user['role']
            return jsonify({'success': True, 'role': user['role']})

        return jsonify({'success': False, 'message': 'Invalid credentials'})

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '')
        role = data.get('role', 'member')

        if not username or not email or not password:
            return jsonify({'success': False, 'message': 'All fields are required'})

        existing = query_row("SELECT user_id FROM users WHERE username = %s OR email = %s", (username, email))
        if existing:
            return jsonify({'success': False, 'message': 'Username or email already exists'})

        hashed = generate_password_hash(password)
        result = query(
            "INSERT INTO users (username, email, password_hash, role) VALUES (%s, %s, %s, %s)",
            (username, email, hashed, role),
            fetch=False
        )
        return jsonify({'success': True, 'message': 'Registration successful'})

    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ===================== ADMIN ROUTES =====================

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    return render_template('admin/dashboard.html', username=session['username'])

@app.route('/admin/members')
@admin_required
def admin_members():
    return render_template('admin/members.html', username=session['username'])

@app.route('/admin/rooms')
@admin_required
def admin_rooms():
    return render_template('admin/rooms.html', username=session['username'])

@app.route('/admin/assignments')
@admin_required
def admin_assignments():
    return render_template('admin/assignments.html', username=session['username'])

@app.route('/admin/food-menu')
@admin_required
def admin_food_menu():
    return render_template('admin/food_menu.html', username=session['username'])

@app.route('/admin/utility-bills')
@admin_required
def admin_utility_bills():
    return render_template('admin/utility_bills.html', username=session['username'])

@app.route('/admin/payments')
@admin_required
def admin_payments():
    return render_template('admin/payments.html', username=session['username'])

@app.route('/admin/reports')
@admin_required
def admin_reports():
    return render_template('admin/reports.html', username=session['username'])

# ==================== ADMIN API ====================

@app.route('/api/admin/dashboard/stats')
@admin_required
def admin_dashboard_stats():
    active_members = query_row("SELECT COUNT(*) as count FROM members WHERE status = 'active'")['count']
    total_rooms = query_row("SELECT COUNT(*) as count FROM rooms")['count']
    pending_bills = query_row("SELECT COUNT(*) as count FROM utility_bills WHERE status = 'unpaid'")['count']
    total_income = query_row("SELECT COALESCE(SUM(amount),0) as total FROM payments WHERE status = 'completed'")['total']
    recent = query("SELECT p.*, m.member_name FROM payments p LEFT JOIN assignments a ON p.assignment_id = a.assign_id LEFT JOIN members m ON a.member_id = m.member_id WHERE p.status = 'completed' ORDER BY p.payment_date DESC LIMIT 5")
    return jsonify({'success': True, 'data': {
        'active_members': active_members,
        'total_rooms': total_rooms,
        'pending_bills': pending_bills,
        'total_income': float(total_income),
        'recent_payments': recent
    }})

@app.route('/api/admin/members', methods=['GET', 'POST'])
@admin_required
def admin_members_api():
    if request.method == 'GET':
        members = query("SELECT m.*, a.room_id, r.room_no, r.building FROM members m LEFT JOIN assignments a ON m.member_id = a.member_id AND a.active = 1 LEFT JOIN rooms r ON a.room_id = r.room_id WHERE m.status = 'active' ORDER BY m.member_id DESC")
        users = query("SELECT user_id, username, email FROM users WHERE user_id NOT IN (SELECT COALESCE(user_id,0) FROM members)")
        return jsonify({'success': True, 'data': members, 'available_users': users})

    data = request.form
    user_id = data.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': 'User selection required'})
    query(
        "INSERT INTO members (user_id, member_name, phone, occupation, district, reg_date, status, gender) VALUES (%s,%s,%s,%s,%s,%s,'active',%s)",
        (data['user_id'], data['member_name'], data['phone'], data['occupation'], data['district'], data['reg_date'], data.get('gender', 1)),
        fetch=False
    )
    return jsonify({'success': True, 'message': 'Member added'})

@app.route('/api/admin/members/update', methods=['POST'])
@admin_required
def admin_members_update():
    data = request.form
    query(
        "UPDATE members SET member_name=%s, phone=%s, occupation=%s, district=%s, status=%s WHERE member_id=%s",
        (data['member_name'], data['phone'], data['occupation'], data['district'], data['status'], data['member_id']),
        fetch=False
    )
    return jsonify({'success': True, 'message': 'Member updated'})

@app.route('/api/admin/room-types', methods=['GET', 'POST'])
@admin_required
def admin_room_types_api():
    if request.method == 'GET':
        types = query("SELECT * FROM room_types ORDER BY rent")
        return jsonify({'success': True, 'data': types})
    data = request.form
    query("INSERT INTO room_types (name, capacity, rent) VALUES (%s,%s,%s)", (data['name'], data['capacity'], data['rent']), fetch=False)
    return jsonify({'success': True, 'message': 'Room type added'})

@app.route('/api/admin/rooms', methods=['GET', 'POST'])
@admin_required
def admin_rooms_api():
    if request.method == 'GET':
        rooms = query("SELECT r.*, rt.name as type_name, rt.rent as base_rent FROM rooms r LEFT JOIN room_types rt ON r.type_id = rt.id ORDER BY r.room_id")
        return jsonify({'success': True, 'data': rooms})
    data = request.form
    query(
        "INSERT INTO rooms (room_no, floor, building, type_id, is_available) VALUES (%s,%s,%s,%s,%s)",
        (data['room_no'], data['floor'], data['building'], data['type_id'], data.get('is_available', 1)),
        fetch=False
    )
    return jsonify({'success': True, 'message': 'Room added'})

@app.route('/api/admin/assignments', methods=['GET', 'POST'])
@admin_required
def admin_assignments_api():
    if request.method == 'GET':
        assignments = query("SELECT a.*, m.member_name, r.room_no, r.building FROM assignments a JOIN members m ON a.member_id = m.member_id JOIN rooms r ON a.room_id = r.room_id WHERE a.active = 1")
        avail_members = query("SELECT * FROM members m WHERE m.status = 'active' AND NOT EXISTS (SELECT 1 FROM assignments a WHERE a.member_id = m.member_id AND a.active = 1)")
        avail_rooms = query("SELECT r.*, rt.rent FROM rooms r JOIN room_types rt ON r.type_id = rt.id WHERE r.is_available = 1")
        return jsonify({'success': True, 'data': {'assignments': assignments, 'available_members': avail_members, 'available_rooms': avail_rooms}})

    data = request.form
    member_id = data['member_id']
    room_id = data['room_id']
    check_in = data['check_in']
    monthly_rent = data['monthly_rent']

    query("INSERT INTO assignments (member_id, room_id, check_in, monthly_rent, active) VALUES (%s,%s,%s,%s,1)", (member_id, room_id, check_in, monthly_rent), fetch=False)
    query("UPDATE rooms SET is_available = 0 WHERE room_id = %s", (room_id,), fetch=False)
    return jsonify({'success': True, 'message': 'Room assigned'})

@app.route('/api/admin/assignments/checkout', methods=['POST'])
@admin_required
def admin_assignments_checkout():
    data = request.form
    assign_id = data['assign_id']
    assignment = query_row("SELECT * FROM assignments WHERE assign_id = %s", (assign_id,))
    if assignment:
        query("UPDATE assignments SET active = 0 WHERE assign_id = %s", (assign_id,), fetch=False)
        still_active = query_row("SELECT COUNT(*) as count FROM assignments WHERE room_id = %s AND active = 1", (assignment['room_id'],))['count']
        if still_active == 0:
            query("UPDATE rooms SET is_available = 1 WHERE room_id = %s", (assignment['room_id'],), fetch=False)
    return jsonify({'success': True, 'message': 'Check-out completed'})

@app.route('/api/admin/food-menu', methods=['GET', 'POST'])
@admin_required
def admin_food_menu_api():
    if request.method == 'GET':
        items = query("SELECT * FROM food_menu WHERE menu_date >= CURDATE() - INTERVAL 7 DAY ORDER BY menu_date DESC, meal_type")
        return jsonify({'success': True, 'data': items})
    data = request.form
    query(
        "INSERT INTO food_menu (menu_date, item, price, meal_type, available) VALUES (%s,%s,%s,%s,1)",
        (data['menu_date'], data['item'], data['price'], data['meal_type']),
        fetch=False
    )
    return jsonify({'success': True, 'message': 'Food item added'})

@app.route('/api/admin/utility-bills', methods=['GET', 'POST'])
@admin_required
def admin_utility_bills_api():
    if request.method == 'GET':
        bills = query("SELECT b.*, r.room_no, r.building FROM utility_bills b JOIN rooms r ON b.room_id = r.room_id ORDER BY b.due_date ASC")
        rooms = query("SELECT r.*, rt.rent FROM rooms r JOIN room_types rt ON r.type_id = rt.id WHERE r.is_available = 0")
        return jsonify({'success': True, 'data': {'bills': bills, 'rooms': rooms}})
    data = request.form
    query(
        "INSERT INTO utility_bills (bill_month, due_date, bill_type, amount, status, room_id) VALUES (%s,%s,%s,%s,'unpaid',%s)",
        (data['bill_month'], data['due_date'], data['bill_type'], data.get('amount', 0), data['room_id']),
        fetch=False
    )
    return jsonify({'success': True, 'message': 'Bill added'})

@app.route('/api/admin/utility-bills/mark-paid', methods=['POST'])
@admin_required
def admin_utility_bills_mark_paid():
    bill_id = request.form['bill_id']
    query("UPDATE utility_bills SET status = 'paid' WHERE bill_id = %s", (bill_id,), fetch=False)
    return jsonify({'success': True, 'message': 'Bill marked as paid'})

@app.route('/api/admin/payments', methods=['GET', 'POST'])
@admin_required
def admin_payments_api():
    if request.method == 'GET':
        payments = query("SELECT p.*, m.member_name FROM payments p LEFT JOIN assignments a ON p.assignment_id = a.assign_id LEFT JOIN members m ON a.member_id = m.member_id ORDER BY p.payment_date DESC LIMIT 50")
        assignments = query("SELECT a.assign_id, m.member_name, a.monthly_rent FROM assignments a JOIN members m ON a.member_id = m.member_id WHERE a.active = 1")
        return jsonify({'success': True, 'data': {'payments': payments, 'assignments': assignments}})
    data = request.form
    query(
        "INSERT INTO payments (payment_date, amount, payment_method, payment_type, status, assignment_id, member_id) VALUES (%s,%s,%s,%s,%s,%s,%s)",
        (data['payment_date'], data['amount'], data['payment_method'], data['payment_type'], data.get('status', 'completed'), data.get('assignment_id'), data.get('member_id')),
        fetch=False
    )
    return jsonify({'success': True, 'message': 'Payment recorded'})

@app.route('/api/admin/reports')
@admin_required
def admin_reports_api():
    members = query("SELECT * FROM members ORDER BY member_id")
    payments = query("SELECT p.*, m.member_name FROM payments p LEFT JOIN assignments a ON p.assignment_id = a.assign_id LEFT JOIN members m ON a.member_id = m.member_id ORDER BY p.payment_date DESC")
    rooms = query("SELECT r.*, rt.name as type_name, rt.rent FROM rooms r LEFT JOIN room_types rt ON r.type_id = rt.id ORDER BY r.room_id")
    orders = query("SELECT mo.*, m.member_name, f.item FROM meal_orders mo JOIN members m ON mo.member_id = m.member_id JOIN food_menu f ON mo.menu_id = f.menu_id ORDER BY mo.order_date DESC")
    return jsonify({'success': True, 'data': {
        'members': members, 'payments': payments, 'rooms': rooms, 'orders': orders
    }})

# ==================== MEMBER ROUTES ====================

@app.route('/member/dashboard')
@member_required
def member_dashboard():
    return render_template('member/dashboard.html', username=session['username'])

@app.route('/member/bills')
@member_required
def member_bills():
    return render_template('member/bills.html', username=session['username'])

@app.route('/member/payments')
@member_required
def member_payments():
    return render_template('member/payments.html', username=session['username'])

@app.route('/member/food-booking')
@member_required
def member_food_booking():
    return render_template('member/food_booking.html', username=session['username'])

@app.route('/member/expenses')
@member_required
def member_expenses():
    return render_template('member/expenses.html', username=session['username'])

# ==================== MEMBER API ====================

@app.route('/api/member/dashboard')
@member_required
def member_dashboard_api():
    user_id = session['user_id']
    member = query_row("SELECT * FROM members WHERE user_id = %s", (user_id,))
    if not member:
        return jsonify({'success': False, 'message': 'Not registered as member'})

    assignment = query_row("SELECT a.*, r.room_no, r.building, rt.name as type_name FROM assignments a JOIN rooms r ON a.room_id = r.room_id JOIN room_types rt ON r.type_id = rt.id WHERE a.member_id = %s AND a.active = 1", (member['member_id'],))
    payment = query("SELECT p.* FROM payments p WHERE p.member_id = %s OR p.assignment_id IN (SELECT assign_id FROM assignments WHERE member_id = %s)", (member['member_id'], member['member_id']))
    total_paid = sum(float(p['amount']) for p in payment if p['status'] == 'completed')
    meal_total = query_row("SELECT COALESCE(SUM(total),0) as total FROM meal_orders WHERE member_id = %s", (member['member_id'],))['total']
    unpaid_bills_count = 0
    rent_due = 0
    rent_paid_this_month = 0
    if assignment:
        unpaid_bills_count = query_row("SELECT COUNT(*) as count FROM utility_bills WHERE room_id = %s AND status = 'unpaid'", (assignment['room_id'],))['count']
        import datetime
        this_month = datetime.date.today().strftime('%Y-%m')
        rent_paid = query_row("SELECT COALESCE(SUM(amount),0) as total FROM payments WHERE member_id = %s AND payment_type = 'rent' AND status = 'completed' AND DATE_FORMAT(payment_date, '%Y-%m') = %s", (member['member_id'], this_month))
        rent_paid_this_month = float(rent_paid['total']) if rent_paid else 0
        rent_due = max(0, float(assignment['monthly_rent']) - rent_paid_this_month)

    return jsonify({'success': True, 'data': {
        'member': member,
        'assignment': assignment,
        'total_paid': float(total_paid),
        'meal_expense': float(meal_total),
        'unpaid_bills': unpaid_bills_count,
        'monthly_rent': float(assignment['monthly_rent']) if assignment else 0,
        'rent_paid_this_month': rent_paid_this_month,
        'rent_due': rent_due
    }})

@app.route('/api/member/bills')
@member_required
def member_bills_api():
    user_id = session['user_id']
    member = query_row("SELECT * FROM members WHERE user_id = %s", (user_id,))
    if not member:
        return jsonify({'success': False, 'message': 'Not registered'})
    assignment = query_row("SELECT * FROM assignments WHERE member_id = %s AND active = 1", (member['member_id'],))
    if not assignment:
        return jsonify({'success': False, 'data': [], 'message': 'No room assigned'})
    bills = query("SELECT * FROM utility_bills WHERE room_id = %s ORDER BY due_date DESC", (assignment['room_id'],))
    for b in bills:
        paid = query_row("SELECT COALESCE(SUM(amount),0) as total FROM payments WHERE bill_id = %s AND status = 'completed'", (b['bill_id'],))
        b['paid_so_far'] = float(paid['total']) if paid else 0
        b['outstanding'] = float(b['amount']) - b['paid_so_far']
        if b['outstanding'] <= 0 and b['status'] == 'unpaid':
            query("UPDATE utility_bills SET status = 'paid' WHERE bill_id = %s", (b['bill_id'],), fetch=False)
            b['status'] = 'paid'
    return jsonify({'success': True, 'data': bills, 'room': assignment})

@app.route('/api/member/payments', methods=['GET', 'POST'])
@member_required
def member_payments_api():
    user_id = session['user_id']
    member = query_row("SELECT * FROM members WHERE user_id = %s", (user_id,))

    if request.method == 'GET':
        if not member:
            return jsonify({'success': False, 'data': []})
        payments = query(
            "SELECT p.* FROM payments p WHERE p.member_id = %s OR p.assignment_id IN (SELECT assign_id FROM assignments WHERE member_id = %s) ORDER BY p.payment_date DESC",
            (member['member_id'], member['member_id'])
        )
        return jsonify({'success': True, 'data': payments})

    data = request.form
    if not member:
        return jsonify({'success': False, 'message': 'Not registered'})
    bill_id = data.get('bill_id')
    query(
        "INSERT INTO payments (payment_date, amount, payment_method, payment_type, status, member_id, bill_id) VALUES (%s,%s,%s,%s,%s,%s,%s)",
        (data['payment_date'], data['amount'], data['payment_method'], data.get('payment_type', 'rent'), 'completed', member['member_id'], bill_id if bill_id else None),
        fetch=False
    )
    if bill_id:
        paid = query_row("SELECT COALESCE(SUM(amount),0) as total FROM payments WHERE bill_id = %s AND status = 'completed'", (bill_id,))
        bill = query_row("SELECT * FROM utility_bills WHERE bill_id = %s", (bill_id,))
        if bill and paid and float(paid['total']) >= float(bill['amount']):
            query("UPDATE utility_bills SET status = 'paid' WHERE bill_id = %s", (bill_id,), fetch=False)
    return jsonify({'success': True, 'message': 'Payment submitted'})

@app.route('/api/member/food-menu')
@member_required
def member_food_menu_api():
    date = request.args.get('date', '')
    meal_type = request.args.get('meal_type', '')
    sql = "SELECT * FROM food_menu WHERE available = 1"
    params = []
    if date:
        sql += " AND menu_date = %s"
        params.append(date)
    if meal_type:
        sql += " AND meal_type = %s"
        params.append(meal_type)
    sql += " ORDER BY meal_type"
    items = query(sql, params)
    return jsonify({'success': True, 'data': items})

@app.route('/api/member/order-food', methods=['POST'])
@member_required
def member_order_food():
    user_id = session['user_id']
    member = query_row("SELECT * FROM members WHERE user_id = %s", (user_id,))
    if not member:
        return jsonify({'success': False, 'message': 'Not registered as member'})

    data = request.form
    menu_id = data['menu_id']
    qty = int(data.get('quantity', 1))
    menu_item = query_row("SELECT * FROM food_menu WHERE menu_id = %s", (menu_id,))
    if not menu_item:
        return jsonify({'success': False, 'message': 'Menu item not found'})
    total = float(menu_item['price']) * qty
    query(
        "INSERT INTO meal_orders (member_id, menu_id, quantity, order_date, total, status) VALUES (%s,%s,%s,CURDATE(),%s,'confirmed')",
        (member['member_id'], menu_id, qty, total),
        fetch=False
    )
    return jsonify({'success': True, 'message': 'Order placed', 'total': total})

@app.route('/api/member/orders')
@member_required
def member_orders_api():
    user_id = session['user_id']
    member = query_row("SELECT * FROM members WHERE user_id = %s", (user_id,))
    if not member:
        return jsonify({'success': False, 'data': []})
    orders = query(
        "SELECT mo.*, f.item, f.meal_type, f.price FROM meal_orders mo JOIN food_menu f ON mo.menu_id = f.menu_id WHERE mo.member_id = %s ORDER BY mo.order_date DESC LIMIT 20",
        (member['member_id'],)
    )
    return jsonify({'success': True, 'data': orders})

@app.route('/api/member/expenses')
@member_required
def member_expenses_api():
    user_id = session['user_id']
    member = query_row("SELECT * FROM members WHERE user_id = %s", (user_id,))
    if not member:
        return jsonify({'success': False, 'data': {}})
    payments = query("SELECT * FROM payments WHERE member_id = %s ORDER BY payment_date DESC", (member['member_id'],))
    orders = query(
        "SELECT mo.*, f.item, f.meal_type FROM meal_orders mo JOIN food_menu f ON mo.menu_id = f.menu_id WHERE mo.member_id = %s ORDER BY mo.order_date DESC",
        (member['member_id'],)
    )
    return jsonify({'success': True, 'data': {'payments': payments, 'orders': orders}})

# ===================== SEED DATA =====================

@app.route('/api/seed-data')
def seed_data():
    try:
        if query_row("SELECT COUNT(*) as count FROM members")['count'] > 0:
            return jsonify({'success': True, 'message': 'Data already exists'})

        member = query_row("SELECT member_id FROM members LIMIT 1")
        if not member:
            user = query_row("SELECT user_id FROM users WHERE role = 'member' LIMIT 1")
            if user:
                query("INSERT INTO members (user_id, member_name, phone, occupation, district, reg_date, status, gender) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
                    (user['user_id'], 'Rahim Uddin', '01711223344', 'Student', 'Dhaka', '2024-01-10', 'active', 'male'), fetch=False)

        types = query_row("SELECT COUNT(*) as count FROM room_types")['count']
        if types == 0:
            query("INSERT INTO room_types (name, capacity, rent) VALUES ('Single',1,3500), ('Double',2,2500), ('Triple',3,2000)", fetch=False)

        rooms = query_row("SELECT COUNT(*) as count FROM rooms")['count']
        if rooms == 0:
            query("INSERT INTO rooms (room_no, floor, building, type_id, is_available) VALUES (101,1,'Block A',1,0), (102,1,'Block A',2,1), (201,2,'Block B',1,1)", fetch=False)

        assignments = query_row("SELECT COUNT(*) as count FROM assignments")['count']
        if assignments == 0:
            member_row = query_row("SELECT member_id FROM members LIMIT 1")
            room_row = query_row("SELECT room_id FROM rooms WHERE is_available = 0 LIMIT 1")
            if member_row and room_row:
                query("INSERT INTO assignments (member_id, room_id, check_in, monthly_rent, active) VALUES (%s,%s,'2024-01-10',3500,1)", (member_row['member_id'], room_row['room_id']), fetch=False)

        food = query_row("SELECT COUNT(*) as count FROM food_menu")['count']
        if food == 0:
            query("INSERT INTO food_menu (menu_date, item, price, meal_type, available) VALUES (CURDATE(),'Paratha + Egg',50,'breakfast',1), (CURDATE(),'Rice + Chicken Curry',120,'lunch',1), (CURDATE(),'Rice + Fish Curry',100,'dinner',1)", fetch=False)

        return jsonify({'success': True, 'message': 'Sample data created successfully! Refresh the page.'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/seed-historical-data')
def seed_historical_data():
    try:
        existing = query_row("SELECT COUNT(*) as count FROM members")['count']
        if existing >= 3:
            return jsonify({'success': True, 'message': 'Historical data already exists'})

        user2 = query_row("SELECT user_id FROM users WHERE username = 'karim'")
        if not user2:
            query("INSERT INTO users (username, email, password_hash, role) VALUES (%s,%s,%s,%s)",
                ('karim', 'karim@mess.com', generate_password_hash('member123'), 'member'), fetch=False)
            user2 = query_row("SELECT user_id FROM users WHERE username = 'karim'")

        user3 = query_row("SELECT user_id FROM users WHERE username = 'sumon'")
        if not user3:
            query("INSERT INTO users (username, email, password_hash, role) VALUES (%s,%s,%s,%s)",
                ('sumon', 'sumon@mess.com', generate_password_hash('member123'), 'member'), fetch=False)
            user3 = query_row("SELECT user_id FROM users WHERE username = 'sumon'")

        query("INSERT INTO members (user_id, member_name, phone, occupation, district, reg_date, status, gender) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
            (user2['user_id'], 'Karim Hossain', '01822334455', 'Job Holder', 'Chittagong', '2024-02-05', 'active', 'male'), fetch=False)
        query("INSERT INTO members (user_id, member_name, phone, occupation, district, reg_date, status, gender) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
            (user3['user_id'], 'Sumon Ahmed', '01933445566', 'Student', 'Sylhet', '2024-03-12', 'active', 'male'), fetch=False)

        rooms = query("SELECT room_id, type_id FROM rooms WHERE is_available = 1 LIMIT 2")
        members_list = query("SELECT member_id FROM members WHERE member_id > 1 ORDER BY member_id LIMIT 2")
        if rooms and len(rooms) >= 2 and members_list and len(members_list) >= 2:
            query("INSERT INTO assignments (member_id, room_id, check_in, monthly_rent, active) VALUES (%s,%s,'2024-02-05',2500,1)", (members_list[0]['member_id'], rooms[0]['room_id']), fetch=False)
            query("INSERT INTO assignments (member_id, room_id, check_in, monthly_rent, active) VALUES (%s,%s,'2024-03-12',2000,1)", (members_list[1]['member_id'], rooms[1]['room_id']), fetch=False)
            query("UPDATE rooms SET is_available = 0 WHERE room_id = %s", (rooms[0]['room_id'],), fetch=False)
            query("UPDATE rooms SET is_available = 0 WHERE room_id = %s", (rooms[1]['room_id'],), fetch=False)

        all_rooms = query("SELECT room_id FROM rooms")
        import datetime
        today = datetime.date.today()
        for i in range(6):
            m = today - datetime.timedelta(days=30*i)
            month_str = m.strftime('%Y-%m')
            due = m.replace(day=20).isoformat()
            for room in all_rooms:
                is_paid = 'paid' if i > 2 else 'unpaid'
                bill_type = 'electricity' if room['room_id'] % 2 == 0 else 'water'
                amount = 500 + (room['room_id'] * 100)
                query("INSERT INTO utility_bills (bill_month, due_date, bill_type, amount, status, room_id) VALUES (%s,%s,%s,%s,%s,%s)",
                    (month_str, due, bill_type, amount, is_paid, room['room_id']), fetch=False)

        for i in range(30):
            d = today - datetime.timedelta(days=i)
            query("INSERT INTO food_menu (menu_date, item, price, meal_type, available) VALUES (%s,'Paratha + Egg',50,'breakfast',1)", (d.isoformat(),), fetch=False)
            query("INSERT INTO food_menu (menu_date, item, price, meal_type, available) VALUES (%s,'Rice + Chicken Curry',120,'lunch',1)", (d.isoformat(),), fetch=False)
            query("INSERT INTO food_menu (menu_date, item, price, meal_type, available) VALUES (%s,'Rice + Fish Curry',100,'dinner',1)", (d.isoformat(),), fetch=False)

        all_members = query("SELECT member_id FROM members")
        for member in all_members:
            for i in range(10):
                d = today - datetime.timedelta(days=i*3)
                qty = 1 + (member['member_id'] % 3)
                menu = query("SELECT menu_id, price FROM food_menu WHERE menu_date = %s LIMIT 1", (d.isoformat(),))
                if menu:
                    total = float(menu[0]['price']) * qty
                    query("INSERT INTO meal_orders (member_id, menu_id, quantity, order_date, total, status) VALUES (%s,%s,%s,%s,%s,'confirmed')",
                        (member['member_id'], menu[0]['menu_id'], qty, d.isoformat(), total), fetch=False)

        for member in all_members:
            assign = query_row("SELECT a.assign_id, a.monthly_rent FROM assignments a WHERE a.member_id = %s AND a.active = 1", (member['member_id'],))
            if assign:
                for i in range(3):
                    d = today - datetime.timedelta(days=30*i)
                    status = 'completed' if i > 0 else 'pending'
                    query("INSERT INTO payments (payment_date, amount, payment_method, payment_type, status, assignment_id, member_id) VALUES (%s,%s,%s,%s,%s,%s,%s)",
                        (d.isoformat(), assign['monthly_rent'], 'Cash' if i % 2 == 0 else 'Mobile Banking', 'rent', status, assign['assign_id'], member['member_id']), fetch=False)

        return jsonify({'success': True, 'message': 'Historical data added: 3 members, 6 months bills (some unpaid), 30 days food menu, meal orders & payments!'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# ===================== RUN =====================

if __name__ == '__main__':
    app.run(debug=True, port=5000)
