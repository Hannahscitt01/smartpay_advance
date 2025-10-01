document.addEventListener("DOMContentLoaded", function() {
    // ================= Salary Requests Toggle =================
    const cardBtn = document.getElementById("reqCardViewBtn");
    const tableBtn = document.getElementById("reqTableViewBtn");
    const cardView = document.getElementById("requestCards");
    const tableView = document.getElementById("requestTable");

    if (cardBtn && tableBtn && cardView && tableView) {
        cardBtn.addEventListener("click", function () {
            cardView.style.display = "block";
            tableView.style.display = "none";
            cardBtn.classList.add("active");
            tableBtn.classList.remove("active");
        });

        tableBtn.addEventListener("click", function () {
            cardView.style.display = "none";
            tableView.style.display = "block";
            tableBtn.classList.add("active");
            cardBtn.classList.remove("active");
        });
    }
});
