// document.addEventListener("click", async function (e) {
//     const approveBtn = e.target.closest(".approve-btn");
//     const rejectBtn = e.target.closest(".reject-btn");

//     if (approveBtn) {
//         const id = approveBtn.dataset.id;
//         const res = await fetch(`/approve/${id}`, { method: "POST" });
//         const data = await res.json();
//         alert(data.reply);
//         location.reload();
//     }

//     if (rejectBtn) {
//         const id = rejectBtn.dataset.id;
//         const res = await fetch(`/reject/${id}`, { method: "POST" });
//         const data = await res.json();
//         alert(data.reply);
//         location.reload();
//     }
// });

document.addEventListener("click", async function (e) {
    const approveBtn = e.target.closest(".approve-btn");
    const rejectBtn = e.target.closest(".reject-btn");

    if (approveBtn) {
        const id = approveBtn.dataset.id;
        const card = approveBtn.closest(".approval-card");
        const res = await fetch(`/approve/${id}`, { method: "POST" });
        const data = await res.json();
        showToast(data.reply, !data.success);
        if (data.success) fadeOutAndRemove(card);
    }

    if (rejectBtn) {
        const id = rejectBtn.dataset.id;
        const card = rejectBtn.closest(".approval-card");
        const res = await fetch(`/reject/${id}`, { method: "POST" });
        const data = await res.json();
        showToast(data.reply, !data.success);
        if (data.success) fadeOutAndRemove(card);
    }

    if (window.refreshApprovalBadge) window.refreshApprovalBadge();
});

function fadeOutAndRemove(card) {
    card.style.transition = "opacity 0.3s ease, transform 0.3s ease";
    card.style.opacity = "0";
    card.style.transform = "translateX(20px)";
    setTimeout(() => {
        card.remove();
        const remaining = document.querySelectorAll(".approval-card").length;
        if (remaining === 0) {
            document.querySelector(".col-md-8.offset-md-2").insertAdjacentHTML("beforeend",
                `<div class="empty-state"><i class="bi bi-check-circle"></i><p>No pending approvals right now.</p></div>`
            );
        }
    }, 300);
}