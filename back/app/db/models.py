from datetime import date, datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    salt: Mapped[str] = mapped_column(String(64), nullable=False)
    nombre_completo: Mapped[str] = mapped_column(String(255), nullable=False)
    rol: Mapped[str] = mapped_column(String(20), nullable=False, default="digitador")
    permisos: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    creado_por: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id"), nullable=True)


class Upgd(Base):
    __tablename__ = "upgd"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    cod_prestador: Mapped[str] = mapped_column(String(50), nullable=False)
    subred: Mapped[str | None] = mapped_column(String(255))
    fecha_caracteriza: Mapped[date | None] = mapped_column(Date)
    fecha_inicio_uso: Mapped[date | None] = mapped_column(Date)
    razon_social: Mapped[str] = mapped_column(String(255), nullable=False)
    nit: Mapped[str | None] = mapped_column(String(50))
    direccion: Mapped[str | None] = mapped_column(String(255))
    representante_legal: Mapped[str | None] = mapped_column(String(255))
    correo_electronico: Mapped[str | None] = mapped_column(String(255))
    responsable_notif: Mapped[str | None] = mapped_column(String(255))
    telefono: Mapped[str | None] = mapped_column(String(50))
    fecha_constitucion: Mapped[date | None] = mapped_column(Date)
    naturaleza_juridica: Mapped[str | None] = mapped_column(String(100))
    nivel_complejidad: Mapped[str | None] = mapped_column(String(50))
    tipo_unidad: Mapped[str | None] = mapped_column(String(50))
    estado: Mapped[str] = mapped_column(String(20), nullable=False, default="Activa")
    localidad_zona: Mapped[str | None] = mapped_column(String(255))
    notif_iad: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    notif_iso: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    notif_cab: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    unidad_analisis: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    cove: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    talento_humano: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    fax_modem: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    correo_recurso: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    internet: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    telefax: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    radio_telefono: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    computador: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    activa_sivigila: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class Evento(Base):
    __tablename__ = "eventos"

    codigo: Mapped[str] = mapped_column(String(10), primary_key=True)
    nombre: Mapped[str] = mapped_column(String(255), nullable=False)
    campos_json: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False)


class Notificacion(Base):
    __tablename__ = "notificaciones"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    upgd_id: Mapped[int] = mapped_column(ForeignKey("upgd.id"), nullable=False, index=True)
    codigo_ficha: Mapped[str | None] = mapped_column(String(50))
    ajuste: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    fecha_grabacion: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    codigo_evento: Mapped[str] = mapped_column(
        ForeignKey("eventos.codigo"), nullable=False, index=True
    )
    fecha_notificacion: Mapped[date | None] = mapped_column(Date)
    anio: Mapped[int | None] = mapped_column(Integer)
    semana: Mapped[int | None] = mapped_column(Integer)
    tipo_id: Mapped[str | None] = mapped_column(String(10))
    numero_id: Mapped[str | None] = mapped_column(String(50), index=True)
    primer_nombre: Mapped[str | None] = mapped_column(String(100))
    segundo_nombre: Mapped[str | None] = mapped_column(String(100))
    primer_apellido: Mapped[str | None] = mapped_column(String(100), index=True)
    segundo_apellido: Mapped[str | None] = mapped_column(String(100))
    telefono: Mapped[str | None] = mapped_column(String(50))
    fecha_nacimiento: Mapped[date | None] = mapped_column(Date)
    edad: Mapped[int | None] = mapped_column(Integer)
    unidad_edad: Mapped[str | None] = mapped_column(String(20))
    sexo: Mapped[str | None] = mapped_column(String(5))
    nacionalidad: Mapped[str | None] = mapped_column(String(100))
    pais_procedencia: Mapped[str | None] = mapped_column(String(100))
    departamento: Mapped[str | None] = mapped_column(String(100))
    municipio: Mapped[str | None] = mapped_column(String(100))
    area: Mapped[str | None] = mapped_column(String(50))
    localidad: Mapped[str | None] = mapped_column(String(100))
    centro_poblado: Mapped[str | None] = mapped_column(String(100))
    vereda: Mapped[str | None] = mapped_column(String(100))
    barrio: Mapped[str | None] = mapped_column(String(100))
    ocupacion: Mapped[str | None] = mapped_column(String(150))
    tipo_regimen: Mapped[str | None] = mapped_column(String(50))
    administradora: Mapped[str | None] = mapped_column(String(150))
    pertenencia_etnica: Mapped[str | None] = mapped_column(String(100))
    grupo_etnico: Mapped[str | None] = mapped_column(String(100))
    fuente: Mapped[str | None] = mapped_column(String(50))
    direccion_residencia: Mapped[str | None] = mapped_column(String(255))
    fecha_consulta: Mapped[date | None] = mapped_column(Date)
    fecha_inicio_sintomas: Mapped[date | None] = mapped_column(Date)
    clasificacion_caso: Mapped[str | None] = mapped_column(String(100))
    hospitalizado: Mapped[bool | None] = mapped_column(Boolean)
    fecha_hospitalizacion: Mapped[date | None] = mapped_column(Date)
    condicion: Mapped[str | None] = mapped_column(String(50))
    fecha_defuncion: Mapped[date | None] = mapped_column(Date)
    certificado_defuncion: Mapped[str | None] = mapped_column(String(50))
    causa_basica: Mapped[str | None] = mapped_column(String(255))
    nombre_diligencia: Mapped[str | None] = mapped_column(String(255))
    telefono_diligencia: Mapped[str | None] = mapped_column(String(50))
    datos_complementarios: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    estado_ficha: Mapped[str] = mapped_column(String(20), nullable=False, default="En proceso")
    creado_por: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id"), nullable=True)
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    actualizado_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    laboratorios: Mapped[list["Laboratorio"]] = relationship(
        back_populates="notificacion", cascade="all, delete-orphan"
    )


class Laboratorio(Base):
    __tablename__ = "laboratorios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    notificacion_id: Mapped[int] = mapped_column(
        ForeignKey("notificaciones.id", ondelete="CASCADE"), nullable=False, index=True
    )
    fecha_toma: Mapped[date | None] = mapped_column(Date)
    fecha_recepcion: Mapped[date | None] = mapped_column(Date)
    muestra: Mapped[str | None] = mapped_column(String(150))
    prueba: Mapped[str | None] = mapped_column(String(150))
    agente: Mapped[str | None] = mapped_column(String(150))
    resultado: Mapped[str | None] = mapped_column(String(150))
    fecha_resultado: Mapped[date | None] = mapped_column(Date)
    valor: Mapped[str | None] = mapped_column(String(100))
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    notificacion: Mapped["Notificacion"] = relationship(back_populates="laboratorios")


class Auditoria(Base):
    __tablename__ = "auditoria"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    usuario_id: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id"), nullable=True)
    accion: Mapped[str | None] = mapped_column(String(50))
    detalle: Mapped[str | None] = mapped_column(Text)
    fecha: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
