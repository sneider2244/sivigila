"""
Definición de los campos de cada formulario. Cada campo es un dict
{"key", "label", "tipo"} con tipo ∈ texto | fecha | lista | si_no, y "opciones" si es lista.
Es el mismo formato de eventos.campos_json, así un solo macro y un solo validador sirven para todo.
"""

SI_NO = ["Sí", "No"]
PREFIJO_COMP = "comp__"  # prefijo de los campos complementarios en el formulario

ROL_LABELS = {
    "super_admin": "Super administrador",
    "admin": "Administrador",
    "digitador": "Digitador",
    "consulta": "Solo consulta",
}


def _texto(key, label):
    return {"key": key, "label": label, "tipo": "texto"}


def _fecha(key, label):
    return {"key": key, "label": label, "tipo": "fecha"}


def _lista(key, label, opciones):
    return {"key": key, "label": label, "tipo": "lista", "opciones": opciones}


CAMPOS_BASICOS = [
    _lista("tipo_id", "Tipo de identificación", ["CC", "TI", "RC", "CE", "PA", "MS"]),
    _texto("numero_id", "Número de identificación"),
    _texto("primer_nombre", "Primer nombre"),
    _texto("segundo_nombre", "Segundo nombre"),
    _texto("primer_apellido", "Primer apellido"),
    _texto("segundo_apellido", "Segundo apellido"),
    _texto("telefono", "Teléfono"),
    _fecha("fecha_nacimiento", "Fecha de nacimiento"),
    _lista("sexo", "Sexo", ["F", "M", "I"]),
    _texto("nacionalidad", "Nacionalidad"),
    _texto("pais_procedencia", "País de procedencia"),
    _texto("departamento", "Departamento de ocurrencia"),
    _texto("municipio", "Municipio de ocurrencia"),
    _lista("area", "Área", ["Cabecera municipal", "Centro poblado", "Rural disperso"]),
    _texto("barrio", "Barrio"),
    _texto("vereda", "Vereda"),
    _texto("ocupacion", "Ocupación"),
    _lista("tipo_regimen", "Tipo de régimen", ["Contributivo", "Subsidiado", "Especial", "No asegurado"]),
    _texto("administradora", "Administradora (EPS)"),
    _lista("fuente", "Fuente de notificación", ["UPGD", "COVE", "Laboratorio", "Comunitaria"]),
    _texto("direccion_residencia", "Dirección de residencia"),
    _fecha("fecha_consulta", "Fecha de consulta"),
    _fecha("fecha_inicio_sintomas", "Fecha de inicio de síntomas"),
    _lista("clasificacion_caso", "Clasificación del caso",
           ["Sospechoso", "Probable", "Confirmado por laboratorio",
            "Confirmado por clínica", "Confirmado por nexo epidemiológico"]),
    _lista("hospitalizado", "¿Hospitalizado?", SI_NO),
    _fecha("fecha_hospitalizacion", "Fecha de hospitalización"),
    _lista("condicion", "Condición final", ["Vivo", "Fallecido"]),
    _fecha("fecha_defuncion", "Fecha de defunción"),
    _texto("nombre_diligencia", "Nombre de quien diligencia la ficha"),
    _texto("telefono_diligencia", "Teléfono de quien diligencia"),
]

OBLIGATORIOS_GUARDAR = {"numero_id", "primer_nombre"}
OBLIGATORIOS_TERMINAR = {
    "tipo_id", "numero_id", "primer_nombre", "primer_apellido", "sexo",
    "fecha_nacimiento", "fecha_consulta", "fecha_inicio_sintomas",
    "clasificacion_caso", "condicion",
}

CAMPOS_UPGD = [
    _texto("cod_prestador", "Código prestador"),
    _texto("subred", "Subred / seccional"),
    _texto("nit", "NIT"),
    _texto("razon_social", "Razón social"),
    _texto("direccion", "Dirección"),
    _texto("telefono", "Teléfono"),
    _texto("representante_legal", "Representante legal"),
    _texto("correo_electronico", "Correo electrónico"),
    _texto("responsable_notif", "Responsable de la notificación"),
    _lista("naturaleza_juridica", "Naturaleza jurídica",
           ["Privada sin ánimo de lucro", "Privada con ánimo de lucro", "Mixta", "Pública"]),
    _lista("nivel_complejidad", "Nivel de complejidad", ["I Nivel", "II Nivel", "III Nivel"]),
    _lista("tipo_unidad", "Tipo de unidad", ["UPGD", "UI", "Laboratorio"]),
    _texto("localidad_zona", "Localidad o zona (si aplica)"),
    _lista("estado", "Estado de la unidad", ["Activa", "Inactiva"]),
]

OBLIGATORIOS_UPGD = {"cod_prestador", "razon_social"}

RECURSOS_UPGD = {
    "unidad_analisis": "Unidad de análisis",
    "cove": "COVE",
    "talento_humano": "Talento humano disponible",
    "computador": "Computador",
    "fax_modem": "Fax/Módem",
    "correo_recurso": "Correo electrónico",
    "internet": "Internet",
    "telefax": "Telefax",
    "radio_telefono": "Radioteléfono",
}

CAMPOS_LAB = [
    _fecha("fecha_toma", "Fecha de toma"),
    _fecha("fecha_recepcion", "Fecha de recepción"),
    _texto("muestra", "Muestra"),
    _texto("prueba", "Prueba"),
    _texto("agente", "Agente"),
    _texto("resultado", "Resultado"),
    _fecha("fecha_resultado", "Fecha de resultado"),
    _texto("valor", "Valor (si aplica)"),
]
