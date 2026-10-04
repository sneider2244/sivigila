// Pestañas de la ficha: solo muestran u ocultan paneles. No hay viaje al servidor y no se pierde lo escrito.
function activarPestana(boton) {
  const grupo = boton.closest("[data-tabs]");
  grupo.querySelectorAll("[data-tab]").forEach((b) => b.classList.toggle("activa", b === boton));
  document.querySelectorAll("[data-panel]").forEach((p) => {
    p.hidden = p.dataset.panel !== boton.dataset.tab;
  });
}

document.addEventListener("click", (e) => {
  const boton = e.target.closest("[data-tab]");
  if (boton) activarPestana(boton);
});

// Si el servidor devolvió errores, abre la primera pestaña que tenga un campo con error.
document.addEventListener("DOMContentLoaded", () => {
  const conError = document.querySelector("[data-panel] .campo-error");
  if (!conError) return;
  const panel = conError.closest("[data-panel]").dataset.panel;
  const boton = document.querySelector(`[data-tab="${panel}"]`);
  if (boton) activarPestana(boton);
});
