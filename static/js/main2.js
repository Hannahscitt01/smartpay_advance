/* ======================================================================
   HR & FINANCE DASHBOARD MASTER SCRIPT
   ----------------------------------------------------------------------
   This unified JavaScript file manages interactivity across modules:
     - Finance requests (toggle + AJAX)
     - HR dashboard clock
     - Department view toggle & charts
     - Attendance management (check-in / check-out)
     - Payroll interactions (payslip modal & search)
     - Message centre functionality
     - Alert handling & utilities (CSRF helper)
   ----------------------------------------------------------------------
  
====================================================================== */


/* ======================================================================
   1. FINANCE REQUESTS TOGGLE
   Handles switching between Card and Table views for finance requests.
====================================================================== */
document.addEventListener("DOMContentLoaded", function () {
  try {
    const cardBtn = document.getElementById("reqCardViewBtn");
    const tableBtn = document.getElementById("reqTableViewBtn");
    const cardContainer = document.getElementById("requestCards");
    const tableContainer = document.getElementById("requestTable");

    if (!cardBtn || !tableBtn || !cardContainer || !tableContainer) return;

    // Restore user's previous view preference
    const saved = localStorage.getItem("finance_view") || "card";

    // --- Show Card View ---
    function showCard() {
      cardContainer.style.display = "block";
      tableContainer.style.display = "none";
      cardBtn.classList.add("active");
      tableBtn.classList.remove("active");
      localStorage.setItem("finance_view", "card");
      cardContainer.setAttribute("aria-hidden", "false");
      tableContainer.setAttribute("aria-hidden", "true");
    }

    // --- Show Table View ---
    function showTable() {
      cardContainer.style.display = "none";
      tableContainer.style.display = "block";
      tableBtn.classList.add("active");
      cardBtn.classList.remove("active");
      localStorage.setItem("finance_view", "table");
      cardContainer.setAttribute("aria-hidden", "true");
      tableContainer.setAttribute("aria-hidden", "false");
    }

    // Initialize view
    saved === "table" ? showTable() : showCard();

    // Event listeners
    cardBtn.addEventListener("click", showCard);
    tableBtn.addEventListener("click", showTable);

  } catch (err) {
    console.error("Finance Requests Toggle Error:", err);
  }
});


/* ======================================================================
   2. FINANCE REQUESTS AJAX HANDLING
   Handles approval/rejection asynchronously with Django backend.
====================================================================== */
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
          // Update badge and replace action row
          badge.textContent = data.status;
          badge.className = "badge status-" + data.status.toLowerCase();
          if (actionRow)
            actionRow.innerHTML = `<p class="processed-text"><em>${data.status}</em></p>`;
        } else {
          alert(data.error || "Action failed.");
        }
      } catch (err) {
        console.error("Finance AJAX Error:", err);
        alert("Network error. Try again.");
      }
    });
  });
});


/* ======================================================================
   3. CSRF TOKEN HELPER
   Retrieves Django CSRF token from cookies.
   Single helper used across the file.
====================================================================== */
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


/* ======================================================================
   4. HR DASHBOARD CLOCK
   Displays real-time date and time on dashboard.
====================================================================== */
(function () {
  function updateTime() {
    const now = new Date();
    const options = { year: "numeric", month: "short", day: "numeric" };
    const dateStr = now.toLocaleDateString(undefined, options);
    const timeStr = now.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", hour12: true });

    const dateElement = document.getElementById("current-date");
    const timeElement = document.getElementById("current-time");

    if (dateElement) dateElement.textContent = dateStr;
    if (timeElement) timeElement.textContent = timeStr;
  }

  updateTime();
  setInterval(updateTime, 60000); // Update every 60s
})();


/* ======================================================================
   5. HR DEPARTMENT VIEW TOGGLE & CHART INITIALIZATION
   Manages department card/table toggle and chart visualization.
====================================================================== */
document.addEventListener("DOMContentLoaded", function () {
  const toggleBtn = document.getElementById("deptToggleBtn");
  const cardView = document.getElementById("cardView");
  const tableView = document.getElementById("tableView");

  // --- Toggle View ---
  toggleBtn && toggleBtn.addEventListener("click", () => {
    const showingCards = !cardView.classList.contains("hidden");
    cardView.classList.toggle("hidden", showingCards);
    tableView.classList.toggle("hidden", !showingCards);
    toggleBtn.innerHTML = showingCards
      ? '<i class="fas fa-th-large"></i> Switch to Card View'
      : '<i class="fas fa-th-list"></i> Switch to Table View';
  });

  // --- Placeholder Add Dept Button ---
  const addBtn = document.getElementById("addDeptBtn");
  addBtn && addBtn.addEventListener("click", () =>
    alert("Add New Department — modal coming soon.")
  );

  // --- On Department View Click ---
  function onViewClicked(deptName) {
    const ops = document.getElementById("deptOperations");
    const staff = document.getElementById("deptStaff");
    const analytics = document.getElementById("deptAnalytics");

    [ops, staff, analytics].forEach(el => el && el.classList.remove("hidden"));

    ["opsDeptName", "staffDeptName", "analyticsDeptName"].forEach(id => {
      const el = document.getElementById(id);
      if (el) el.textContent = deptName;
    });

    if (ops) setTimeout(() => ops.scrollIntoView({ behavior: "smooth" }), 120);
    initCharts(deptName);
  }

  // Attach event listeners to view buttons
  document.querySelectorAll(".btn-view").forEach(btn => {
    btn.addEventListener("click", e => {
      const card = e.target.closest(".dept-card");
      const row = e.target.closest("tr");
      const deptName =
        card?.dataset.dept ||
        card?.querySelector("h3")?.innerText ||
        row?.dataset.dept ||
        row?.children[0]?.innerText ||
        "Department";
      onViewClicked(deptName);
    });
  });

  // --- Chart Initialization (Placeholder) ---
  function initCharts(deptName) {
    const chartConfigs = [
      { id: "staffGrowthChart", type: "line", data: [20, 22, 24, 26, 28] },
      { id: "genderRatioChart", type: "doughnut", data: [60, 40] },
      { id: "attritionChart", type: "bar", data: [2, 3, 1.5, 2.8] },
      { id: "budgetChart", type: "pie", data: [65, 35] }
    ];

    chartConfigs.forEach(({ id, type, data }) => {
      const ctx = document.getElementById(id);
      if (!ctx) return;

      if (ctx._chart) ctx._chart.destroy();
      ctx._chart = new Chart(ctx, {
        type,
        data: {
          labels: ["Jan", "Feb", "Mar", "Apr", "May"],
          datasets: [{
            label: deptName,
            data,
            backgroundColor: ["#0055aa", "#08bd4a", "#ef4444", "#2563eb"]
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { position: "bottom" } }
        }
      });
    });
  }
});


/* ======================================================================
   6. TOGGLE DEPARTMENT ANALYTICS SECTION
   Shows or hides analytics area dynamically.
====================================================================== */
document.addEventListener("DOMContentLoaded", function () {
  const toggleAnalyticsBtn = document.getElementById("toggleAnalyticsBtn");
  const analyticsSection = document.getElementById("deptAnalytics");

  if (!toggleAnalyticsBtn || !analyticsSection) return;

  function updateAnalyticsButton() {
    const visible = !analyticsSection.classList.contains("hidden");
    toggleAnalyticsBtn.innerHTML = visible
      ? '<i class="fas fa-chart-bar"></i>&nbsp; Hide Analytics'
      : '<i class="fas fa-chart-bar"></i>&nbsp; Show Analytics';
  }

  updateAnalyticsButton();

  toggleAnalyticsBtn.addEventListener("click", e => {
    e.preventDefault();
    analyticsSection.classList.toggle("hidden");
    updateAnalyticsButton();
  });
});


/* ======================================================================
   7. ALERT DISMISSAL HANDLER
   Enables closing/dismissing notification alerts.
====================================================================== */
document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".alert-dismiss").forEach(btn => {
    btn.addEventListener("click", e => e.target.closest("li").remove());
  });
});


/* ======================================================================
   8. PAYROLL MODULE INTERACTIONS
   Manages payroll preview toggle, search, and payslip modal.
====================================================================== */
document.addEventListener("DOMContentLoaded", function () {
  const toggleBtn = document.getElementById("togglePayrollBtn");
  const previewSection = document.getElementById("payrollPreview");

  // Toggle Payroll Preview
  if (toggleBtn)
    toggleBtn.addEventListener("click", () =>
      previewSection.classList.toggle("hidden")
    );

  // Payslip Modal Setup
  const modal = document.getElementById("payslipModal");
  const modalEmployeeName = document.getElementById("modalEmployeeName");
  const modalGross = document.getElementById("modalGross");
  const modalDeductions = document.getElementById("modalDeductions");
  const modalNet = document.getElementById("modalNet");
  const closeModal = document.querySelector(".modal .close");

  document.querySelectorAll(".btn-view-payslip").forEach(btn => {
    btn.addEventListener("click", () => {
      const row = btn.closest("tr");
      modalEmployeeName.textContent = row.children[0].textContent;
      modalGross.textContent = row.children[2].textContent;
      modalDeductions.textContent = row.children[3].textContent;
      modalNet.textContent = row.children[4].textContent;
      modal.classList.remove("hidden");
    });
  });

  closeModal && closeModal.addEventListener("click", () => modal.classList.add("hidden"));

  // Payroll Search Filter
  const searchInput = document.getElementById("searchPayroll");
  if (searchInput) {
    searchInput.addEventListener("keyup", () => {
      const filter = searchInput.value.toLowerCase();
      document.querySelectorAll("#payrollBody tr").forEach(tr => {
        const name = tr.children[0].textContent.toLowerCase();
        tr.style.display = name.includes(filter) ? "" : "none";
      });
    });
  }
});


/* ======================================================================
   9. HR SETTINGS NAVIGATION
   Smoothly scrolls to selected HR setting section.
====================================================================== */
function navigateToSection(select) {
  const sectionId = select.value;
  if (sectionId) {
    const target = document.querySelector(sectionId);
    if (target) target.scrollIntoView({ behavior: "smooth", block: "start" });
  }
}


/* ======================================================================
   10. MESSAGE CENTRE FUNCTIONALITY
   Handles chat tabs, chat interaction, and simulated responses.
====================================================================== */
document.addEventListener("DOMContentLoaded", () => {
  const tabs = document.querySelectorAll(".conversation-tabs .tab");
  const conversations = document.querySelectorAll(".conversation");
  const chatHeaderTitle = document.querySelector(".chat-header h3");
  const chatBody = document.querySelector(".chat-body");
  const chatInput = document.querySelector(".chat-footer input");
  const sendBtn = document.querySelector(".chat-footer button");

  // Utility: Format Time
  function nowTime() {
    return new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  }

  // Append Message to Chat
  function appendMessage({ text, type = "sent", time = null }) {
    if (!chatBody) return;
    const wrapper = document.createElement("div");
    wrapper.className = `message ${type}`;
    wrapper.innerHTML = `<p>${text}</p><span class="time">${time || nowTime()}</span>`;
    chatBody.appendChild(wrapper);
    chatBody.scrollTop = chatBody.scrollHeight;
  }

  // Handle Sending Message
  function sendMessage() {
    const text = chatInput.value.trim();
    if (!text) return;
    appendMessage({ text, type: "sent" });
    chatInput.value = "";
  }

  // Event listeners for sending messages
  sendBtn?.addEventListener("click", e => { e.preventDefault(); sendMessage(); });
  chatInput?.addEventListener("keydown", e => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendMessage(); }
  });

  // Tab Filtering
  tabs?.forEach(tab => {
    tab.addEventListener("click", () => {
      tabs.forEach(t => t.classList.remove("active"));
      tab.classList.add("active");
      const filter = tab.dataset.filter || tab.textContent.toLowerCase();
      conversations.forEach(conv => {
        const type = conv.dataset.type || "";
        conv.style.display = (filter === "all" || type === filter) ? "" : "none";
      });
    });
  });

  // Conversation Selection
  conversations?.forEach(item => {
    item.addEventListener("click", () => {
      conversations.forEach(c => c.classList.remove("active"));
      item.classList.add("active");
      const nameEl = item.querySelector(".details h4");
      const snippetEl = item.querySelector(".details p");
      const timeEl = item.querySelector(".time");
      if (chatHeaderTitle && nameEl) chatHeaderTitle.textContent = nameEl.textContent.trim();
      if (chatBody) {
        chatBody.innerHTML = "";
        appendMessage({ text: snippetEl?.textContent.trim() || "", type: "received", time: timeEl?.textContent });
      }
    });
  });

  // Auto-load first conversation
  if (conversations.length) conversations[0].click();
});


/* ======================================================================
   11. ATTENDANCE MANAGEMENT
   Handles live check-in/out, filtering, and view toggling.
   Preserves your original application logic.
====================================================================== */
document.addEventListener("DOMContentLoaded", () => {
  const cardViewBtn = document.getElementById("cardViewBtn");
  const tableViewBtn = document.getElementById("tableViewBtn");
  const cardView = document.getElementById("cardView");
  const tableView = document.getElementById("tableView");
  const searchInput = document.getElementById("employeeSearch");
  const deptSelect = document.getElementById("departmentFilter");

  // Ensure DOM elements are present before wiring events
  if (!cardView || !tableView || !cardViewBtn || !tableViewBtn || !searchInput || !deptSelect) return;

  /* -----------------------------
     View Toggle
  ----------------------------- */
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

  /* -----------------------------
     CSRF Token Helper (Django)
  ----------------------------- */
  function getCsrfToken() {
    const tokenEl = document.querySelector("[name=csrfmiddlewaretoken]");
    return tokenEl ? tokenEl.value : "";
  }

  /* -----------------------------
     Update Employee State in UI
     - Updates status text, color, hours and button enabled states
  ----------------------------- */
function updateEmployeeState(empId, label, color, hrs = 0) {
  // Select all rows or cards that belong to this employee
  document.querySelectorAll(`[data-emp-id="${empId}"]`).forEach(el => {
    // Try to locate elements both within and around the container
    const statusEl = el.querySelector(".status") || el.closest("tr")?.querySelector(".status");
    const checkinBtn = el.querySelector(".btn-checkin") || el.closest("tr")?.querySelector(".btn-checkin");
    const checkoutBtn = el.querySelector(".btn-checkout") || el.closest("tr")?.querySelector(".btn-checkout");
    const hoursEl = el.querySelector(".hours-worked") || el.closest("tr")?.querySelector(".hours-worked");

    // Update status text and color
    if (statusEl) {
      statusEl.textContent = label;
      statusEl.style.color = color || "";
    }

    // Update hours if available
    if (hoursEl && hrs) {
      hoursEl.textContent = `${hrs} hrs`;
    }

    // Toggle button states based on status
    if (label.startsWith("Checked In")) {
      if (checkinBtn) checkinBtn.disabled = true;
      if (checkoutBtn) checkoutBtn.disabled = false;
    } else if (label.startsWith("Checked Out")) {
      if (checkoutBtn) checkoutBtn.disabled = true;
      if (checkinBtn) checkinBtn.disabled = false;
    }
  });
}


  /* -----------------------------
     Handle Check-In / Check-Out
     - Sends request to /attendance_action/
     - Expects JSON {status: "success", action: "checkin"/"checkout", ...}
  ----------------------------- */
  async function handleAttendanceAction(empId, action) {
    try {
      const csrfToken = getCsrfToken();

      // Send request to Django backend
      const response = await fetch("/attendance_action/", {
        method: "POST",
        headers: {
          "X-CSRFToken": csrfToken,
          "Content-Type": "application/x-www-form-urlencoded",
        },
        body: new URLSearchParams({ staff_id: empId, action }),
      });

      if (!response.ok) throw new Error("Network response was not OK");

      const data = await response.json();

      if (data.status === "success") {
        if (data.action === "checkin") {
          let label = "Checked In";
          if (data.late_minutes > 0 && data.late_minutes <= 30) {
            label += ` (Late ${data.late_minutes} min, auto-deducted leave)`;
          } else if (data.late_minutes > 30) {
            label = "Checked In (Late – Explanation Required)";
          }
          updateEmployeeState(empId, label, "green");
        } else if (data.action === "checkout") {
          const hrs = data.hours_worked || 0;
          const label = `Checked Out (${hrs} hrs)`;
          updateEmployeeState(empId, label, "crimson", hrs);
        }
      } else {
        alert(data.message || "Error performing attendance action.");
      }
    } catch (error) {
      console.error("Attendance Network Error:", error);
      alert("Network or server error. Please check the console for details.");
    }
  }

  /* -----------------------------
     Event Listeners for Buttons
     - Delegated click listener handles both checkin and checkout
  ----------------------------- */
  document.addEventListener("click", e => {
    const checkinBtn = e.target.closest(".btn-checkin");
    const checkoutBtn = e.target.closest(".btn-checkout");
    const parent = checkinBtn?.closest("[data-emp-id]") || checkoutBtn?.closest("[data-emp-id]");
    if (!parent) return;
    const empId = parent.getAttribute("data-emp-id");
    if (checkinBtn) handleAttendanceAction(empId, "checkin");
    if (checkoutBtn) handleAttendanceAction(empId, "checkout");
  });

  /* -----------------------------
     Search & Filter
  ----------------------------- */
  function applyFilters() {
    const query = searchInput.value.toLowerCase().trim();
    const deptFilter = deptSelect.value;

    // Card View
    cardView.querySelectorAll(".employee-card").forEach(card => {
      const name = (card.dataset.empName || "").toLowerCase();
      const id = (card.dataset.empId || "").toLowerCase();
      const dept = card.dataset.dept || "";
      const matchesSearch = !query || name.includes(query) || id.includes(query);
      const matchesDept = deptFilter === "all" || dept === deptFilter;
      card.style.display = matchesSearch && matchesDept ? "" : "none";
    });

    // Table View
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

  // Default to card view on load
  showCardView();
});
