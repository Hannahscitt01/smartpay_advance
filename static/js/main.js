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



