from enum import StrEnum


class Rol(StrEnum):
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    DIGITADOR = "digitador"
    CONSULTA = "consulta"


class EstadoFicha(StrEnum):
    EN_PROCESO = "En proceso"
    TERMINADA = "Terminada"


class TipoCampo(StrEnum):
    TEXTO = "texto"
    SI_NO = "si_no"
    LISTA = "lista"
