// =========================
// Finance Requests Toggle
// =========================
document.addEventListener("DOMContentLoaded", function () {
  try {
    const cardBtn = document.getElementById("reqCardViewBtn");
    const tableBtn = document.getElementById("reqTableViewBtn");
    const cardContainer = document.getElementById("requestCards");
    const tableContainer = document.getElementById("requestTable");

    if (!cardBtn || !tableBtn || !cardContainer || !tableContainer) return;

    const saved = localStorage.getItem("finance_view") || "card";

    function showCard() {
      cardContainer.style.display = "block";
      tableContainer.style.display = "none";
      cardBtn.classList.add("active");
      tableBtn.classList.remove("active");
      localStorage.setItem("finance_view", "card");
      cardContainer.setAttribute("aria-hidden", "false");
      tableContainer.setAttribute("aria-hidden", "true");
    }

    function showTable() {
      cardContainer.style.display = "none";
      tableContainer.style.display = "block";
      tableBtn.classList.add("active");
      cardBtn.classList.remove("active");
      localStorage.setItem("finance_view", "table");
      cardContainer.setAttribute("aria-hidden", "true");
      tableContainer.setAttribute("aria-hidden", "false");
    }

    saved === "table" ? showTable() : showCard();
    cardBtn.addEventListener("click", showCard);
    tableBtn.addEventListener("click", showTable);
  } catch (err) {
    console.error("finance_requests_toggle.js error:", err);
  }
});

// =========================
// Finance Requests AJAX
// =========================
document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".ajax-action").forEach(button => {
    button.addEventListener("click", async function () {
      const url = this.dataset.url;
      const card = this.closest("[data-request-id]");
      const badge = card?.querySelector(".badge");
      const actionRow = card?.querySelector(".action-row");

      try {
        const response = await fetch(url, {
          method: "POST",
          headers: {
            "X-CSRFToken": getCookie("csrftoken"),
            "X-Requested-With": "XMLHttpRequest"
          }
        });
        const data = await response.json();
        if (data.success) {
          badge.textContent = data.status;
          badge.className = "badge status-" + data.status.toLowerCase();
          if (actionRow) actionRow.innerHTML = `<p class="processed-text"><em>${data.status}</em></p>`;
        } else {
          alert(data.error || "Action failed.");
        }
      } catch (err) {
        console.error("Error:", err);
        alert("Network error. Try again.");
      }
    });
  });
});

function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== "") {
    document.cookie.split(";").forEach(cookie => {
      cookie = cookie.trim();
      if (cookie.startsWith(name + "=")) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
      }
    });
  }
  return cookieValue;
}

// =========================
// HR Dashboard Clock
// =========================
(function () {
  function updateTime() {
    const now = new Date();
    const options = { year: 'numeric', month: 'short', day: 'numeric' };
    const dateStr = now.toLocaleDateString(undefined, options);
    const timeStr = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: true });
    const dateElement = document.getElementById('current-date');
    const timeElement = document.getElementById('current-time');
    if (dateElement) dateElement.textContent = dateStr;
    if (timeElement) timeElement.textContent = timeStr;
  }
  updateTime();
  setInterval(updateTime, 60000);
})();

// =========================
// HR Department
// =========================
document.addEventListener("DOMContentLoaded", function () {
  const toggleBtn = document.getElementById('deptToggleBtn');
  const cardView = document.getElementById('cardView');
  const tableView = document.getElementById('tableView');

  toggleBtn && toggleBtn.addEventListener('click', () => {
    const showingCards = !cardView.classList.contains('hidden');
    cardView.classList.toggle('hidden', showingCards);
    tableView.classList.toggle('hidden', !showingCards);
    toggleBtn.innerHTML = showingCards
      ? '<i class="fas fa-th-large"></i> Switch to Card View'
      : '<i class="fas fa-th-list"></i> Switch to Table View';
  });

  const addBtn = document.getElementById('addDeptBtn');
  addBtn && addBtn.addEventListener('click', () => alert('Add New Department — modal will open here (to be implemented).'));

  function onViewClicked(deptName) {
    const ops = document.getElementById('deptOperations');
    const staff = document.getElementById('deptStaff');
    const analytics = document.getElementById('deptAnalytics');
    [ops, staff, analytics].forEach(el => el && el.classList.remove('hidden'));
    ['opsDeptName', 'staffDeptName', 'analyticsDeptName'].forEach(id => {
      const el = document.getElementById(id);
      if (el) el.textContent = deptName;
    });
    if (ops) setTimeout(() => ops.scrollIntoView({ behavior: 'smooth', block: 'start' }), 120);
    initCharts(deptName);
  }

  document.querySelectorAll('.btn-view').forEach(btn => {
    btn.addEventListener('click', e => {
      const card = e.target.closest('.dept-card');
      const row = e.target.closest('tr');
      const deptName = card?.dataset.dept || card?.querySelector('h3')?.innerText || row?.dataset.dept || row?.children[0]?.innerText || 'Department';
      onViewClicked(deptName);
    });
  });

  function initCharts(deptName) {
    const chartConfigs = [
      { id: 'staffGrowthChart', type: 'line', data: [20, 22, 24, 26, 28] },
      { id: 'genderRatioChart', type: 'doughnut', data: [60, 40] },
      { id: 'attritionChart', type: 'bar', data: [2, 3, 1.5, 2.8] },
      { id: 'budgetChart', type: 'pie', data: [65, 35] }
    ];
    chartConfigs.forEach(({ id, type, data }) => {
      const ctx = document.getElementById(id);
      if (!ctx) return;
      if (ctx._chart) ctx._chart.destroy();
      ctx._chart = new Chart(ctx, {
        type,
        data: {
          labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May'],
          datasets: [{ label: deptName, data, backgroundColor: ['#0055aa', '#08bd4a', '#ef4444', '#2563eb'] }]
        },
        options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'bottom' } } }
      });
    });
  }
});

// =========================
// Toggle Department Analytics
// =========================
document.addEventListener('DOMContentLoaded', function () {
  const toggleAnalyticsBtn = document.getElementById('toggleAnalyticsBtn');
  const analyticsSection = document.getElementById('deptAnalytics');
  if (!toggleAnalyticsBtn || !analyticsSection) return;

  function updateAnalyticsButton() {
    const visible = !analyticsSection.classList.contains('hidden');
    toggleAnalyticsBtn.innerHTML = visible
      ? '<i class="fas fa-chart-bar"></i>&nbsp; Hide Analytics'
      : '<i class="fas fa-chart-bar"></i>&nbsp; Show Analytics';
  }

  updateAnalyticsButton();
  toggleAnalyticsBtn.addEventListener('click', e => {
    e.preventDefault();
    analyticsSection.classList.toggle('hidden');
    updateAnalyticsButton();
  });
});

// =========================
// Alerts Dismiss
// =========================
document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".alert-dismiss").forEach(btn => {
    btn.addEventListener("click", e => e.target.closest("li").remove());
  });
});

// =========================
// Payroll
// =========================
document.addEventListener("DOMContentLoaded", function () {
  const toggleBtn = document.getElementById("togglePayrollBtn");
  const previewSection = document.getElementById("payrollPreview");
  if (toggleBtn) toggleBtn.addEventListener("click", () => previewSection.classList.toggle("hidden"));

  const modal = document.getElementById('payslipModal');
  const modalEmployeeName = document.getElementById('modalEmployeeName');
  const modalGross = document.getElementById('modalGross');
  const modalDeductions = document.getElementById('modalDeductions');
  const modalNet = document.getElementById('modalNet');
  const closeModal = document.querySelector('.modal .close');

  document.querySelectorAll('.btn-view-payslip').forEach(btn => {
    btn.addEventListener('click', () => {
      const row = btn.closest('tr');
      modalEmployeeName.textContent = row.children[0].textContent;
      modalGross.textContent = row.children[2].textContent;
      modalDeductions.textContent = row.children[3].textContent;
      modalNet.textContent = row.children[4].textContent;
      modal.classList.remove('hidden');
    });
  });
  if (closeModal) closeModal.addEventListener('click', () => modal.classList.add('hidden'));

  const searchInput = document.getElementById('searchPayroll');
  if (searchInput) {
    searchInput.addEventListener('keyup', () => {
      const filter = searchInput.value.toLowerCase();
      document.querySelectorAll('#payrollBody tr').forEach(tr => {
        const name = tr.children[0].textContent.toLowerCase();
        tr.style.display = name.includes(filter) ? '' : 'none';
      });
    });
  }
});

// =========================
// HR Settings Navigation
// =========================
function navigateToSection(select) {
  const sectionId = select.value;
  if (sectionId) {
    const target = document.querySelector(sectionId);
    if (target) target.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
}

// =========================
// Message Centre
// =========================
document.addEventListener('DOMContentLoaded', () => {
  const tabs = document.querySelectorAll('.conversation-tabs .tab');
  const conversations = document.querySelectorAll('.conversation');
  const chatHeaderTitle = document.querySelector('.chat-header h3');
  const chatBody = document.querySelector('.chat-body');
  const chatInput = document.querySelector('.chat-footer input');
  const sendBtn = document.querySelector('.chat-footer button');

  function nowTime() {
    return new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }

  function appendMessage({ text, type = 'sent', time = null }) {
    if (!chatBody) return;
    const wrapper = document.createElement('div');
    wrapper.className = `message ${type}`;
    wrapper.innerHTML = `<p>${text}</p><span class="time">${time || nowTime()}</span>`;
    chatBody.appendChild(wrapper);
    chatBody.scrollTop = chatBody.scrollHeight;
  }

  function sendMessage() {
    const text = chatInput.value.trim();
    if (!text) return;
    appendMessage({ text, type: 'sent' });
    chatInput.value = '';
  }

  sendBtn?.addEventListener('click', e => { e.preventDefault(); sendMessage(); });
  chatInput?.addEventListener('keydown', e => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
  });

  tabs?.forEach(tab => {
    tab.addEventListener('click', () => {
      tabs.forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      const filter = tab.dataset.filter || tab.textContent.toLowerCase();
      conversations.forEach(conv => {
        const type = conv.dataset.type || '';
        conv.style.display = (filter === 'all' || type === filter) ? '' : 'none';
      });
    });
  });

  conversations?.forEach(item => {
    item.addEventListener('click', () => {
      conversations.forEach(c => c.classList.remove('active'));
      item.classList.add('active');
      const nameEl = item.querySelector('.details h4');
      const snippetEl = item.querySelector('.details p');
      const timeEl = item.querySelector('.time');
      if (chatHeaderTitle && nameEl) chatHeaderTitle.textContent = nameEl.textContent.trim();
      if (chatBody) {
        chatBody.innerHTML = '';
        appendMessage({ text: snippetEl?.textContent.trim() || '', type: 'received', time: timeEl?.textContent });
      }
    });
  });

  if (conversations.length) conversations[0].click();
});

// =========================
// Attendance (Dynamic Search & Filter Integrated)
// =========================
document.addEventListener("DOMContentLoaded", () => {
  const cardViewBtn = document.getElementById("cardViewBtn");
  const tableViewBtn = document.getElementById("tableViewBtn");
  const cardView = document.getElementById("cardView");
  const tableView = document.getElementById("tableView");
  const searchInput = document.getElementById("employeeSearch");
  const deptSelect = document.getElementById("departmentFilter");

  if (!cardView || !tableView || !cardViewBtn || !tableViewBtn || !searchInput || !deptSelect) return;

  // View toggle
  function showCardView() {
    cardView.classList.remove("hidden");
    tableView.classList.add("hidden");
    cardViewBtn.classList.add("active");
    tableViewBtn.classList.remove("active");
  }

  function showTableView() {
    tableView.classList.remove("hidden");
    cardView.classList.add("hidden");
    tableViewBtn.classList.add("active");
    cardViewBtn.classList.remove("active");
  }

  cardViewBtn.addEventListener("click", showCardView);
  tableViewBtn.addEventListener("click", showTableView);

  // Employee check-in/out status
  function updateEmployeeState(empId, state) {
    document.querySelectorAll(`[data-emp-id="${empId}"]`).forEach(el => {
      const statusEl = el.querySelector(".status");
      const checkinBtn = el.querySelector(".btn-checkin");
      const checkoutBtn = el.querySelector(".btn-checkout");
      if (!statusEl) return;

      if (state === "checked-in") {
        statusEl.textContent = "Checked In";
        statusEl.style.color = "green";
        checkinBtn && (checkinBtn.disabled = true);
        checkoutBtn && (checkoutBtn.disabled = false);
      } else if (state === "checked-out") {
        statusEl.textContent = "Checked Out";
        statusEl.style.color = "crimson";
        checkoutBtn && (checkoutBtn.disabled = true);
        checkinBtn && (checkinBtn.disabled = false);
      } else {
        statusEl.textContent = "Not Checked In";
        statusEl.style.color = "";
        checkinBtn && (checkinBtn.disabled = false);
        checkoutBtn && (checkoutBtn.disabled = true);
      }
    });
  }

  document.addEventListener("click", e => {
    const checkinBtn = e.target.closest(".btn-checkin");
    const checkoutBtn = e.target.closest(".btn-checkout");
    const parent = checkinBtn?.closest("[data-emp-id]") || checkoutBtn?.closest("[data-emp-id]");
    if (!parent) return;
    const empId = parent.getAttribute("data-emp-id");
    if (checkinBtn) updateEmployeeState(empId, "checked-in");
    if (checkoutBtn) updateEmployeeState(empId, "checked-out");
  });

  // Dynamic search & filter
  function applyFilters() {
    const query = searchInput.value.toLowerCase().trim();
    const deptFilter = deptSelect.value;

    // Card view
    cardView.querySelectorAll(".employee-card").forEach(card => {
      const name = (card.dataset.empName || "").toLowerCase();
      const id = (card.dataset.empId || "").toLowerCase();
      const dept = card.dataset.dept || "";

      const matchesSearch = !query || name.includes(query) || id.includes(query);
      const matchesDept = deptFilter === "all" || dept === deptFilter;

      card.style.display = matchesSearch && matchesDept ? "" : "none";
    });

    // Table view
    tableView.querySelectorAll("tr[data-emp-id]").forEach(row => {
      const name = (row.dataset.empName || "").toLowerCase();
      const id = (row.dataset.empId || "").toLowerCase();
      const dept = row.dataset.dept || "";

      const matchesSearch = !query || name.includes(query) || id.includes(query);
      const matchesDept = deptFilter === "all" || dept === deptFilter;

      row.style.display = matchesSearch && matchesDept ? "" : "none";
    });
  }

  searchInput.addEventListener("input", applyFilters);
  deptSelect.addEventListener("change", applyFilters);

  // Initialize
  showCardView();
});
