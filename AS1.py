import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field


class ValoracionPerfil(BaseModel):
    años_experiencia: int = Field(ge=0, le=50, description="Años de experiencia: ")
    formacion: str = Field(min_length=2, max_length=50, description="Formación: ")
    skills: str = Field(min_length=2, max_length=100, description="Habilidades separadas por comas: ")
    idiomas: str = Field(min_length=2, max_length=100, description="Idiomas separados por comas: ")
    tiene_certificaciones: bool = Field(default=False, description="Posee certificaciones externas: ")


class ResultadoValoracion(BaseModel):
    experiencia_suficiente: bool
    formacion_suficiente: bool
    skills_necesarias: str
    idiomas_necesarios: str
    score_encaje: float = Field(ge=0, le=100)
    resultado_valoracion: str


app = FastAPI(
    title="Motor Inteligente de valoracion de un perfil para una oferta de empleo",
    description="API para estimar el encaje de trabajadores que postulan a un puesto de trabajo",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuración robusta de la ruta absoluta para la carpeta static
current_file_dir = os.path.dirname(os.path.abspath(__file__))
static_dir = os.path.join(current_file_dir, "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")


# ---------- Configuración de la oferta ----------
SKILLS_REQUERIDAS = {"python", "fastapi", "sql", "git", "docker"}
ANIOS_MINIMOS = 2
FORMACIONES_VALIDAS = ("fp", "ciclo", "grado", "ingenier", "master", "máster", "doctor", "dam", "daw")


def a_lista(texto: str) -> list[str]:
    return [x.strip().lower() for x in texto.split(",") if x.strip()]


@app.get("/", response_class=FileResponse)
def inicio():
    return FileResponse("index.html")


@app.get("/api/estado")
def estado():
    return {
        "servicio": app.title,
        "version": app.version,
        "estado": "operativo",
        "endpoint_inferencia": {"metodo": "POST", "ruta": "/api/valorar-perfil"},
        "aviso": "Resultado orientativo; no constituye una decisión de contratación.",
    }


@app.post("/api/valorar-perfil", response_model=ResultadoValoracion)
def valorar_perfil(perfil: ValoracionPerfil):
    skills = set(a_lista(perfil.skills))
    idiomas = a_lista(perfil.idiomas)
    formacion = perfil.formacion.strip().lower()

    experiencia_suficiente = perfil.años_experiencia >= ANIOS_MINIMOS
    formacion_suficiente = any(f in formacion for f in FORMACIONES_VALIDAS)
    coincidentes = SKILLS_REQUERIDAS & skills
    faltantes = sorted(SKILLS_REQUERIDAS - skills)
    sabe_ingles = any("ingl" in i for i in idiomas)

    # Motor de scoring (0-100)
    score = min(perfil.años_experiencia / 5, 1) * 30                # experiencia: 30
    score += 20 if formacion_suficiente else 5                       # formación: 20
    score += len(coincidentes) / len(SKILLS_REQUERIDAS) * 30         # skills: 30
    score += 12 if sabe_ingles else (4 if idiomas else 0)           # idiomas: 12
    score += 8 if perfil.tiene_certificaciones else 0                # certificaciones: 8
    score = max(0.0, min(100.0, round(score, 1)))

    skills_texto = (
        "Cumple todas las skills requeridas."
        if not faltantes
        else "Faltan por acreditar: " + ", ".join(faltantes) + "."
    )
    idiomas_texto = (
        "Cumple el requisito de inglés."
        if sabe_ingles
        else "No se ha indicado inglés, requerido por la oferta."
    )

    if score >= 70:
        resultado = f"APTO ({score}/100): el perfil encaja con la oferta."
    elif score >= 45:
        resultado = f"REVISAR ({score}/100): encaje parcial, se recomienda revisión manual."
    else:
        resultado = f"NO APTO ({score}/100): el perfil no alcanza el mínimo para la oferta."

    return {
        "experiencia_suficiente": experiencia_suficiente,
        "formacion_suficiente": formacion_suficiente,
        "skills_necesarias": skills_texto,
        "idiomas_necesarios": idiomas_texto,
        "score_encaje": score,
        "resultado_valoracion": resultado,
    }