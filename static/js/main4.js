// static/js/attendance.js
document.addEventListener("DOMContentLoaded", () => {
  // Elements
  const cardViewBtn = document.getElementById("cardViewBtn");
  const tableViewBtn = document.getElementById("tableViewBtn");
  const cardView = document.getElementById("cardView");
  const tableView = document.getElementById("tableView");
  const searchInput = document.getElementById("employeeSearch");
  const deptSelect = document.getElementById("departmentFilter");

  // Safety checks
  if (!cardView || !tableView || !cardViewBtn || !tableViewBtn) {
    console.warn("attendance.js: required elements not found. Check template IDs.");
    return;
  }

  // Toggle handlers
  function showCardView() {
    cardView.classList.remove("hidden");
    tableView.classList.add("hidden");
    cardViewBtn.classList.add("active");
    tableViewBtn.classList.remove("active");
    cardView.setAttribute("aria-hidden", "false");
    tableView.setAttribute("aria-hidden", "true");
  }
  function showTableView() {
    tableView.classList.remove("hidden");
    cardView.classList.add("hidden");
    tableViewBtn.classList.add("active");
    cardViewBtn.classList.remove("active");
    tableView.setAttribute("aria-hidden", "false");
    cardView.setAttribute("aria-hidden", "true");
  }

  cardViewBtn.addEventListener("click", showCardView);
  tableViewBtn.addEventListener("click", showTableView);

  // Utility: update status & buttons across both views for an employee id
  function updateEmployeeState(empId, state) {
    // state: "checked-in" | "checked-out" | "not-checked-in"
    const wrappers = document.querySelectorAll(`[data-emp-id="${empId}"]`);
    wrappers.forEach(w => {
      const statusEl = w.querySelector(".status");
      const checkinBtn = w.querySelector(".btn-checkin");
      const checkoutBtn = w.querySelector(".btn-checkout");

      if (state === "checked-in") {
        if (statusEl) {
          statusEl.textContent = "Checked In";
          statusEl.style.color = "green";
        }
        if (checkinBtn) checkinBtn.disabled = true;
        if (checkoutBtn) checkoutBtn.disabled = false;
      } else if (state === "checked-out") {
        if (statusEl) {
          statusEl.textContent = "Checked Out";
          statusEl.style.color = "crimson";
        }
        if (checkoutBtn) checkoutBtn.disabled = true;
        if (checkinBtn) checkinBtn.disabled = false;
      } else {
        if (statusEl) {
          statusEl.textContent = "Not Checked In";
          statusEl.style.color = "";
        }
        if (checkinBtn) checkinBtn.disabled = false;
        if (checkoutBtn) checkoutBtn.disabled = true;
      }
    });
  }

  // Event delegation for checkin/checkout clicks (works for table & cards)
  document.addEventListener("click", (e) => {
    const checkinBtn = e.target.closest(".btn-checkin");
    const checkoutBtn = e.target.closest(".btn-checkout");

    if (checkinBtn) {
      const parent = checkinBtn.closest("[data-emp-id]");
      if (!parent) return;
      const empId = parent.getAttribute("data-emp-id");
      updateEmployeeState(empId, "checked-in");
      return;
    }

    if (checkoutBtn) {
      const parent = checkoutBtn.closest("[data-emp-id]");
      if (!parent) return;
      const empId = parent.getAttribute("data-emp-id");
      updateEmployeeState(empId, "checked-out");
      return;
    }
  });

  // Filter (search + department) that affects both views
  function applyFilters() {
    const q = (searchInput?.value || "").trim().toLowerCase();
    const dept = (deptSelect?.value || "all");

    // Cards
    document.querySelectorAll(".employee-card[data-emp-id]").forEach(card => {
      const name = (card.getAttribute("data-emp-name") || "").toLowerCase();
      const id = (card.getAttribute("data-emp-id") || "").toLowerCase();
      const cDept = (card.getAttribute("data-dept") || "");
      const matchesQ = !q || name.includes(q) || id.includes(q);
      const matchesDept = (dept === "all") || (cDept === dept);
      card.style.display = (matchesQ && matchesDept) ? "" : "none";
    });

    // Table rows
    document.querySelectorAll('tr[data-emp-id]').forEach(row => {
      const name = (row.getAttribute("data-emp-name") || "").toLowerCase();
      const id = (row.getAttribute("data-emp-id") || "").toLowerCase();
      const rDept = (row.getAttribute("data-dept") || "");
      const matchesQ = !q || name.includes(q) || id.includes(q);
      const matchesDept = (dept === "all") || (rDept === dept);
      row.style.display = (matchesQ && matchesDept) ? "" : "none";
    });
  }

  if (searchInput) {
    searchInput.addEventListener("input", applyFilters);
  }
  if (deptSelect) {
    deptSelect.addEventListener("change", applyFilters);
  }

  // Initialize - ensure card view visible
  showCardView();

  // OPTIONAL: keyboard accessibility - Enter toggles views if focused
  cardViewBtn.addEventListener("keydown", (e) => { if (e.key === "Enter") cardViewBtn.click(); });
  tableViewBtn.addEventListener("keydown", (e) => { if (e.key === "Enter") tableViewBtn.click(); });
});
