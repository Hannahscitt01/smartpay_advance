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
