async function refreshApprovalBadge() {
    try {
        const response = await fetch("/approvals/count");
        const data = await response.json();
        const badge = document.getElementById("approval-badge");
        if (data.count > 0) {
            badge.textContent = data.count;
            badge.classList.remove("d-none");
        } else {
            badge.classList.add("d-none");
        }
    } catch (err) { console.error(err); }
}

window.refreshApprovalBadge = refreshApprovalBadge;
document.addEventListener("DOMContentLoaded", refreshApprovalBadge);