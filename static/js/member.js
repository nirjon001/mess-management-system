// ==================== DASHBOARD ====================
async function loadDashboard() {
    const res = await fetch('/api/member/dashboard');
    const data = await res.json();
    if (!data.success) {
        document.getElementById('memberStatsGrid').innerHTML = `<div class="alert alert-warning">${data.message}</div>`;
        return;
    }
    const d = data.data;

    document.getElementById('memberStatsGrid').innerHTML = `
        <div class="stat-card"><h3>Monthly Rent</h3><p class="stat-number">${Number(d.monthly_rent).toLocaleString()} BDT</p></div>
        <div class="stat-card"><h3>Rent Paid</h3><p class="stat-number">${Number(d.rent_paid_this_month).toLocaleString()} BDT</p></div>
        <div class="stat-card"><h3>Rent Due</h3><p class="stat-number">${Number(d.rent_due).toLocaleString()} BDT</p></div>
        <div class="stat-card"><h3>Unpaid Bills</h3><p class="stat-number">${d.unpaid_bills}</p></div>
    `;

    const infoDiv = document.getElementById('memberRoomInfo');
    if (d.assignment) {
        const dueColor = d.rent_due > 0 ? '#e74c3c' : '#27ae60';
        infoDiv.innerHTML = `
            <div class="info-box d-flex flex-wrap gap-3 align-items-center">
                <span><strong>Room:</strong> ${d.assignment.building} - Room ${d.assignment.room_no}</span>
                <span><strong>Type:</strong> ${d.assignment.type_name || 'N/A'}</span>
                <span><strong>Monthly Rent:</strong> ${Number(d.monthly_rent).toLocaleString()} BDT</span>
                <span><strong>Paid:</strong> ${Number(d.rent_paid_this_month).toLocaleString()} BDT</span>
                <span style="color:${dueColor};font-weight:bold;"><strong>Due:</strong> ${Number(d.rent_due).toLocaleString()} BDT</span>
            </div>
        `;
    }
}

// ==================== BILLS ====================
async function loadBills() {
    const res = await fetch('/api/member/bills');
    const data = await res.json();
    const content = document.getElementById('billsContent');

    if (!data.success) {
        content.innerHTML = `<div class="alert alert-warning">${data.message}</div>`;
        return;
    }

    let html = '';
    if (data.room) {
        html += `<div class="info-box"><strong>Room:</strong> ${data.room.room_no || ''}</div>`;
    }

    if (!data.data || !data.data.length) {
        html += '<div class="alert alert-info">No utility bills found for your room.</div>';
    } else {
        html += `
            <div class="card">
                <div class="card-header"><h5 class="mb-0">Utility Bills</h5></div>
                <div class="card-body">
                    <div class="table-responsive">
                        <table class="table table-hover">
                            <thead><tr><th>Month</th><th>Type</th><th>Amount</th><th>Paid</th><th>Outstanding</th><th>Due Date</th><th>Status</th><th>Action</th></tr></thead>
                            <tbody>
                                ${data.data.map(b => `
                                    <tr>
                                        <td>${b.bill_month}</td>
                                        <td>${b.bill_type}</td>
                                        <td>${Number(b.amount).toLocaleString()} BDT</td>
                                        <td>${Number(b.paid_so_far || 0).toLocaleString()} BDT</td>
                                        <td><strong>${Number(b.outstanding || b.amount).toLocaleString()} BDT</strong></td>
                                        <td>${b.due_date}</td>
                                        <td><span class="badge bg-${b.status === 'paid' ? 'success' : 'danger'}">${b.status}</span></td>
                                        <td>${b.status === 'unpaid' ? `
                                            <div class="input-group input-group-sm" style="min-width:150px;">
                                                <input type="number" id="payBillAmount_${b.bill_id}" class="form-control" value="${Number(b.outstanding || b.amount)}" min="1" style="width:70px;">
                                                <button class="btn btn-success btn-sm" onclick="payBill(${b.bill_id})">Pay</button>
                                            </div>
                                        ` : '<span class="text-success">Paid</span>'}</td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        `;
    }
    content.innerHTML = html;
}

async function payBill(billId) {
    const amount = document.getElementById('payBillAmount_' + billId).value;
    if (!amount || amount <= 0) { showAlert('Enter a valid amount', 'error'); return; }
    const fd = new FormData();
    fd.append('payment_date', getToday());
    fd.append('amount', amount);
    fd.append('payment_method', 'Mobile Banking');
    fd.append('payment_type', 'utility');
    fd.append('bill_id', billId);
    const res = await fetch('/api/member/payments', { method: 'POST', body: fd });
    const data = await res.json();
    showAlert(data.message, data.success ? 'success' : 'error');
    if (data.success) loadBills();
}

// ==================== PAYMENTS ====================
async function loadPayments() {
    document.getElementById('mpDate').value = getToday();

    const dashRes = await fetch('/api/member/dashboard');
    const dashData = await dashRes.json();
    const rentStatusBody = document.getElementById('rentStatusBody');
    if (dashData.success && dashData.data.assignment) {
        const d = dashData.data;
        const dueColor = d.rent_due > 0 ? '#e74c3c' : '#27ae60';
        rentStatusBody.innerHTML = `
            <div class="row text-center">
                <div class="col-md-3"><strong>Monthly Rent</strong><br><span style="font-size:1.3rem;">${Number(d.monthly_rent).toLocaleString()} BDT</span></div>
                <div class="col-md-3"><strong>Paid This Month</strong><br><span style="font-size:1.3rem;color:#27ae60;">${Number(d.rent_paid_this_month).toLocaleString()} BDT</span></div>
                <div class="col-md-3"><strong>Due</strong><br><span style="font-size:1.3rem;color:${dueColor};font-weight:bold;">${Number(d.rent_due).toLocaleString()} BDT</span></div>
                <div class="col-md-3"><strong>Unpaid Bills</strong><br><span style="font-size:1.3rem;">${d.unpaid_bills}</span></div>
            </div>
        `;
    } else {
        rentStatusBody.innerHTML = '<div class="text-center text-muted">No room assigned</div>';
    }

    const res = await fetch('/api/member/payments');
    const data = await res.json();
    const tbody = document.getElementById('mpHistoryBody');
    if (!data.success || !data.data.length) {
        tbody.innerHTML = '<tr><td colspan="5">No payments yet</td></tr>';
        return;
    }
    tbody.innerHTML = data.data.map(p => `
        <tr>
            <td>${p.payment_date}</td>
            <td>${Number(p.amount).toLocaleString()} BDT</td>
            <td>${p.payment_method}</td>
            <td>${p.payment_type}</td>
            <td><span class="badge bg-${p.status === 'completed' ? 'success' : 'warning'}">${p.status}</span></td>
        </tr>
    `).join('');
}

document.getElementById('memberPaymentForm')?.addEventListener('submit', async function(e) {
    e.preventDefault();
    const fd = new FormData(this);
    const res = await fetch('/api/member/payments', { method: 'POST', body: fd });
    const data = await res.json();
    showAlert(data.message, data.success ? 'success' : 'error');
    if (data.success) { this.reset(); document.getElementById('mpDate').value = getToday(); loadPayments(); }
});

// ==================== FOOD BOOKING ====================
let fbMenuItems = [];

async function loadFoodBooking() {
    document.getElementById('fbDate').value = getToday();
    await filterMenu();
    await loadMyOrders();
}

async function filterMenu() {
    const date = document.getElementById('fbDate').value || getToday();
    const mealType = document.getElementById('fbMealType').value;
    let url = `/api/member/food-menu?date=${date}`;
    if (mealType) url += `&meal_type=${mealType}`;

    const res = await fetch(url);
    const data = await res.json();
    fbMenuItems = data.data || [];
    const tbody = document.getElementById('fbMenuBody');

    if (!fbMenuItems.length) {
        tbody.innerHTML = '<tr><td colspan="4">No menu items available</td></tr>';
        return;
    }
    tbody.innerHTML = fbMenuItems.map(m => `
        <tr>
            <td>${m.item}</td>
            <td>${Number(m.price).toLocaleString()} BDT</td>
            <td>${m.meal_type}</td>
            <td>
                <div class="input-group input-group-sm" style="width:140px;">
                    <input type="number" id="fbQty_${m.menu_id}" value="1" min="1" class="form-control" style="width:50px;">
                    <button class="btn btn-primary" onclick="orderFood(${m.menu_id})">Book</button>
                </div>
            </td>
        </tr>
    `).join('');
}

async function orderFood(menuId) {
    const qty = document.getElementById('fbQty_' + menuId).value || 1;
    const fd = new FormData();
    fd.append('menu_id', menuId);
    fd.append('quantity', qty);
    const res = await fetch('/api/member/order-food', { method: 'POST', body: fd });
    const data = await res.json();
    showAlert(data.message, data.success ? 'success' : 'error');
    if (data.success) loadMyOrders();
}

async function loadMyOrders() {
    const res = await fetch('/api/member/orders');
    const data = await res.json();
    const tbody = document.getElementById('fbOrdersBody');
    if (!data.success || !data.data.length) {
        tbody.innerHTML = '<tr><td colspan="5">No orders yet</td></tr>';
        return;
    }
    tbody.innerHTML = data.data.map(o => `
        <tr>
            <td>${o.order_date}</td>
            <td>${o.item} (${o.meal_type})</td>
            <td>${o.quantity}</td>
            <td>${Number(o.total).toLocaleString()} BDT</td>
            <td><span class="badge bg-${o.status === 'confirmed' ? 'success' : o.status === 'pending' ? 'warning' : 'secondary'}">${o.status}</span></td>
        </tr>
    `).join('');
}

// ==================== EXPENSES ====================
async function loadExpenses() {
    const res = await fetch('/api/member/expenses');
    const data = await res.json();
    if (!data.success) return;
    const d = data.data;

    const payBody = document.getElementById('expPaymentsBody');
    if (d.payments && d.payments.length) {
        payBody.innerHTML = d.payments.map(p => `
            <tr>
                <td>${p.payment_date}</td>
                <td>${Number(p.amount).toLocaleString()} BDT</td>
                <td>${p.payment_method}</td>
                <td>${p.payment_type}</td>
                <td><span class="badge bg-${p.status === 'completed' ? 'success' : 'warning'}">${p.status}</span></td>
            </tr>
        `).join('');
    } else {
        payBody.innerHTML = '<tr><td colspan="5">No payments</td></tr>';
    }

    const orderBody = document.getElementById('expOrdersBody');
    if (d.orders && d.orders.length) {
        orderBody.innerHTML = d.orders.map(o => `
            <tr>
                <td>${o.order_date}</td>
                <td>${o.item} (${o.meal_type})</td>
                <td>${o.quantity}</td>
                <td>${Number(o.total).toLocaleString()} BDT</td>
                <td><span class="badge bg-${o.status === 'confirmed' ? 'success' : o.status === 'pending' ? 'warning' : 'secondary'}">${o.status}</span></td>
            </tr>
        `).join('');
    } else {
        orderBody.innerHTML = '<tr><td colspan="5">No orders</td></tr>';
    }
}
