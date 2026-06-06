// ==================== DASHBOARD ====================
async function loadDashboard() {
    const res = await fetch('/api/admin/dashboard/stats');
    const data = await res.json();
    if (!data.success) return;

    const s = data.data;
    document.getElementById('statsGrid').innerHTML = `
        <div class="stat-card"><h3>Active Members</h3><p class="stat-number">${s.active_members}</p></div>
        <div class="stat-card"><h3>Total Rooms</h3><p class="stat-number">${s.total_rooms}</p></div>
        <div class="stat-card"><h3>Pending Bills</h3><p class="stat-number">${s.pending_bills}</p></div>
        <div class="stat-card"><h3>Total Income</h3><p class="stat-number">${Number(s.total_income).toLocaleString()} BDT</p></div>
    `;

    const tbody = document.getElementById('recentPaymentsBody');
    if (s.recent_payments && s.recent_payments.length) {
        tbody.innerHTML = s.recent_payments.map(p => `
            <tr><td>${p.payment_date}</td><td>${p.member_name || 'N/A'}</td><td>${Number(p.amount).toLocaleString()} BDT</td><td>${p.payment_method}</td></tr>
        `).join('');
    } else {
        tbody.innerHTML = '<tr><td colspan="4">No recent payments</td></tr>';
    }
}

// ==================== MEMBERS ====================
async function loadMembers() {
    const res = await fetch('/api/admin/members');
    const data = await res.json();
    if (!data.success) return;

    const userSelect = document.getElementById('memberUserId');
    userSelect.innerHTML = '<option value="">-- Select User --</option>' +
        (data.available_users || []).map(u => `<option value="${u.user_id}">${u.username} (${u.email})</option>`).join('');

    document.getElementById('memberRegDate').value = getToday();

    const tbody = document.getElementById('membersTableBody');
    if (data.data.length === 0) {
        tbody.innerHTML = '<tr><td colspan="9">No members found</td></tr>';
        return;
    }
    tbody.innerHTML = data.data.map(m => `
        <tr>
            <td>${m.member_id}</td>
            <td>${m.member_name}</td>
            <td>${m.phone || ''}</td>
            <td>${m.occupation || ''}</td>
            <td>${m.district || ''}</td>
            <td>${m.room_no ? m.building + ' - Room ' + m.room_no : '<span class="text-muted">Not assigned</span>'}</td>
            <td>${m.reg_date || ''}</td>
            <td><span class="badge bg-${m.status === 'active' ? 'success' : 'secondary'}">${m.status}</span></td>
            <td><button class="btn btn-sm btn-outline-primary" onclick="openEditMember(${m.member_id}, '${m.member_name}', '${m.phone || ''}', '${m.occupation || ''}', '${m.district || ''}', '${m.status}')">Edit</button></td>
        </tr>
    `).join('');
}

document.getElementById('memberForm')?.addEventListener('submit', async function(e) {
    e.preventDefault();
    const editId = document.getElementById('editMemberId').value;
    const formData = new FormData();
    formData.append('member_name', document.getElementById('memberName').value);
    formData.append('phone', document.getElementById('memberPhone').value);
    formData.append('occupation', document.getElementById('memberOccupation').value);
    formData.append('district', document.getElementById('memberDistrict').value);
    formData.append('reg_date', document.getElementById('memberRegDate').value);
    formData.append('gender', document.getElementById('memberGender').value);

    let url, msg;
    if (editId) {
        formData.append('member_id', editId);
        formData.append('status', document.getElementById('memberStatus').value);
        url = '/api/admin/members/update';
        msg = 'Member updated';
    } else {
        formData.append('user_id', document.getElementById('memberUserId').value);
        url = '/api/admin/members';
        msg = 'Member added';
    }

    const res = await fetch(url, { method: 'POST', body: formData });
    const data = await res.json();
    showAlert(data.message, data.success ? 'success' : 'error');
    if (data.success) {
        this.reset();
        document.getElementById('memberRegDate').value = getToday();
        document.getElementById('editMemberId').value = '';
        document.getElementById('memberFormTitle').textContent = 'Add New Member';
        document.getElementById('userSelectGroup').style.display = 'block';
        document.getElementById('memberUserId').required = true;
        document.getElementById('memberStatusGroup').style.display = 'none';
        document.getElementById('memberSubmitBtn').textContent = 'Add Member';
        document.getElementById('memberCancelBtn').style.display = 'none';
        loadMembers();
    }
});

function openEditMember(id, name, phone, occ, district, status) {
    document.getElementById('editMemberId').value = id;
    document.getElementById('memberFormTitle').textContent = 'Update Member';
    document.getElementById('memberName').value = name;
    document.getElementById('memberPhone').value = phone;
    document.getElementById('memberOccupation').value = occ;
    document.getElementById('memberDistrict').value = district;
    document.getElementById('userSelectGroup').style.display = 'none';
    document.getElementById('memberUserId').required = false;
    document.getElementById('memberStatusGroup').style.display = 'block';
    document.getElementById('memberStatus').value = status;
    document.getElementById('memberSubmitBtn').textContent = 'Update Member';
    document.getElementById('memberCancelBtn').style.display = 'inline-block';
    window.scrollTo(0, 0);
}

function cancelMemberEdit() {
    document.getElementById('editMemberId').value = '';
    document.getElementById('memberFormTitle').textContent = 'Add New Member';
    document.getElementById('memberForm').reset();
    document.getElementById('memberRegDate').value = getToday();
    document.getElementById('userSelectGroup').style.display = 'block';
    document.getElementById('memberUserId').required = true;
    document.getElementById('memberStatusGroup').style.display = 'none';
    document.getElementById('memberSubmitBtn').textContent = 'Add Member';
    document.getElementById('memberCancelBtn').style.display = 'none';
}

// ==================== ROOMS ====================
async function loadRooms() {
    const rtypes = await (await fetch('/api/admin/room-types')).json();
    if (rtypes.success) {
        const sel = document.getElementById('roomTypeId');
        sel.innerHTML = '<option value="">-- Select --</option>' +
            rtypes.data.map(t => `<option value="${t.id}">${t.name} (Cap: ${t.capacity}, Rent: ${Number(t.rent).toLocaleString()} BDT)</option>`).join('');
    }

    const res = await fetch('/api/admin/rooms');
    const data = await res.json();
    const tbody = document.getElementById('roomsTableBody');
    if (!data.success || !data.data.length) {
        tbody.innerHTML = '<tr><td colspan="7">No rooms</td></tr>';
        return;
    }
    tbody.innerHTML = data.data.map(r => `
        <tr>
            <td>${r.room_id}</td>
            <td>${r.room_no}</td>
            <td>${r.floor}</td>
            <td>${r.building}</td>
            <td>${r.type_name || ''}</td>
            <td>${r.base_rent ? Number(r.base_rent).toLocaleString() + ' BDT' : ''}</td>
            <td><span class="badge bg-${r.is_available ? 'success' : 'danger'}">${r.is_available ? 'Available' : 'Occupied'}</span></td>
        </tr>
    `).join('');
}

document.getElementById('roomTypeForm')?.addEventListener('submit', async function(e) {
    e.preventDefault();
    const fd = new FormData();
    fd.append('name', document.getElementById('rtName').value);
    fd.append('capacity', document.getElementById('rtCapacity').value);
    fd.append('rent', document.getElementById('rtRent').value);
    const res = await fetch('/api/admin/room-types', { method: 'POST', body: fd });
    const data = await res.json();
    showAlert(data.message, data.success ? 'success' : 'error');
    if (data.success) { this.reset(); loadRooms(); }
});

document.getElementById('roomForm')?.addEventListener('submit', async function(e) {
    e.preventDefault();
    const fd = new FormData();
    fd.append('room_no', document.getElementById('roomNo').value);
    fd.append('floor', document.getElementById('roomFloor').value);
    fd.append('building', document.getElementById('roomBuilding').value);
    fd.append('type_id', document.getElementById('roomTypeId').value);
    fd.append('is_available', document.getElementById('roomStatus').value);
    const res = await fetch('/api/admin/rooms', { method: 'POST', body: fd });
    const data = await res.json();
    showAlert(data.message, data.success ? 'success' : 'error');
    if (data.success) { this.reset(); loadRooms(); }
});

// ==================== ASSIGNMENTS ====================
async function loadAssignments() {
    const res = await fetch('/api/admin/assignments');
    const data = await res.json();
    if (!data.success) return;

    const d = data.data;
    document.getElementById('assignMemberId').innerHTML = '<option value="">-- Select --</option>' +
        (d.available_members || []).map(m => `<option value="${m.member_id}">${m.member_name}</option>`).join('');
    document.getElementById('assignRoomId').innerHTML = '<option value="">-- Select --</option>' +
        (d.available_rooms || []).map(r => `<option value="${r.room_id}" data-rent="${r.rent}">${r.building} - Room ${r.room_no} (${Number(r.rent).toLocaleString()} BDT)</option>`).join('');
    document.getElementById('assignCheckIn').value = getToday();

    const tbody = document.getElementById('assignmentsTableBody');
    if (!d.assignments || !d.assignments.length) {
        tbody.innerHTML = '<tr><td colspan="6">No active assignments</td></tr>';
        return;
    }
    tbody.innerHTML = d.assignments.map(a => `
        <tr>
            <td>${a.assign_id}</td>
            <td>${a.member_name}</td>
            <td>${a.building} - Room ${a.room_no}</td>
            <td>${a.check_in}</td>
            <td>${Number(a.monthly_rent).toLocaleString()} BDT</td>
            <td><button class="btn btn-sm btn-outline-danger" onclick="checkout(${a.assign_id})">Check-out</button></td>
        </tr>
    `).join('');
}

function updateRent() {
    const sel = document.getElementById('assignRoomId');
    const opt = sel.options[sel.selectedIndex];
    if (opt && opt.dataset.rent) {
        document.getElementById('assignRent').value = opt.dataset.rent;
    }
}

async function checkout(assignId) {
    if (!confirm('Confirm check-out?')) return;
    const fd = new FormData();
    fd.append('assign_id', assignId);
    const res = await fetch('/api/admin/assignments/checkout', { method: 'POST', body: fd });
    const data = await res.json();
    showAlert(data.message, data.success ? 'success' : 'error');
    if (data.success) loadAssignments();
}

document.getElementById('assignForm')?.addEventListener('submit', async function(e) {
    e.preventDefault();
    const fd = new FormData(this);
    const res = await fetch('/api/admin/assignments', { method: 'POST', body: fd });
    const data = await res.json();
    showAlert(data.message, data.success ? 'success' : 'error');
    if (data.success) { this.reset(); loadAssignments(); }
});

// ==================== FOOD MENU ====================
async function loadFoodMenu() {
    const res = await fetch('/api/admin/food-menu');
    const data = await res.json();
    document.getElementById('menuDate').value = getToday();

    const tbody = document.getElementById('foodMenuTableBody');
    if (!data.success || !data.data.length) {
        tbody.innerHTML = '<tr><td colspan="6">No menu items</td></tr>';
        return;
    }
    tbody.innerHTML = data.data.map(m => `
        <tr>
            <td>${m.menu_id}</td>
            <td>${m.menu_date}</td>
            <td>${m.item}</td>
            <td>${Number(m.price).toLocaleString()} BDT</td>
            <td>${m.meal_type}</td>
            <td><span class="badge bg-${m.available ? 'success' : 'secondary'}">${m.available ? 'Available' : 'Not Available'}</span></td>
        </tr>
    `).join('');
}

document.getElementById('foodMenuForm')?.addEventListener('submit', async function(e) {
    e.preventDefault();
    const fd = new FormData(this);
    const res = await fetch('/api/admin/food-menu', { method: 'POST', body: fd });
    const data = await res.json();
    showAlert(data.message, data.success ? 'success' : 'error');
    if (data.success) { this.reset(); loadFoodMenu(); }
});

// ==================== UTILITY BILLS ====================
async function loadUtilityBills() {
    const res = await fetch('/api/admin/utility-bills');
    const data = await res.json();
    if (!data.success) return;

    const rooms = data.data.rooms || [];
    document.getElementById('billRoomId').innerHTML = '<option value="">-- Select --</option>' +
        rooms.map(r => `<option value="${r.room_id}">${r.building} - Room ${r.room_no}</option>`).join('');

    const tbody = document.getElementById('billsTableBody');
    const bills = data.data.bills || [];
    if (!bills.length) {
        tbody.innerHTML = '<tr><td colspan="8">No bills</td></tr>';
        return;
    }
    tbody.innerHTML = bills.map(b => `
        <tr>
            <td>${b.bill_id}</td>
            <td>${b.bill_month}</td>
            <td>${b.building} - Room ${b.room_no}</td>
            <td>${b.bill_type}</td>
            <td>${Number(b.amount).toLocaleString()} BDT</td>
            <td>${b.due_date}</td>
            <td><span class="badge bg-${b.status === 'paid' ? 'success' : 'danger'}">${b.status}</span></td>
            <td>${b.status === 'unpaid' ? `<button class="btn btn-sm btn-outline-success" onclick="markBillPaid(${b.bill_id})">Mark Paid</button>` : ''}</td>
        </tr>
    `).join('');
}

async function markBillPaid(billId) {
    const fd = new FormData();
    fd.append('bill_id', billId);
    const res = await fetch('/api/admin/utility-bills/mark-paid', { method: 'POST', body: fd });
    const data = await res.json();
    showAlert(data.message, data.success ? 'success' : 'error');
    if (data.success) loadUtilityBills();
}

document.getElementById('billForm')?.addEventListener('submit', async function(e) {
    e.preventDefault();
    const fd = new FormData(this);
    const res = await fetch('/api/admin/utility-bills', { method: 'POST', body: fd });
    const data = await res.json();
    showAlert(data.message, data.success ? 'success' : 'error');
    if (data.success) { this.reset(); loadUtilityBills(); }
});

// ==================== PAYMENTS ====================
async function loadPayments() {
    document.getElementById('payDate').value = getToday();

    const res = await fetch('/api/admin/payments');
    const data = await res.json();
    if (!data.success) return;

    const assignSel = document.getElementById('payAssignmentId');
    assignSel.innerHTML = '<option value="">-- None --</option>' +
        (data.data.assignments || []).map(a => `<option value="${a.assign_id}">${a.member_name} - ${Number(a.monthly_rent).toLocaleString()} BDT</option>`).join('');

    const tbody = document.getElementById('paymentsTableBody');
    const payments = data.data.payments || [];
    if (!payments.length) {
        tbody.innerHTML = '<tr><td colspan="7">No payments</td></tr>';
        return;
    }
    tbody.innerHTML = payments.map(p => `
        <tr>
            <td>${p.payment_id}</td>
            <td>${p.payment_date}</td>
            <td>${p.member_name || 'N/A'}</td>
            <td>${Number(p.amount).toLocaleString()} BDT</td>
            <td>${p.payment_method}</td>
            <td>${p.payment_type}</td>
            <td><span class="badge bg-${p.status === 'completed' ? 'success' : 'warning'}">${p.status}</span></td>
        </tr>
    `).join('');
}

document.getElementById('paymentForm')?.addEventListener('submit', async function(e) {
    e.preventDefault();
    const fd = new FormData(this);
    const res = await fetch('/api/admin/payments', { method: 'POST', body: fd });
    const data = await res.json();
    showAlert(data.message, data.success ? 'success' : 'error');
    if (data.success) { this.reset(); loadPayments(); }
});

// ==================== REPORTS ====================
async function loadReports() {
    const res = await fetch('/api/admin/reports');
    const data = await res.json();
    if (!data.success) return;
    const d = data.data;

    document.getElementById('reportMembersBody').innerHTML = (d.members || []).map(m => `
        <tr><td>${m.member_id}</td><td>${m.member_name}</td><td>${m.phone || ''}</td><td>${m.occupation || ''}</td><td>${m.district || ''}</td>
        <td><span class="badge bg-${m.status === 'active' ? 'success' : 'secondary'}">${m.status}</span></td></tr>
    `).join('') || '<tr><td colspan="6">No members</td></tr>';

    document.getElementById('reportPaymentsBody').innerHTML = (d.payments || []).map(p => `
        <tr><td>${p.payment_id}</td><td>${p.payment_date}</td><td>${p.member_name || 'N/A'}</td>
        <td>${Number(p.amount).toLocaleString()} BDT</td><td>${p.payment_method}</td><td>${p.payment_type}</td>
        <td><span class="badge bg-${p.status === 'completed' ? 'success' : 'warning'}">${p.status}</span></td></tr>
    `).join('') || '<tr><td colspan="7">No payments</td></tr>';

    document.getElementById('reportRoomsBody').innerHTML = (d.rooms || []).map(r => `
        <tr><td>${r.room_id}</td><td>${r.room_no}</td><td>${r.building}</td><td>${r.type_name || ''}</td>
        <td>${r.rent ? Number(r.rent).toLocaleString() + ' BDT' : ''}</td>
        <td><span class="badge bg-${r.is_available ? 'success' : 'danger'}">${r.is_available ? 'Available' : 'Occupied'}</span></td></tr>
    `).join('') || '<tr><td colspan="6">No rooms</td></tr>';

    document.getElementById('reportFoodBody').innerHTML = (d.orders || []).map(o => `
        <tr><td>${o.order_id}</td><td>${o.member_name}</td><td>${o.item}</td><td>${o.quantity}</td>
        <td>${Number(o.total).toLocaleString()} BDT</td><td>${o.order_date}</td>
        <td><span class="badge bg-${o.status === 'confirmed' ? 'success' : o.status === 'pending' ? 'warning' : 'secondary'}">${o.status}</span></td></tr>
    `).join('') || '<tr><td colspan="7">No orders</td></tr>';
}
