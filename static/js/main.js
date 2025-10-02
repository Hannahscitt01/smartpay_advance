document.addEventListener("DOMContentLoaded", function() {
    const gridBtn = document.getElementById("gridViewBtn");
    const tableBtn = document.getElementById("tableViewBtn");
    const cards = document.getElementById("employeeCards");
    const table = document.getElementById("employeeTable");

    gridBtn.addEventListener("click", function() {
        cards.style.display = "block";
        table.style.display = "none";
        gridBtn.classList.add("active");
        tableBtn.classList.remove("active");
    });

    tableBtn.addEventListener("click", function() {
        cards.style.display = "none";
        table.style.display = "block";
        tableBtn.classList.add("active");
        gridBtn.classList.remove("active");
    });
});



///Message centre
// Handle switching tabs (All / Departments / Employees)
document.querySelectorAll('.conversation-tabs .tab').forEach(tab => {
  tab.addEventListener('click', () => {
    document.querySelectorAll('.conversation-tabs .tab').forEach(t => t.classList.remove('active'));
    tab.classList.add('active');
  });
});

// Handle sending messages
const chatInput = document.querySelector('.chat-footer input');
const chatBody = document.querySelector('.chat-body');
const sendBtn = document.querySelector('.chat-footer button');

sendBtn.addEventListener('click', () => {
  if (chatInput.value.trim() !== "") {
    const msg = document.createElement('div');
    msg.classList.add('message', 'sent');
    msg.innerHTML = `<p>${chatInput.value}</p><span class="time">Now</span>`;
    chatBody.appendChild(msg);
    chatInput.value = "";
    chatBody.scrollTop = chatBody.scrollHeight;
  }
});