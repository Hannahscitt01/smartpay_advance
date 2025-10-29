// static/js/attendance.js
document.addEventListener("DOMContentLoaded", () => {
  "use strict";

  // ===============================
  // ATTENDANCE CARD / TABLE TOGGLE
  // ===============================
  const cardViewBtn = document.getElementById("cardViewBtn");
  const tableViewBtn = document.getElementById("tableViewBtn");
  const cardView = document.getElementById("cardView");
  const tableView = document.getElementById("tableView");

  if (cardView && tableView && cardViewBtn && tableViewBtn) {
    const showCardView = () => {
      cardView.classList.remove("hidden");
      tableView.classList.add("hidden");
      cardViewBtn.classList.add("active");
      tableViewBtn.classList.remove("active");
      cardView.setAttribute("aria-hidden", "false");
      tableView.setAttribute("aria-hidden", "true");
    };
    const showTableView = () => {
      tableView.classList.remove("hidden");
      cardView.classList.add("hidden");
      tableViewBtn.classList.add("active");
      cardViewBtn.classList.remove("active");
      tableView.setAttribute("aria-hidden", "false");
      cardView.setAttribute("aria-hidden", "true");
    };

    cardViewBtn.addEventListener("click", showCardView);
    tableViewBtn.addEventListener("click", showTableView);

    cardViewBtn.addEventListener("keydown", (e) => { if (e.key === "Enter") showCardView(); });
    tableViewBtn.addEventListener("keydown", (e) => { if (e.key === "Enter") showTableView(); });

    // Initialize view
    showCardView();
  }

  // =========================================
  // ATTENDANCE CHECK-IN / CHECK-OUT UPDATE
  // =========================================
  function updateEmployeeState(empId, label, color, hrs = 0) {
    const wrappers = document.querySelectorAll(`[data-emp-id="${empId}"]`);
    wrappers.forEach(el => {
      const statusEl = el.querySelector(".status1") || el.querySelector(".status");
      const checkinBtn = el.querySelector(".btn-checkin") || el.closest("tr")?.querySelector(".btn-checkin");
      const checkoutBtn = el.querySelector(".btn-checkout") || el.closest("tr")?.querySelector(".btn-checkout");
      const hoursEl = el.querySelector(".hours-worked") || el.closest("tr")?.querySelector(".hours-worked");

      if (statusEl) {
        statusEl.textContent = label;
        statusEl.style.color = color || "";
      }

      if (hoursEl && hrs) {
        hoursEl.textContent = `${hrs} hrs`;
      }

      if (label.toLowerCase().includes("checked in")) {
        if (checkinBtn) checkinBtn.disabled = true;
        if (checkoutBtn) checkoutBtn.disabled = false;
      } else if (label.toLowerCase().includes("checked out")) {
        if (checkoutBtn) checkoutBtn.disabled = true;
        if (checkinBtn) checkinBtn.disabled = false;
      } else {
        if (checkinBtn) checkinBtn.disabled = false;
        if (checkoutBtn) checkoutBtn.disabled = true;
      }
    });
  }

  document.addEventListener("click", (e) => {
    const checkinBtn = e.target.closest(".btn-checkin");
    const checkoutBtn = e.target.closest(".btn-checkout");

    if (checkinBtn) {
      const parent = checkinBtn.closest("[data-emp-id]");
      if (!parent) return;
      const empId = parent.getAttribute("data-emp-id");
      updateEmployeeState(empId, "checked-in");
    }

    if (checkoutBtn) {
      const parent = checkoutBtn.closest("[data-emp-id]");
      if (!parent) return;
      const empId = parent.getAttribute("data-emp-id");
      updateEmployeeState(empId, "checked-out");
    }
  });

  // ==============================
  // FILTER / SEARCH FUNCTIONALITY
  // ==============================
  const searchInput = document.getElementById("employeeSearch");
  const deptSelect = document.getElementById("departmentFilter");

  function applyFilters() {
    const q = (searchInput?.value || "").trim().toLowerCase();
    const dept = (deptSelect?.value || "all");

    document.querySelectorAll(".employee-card[data-emp-id]").forEach(card => {
      const name = (card.getAttribute("data-emp-name") || "").toLowerCase();
      const id = (card.getAttribute("data-emp-id") || "").toLowerCase();
      const cDept = card.getAttribute("data-dept") || "";
      const visible = (!q || name.includes(q) || id.includes(q)) && (dept === "all" || cDept === dept);
      card.style.display = visible ? "" : "none";
    });

    document.querySelectorAll("tr[data-emp-id]").forEach(row => {
      const name = (row.getAttribute("data-emp-name") || "").toLowerCase();
      const id = (row.getAttribute("data-emp-id") || "").toLowerCase();
      const rDept = row.getAttribute("data-dept") || "";
      const visible = (!q || name.includes(q) || id.includes(q)) && (dept === "all" || rDept === dept);
      row.style.display = visible ? "" : "none";
    });
  }

  if (searchInput) searchInput.addEventListener("input", applyFilters);
  if (deptSelect) deptSelect.addEventListener("change", applyFilters);

  // ==============================
  // LEAVE DAYS CALCULATION
  // ==============================
  const startInput = document.getElementById("start_date");
  const endInput = document.getElementById("end_date");
  const totalDisplay = document.getElementById("total_days_display");
  const resumeDisplay = document.getElementById("resumption_date_display");

  function calculateDaysAndResumption() {
    const start = new Date(startInput.value);
    const end = new Date(endInput.value);

    if (start && end && end >= start) {
      let dayCount = 0;
      let current = new Date(start);

      while (current <= end) {
        if (current.getDay() !== 0) dayCount++;
        current.setDate(current.getDate() + 1);
      }

      totalDisplay.textContent = `${dayCount} Days`;

      let resume = new Date(end);
      resume.setDate(resume.getDate() + 1);
      if (resume.getDay() === 0) resume.setDate(resume.getDate() + 1);

      resumeDisplay.textContent = resume.toLocaleDateString("en-US", {
        day: "numeric",
        month: "short",
        year: "numeric"
      });
    }
  }

  startInput?.addEventListener("change", calculateDaysAndResumption);
  endInput?.addEventListener("change", calculateDaysAndResumption);

  // ===============================
  // PR HERO CAROUSEL
  // ===============================
  const heroSlides = document.querySelectorAll(".hero-slider .slide");
  if (heroSlides.length) {
    let currentHero = 0;
    heroSlides[currentHero].classList.add("active");

    setInterval(() => {
      heroSlides[currentHero].classList.remove("active");
      currentHero = (currentHero + 1) % heroSlides.length;
      heroSlides[currentHero].classList.add("active");
    }, 6000);
  }

  // ===============================
  // PRODUCT SLIDER
  // ===============================
  const track = document.querySelector(".demo-track");
  if (track) {
    const productSlides = Array.from(track.children);
    let index = 0;
    const slideWidth = productSlides[0].offsetWidth + 16;

    setInterval(() => {
      index++;
      if (index > productSlides.length - 3) index = 0;
      track.style.transform = `translateX(-${index * slideWidth}px)`;
    }, 3000);
  }

  // ===============================
  // NAVBAR TOGGLE
  // ===============================
  const navToggle = document.getElementById("navToggle");
  const navMenu = document.getElementById("navMenu");

  if (navToggle && navMenu) {
    navToggle.addEventListener("click", () => navMenu.classList.toggle("show"));

    document.addEventListener("click", (e) => {
      if (!navMenu.contains(e.target) && !navToggle.contains(e.target)) {
        navMenu.classList.remove("show");
      }
    });
  }

});

document.addEventListener("DOMContentLoaded", () => {
  const navToggle = document.getElementById("nav-toggle");
  const navLinks = document.getElementById("nav-links");

  if (navToggle && navLinks) {
    navToggle.addEventListener("click", () => {
      navLinks.classList.toggle("show");
    });

    // Close menu when clicking outside
    document.addEventListener("click", (e) => {
      if (!navLinks.contains(e.target) && !navToggle.contains(e.target)) {
        navLinks.classList.remove("show");
      }
    });
  }
});

