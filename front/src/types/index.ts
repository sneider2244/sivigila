export type Rol =
  | "UPGD"
  | "UI"
  | "MUNICIPAL"
  | "DEPARTAMENTAL"
  | "NACIONAL"
  | "DOCENTE";

export interface Usuario {
  id: number;
  username: string;
  nombreCompleto: string;
  rol: Rol;
  codUpgd: string | null;
  activo: boolean;
}

export interface LoginResponse {
  accessToken: string;
  refreshToken: string;
  tokenType: string;
  user: Usuario;
}

export interface UPGD {
  codigo: string;
  nombre: string;
  departamento: string;
  municipio: string;
}

export interface Caso {
  id: string;
  estado: "borrador" | "notificado";
}

export type NivelComplejidad = 1 | 2 | 3 | 4;

export interface UpgdCaracterizacion {
  codPrestador: string;
  razonSocial: string;
  nit: string;
  nivelComplejidad: NivelComplejidad;
  cove: boolean;
  unidadAnalisis: boolean;
  internet: boolean;
  activo: boolean;
  departamentoCodigo: string | null;
  municipioCodigo: string | null;
}

export interface UpgdCaracterizacionRaw {
  cod_prestador: string;
  razon_social: string;
  nit: string;
  nivel_complejidad: number;
  cove: boolean;
  unidad_analisis: boolean;
  internet: boolean;
  activo: boolean;
  departamento_codigo: string | null;
  municipio_codigo: string | null;
}

export function mapUpgdCaracterizacion(
  raw: UpgdCaracterizacionRaw,
): UpgdCaracterizacion {
  return {
    codPrestador: raw.cod_prestador,
    razonSocial: raw.razon_social,
    nit: raw.nit,
    nivelComplejidad: raw.nivel_complejidad as NivelComplejidad,
    cove: raw.cove,
    unidadAnalisis: raw.unidad_analisis,
    internet: raw.internet,
    activo: raw.activo,
    departamentoCodigo: raw.departamento_codigo,
    municipioCodigo: raw.municipio_codigo,
  };
}

export function mapUpgdCaracterizacionToRaw(
  upgd: UpgdCaracterizacion,
): UpgdCaracterizacionRaw {
  return {
    cod_prestador: upgd.codPrestador,
    razon_social: upgd.razonSocial,
    nit: upgd.nit,
    nivel_complejidad: upgd.nivelComplejidad,
    cove: upgd.cove,
    unidad_analisis: upgd.unidadAnalisis,
    internet: upgd.internet,
    activo: upgd.activo,
    departamento_codigo: upgd.departamentoCodigo,
    municipio_codigo: upgd.municipioCodigo,
  };
}

export type Sexo = "M" | "F";
export type UnidadMedidaEdad = 1 | 2 | 3;
export type AreaOcurrencia = 1 | 2 | 3;
export type ClasificacionCaso = 1 | 2 | 3 | 4;
export type CondicionFinal = 1 | 2;

export interface GruposPoblacionales {
  gestante: boolean;
  semanasGestacion: number | null;
  desplazado: boolean;
  otraIdentidad: string | null;
  fHospitalizacion: string | null;
  fDefuncion: string | null;
  certificado: string | null;
}

export type EstadoFicha =
  | "NOTIFICADA"
  | "EN_AJUSTE"
  | "CONFIRMADA"
  | "DESCARTADA";

export interface FichaDatosBasicos {
  codUpgd: string;
  subindice: string;
  codEvento: string;
  fGrabacion: string;
  fNotificacion: string;
  anio: number;
  semanaEpidemiologica: number;
  tipoId: string;
  numId: string;
  primerNombre: string;
  segundoNombre: string | null;
  primerApellido: string;
  segundoApellido: string | null;
  telefono: string | null;
  fNacimiento: string;
  edad: number;
  undMedEdad: UnidadMedidaEdad;
  sexo: Sexo;
  identidadGenero: number;
  orientacionSexual: number;
  paisOcurrencia: string;
  dptoOcurrencia: string;
  muniOcurrencia: string;
  areaOcurrencia: AreaOcurrencia;
  gruposPoblacionales: GruposPoblacionales;
  clasificacionCaso: ClasificacionCaso;
  hospitalizado: boolean;
  condicionFinal: CondicionFinal;
  estado: EstadoFicha;
}

export interface GruposPoblacionalesRaw {
  gestante: boolean;
  semanas_gestacion: number | null;
  desplazado: boolean;
  otra_identidad: string | null;
  f_hospitalizacion: string | null;
  f_defuncion: string | null;
  certificado: string | null;
}

export interface FichaDatosBasicosRaw {
  cod_upgd: string;
  subindice: string;
  cod_evento: string;
  f_grabacion: string;
  f_notificacion: string;
  anio: number;
  semana_epidemiologica: number;
  tipo_id: string;
  num_id: string;
  primer_nombre: string;
  segundo_nombre: string | null;
  primer_apellido: string;
  segundo_apellido: string | null;
  telefono: string | null;
  f_nacimiento: string;
  edad: number;
  und_med_edad: UnidadMedidaEdad;
  sexo: Sexo;
  identidad_genero: number;
  orientacion_sexual: number;
  pais_ocurrencia: string;
  dpto_ocurrencia: string;
  muni_ocurrencia: string;
  area_ocurrencia: AreaOcurrencia;
  grupos_poblacionales: GruposPoblacionalesRaw;
  clasificacion_caso: ClasificacionCaso;
  hospitalizado: boolean;
  condicion_final: CondicionFinal;
  estado: EstadoFicha;
}

export function mapGruposPoblacionales(
  raw: GruposPoblacionalesRaw,
): GruposPoblacionales {
  return {
    gestante: raw.gestante,
    semanasGestacion: raw.semanas_gestacion,
    desplazado: raw.desplazado,
    otraIdentidad: raw.otra_identidad,
    fHospitalizacion: raw.f_hospitalizacion,
    fDefuncion: raw.f_defuncion,
    certificado: raw.certificado,
  };
}

export function mapGruposPoblacionalesToRaw(
  grupos: GruposPoblacionales,
): GruposPoblacionalesRaw {
  return {
    gestante: grupos.gestante,
    semanas_gestacion: grupos.semanasGestacion,
    desplazado: grupos.desplazado,
    otra_identidad: grupos.otraIdentidad,
    f_hospitalizacion: grupos.fHospitalizacion,
    f_defuncion: grupos.fDefuncion,
    certificado: grupos.certificado,
  };
}

export function mapFichaDatosBasicos(
  raw: FichaDatosBasicosRaw,
): FichaDatosBasicos {
  return {
    codUpgd: raw.cod_upgd,
    subindice: raw.subindice,
    codEvento: raw.cod_evento,
    fGrabacion: raw.f_grabacion,
    fNotificacion: raw.f_notificacion,
    anio: raw.anio,
    semanaEpidemiologica: raw.semana_epidemiologica,
    tipoId: raw.tipo_id,
    numId: raw.num_id,
    primerNombre: raw.primer_nombre,
    segundoNombre: raw.segundo_nombre,
    primerApellido: raw.primer_apellido,
    segundoApellido: raw.segundo_apellido,
    telefono: raw.telefono,
    fNacimiento: raw.f_nacimiento,
    edad: raw.edad,
    undMedEdad: raw.und_med_edad,
    sexo: raw.sexo,
    identidadGenero: raw.identidad_genero,
    orientacionSexual: raw.orientacion_sexual,
    paisOcurrencia: raw.pais_ocurrencia,
    dptoOcurrencia: raw.dpto_ocurrencia,
    muniOcurrencia: raw.muni_ocurrencia,
    areaOcurrencia: raw.area_ocurrencia,
    gruposPoblacionales: mapGruposPoblacionales(raw.grupos_poblacionales),
    clasificacionCaso: raw.clasificacion_caso,
    hospitalizado: raw.hospitalizado,
    condicionFinal: raw.condicion_final,
    estado: raw.estado,
  };
}

export function mapFichaDatosBasicosToRaw(
  ficha: FichaDatosBasicos,
): FichaDatosBasicosRaw {
  return {
    cod_upgd: ficha.codUpgd,
    subindice: ficha.subindice,
    cod_evento: ficha.codEvento,
    f_grabacion: ficha.fGrabacion,
    f_notificacion: ficha.fNotificacion,
    anio: ficha.anio,
    semana_epidemiologica: ficha.semanaEpidemiologica,
    tipo_id: ficha.tipoId,
    num_id: ficha.numId,
    primer_nombre: ficha.primerNombre,
    segundo_nombre: ficha.segundoNombre,
    primer_apellido: ficha.primerApellido,
    segundo_apellido: ficha.segundoApellido,
    telefono: ficha.telefono,
    f_nacimiento: ficha.fNacimiento,
    edad: ficha.edad,
    und_med_edad: ficha.undMedEdad,
    sexo: ficha.sexo,
    identidad_genero: ficha.identidadGenero,
    orientacion_sexual: ficha.orientacionSexual,
    pais_ocurrencia: ficha.paisOcurrencia,
    dpto_ocurrencia: ficha.dptoOcurrencia,
    muni_ocurrencia: ficha.muniOcurrencia,
    area_ocurrencia: ficha.areaOcurrencia,
    grupos_poblacionales: mapGruposPoblacionalesToRaw(
      ficha.gruposPoblacionales,
    ),
    clasificacion_caso: ficha.clasificacionCaso,
    hospitalizado: ficha.hospitalizado,
    condicion_final: ficha.condicionFinal,
    estado: ficha.estado,
  };
}

export interface DatosAccidente {
  fecha: string;
  direccion: string;
  agenteAgresor: number;
}

export interface DatosAccidenteRaw {
  fecha: string;
  direccion: string;
  agente_agresor: number;
}

export interface ManifestacionesLocales {
  edema: boolean;
  dolor: boolean;
  eritema: boolean;
  equimosis: boolean;
  flictenas: boolean;
  necrosisLocal: boolean;
}

export interface ManifestacionesLocalesRaw {
  edema: boolean;
  dolor: boolean;
  eritema: boolean;
  equimosis: boolean;
  flictenas: boolean;
  necrosis_local: boolean;
}

export interface ManifestacionesSistemicas {
  nauseas: boolean;
  vomito: boolean;
  dolorAbdominal: boolean;
  bradicardia: boolean;
  hipotension: boolean;
  sangrado: boolean;
}

export interface ManifestacionesSistemicasRaw {
  nauseas: boolean;
  vomito: boolean;
  dolor_abdominal: boolean;
  bradicardia: boolean;
  hipotension: boolean;
  sangrado: boolean;
}

export interface Complicaciones {
  celulitis: boolean;
  necrosis: boolean;
  insuficienciaRenal: boolean;
  hipoxia: boolean;
}

export interface ComplicacionesRaw {
  celulitis: boolean;
  necrosis: boolean;
  insuficiencia_renal: boolean;
  hipoxia: boolean;
}

export interface AtencionHospitalaria {
  empleoSuero: number;
  dosis: number | null;
}

export interface AtencionHospitalariaRaw {
  empleo_suero: number;
  dosis: number | null;
}

export interface ContenidoOfidico {
  datosAccidente: DatosAccidente;
  manifestacionesLocales: ManifestacionesLocales;
  manifestacionesSistemicas: ManifestacionesSistemicas;
  complicaciones: Complicaciones;
  atencionHospitalaria: AtencionHospitalaria;
}

export interface ContenidoOfidicoRaw {
  datos_accidente: DatosAccidenteRaw;
  manifestaciones_locales: ManifestacionesLocalesRaw;
  manifestaciones_sistemicas: ManifestacionesSistemicasRaw;
  complicaciones: ComplicacionesRaw;
  atencion_hospitalaria: AtencionHospitalariaRaw;
}

export interface FichaDatosComplementarios {
  fichaBasicaId: number;
  codEvento: string;
  contenido: ContenidoOfidico;
}

export interface FichaDatosComplementariosRaw {
  ficha_basica_id: number;
  cod_evento: string;
  contenido: ContenidoOfidicoRaw;
}

export function mapContenidoOfidico(
  raw: ContenidoOfidicoRaw,
): ContenidoOfidico {
  return {
    datosAccidente: {
      fecha: raw.datos_accidente.fecha,
      direccion: raw.datos_accidente.direccion,
      agenteAgresor: raw.datos_accidente.agente_agresor,
    },
    manifestacionesLocales: {
      edema: raw.manifestaciones_locales.edema,
      dolor: raw.manifestaciones_locales.dolor,
      eritema: raw.manifestaciones_locales.eritema,
      equimosis: raw.manifestaciones_locales.equimosis,
      flictenas: raw.manifestaciones_locales.flictenas,
      necrosisLocal: raw.manifestaciones_locales.necrosis_local,
    },
    manifestacionesSistemicas: {
      nauseas: raw.manifestaciones_sistemicas.nauseas,
      vomito: raw.manifestaciones_sistemicas.vomito,
      dolorAbdominal: raw.manifestaciones_sistemicas.dolor_abdominal,
      bradicardia: raw.manifestaciones_sistemicas.bradicardia,
      hipotension: raw.manifestaciones_sistemicas.hipotension,
      sangrado: raw.manifestaciones_sistemicas.sangrado,
    },
    complicaciones: {
      celulitis: raw.complicaciones.celulitis,
      necrosis: raw.complicaciones.necrosis,
      insuficienciaRenal: raw.complicaciones.insuficiencia_renal,
      hipoxia: raw.complicaciones.hipoxia,
    },
    atencionHospitalaria: {
      empleoSuero: raw.atencion_hospitalaria.empleo_suero,
      dosis: raw.atencion_hospitalaria.dosis,
    },
  };
}

export function mapContenidoOfidicoToRaw(
  contenido: ContenidoOfidico,
): ContenidoOfidicoRaw {
  return {
    datos_accidente: {
      fecha: contenido.datosAccidente.fecha,
      direccion: contenido.datosAccidente.direccion,
      agente_agresor: contenido.datosAccidente.agenteAgresor,
    },
    manifestaciones_locales: {
      edema: contenido.manifestacionesLocales.edema,
      dolor: contenido.manifestacionesLocales.dolor,
      eritema: contenido.manifestacionesLocales.eritema,
      equimosis: contenido.manifestacionesLocales.equimosis,
      flictenas: contenido.manifestacionesLocales.flictenas,
      necrosis_local: contenido.manifestacionesLocales.necrosisLocal,
    },
    manifestaciones_sistemicas: {
      nauseas: contenido.manifestacionesSistemicas.nauseas,
      vomito: contenido.manifestacionesSistemicas.vomito,
      dolor_abdominal: contenido.manifestacionesSistemicas.dolorAbdominal,
      bradicardia: contenido.manifestacionesSistemicas.bradicardia,
      hipotension: contenido.manifestacionesSistemicas.hipotension,
      sangrado: contenido.manifestacionesSistemicas.sangrado,
    },
    complicaciones: {
      celulitis: contenido.complicaciones.celulitis,
      necrosis: contenido.complicaciones.necrosis,
      insuficiencia_renal: contenido.complicaciones.insuficienciaRenal,
      hipoxia: contenido.complicaciones.hipoxia,
    },
    atencion_hospitalaria: {
      empleo_suero: contenido.atencionHospitalaria.empleoSuero,
      dosis: contenido.atencionHospitalaria.dosis,
    },
  };
}

export function mapFichaDatosComplementarios(
  raw: FichaDatosComplementariosRaw,
): FichaDatosComplementarios {
  return {
    fichaBasicaId: raw.ficha_basica_id,
    codEvento: raw.cod_evento,
    contenido: mapContenidoOfidico(raw.contenido),
  };
}

export function mapFichaDatosComplementariosToRaw(
  ficha: FichaDatosComplementarios,
): FichaDatosComplementariosRaw {
  return {
    ficha_basica_id: ficha.fichaBasicaId,
    cod_evento: ficha.codEvento,
    contenido: mapContenidoOfidicoToRaw(ficha.contenido),
  };
}
