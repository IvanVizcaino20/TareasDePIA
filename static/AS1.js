const API_BASE = "";
const ENDPOINT = API_BASE + "/api/valorar-perfil";

const $ = (id) => document.getElementById(id);

function mostrarError(texto) {
  $("vacio").classList.add("hidden");
  $("resultado").classList.add("hidden");
  $("error").textContent = texto;
  $("error").classList.remove("hidden");
}

function marca(el, ok) {
  el.textContent = ok ? "✓" : "✗";
  el.className = "font-bold " + (ok ? "text-teal-700" : "text-red-700");
}

function mostrarResultado(r) {
  $("vacio").classList.add("hidden");
  $("error").classList.add("hidden");
  $("resultado").classList.remove("hidden");

  const texto = r.resultado_valoracion || "";
  const v = $("veredicto");
  v.textContent = texto;

  if (texto.startsWith("NO APTO")) v.className = "rounded px-4 py-3 text-lg font-bold bg-red-100 text-red-900";
  else if (texto.startsWith("REVISAR")) v.className = "rounded px-4 py-3 text-lg font-bold bg-amber-100 text-amber-900";
  else v.className = "rounded px-4 py-3 text-lg font-bold bg-teal-100 text-teal-900";

  if (typeof r.score_encaje === "number") {
    $("bloque-score").classList.remove("hidden");
    $("score-num").textContent = r.score_encaje + " / 100";
    $("score-barra").style.width = Math.max(0, Math.min(100, r.score_encaje)) + "%";
  } else {
    $("bloque-score").classList.add("hidden");
  }

  marca($("ic-exp"), r.experiencia_suficiente);
  marca($("ic-form"), r.formacion_suficiente);
  $("t-skills").textContent = r.skills_necesarias;
  $("t-idiomas").textContent = r.idiomas_necesarios;
}

function textoErrorValidacion(detail) {
  if (!Array.isArray(detail)) return "Los datos enviados no son válidos.";
  return detail.map((d) => {
    const campo = d.loc ? d.loc[d.loc.length - 1] : "campo";
    return campo + ": " + d.msg;
  }).join("\n");
}

$("form").addEventListener("submit", async (e) => {
  e.preventDefault();

  const datos = {
    "años_experiencia": parseInt($("anios").value, 10),
    "formacion": $("formacion").value.trim(),
    "skills": $("skills").value.trim(),
    "idiomas": $("idiomas").value.trim(),
    "tiene_certificaciones": $("certs").checked,
  };

  if (Number.isNaN(datos["años_experiencia"])) {
    mostrarError("Indica los años de experiencia como un número entero.");
    return;
  }

  const btn = $("btn");
  btn.disabled = true;
  btn.textContent = "Valorando…";

  try {
    const resp = await fetch(ENDPOINT, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(datos),
    });
    const cuerpo = await resp.json();

    if (resp.ok) mostrarResultado(cuerpo);
    else if (resp.status === 422) mostrarError(textoErrorValidacion(cuerpo.detail));
    else mostrarError("El servidor respondió con un error (" + resp.status + ").");
  } catch (err) {
    mostrarError("No se pudo conectar con la API. Comprueba que uvicorn está en marcha.");
  } finally {
    btn.disabled = false;
    btn.textContent = "Valorar perfil";
  }
});