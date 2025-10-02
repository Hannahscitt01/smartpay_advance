// finance_requests_toggle.js
document.addEventListener("DOMContentLoaded", function () {
    try {
        const cardBtn = document.getElementById("reqCardViewBtn");
        const tableBtn = document.getElementById("reqTableViewBtn");
        const cardContainer = document.getElementById("requestCards");
        const tableContainer = document.getElementById("requestTable");

        if (!cardBtn || !tableBtn || !cardContainer || !tableContainer) {
            // Not on this page — do nothing
            return;
        }

        const saved = localStorage.getItem("finance_view") || "card";

        function showCard() {
            cardContainer.style.display = "block";
            tableContainer.style.display = "none";
            cardBtn.classList.add("active");
            tableBtn.classList.remove("active");
            localStorage.setItem("finance_view", "card");
            // accessibility
            cardContainer.setAttribute("aria-hidden", "false");
            tableContainer.setAttribute("aria-hidden", "true");
        }

        function showTable() {
            cardContainer.style.display = "none";
            tableContainer.style.display = "block";
            tableBtn.classList.add("active");
            cardBtn.classList.remove("active");
            localStorage.setItem("finance_view", "table");
            // accessibility
            cardContainer.setAttribute("aria-hidden", "true");
            tableContainer.setAttribute("aria-hidden", "false");
        }

        // apply saved preference
        if (saved === "table") showTable();
        else showCard();

        cardBtn.addEventListener("click", showCard);
        tableBtn.addEventListener("click", showTable);

        // helpful debug log
        // console.info("Finance requests toggle initialized. view:", localStorage.getItem("finance_view"));
    } catch (err) {
        // Fail silently but log for devs
        console.error("finance_requests_toggle.js error:", err);
    }
});


document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll(".ajax-action").forEach(button => {
        button.addEventListener("click", async function () {
            const url = this.dataset.url;
            const card = this.closest("[data-request-id]");
            const badge = card.querySelector(".badge");
            const actionRow = card.querySelector(".action-row");

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
                    // ✅ Update badge
                    badge.textContent = data.status;
                    badge.className = "badge status-" + data.status.toLowerCase();

                    // ✅ Replace action buttons with "Processed"
                    if (actionRow) {
                        actionRow.innerHTML = `<p class="processed-text"><em>${data.status}</em></p>`;
                    }
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

// CSRF helper
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== "") {
        const cookies = document.cookie.split(";");
        for (let cookie of cookies) {
            cookie = cookie.trim();
            if (cookie.startsWith(name + "=")) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}


// hr_dashboard.js

function updateTime() {
    const now = new Date();
    const options = { year: 'numeric', month: 'short', day: 'numeric' };
    const dateStr = now.toLocaleDateString(undefined, options);
    const timeStr = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: true });

    const dateElement = document.getElementById('current-date');
    const timeElement = document.getElementById('current-time');

    if(dateElement) dateElement.textContent = dateStr;
    if(timeElement) timeElement.textContent = timeStr;
}

// Initial call
updateTime();

// Update every minute
setInterval(updateTime, 60000);


// Hr department js
document.addEventListener("DOMContentLoaded", function () {
  // Toggle Card/Table view
  const toggleBtn = document.getElementById('deptToggleBtn');
  const cardView = document.getElementById('cardView');
  const tableView = document.getElementById('tableView');

  toggleBtn && toggleBtn.addEventListener('click', () => {
    const showingCards = !cardView.classList.contains('hidden');
    if (showingCards) {
      cardView.classList.add('hidden');
      tableView.classList.remove('hidden');
      toggleBtn.innerHTML = '<i class="fas fa-th-large"></i> Switch to Card View';
    } else {
      cardView.classList.remove('hidden');
      tableView.classList.add('hidden');
      toggleBtn.innerHTML = '<i class="fas fa-th-large"></i> Switch to Table View';
    }
  });

  // Add department placeholder
  const addBtn = document.getElementById('addDeptBtn');
  addBtn && addBtn.addEventListener('click', () => {
    // placeholder action for now (you'll hook the modal/form later)
    alert('Add New Department — modal will open here (to be implemented).');
  });

  // When "View" clicked (either in card or table), reveal operations/staff/analytics
  function onViewClicked(deptName) {
    // show sections
    const ops = document.getElementById('deptOperations');
    const staff = document.getElementById('deptStaff');
    const analytics = document.getElementById('deptAnalytics');

    if (ops) ops.classList.remove('hidden');
    if (staff) staff.classList.remove('hidden');
    if (analytics) analytics.classList.remove('hidden');

    // populate headings
    const opsDeptName = document.getElementById('opsDeptName');
    const staffDeptName = document.getElementById('staffDeptName');
    const analyticsDeptName = document.getElementById('analyticsDeptName');

    if (opsDeptName) opsDeptName.textContent = deptName;
    if (staffDeptName) staffDeptName.textContent = deptName;
    if (analyticsDeptName) analyticsDeptName.textContent = deptName;

    // populate placeholder operations data (you will replace with real data via AJAX)
    const opsProjects = document.getElementById('opsProjects');
    const opsBudget = document.getElementById('opsBudget');
    const opsKpis = document.getElementById('opsKpis');
    const opsOpenPositions = document.getElementById('opsOpenPositions');

    if (opsProjects) opsProjects.textContent = 'Project A, Project B';
    if (opsBudget) opsBudget.textContent = 'KSh 1,200,000';
    if (opsKpis) opsKpis.textContent = 'On-time payroll, < 2% variance';
    if (opsOpenPositions) opsOpenPositions.textContent = '2';

    // scroll to operations
    setTimeout(() => {
      ops && ops.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 120);

    // init/update charts with demo data
    initCharts(deptName);
  }

  // wire view buttons from both card & table
  document.querySelectorAll('.btn-view').forEach(btn => {
    btn.addEventListener('click', (e) => {
      // find dept name from nearest card or table row
      const card = e.target.closest('.dept-card');
      let deptName = null;
      if (card) deptName = card.getAttribute('data-dept') || card.querySelector('h3').innerText;
      else {
        const row = e.target.closest('tr');
        if (row) deptName = row.getAttribute('data-dept') || row.children[0].innerText;
      }
      if (!deptName) deptName = 'Department';
      onViewClicked(deptName);
    });
  });

  // ------------------- Charts (demo placeholders) -------------------
  function initCharts(deptName) {
    // Staff Growth (line)
    const sCtx = document.getElementById('staffGrowthChart');
    if (sCtx) {
      if (sCtx._chart) sCtx._chart.destroy();
      sCtx._chart = new Chart(sCtx, {
        type: 'line',
        data: {
          labels: ['Mar', 'Apr', 'May', 'Jun', 'Jul'],
          datasets: [{ label: `${deptName} - Staff`, data: [20, 22, 24, 26, 28], borderColor: '#0055aa', backgroundColor: 'rgba(0,85,170,0.06)', fill: true }]
        },
        options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } } }
      });
    }

    // Gender Ratio (doughnut)
    const gCtx = document.getElementById('genderRatioChart');
    if (gCtx) {
      if (gCtx._chart) gCtx._chart.destroy();
      gCtx._chart = new Chart(gCtx, {
        type: 'doughnut',
        data: { labels: ['Male','Female'], datasets: [{ data: [60,40], backgroundColor: ['#0055aa','#08bd4a'] }] },
        options: { responsive:true, maintainAspectRatio:false, plugins:{ legend:{ position:'bottom' } } }
      });
    }

    // Attrition (bar)
    const aCtx = document.getElementById('attritionChart');
    if (aCtx) {
      if (aCtx._chart) aCtx._chart.destroy();
      aCtx._chart = new Chart(aCtx, {
        type: 'bar',
        data: { labels:['Jan','Feb','Mar','Apr'], datasets:[{ label:'Attrition %', data:[2,3,1.5,2.8], backgroundColor:'#ef4444' }] },
        options:{ responsive:true, maintainAspectRatio:false, plugins:{ legend:{ display:false } } }
      });
    }

    // Budget (pie)
    const bCtx = document.getElementById('budgetChart');
    if (bCtx) {
      if (bCtx._chart) bCtx._chart.destroy();
      bCtx._chart = new Chart(bCtx, {
        type:'pie',
        data:{ labels:['Used','Remaining'], datasets:[{ data:[65,35], backgroundColor:['#2563eb','#cbd5e1'] }] },
        options:{ responsive:true, maintainAspectRatio:false, plugins:{ legend:{ position:'bottom' } } }
      });
    }
  }

  // Optional: pre-init charts (hidden until view clicked)
});

//toggle department analytics
document.addEventListener('DOMContentLoaded', function () {
  // --- reference elements ---
  const toggleAnalyticsBtn = document.getElementById('toggleAnalyticsBtn');
  const analyticsSection = document.getElementById('deptAnalytics');

  // safety checks & helpful console warnings
  if (!toggleAnalyticsBtn) {
    console.warn('hr_departments.js: toggleAnalyticsBtn not found. Check the button id in the template.');
    return;
  }
  if (!analyticsSection) {
    console.warn('hr_departments.js: deptAnalytics section not found. Check the section id in the template.');
    return;
  }

  // utility: render button text/icon according to visible state
  function updateAnalyticsButton() {
    const visible = !analyticsSection.classList.contains('hidden');
    // keep icon + text, matching your fontawesome usage
    toggleAnalyticsBtn.innerHTML = visible
      ? '<i class="fas fa-chart-bar"></i>&nbsp; Hide Analytics'
      : '<i class="fas fa-chart-bar"></i>&nbsp; Show Analytics';
    toggleAnalyticsBtn.setAttribute('aria-pressed', visible ? 'true' : 'false');
  }

  // initial button label state
  updateAnalyticsButton();

  // toggle on click
  toggleAnalyticsBtn.addEventListener('click', function (e) {
    e.preventDefault();
    const isHidden = analyticsSection.classList.contains('hidden');

    if (isHidden) {
      analyticsSection.classList.remove('hidden');
      // optional: smooth scroll to analytics
      setTimeout(() => analyticsSection.scrollIntoView({ behavior: 'smooth', block: 'start' }), 120);
    } else {
      analyticsSection.classList.add('hidden');
    }
    updateAnalyticsButton();
  });
});


document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".alert-dismiss").forEach(btn => {
    btn.addEventListener("click", (e) => {
      e.target.closest("li").remove();
    });
  });
});


//Payroll
document.addEventListener("DOMContentLoaded", function() {
  const toggleBtn = document.getElementById("togglePayrollBtn");
  const previewSection = document.getElementById("payrollPreview");

  toggleBtn.addEventListener("click", function() {
    previewSection.classList.toggle("hidden");
  });
});


// ===== Modal Functionality =====
const modal = document.getElementById('payslipModal');
const modalEmployeeName = document.getElementById('modalEmployeeName');
const modalGross = document.getElementById('modalGross');
const modalDeductions = document.getElementById('modalDeductions');
const modalNet = document.getElementById('modalNet');
const modalBreakdown = document.getElementById('modalBreakdown');

document.querySelectorAll('.btn-view-payslip').forEach(btn=>{
  btn.addEventListener('click', ()=>{
    const row = btn.closest('tr');
    modalEmployeeName.textContent = row.children[0].textContent;
    modalGross.textContent = row.children[2].textContent;
    modalDeductions.textContent = row.children[3].textContent;
    modalNet.textContent = row.children[4].textContent;
    modal.classList.remove('hidden');
  });
});

document.querySelector('.modal .close').addEventListener('click', ()=>{
  modal.classList.add('hidden');
});

// ===== Search Filter =====
const searchInput = document.getElementById('searchPayroll');
searchInput.addEventListener('keyup', ()=>{
  const filter = searchInput.value.toLowerCase();
  document.querySelectorAll('#payrollBody tr').forEach(tr=>{
    const name = tr.children[0].textContent.toLowerCase();
    tr.style.display = name.includes(filter) ? '' : 'none';
  });
});


//hr settings

function navigateToSection(select) {
  const sectionId = select.value;
  if (sectionId) {
    const target = document.querySelector(sectionId);
    if (target) {
      target.scrollIntoView({
        behavior: 'smooth',
        block: 'start'
      });
    }
  }
}



///Message centre
// messages.js
document.addEventListener('DOMContentLoaded', () => {
  // --- Elements ---
  const tabs = document.querySelectorAll('.conversation-tabs .tab');
  const conversations = document.querySelectorAll('.conversation');
  const chatHeaderTitle = document.querySelector('.chat-header h3');
  const chatBody = document.querySelector('.chat-body');
  const chatInput = document.querySelector('.chat-footer input');
  const sendBtn = document.querySelector('.chat-footer button');

  // Defensive checks
  if (!chatBody) console.warn('messages.js: .chat-body not found');
  if (!chatInput) console.warn('messages.js: .chat-footer input not found');
  if (!sendBtn) console.warn('messages.js: .chat-footer button not found');

  // --- Helper: format time "HH:MM" ---
  function nowTime() {
    try {
      return new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } catch (e) {
      return new Date().toLocaleTimeString();
    }
  }

  // --- Helper: append message safely ---
  function appendMessage({ text, type = 'sent', time = null }) {
    if (!chatBody) return;
    const wrapper = document.createElement('div');
    wrapper.className = `message ${type}`;
    const p = document.createElement('p');
    p.textContent = text;
    const timeSpan = document.createElement('span');
    timeSpan.className = 'time';
    timeSpan.textContent = time || nowTime();
    wrapper.appendChild(p);
    wrapper.appendChild(timeSpan);
    chatBody.appendChild(wrapper);
    // scroll to bottom
    chatBody.scrollTop = chatBody.scrollHeight;
  }

  // --- Send message action ---
  function sendMessage() {
    if (!chatInput) return;
    const text = chatInput.value.trim();
    if (!text) return;
    appendMessage({ text, type: 'sent' });
    chatInput.value = '';

    // TODO: send to backend (fetch / websocket) - placeholder
    // fetch('/api/messages/send', { method: 'POST', body: JSON.stringify({ text, recipient }) })

    // mimic auto-reply for demo (optional)
    // setTimeout(() => appendMessage({ text: 'Auto-reply: message received', type: 'received' }), 700);
  }

  // Wire up send button
  if (sendBtn) {
    sendBtn.addEventListener('click', (e) => {
      e.preventDefault();
      sendMessage();
    });
  }

  // Enter to send (Shift+Enter = newline)
  if (chatInput) {
    chatInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
      }
    });
  }

  // --- Tabs switching (All / Departments / Employees) ---
  if (tabs && tabs.length) {
    tabs.forEach(tab => {
      tab.addEventListener('click', () => {
        tabs.forEach(t => t.classList.remove('active'));
        tab.classList.add('active');

        // optional filter: uses data-filter on tab and data-type on items
        const filter = (tab.dataset.filter || tab.textContent || '').toLowerCase().trim();
        if (filter && filter !== 'all' && conversations && conversations.length) {
          conversations.forEach(conv => {
            const type = (conv.dataset.type || '').toLowerCase();
            conv.style.display = (type === filter || type === '') ? '' : 'none';
          });
        } else {
          conversations.forEach(conv => conv.style.display = '');
        }
      });
    });
  }

  // --- Conversation click: load into chat window ---
  if (conversations && conversations.length) {
    conversations.forEach(item => {
      item.addEventListener('click', () => {
        // toggle active visual
        conversations.forEach(c => c.classList.remove('active'));
        item.classList.add('active');

        // set header title
        const nameEl = item.querySelector('.details h4');
        const snippetEl = item.querySelector('.details p');
        const timeEl = item.querySelector('.time');
        if (chatHeaderTitle && nameEl) chatHeaderTitle.textContent = nameEl.textContent.trim();

        // clear existing messages
        if (chatBody) chatBody.innerHTML = '';

        // If your li has data-messages (JSON) you'd parse and display them.
        // For now show the snippet as the most recent received message:
        if (snippetEl && chatBody) {
          appendMessage({ text: snippetEl.textContent.trim(), type: 'received', time: timeEl ? timeEl.textContent : nowTime() });
        }

        // Optionally, you can fetch the full thread from backend here:
        // fetch(`/api/messages/thread/${threadId}`).then(...)

      });
    });
  }

  // --- Keyboard accessibility for tabs (optional) ---
  if (tabs && tabs.length) {
    tabs.forEach(tab => {
      tab.setAttribute('tabindex', '0');
      tab.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          tab.click();
        }
      });
    });
  }

  // Auto-select first conversation (if none active)
  if (conversations && conversations.length) {
    const active = document.querySelector('.conversation.active') || conversations[0];
    if (active) active.click();
  }
});

