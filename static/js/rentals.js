document.addEventListener("DOMContentLoaded", () => {

    const modal = document.getElementById("rentalModal");

    const openButton = document.querySelector(".new-rental-btn");

    const closeButton = document.querySelector(".close-modal");

    const cancelButton = document.getElementById("cancelRental");

    const modalTitle = document.querySelector(".modal-header h2");

    const form = modal.querySelector("form");

    // Campos

    const customer = document.getElementById("customer_name");
const phone = document.getElementById("phone");
const court = document.getElementById("court");
const date = document.getElementById("scheduled_date");
const time = document.getElementById("scheduled_time");
const duration = document.getElementById("duration");

const rentalId = document.getElementById("rental_id");

    // ============================
    // Abrir Novo
    // ============================

    function openNewRental() {

        modalTitle.textContent = "Novo Aluguel";

        form.action = "/rentals/create";

        form.reset();

rentalId.value = "";

modal.classList.add("show");

    }

    // ============================
    // Fechar
    // ============================

    function closeModal() {

        modal.classList.remove("show");

    }

    // ============================
    // Editar
    // ============================

    function openEditRental(button){

        modalTitle.textContent = "Editar Aluguel";

        rentalId.value = button.dataset.id;

        customer.value = button.dataset.customer;

        phone.value = button.dataset.phone;

        court.value = button.dataset.court;

        date.value = button.dataset.date;

        time.value = button.dataset.time;

        duration.value = button.dataset.duration;

        // por enquanto continua usando create
        // depois vamos trocar para update

        form.action = "/rentals/create";

        modal.classList.add("show");

    }

    // ============================
    // Eventos
    // ============================

    openButton.addEventListener("click", openNewRental);

    closeButton.addEventListener("click", closeModal);

    cancelButton.addEventListener("click", closeModal);

    modal.addEventListener("click",(e)=>{

        if(e.target===modal){

            closeModal();

        }

    });

    // Botões Editar

    document.querySelectorAll(".btn-edit").forEach(button=>{

        if(button.id==="cancelRental") return;

        button.addEventListener("click",()=>{

            openEditRental(button);

        });

    });

});

// ============================
// Modal Tempo Extra
// ============================

const extraModal = document.getElementById("extraTimeModal");

const closeExtra = document.getElementById("closeExtraTime");

const cancelExtra = document.getElementById("cancelExtraTime");

const extraRentalId = document.getElementById("extraRentalId");

document.querySelectorAll(".btn-extra").forEach(button => {

    button.addEventListener("click", () => {

        extraRentalId.value = button.dataset.id;

        extraModal.classList.add("show");

    });

});

closeExtra.addEventListener("click", () => {

    extraModal.classList.remove("show");

});

cancelExtra.addEventListener("click", () => {

    extraModal.classList.remove("show");

});

extraModal.addEventListener("click", (e) => {

    if (e.target === extraModal) {

        extraModal.classList.remove("show");

    }

});

// ============================
// Enviar Tempo Extra
// ============================

const extraForm = document.getElementById("extraTimeForm");

extraForm.action = "/rentals/add-time";