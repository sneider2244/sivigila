import json
from datetime import date

import pytest

from sivigila.validacion import (
    calcular_edad, comp_de_form, parsear_fecha, validar_campos, validar_ficha,
    validar_laboratorio, validar_upgd,
)
from tests.utils import ficha_completa

HOY = date(2026, 10, 3)


def test_parsear_fecha_solo_acepta_iso():
    assert parsear_fecha("2026-10-03") == HOY
    for malo in ("03/10/2026", "20261003", "2026-13-01"):
        with pytest.raises(ValueError):
            parsear_fecha(malo)


@pytest.mark.parametrize("nacimiento, esperado", [
    (date(1996, 10, 3), (30, "Años")),
    (date(1996, 10, 4), (29, "Años")),
    (date(2026, 5, 3), (5, "Meses")),
    (date(2026, 9, 20), (13, "Días")),
])
def test_calcular_edad(nacimiento, esperado):
    assert calcular_edad(nacimiento, HOY) == esperado


def test_validar_campos_detecta_obligatorio_lista_y_fecha_futura():
    campos = [
        {"key": "a", "label": "A", "tipo": "texto"},
        {"key": "b", "label": "B", "tipo": "lista", "opciones": ["X", "Y"]},
        {"key": "c", "label": "C", "tipo": "fecha"},
        {"key": "d", "label": "D", "tipo": "si_no"},
    ]
    datos, errores = validar_campos(
        campos, {"a": "", "b": "Z", "c": "2026-10-04", "d": "Sí"}, {"a"}, HOY
    )
    assert errores == {
        "a": "Este campo es obligatorio.",
        "b": "Selecciona una opción de la lista.",
        "c": "La fecha no puede ser posterior a hoy.",
    }
    assert datos["d"] == "Sí"
    assert datos["a"] is None


def test_guardar_minimo_sin_errores(db):
    form = {"codigo_evento": "210", "numero_id": "1", "primer_nombre": "Ana"}
    datos, errores = validar_ficha(form, db.get_evento("210"), completa=False, hoy=HOY)
    assert errores == {}
    assert datos["codigo_evento"] == "210"
    assert datos["datos_complementarios"] == "{}"
    assert datos["edad"] is None


def test_guardar_exige_numero_id_y_nombre(db):
    _, errores = validar_ficha({"codigo_evento": "210"}, db.get_evento("210"), False, HOY)
    assert set(errores) == {"numero_id", "primer_nombre"}


def test_sin_evento_es_error(db):
    _, errores = validar_ficha({"numero_id": "1", "primer_nombre": "Ana"}, None, False, HOY)
    assert "codigo_evento" in errores


def test_terminar_exige_basicos_y_todos_los_complementarios(db):
    form = {"codigo_evento": "210", "numero_id": "1", "primer_nombre": "Ana"}
    _, errores = validar_ficha(form, db.get_evento("210"), completa=True, hoy=HOY)
    assert {"sexo", "fecha_nacimiento", "condicion", "comp__fiebre",
            "comp__clasificacion_dengue"} <= set(errores)


def test_terminar_completa_sin_errores_y_calcula_edad(db):
    hoy = date.today()
    datos, errores = validar_ficha(ficha_completa(), db.get_evento("210"), True, hoy)
    assert errores == {}
    assert datos["edad"] == 30
    assert datos["unidad_edad"] == "Años"
    assert json.loads(datos["datos_complementarios"])["fiebre"] == "Sí"


def test_fechas_fuera_de_orden(db):
    form = ficha_completa(fecha_nacimiento="2020-01-10", fecha_inicio_sintomas="2019-12-01")
    _, errores = validar_ficha(form, db.get_evento("210"), False, date.today())
    assert errores["fecha_inicio_sintomas"] == "No puede ser anterior a la fecha de nacimiento."


def test_hospitalizado_y_fallecido_exigen_fecha_al_terminar(db):
    form = ficha_completa(hospitalizado="Sí", condicion="Fallecido")
    _, errores = validar_ficha(form, db.get_evento("210"), True, date.today())
    assert "fecha_hospitalizacion" in errores
    assert "fecha_defuncion" in errores


def test_complementario_de_otro_evento_es_rechazado(db):
    form = {"codigo_evento": "210", "numero_id": "1", "primer_nombre": "Ana", "comp__gravedad": "Leve"}
    _, errores = validar_ficha(form, db.get_evento("210"), False, HOY)
    assert "gravedad" in errores["general"]


def test_opcion_complementaria_invalida(db):
    form = {"codigo_evento": "210", "numero_id": "1", "primer_nombre": "Ana",
            "comp__clasificacion_dengue": "Dengue inventado"}
    _, errores = validar_ficha(form, db.get_evento("210"), False, HOY)
    assert errores["comp__clasificacion_dengue"] == "Selecciona una opción de la lista."


def test_comp_de_form_quita_prefijo():
    assert comp_de_form({"comp__fiebre": "Sí", "numero_id": "1"}) == {"fiebre": "Sí"}


def test_validar_laboratorio_exige_prueba():
    _, errores = validar_laboratorio({"muestra": "Suero"}, HOY)
    assert errores == {"prueba": "Este campo es obligatorio."}


def test_validar_upgd_convierte_recursos():
    datos, errores = validar_upgd({"cod_prestador": "1", "razon_social": "X", "cove": "1"}, HOY)
    assert errores == {}
    assert datos["cove"] == 1
    assert datos["internet"] == 0
