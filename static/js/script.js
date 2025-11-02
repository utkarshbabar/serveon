// script.js - dashboard search filtering
document.addEventListener("DOMContentLoaded", function () {
  const searchInput = document.getElementById("search-input");
  if (!searchInput) return;
  const rows = Array.from(document.querySelectorAll("#files-table tbody tr"));

  function normalize(s) {
    return (s || "").toLowerCase();
  }

  function matches(row, q) {
    if (!q) return true;
    const display = normalize(row.querySelector(".col-display")?.textContent);
    const category = normalize(row.querySelector(".col-category")?.textContent);
    const original = normalize(row.querySelector(".col-original")?.textContent);
    return display.includes(q) || category.includes(q) || original.includes(q);
  }

  searchInput.addEventListener("input", function () {
    const q = normalize(this.value.trim());
    rows.forEach(row => {
      if (matches(row, q)) {
        row.style.display = "";
      } else {
        row.style.display = "none";
      }
    });
  });
});
