/*
 * Addax Software Development, S.A. Copyright (c) 2017.
 */

var CONFIG = (function() {
    var SNIT_SERVER_NAME = "www.snitcr.go.cr";
    var SNITAPIHOST = "https://www.snitcr.go.cr";
    var SNITHOST = "https://" + SNIT_SERVER_NAME;
    var SNITHOSTFILES = "https://files.snitcr.go.cr" ;

    var MAX_CSV_SIZE = 30*1024*1024;

    var VISOR_TAB_NAME = 'Visor';

    var URL_DATOS_USUARIO = SNITHOST + "/datos_usuario";

    var URL_ORTOMAPAS_INTERES = SNITHOST + "/ortomapas_interes";
    var URL_TEMATICAS = SNITHOST + "/tematicas";
    var URL_CAPAS_RECIENTES = SNITHOST + "/capas_recientes";
    var URL_CAPAS_FUNDAMENTALES = SNITHOST + "/capas_fundamentales";
    var URL_CAPAS_POPULARES = SNITHOST + "/capas_populares";
    var URL_NOTICIAS = SNITHOST + "/Noticias/noticias";
    var URL_DETALLE_NOTICIAS = SNITHOST + "/Noticias/detallenoticia";
    var URL_NOTICIAS_RELEVANTES = SNITHOST + "/Noticias/noticias_relevantes";
    var URL_BUSQUEDA_CAPAS = SNITHOST + "/busqueda_capas";
    var URL_AGREGAR_WMS = SNITHOST + "/agregar_wms";
    var URL_AGREGAR_VISOR = SNITHOST + "/agregar_visor";
    var URL_DETALLE_CAPA = SNITHOST + "/Visor/detalles_capa";
    var URL_ELIMINAR_VISOR = SNITHOST + "/Visor/eliminar_visor";
    var URL_AGREGAR_WFS = SNITHOST + "/agregar_wfs";
    var URL_DOCUMENTOS_MANUALES = SNITHOST + "/documentos_manuales";
    var URL_TUTORIALES_PRESENTACIONES = SNITHOST + "/lista_tutoriales_presentaciones";
    var URL_BANNER = SNITHOST + "/banner";
    var URL_NOTICIAS_BANNER = SNITHOST + "/noticias_banner";
    var URL_FORMULARIO_COORDENADAS_XY = SNITHOST + "/formulario_coordenadasXY_guardar_datos";

    var URL_CHARLAS = SNITHOST + "/lista_charlas";
    var URL_GUIAS = SNITHOST + "/lista_guias";

    var URL_LOGIN = SNITHOST + "/User/login";
    var URL_LOGOUT = SNITHOST + "/User/logout";
    var URL_LOGGED = SNITHOST + "/User/logged";
    var URL_GET_FORM_REGISTRO_PASO1 = SNITHOST + "/User/usuario_registro_paso1";
    var URL_USUARIO_REGISTRATION_PASO1 = SNITHOST + "/User/registration_paso1";
    var URL_USUARIO_REGISTRATION_PASO2 = SNITHOST + "/User/registration_paso2";
    var URL_USUARIO_CAMBIAR_PASS = SNITHOST + "/User/cambiar_pass";
    var URL_USUARIO_ACTUALIZAR_PASS = SNITHOST + "/User/actualizar_contrasena.php";
    var URL_USUARIO_FORGOT = SNITHOST + "/User/forgotPass";
    var URL_TEMAS_INTERES = SNITHOST + "/User/temas_interes";
    var URL_TIPO_USUARIO = SNITHOST + "/User/tipo_usuario";
    var URL_INSTITUCION_USUARIO = SNITHOST + "/User/institucion_usuario";
    var URL_DATOS_PROFILE = SNITHOST + "/User/datos_profile";
    var URL_GET_COMPARTIDOS_BY_PROJECT_KEY = SNITHOST + "/User/get_compartidos_by_project_key";
    var URL_USERS_PDFS = SNITHOST + "/User/pdfs";
    var URL_DOCUMENTOS_LEGAL = SNITHOST + "/lista_documentos_legal2";
    var URL_DOCUMENTOS_DECRETOS = SNITHOST + "/lista_documentos_decretos";
    var URL_INFORMES_SEMESTRALES = SNITHOST + "/ign_lista_informes_semestrales";
    var URL_GEOPORTAL_LIMITES_DOCUMENTOS = SNITHOST + "/get_geoportal_limites_documentos";
    var URL_AVISOS = SNITHOST + "/biblioteca_lista_avisos";
    var URL_PRESENTACIONES = SNITHOST + "/ign_lista_presentaciones";
    var URL_UTILIDADES = SNITHOST + "/ico_lista_utilidades";
    var URL_REPOSITORIO_DOCUMENTOS = SNITHOST + "/lista_repositorio_documentos";
    var URL_CONSULTAR_DTA_LEGAL = SNITHOST + "/consultar_DTA_legal";
    var URL_CONSULTAR_DTA_DOCUMENTOS_GENERALES = SNITHOST + "/consultar_DTA_documentos_generales";
    var URL_CONSULTAR_NG_LEGAL = SNITHOST + "/consultar_NG_legal";
    var URL_GUARDAR_DTA_LEGAL = SNITHOST + "/guardar_DTA_legal";
    var URL_GUARDAR_NG_LEGAL = SNITHOST + "/guardar_NG_legal";

    var URL_HOME_UPLOAD = SNITHOST + "/savefile";
    var URL_HOME_DOWNLOAD = SNITHOST + "/vf";
    var URL_AGREGAR_DTA_LEGAL_DOC = SNITHOST + "/DTAlegal_agregar";
    var URL_AGREGAR_DTA_LEGAL_DOC2 = SNITHOST + "/agregar_dta_legal2";//"/DTAlegal_agregar2";
    var URL_AGREGAR_NG_LEGAL_DOC = SNITHOST + "/NGlegal_agregar";
    var URL_BORRAR_DTA_LEGAL_DOC = SNITHOST + "/borrar_DTA_legal_Doc";
    var URL_BORRAR_NG_LEGAL_DOC = SNITHOST + "/borrar_NG_legal_Doc";
    var URL_DTA_LEGAL = SNITHOST + "/dta_legal";
    var URL_DTA_LEGAL2 = SNITHOST + "/DTAlegal2";
    var URL_NG_LEGAL = SNITHOST + "/NGlegal";
    var URL_GET_ANIOS = SNITHOST + "/get_anios";
    var URL_BIBLIOTECA_DTA = SNITHOST + '/biblioteca_DTA';

    var URL_NOTICIAS_UPLOAD = SNITHOST + "/Noticias/savefile";
    var URL_NOTICIAS_DOWNLOAD = SNITHOST + "/Noticias/vf";
    var URL_GUARDAR_NOTICIAS = SNITHOST + "/Noticias/guardar_noticia";
    var URL_GET_NOTICIAS = SNITHOST + "/Noticias/get_noticia";
    var URL_GET_EDITAR_NOTICIAS = SNITHOST + "/Noticias/editar_noticia";
    var URL_GET_BORRAR_NOTICIAS = SNITHOST + "/Noticias/borrar_noticia";


    var URL_VISOR_POINT_QUERY = SNITAPIHOST + "/Visor/pointquery";

    var URL_FULLMETADATA = SNITHOST + "/Metadatos/get_full_metadata";
    var URL_GETXMLMETADATA = SNITHOST + "/Metadatos/get_xml_metadata";
    var URL_GETDOCXMETADATA = SNITHOST + "/Metadatos/get_docx_metadata";
    var URL_GETPDFMETADATA = SNITHOST + "/Metadatos/get_pdf_metadata";

    var URL_GUARDARMETADATA = SNITHOST + "/Metadatos/guardar_metadata";
    var URL_GUARDARMETADATA_V_101 = SNITHOST + "/Metadatos/guardar_metadata_V_101";

    var URL_EDITARMETADATA = SNITHOST + "/Metadatos/editar_metadata_V_101";
    var URL_EDITARMETADATA2 = SNITHOST + "/Metadatos/editar_metadata_V_101_2";
    var URL_CREARMETADATA = SNITHOST + "/Metadatos/crear_metadata_V_101";
    var URL_CREARMETADATA2 = SNITHOST + "/Metadatos/crear_metadata_V_101_2";
    var URL_COPIARMETADATO = SNITHOST + "/Metadatos/copiar_metadata";
    var URL_ELIMINARMETADATO = SNITHOST + "/Metadatos/eliminar_metadata";

    var URL_CAMBIARESTADOMETADATA = SNITHOST + "/Metadatos/cambiar_estado_metadata";
    var URL_LISTADOMETADATA = SNITHOST + "/Metadatos/listado_metadata";

    var URL_GETFORMMETADATA = SNITHOST + "/Metadatos/get_version_form_metadata";
    var URL_GETFORMMETADATA_V_101 = SNITHOST + "/Metadatos/get_version_form_metadata_V_101";
    var URL_GETFORMMETADATA_V_101_2 = SNITHOST + "/Metadatos/get_version_form_metadata_V_101_2";
    var URL_TOOLTIPS_METADATA = SNITHOST + "/Metadatos/get_tooltips";
    var URL_XML_CAPA_METADATOS_METADATA = SNITHOST + "/Metadatos/get_xml_capa_metadatos";
    var URL_XML_CAPA_FULLMETADATOS_METADATA = SNITHOST + "/Metadatos/get_fullmetadata_xml";
    var URL_DOCX_CAPA_METADATOS_METADATA = SNITHOST + "/Metadatos/get_docx_capa_metadatos";
    var URL_PDF_CAPA_METADATOS_METADATA = SNITHOST + "/Metadatos/get_pdf_capa_metadatos";

    var URL_VERMETADATA = SNITHOST + "/Metadatos/ver_metadata_V_101";
    var URL_VERMETADATA2 = SNITHOST + "/Metadatos/ver_metadata_V_101_2";
    var URL_VERMETADATAPUBLICO = SNITHOST + "/Metadatos/ver_metadata_publico";
    var URL_VERMETADATAPUBLICO2 = SNITHOST + "/Metadatos/ver_metadata_publico2";
    var URL_ALLMETADATA = SNITHOST + "/Metadatos/get_all_metadata";
    var URL_DISPLAYFULLMETADATA = SNITHOST + "/Metadatos/full_metadata";
    var URL_DISPLAYFULLMETADATA2 = SNITHOST + "/Metadatos/full_metadata2";
    var URL_METADATOS_UPLOAD = SNITHOST + "/Metadatos/savefile";
    var URL_METADATOS_DOWNLOAD = SNITHOST + "/Metadatos/vf";
    var URL_METADATOS_DESCARGAR_PLANTILLA_XML_METADATOS = SNITHOST + "/Metadatos/descargar_plantilla_xml_metadatos";

    var URL_ACTUALIZAR_USUARIO = SNITHOST + "/User/actualizar_usuario";
    var URL_CAMBIAR_CLAVE_USUARIO = SNITHOST + "/User/cambiar_clave";
    var URL_EDITARPROYECTOS =  "/User/editarproyectos";
    var URL_EDITARPROYECTOUSUARIOSCOMPARTIDOS =  "/User/editar_compartidos";
    var URL_GETPROYECTOSEDICION =  "/User/getproyectosedicion";
    var URL_GETUSERACTUALIZARPROYECTO = "/User/actualizar_proyecto";
    var URL_GETUSERBORRARPROYECTO = "/User/borrar_proyecto";
    var URL_GETUSERCOMPARTIRPROYECTO = "/User/compartir_proyecto";
    var URL_GETUSERCOMPARTIRPROYECTOACEPTAR = "/User/compartir_proyecto_aceptar";
    var URL_GETUSERCOMPARTIRPROYECTONEGAR = "/User/compartir_proyecto_denegar";
    var URL_USER_CHANGE_PASSWORD = "/User/change_password";

    var URL_VISOR_UPLOAD = "/Visor/savefile";
    var URL_VISOR_PLANTILLAS = "/Visor/imprimirplantillas";
    var URL_PROYECTOSLISTA =  "/Visor/listarproyectos";
    var URL_PROYECTOSLISTADETALLADA =  "/Visor/listadetalladaproyectos";
    var URL_PROYECTOACTUAL = "/Visor/projects";
    var URL_VISOR_VERFILE = "/Visor/vf";
    var URL_DATOS_PROYECTO = "/Visor/datos_proyecto";
    var URL_CHECKFILES = "/Visor/checkfile";
    var URL_PDF_HOJAS_BASE = SNITHOSTFILES+"/Visor/pdf/hojas";
    var URL_PDF_HOJAS_TIPOS_ZIPFULL = SNITHOSTFILES  +"/Visor";
    var URL_PDF_HOJAS_TIPOS_ZIPREC = SNITHOSTFILES  +"/Visor";
    var URL_PDF_HOJAS_TIPOS_RARFULL= SNITHOSTFILES  +"/Visor";
    var URL_PDF_HOJAS_TIPOS_RARREC= SNITHOSTFILES  +"/Visor";
    var URL_PDF_LIMITES_MARITIMOS= SNITHOSTFILES  +"/Visor/limites";
    var URL_BANCOSNIVEL= "/static/Fichas_BancosNivel/FICHAS-SNIT-NUEVAS/";

    var URL_CONT_PROYECTO = "/Visor/proyectos_cont";
    var URL_SERVICIOS_OGC = SNITHOST + "/lista_capas_servicio_ogc";
    var URL_SUGERENCIACAPAS = SNITHOST + "/Visor/sugerencias_capas";
    var URL_EXPLORADOR_CAPAS = SNITHOST + "/Visor/exploradorcapas";
    var URL_LISTA_CAPAS_EXPLORADOR = SNITHOST + "/Visor/listar_capas_explorador";
    var URL_D3_CAPAS_EXPLORADOR = SNITHOST + "/Visor/capas_d3";
    var URL_PREVISUALIZAR_CAPA = SNITHOST + "/Visor/index?k=";
    var URL_VISOR_DEFAULT = SNITHOST + "/Visor/index";
    var URL_D3_NODOS = SNITHOST + "/Visor/get_nodos.php";
    var URL_GET_AGREGAR_CAPAS = SNITHOST + "/Visor/get_agregarcapas_nodos.php";
    var URL_DATOS_NODO = SNITHOST + "/Visor/detalle_nodo";
    var URL_AVISOS_DATOS_NODO = SNITHOST + "/Visor/aviso_nodo";

    var URL_CAPAS_DE_NODO = SNITHOST + "/Visor/capas_de_nodo";

    var URL_CONSULTAS_RPN = SNITHOST + "/consultas_rpn";
    var URL_CONSULTAS_FODESAF = SNITHOST + "/consultas_fodesaf";
    var URL_CONSULTAS_CCSS = SNITHOST + "/consultas_ccss";

    var URL_CONSULTAS_COLEGIO_ABOGADOS = SNITHOST + "/consultas_colegio_abogados";

    var URL_METADATOS_CAPA = SNITHOST + "/Metadatos/resumen_metadatos_capa";
    var URL_CAMBIAR_PROYECTO = /*SNITHOST + */"/Visor/cambiarproyecto";
    var URL_SERVICIOS_BANCOIMAGENES = /*SNITHOST + */"/Visor/services/bancoimagenes";
    var URL_GUARDAR_PROYECTO = /*SNITHOST + */"/Visor/estadocapas";
    var URL_RED_GEODESICA = /*SNITHOST + */"/Visor/redgeodesica";
    var URL_NOMBRE_GEOGRAFICO = /*SNITHOST + */"/Visor/nombregeografico";
    var URL_FILE_MANAGER = /*SNITHOST + */"/Visor/fileman";
    var URL_GET_NODOS_SNIT = /*SNITHOST + */"/Visor/get_nodos_snit";
    var URL_GET_CATALOGO_MAPA_FOTOS1 = /*SNITHOST + */"/catalogo/mapafotos/";

    // http://images.snitcr.go.cr/fotohistorica/<vuelo>/xxxxxx
    // terra1998, cwa1940, jica1970
    var URL_GET_CATALOGO_MAPA_FOTOSTERRA = /*SNITHOST + */"https://files.snitcr.go.cr/ARCHIVOS_ORIGINALES/CatalogodeFotos/TERRA/";
    var URL_GET_CATALOGO_MAPA_FOTOSCWA = /*SNITHOST + */"https://files.snitcr.go.cr/ARCHIVOS_ORIGINALES/CatalogodeFotos/CAW/";
    var URL_GET_CATALOGO_MAPA_FOTOSJICA = /*SNITHOST + */"https://files.snitcr.go.cr/ARCHIVOS_ORIGINALES/CatalogodeFotos/JICA/";
    var URL_GET_CATALOGO_MAPA_FOTOSINFORMATION = SNITAPIHOST+"/Visor/mapasfotos";

    var URL_WEBSOCKET_VISOR = "wss://" + SNIT_SERVER_NAME + "/VisorPusher/"
    var URL_BASE_GEOP = "/Geop/geop";
    var URL_RECIBIR_CAPA_USUARIO = "/Visor/recibircapausuario";
    var URL_CARGAR_CAPA_USUARIO = "/Visor/obtenercapausuario";
    var MAX_SHAPEFILE_ZIP_SIZE = 22*1024*1024; //cambiar a 5
    var MAX_ZIP_SIZE = 2*1024*1024;
    var MAX_PDF_SIZE = 2*1024*1024;
    var MAX_IMAGENES_SIZE = 2*1024*1024;
    var MAX_PLANTILLA_DOC_SIZE = 2*1024*1024;
    var RADIO_RANGO_NOMBRES_GEOGRAFICOS = 20*1000;//20 km en metros.
    var URL_BASE_GEOP_MAP = [];
    URL_BASE_GEOP_MAP.push('http://geop1.www.snitcr.go.cr/GeoP/geop');
    URL_BASE_GEOP_MAP.push('http://geop2.www.snitcr.go.cr/GeoP/geop');
    URL_BASE_GEOP_MAP.push('http://geop3.www.snitcr.go.cr/GeoP/geop');
    URL_BASE_GEOP_MAP.push('http://geop4.www.snitcr.go.cr/GeoP/geop');
    URL_BASE_GEOP_MAP.push('http://geop5.www.snitcr.go.cr/GeoP/geop');
    URL_BASE_GEOP_MAP.push('http://geop6.www.snitcr.go.cr/GeoP/geop');
    URL_BASE_GEOP_MAP.push('http://geop7.www.snitcr.go.cr/GeoP/geop');
    URL_BASE_GEOP_MAP.push('http://geop8.www.snitcr.go.cr/GeoP/geop');
    URL_BASE_GEOP_MAP.push('http://geop9.www.snitcr.go.cr/GeoP/geop');
    URL_BASE_GEOP_MAP.push('http://geop10.www.snitcr.go.cr/GeoP/geop');

    var URL_CONSUMO_DATOS = SNITHOST + "/php/consumo_datos.php";
    var URL_BUSQUEDA = SNITHOST + "/php/resultados_busqueda.php";
    var URL_TRAMITES_OTRAS_INSTITUCIONES = SNITHOST + "/php/tramites_otras_instituciones.php";
    var URL_PROYECTOS = SNITHOST + "/php/proyectos.php";
    var URL_RESULTADOS_BUSQUEDA_NOMENCLATOR = SNITHOST + "/php/busqueda_nomenclator.php";
    var URL_ELIMINAR_CAPA = SNITHOST + "/php/eliminar_capa.php";
    var URL_CAPAS_ADMINISTRAR_WFS = SNITHOST + "/php/capas_administrar_wfs.php";
    var URL_CAPAS_ADMINISTRAR_WMS = SNITHOST + "/php/capas_administrar_wms.php";
    var URL_ELIMINAR_CAPA_EN_SERVIDOR_WFS = SNITHOST + "/php/eliminar_capa_servidor_wfs.php";
    var URL_ELIMINAR_CAPA_EN_SERVIDOR_WMS = SNITHOST + "/php/eliminar_capa_servidor_wms.php";
    var URL_REGISTRAR_USUARIO = SNITHOST + "/php/registrar_usuario.php";
    var URL_HOME_CSVS = SNITHOST + "/csvs";

    var URL_PASSWORD_RECOVER = SNITHOST +  "/User/password_recover";

    var CANTIDAD_TEMATICAS = 7;
    var CANTIDAD_TEMATICAS_MOBILE = 3;
    var CANTIDAD_ORTOMAPAS_INTERES = 8;
    var CANTIDAD_ORTOMAPAS_INTERES_MOBILE = 4;
    var CANTIDAD_CAPAS_ACTUALIZADAS = 8;
    var CANTIDAD_CAPAS_ACTUALIZADAS_MOBILE = 4;
    var CANTIDAD_CAPAS_FUNDAMENTALES = 8;
    var CANTIDAD_CAPAS_FUNDAMENTALES_MOBILE = 4;
    var CANTIDAD_CAPAS_POPULARES = 5;
    var CANTIDAD_NOTICIAS = 6;
    var CANTIDAD_NOTICIAS_RELEVANTES = 2;
    var CANTIDAD_TRAMITES_OTRAS_INSTITUCIONES = 12;
    var CANTIDAD_TRAMITES_OTRAS_INSTITUCIONES_MOBILE = 8;
    var PROYECTO_ACTUAL;
    var PERSONAL_WFS_URL = SNITHOST + "/wfs/";
    var PERSONAL_WMS_URL = SNITHOST + "/wms/";

    var FORM_REPROYECCION_AVANZADA = SNITHOST + "/form_reproyeccion_avanzada";
    var FORM_REPROYECCION_AVANZADA2 = SNITHOST + "/form_reproyeccion_avanzada2";
    var REPROYECCION_AVANZADA = SNITHOST + "/reproyeccion_avanzada";

    var thisObject = this;

    /** TRAMITES DGM **/


    var URL_CONSULTAS_RPN_DGM = SNITHOST + "/TramitesDGM/consultas_rpn";

    var URL_CONSULTAS_RPN_SETENA = SNITHOST + "/TramitesSETENA/consultas_rpn";


    var URL_CONSULTAS_FODESAF_DGM = SNITHOST + "/consultas_fodesaf";

    var URL_CONSULTAS_CCSS_DGM = SNITHOST + "/TramitesDGM/consultas_ccss";

    var URL_CONSULTAS_CCSS_SETENA = SNITHOST + "/TramitesSETENA/consultas_ccss";

    var URL_DATOS_PRUEBA = SNITHOST + "/TramitesDGM/datos_prueba";

    var URL_DATOS_TRAMITE_CONCESION_MINERA = SNITHOST + "/TramitesDGM/datos_tramite_concesion_minera";

    var URL_DATOS_PRUEBA_2 = SNITHOST + "/TramitesDGM/prueba_2";

    var URL_GET_FORM_HASHES = SNITHOST + "/TramitesDGM/get_form_hashes";

    var URL_DATOS_TRAMITE_CONCESION_MINERA_CNE = SNITHOST + "/TramitesDGM/datos_tramite_concesion_minera_cne";

    var URL_DATOS_TRAMITE_CONCESION_MINERA_ESTADO = SNITHOST + "/TramitesDGM/datos_tramite_concesion_minera_estado";

    var URL_DATOS_TRAMITE_CONCESION_MINERA_AUTONOMAS = SNITHOST + "/TramitesDGM/datos_tramite_concesion_minera_autonomas";

    var URL_DATOS_TRAMITE_CONCESION_MINERA_ARTESANAL = SNITHOST + "/TramitesDGM/datos_tramite_concesion_minera_artesanal";

    var URL_DATOS_TRAMITE_CONCESION_MINERA_MUNICIPALIDAD = SNITHOST + "/TramitesDGM/datos_tramite_concesion_minera_municipalidad";

    var URL_DATOS_TRAMITE_CONCESION_MINERA_PRIVADO = SNITHOST + "/TramitesDGM/datos_tramite_concesion_minera_privado";

    var URL_DATOS_TRAMITES_EN_LINEA_DGM = SNITHOST + "/TramitesDGM/datos_tramites_en_linea";

    var URL_DATOS_FORMALIZACION_TRAMITES_DGM = SNITHOST + "/TramitesDGM/datos_formalizacion";

    var URL_DATOS_FORMALIZACION_ESTADO_TRAMITES_DGM = SNITHOST + "/TramitesDGM/datos_formalizacion_estado";

    var URL_DATOS_FORMALIZACION_MUNICIPALIDAD_TRAMITES_DGM = SNITHOST + "/TramitesDGM/datos_formalizacion_municipalidad";

    var URL_DATOS_FORMALIZACION_AUTONOMAS_TRAMITES_DGM = SNITHOST + "/TramitesDGM/datos_formalizacion_autonomas";

    var URL_DATOS_FORMALIZACION_CNE_TRAMITES_DGM = SNITHOST + "/TramitesDGM/datos_formalizacion_cne";

    var URL_FORM_TRAMITE_CONCESION_MINERA = SNITHOST + "/TramitesDGM/form_tramite_concesion_minera";

    var URL_FORM_TRAMITE_CONCESION_MINERA_CNE = SNITHOST + "/TramitesDGM/form_tramite_concesion_minera_cne";

    var URL_FORM_TRAMITE_CONCESION_MINERA_MUNICIPALIDAD = SNITHOST + "/TramitesDGM/form_tramite_concesion_minera_municipalidad";

    var URL_FORM_TRAMITE_CONCESION_MINERA_AUTONOMAS = SNITHOST + "/TramitesDGM/form_tramite_concesion_minera_autonomas";

    var URL_FORM_TRAMITE_CONCESION_MINERA_ESTADO = SNITHOST + "/TramitesDGM/form_tramite_concesion_minera_estado";

    var URL_FORM_FORMALIZACION= SNITHOST + "/TramitesDGM/form_formalizacion";

    var URL_FORM_FORMALIZACION_ESTADO = SNITHOST + "/TramitesDGM/form_formalizacion_estado";
    var URL_FORM_FORMALIZACION_AUTONOMAS = SNITHOST + "/TramitesDGM/form_formalizacion_autonomas";
    var URL_FORM_FORMALIZACION_MUNICIPALIDAD = SNITHOST + "/TramitesDGM/form_formalizacion_municipalidad";

    var URL_FORM_INFORMACION_GEOESPACIAL_CONCESION_MINERA = SNITHOST + "/TramitesDGM/form_informacion_geoespacial_concesion_minera";

    var URL_FORM_INFORMACION_GEOESPACIAL_CONCESION_MINERA_CNE = SNITHOST + "/TramitesDGM/form_informacion_geoespacial_concesion_minera_cne";

    var URL_FORM_INFORMACION_GEOESPACIAL_CONCESION_MINERA_ARTESANAL = SNITHOST + "/TramitesDGM/form_informacion_geoespacial_concesion_minera_artesanal";

    var URL_FORM_INFORMACION_GEOESPACIAL_CONCESION_MINERA_AUTONOMAS = SNITHOST + "/TramitesDGM/form_informacion_geoespacial_concesion_minera_autonomas";

    var URL_FORM_INFORMACION_GEOESPACIAL_CONCESION_MINERA_MUNICIPALIDAD = SNITHOST + "/TramitesDGM/form_informacion_geoespacial_concesion_minera_municipalidad";

    var URL_FORM_INFORMACION_GEOESPACIAL_CONCESION_MINERA_ESTADO = SNITHOST + "/TramitesDGM/form_informacion_geoespacial_concesion_minera_estado";

    var URL_FORM_INFORMACION_GEOESPACIAL_CONCESION_MINERA_PRIVADO = SNITHOST + "/TramitesDGM/form_informacion_geoespacial_concesion_minera_privado";

    var URL_FORM_RESULTADO_TRAMITE_CONCESION_MINERA = SNITHOST + "/TramitesDGM/form_resultado_tramite_concesion_minera";

    var URL_FORM_PUNTOS_FORMALIZACION = SNITHOST + "/TramitesDGM/form_puntos_formalizacion";

    var URL_FORM_PUNTOS_FORMALIZACION_ESTADO = SNITHOST + "/TramitesDGM/form_puntos_formalizacion_estado";
    var URL_FORM_PUNTOS_FORMALIZACION_MUNICIPALIDAD = SNITHOST + "/TramitesDGM/form_puntos_formalizacion_municipalidad";
    var URL_FORM_PUNTOS_FORMALIZACION_AUTONOMAS = SNITHOST + "/TramitesDGM/form_puntos_formalizacion_autonomas";

    var URL_MIS_TRAMITES_DGM = SNITHOST + "/TramitesDGM/mis_tramites";

    var URL_MIS_TRAMITES_IGN = SNITHOST + "/Tramites/mis_tramites";


    var URL_FORMN_TRAMITES_EN_LINEA_DGM = SNITHOST + "/TramitesDGM/form_tramites_en_linea";

    var URL_FORM_SELECCIONAR_MAPA_TRAMITES_EN_LINEA_DGM = SNITHOST + "/TramitesDGM/form_seleccionar_mapa_tramites_en_linea";

    var URL_GET_DOCX_TRAMITE_CONCESION_MINERA = SNITHOST + "/TramitesDGM/get_docx_tramite_concesion_minera";

    var URL_GET_DOCX_FORMALIZACION = SNITHOST + "/TramitesDGM/get_docx_formalizacion";


    /**TRAMITES SETENA**/

    var URL_DATOS_NUEVO_PROYECTO_SETENA = SNITHOST + "/TramitesSETENA/datos_nuevo_proyecto";

    var URL_DATOS_FORMULARIO_D1_SETENA = SNITHOST + "/TramitesSETENA/datos_formularios_D1";

    var URL_DATOS_REGISTRO_CONSULTORES_SETENA = SNITHOST + "/TramitesSETENA/datos_registro_consultores";

    var URL_DATOS_FORMULARIO_D2_SETENA = SNITHOST + "/TramitesSETENA/datos_formularios_D2";

    var URL_DATOS_TRAMITES_EN_LINEA_SETENA = SNITHOST + "/TramitesSETENA/datos_tramites_en_linea";

    var URL_DATOS_NUEVO_PLAN_ORDENAMIENTO_TERRITORIAL_SETENA = SNITHOST + "/TramitesSETENA/datos_nuevo_plan_ordenamiento_territorial";

    var URL_FORM_UBICACION_PRELIMINAR_NUEVO_PROYECTO = SNITHOST + "/TramitesSETENA/form_ubicacion_preliminar_nuevo_proyecto";

    var URL_FORM_UBICACION_DETALLADA_FORMULARIO_D1_3 = SNITHOST + "/TramitesSETENA/form_ubicacion_detallada_formulario_D1";

    var URL_FORM_NUEVO_PROYECTO_SETENA = SNITHOST + "/TramitesSETENA/form_nuevo_proyecto";

    var URL_FORM_FORMULARIO_D1 = SNITHOST + "/TramitesSETENA/form_formulario_D1";

    var URL_FORM_FORMULARIO_D2 = SNITHOST + "/TramitesSETENA/form_formulario_D2";

    var URL_SELECCIONAR_MAPA_TRAMITES_EN_LINEA_SETENA = SNITHOST + "/TramitesSETENA/form_seleccionar_en_mapa_tramites_en_linea";

    var URL_TRAMITES_EN_LINEA_SETENA = SNITHOST + "/TramitesSETENA/form_tramites_en_linea";

    var URL_NUEVO_PLAN_ORDENAMIENTO_TERRITORIAL_SETENA = SNITHOST + "/TramitesSETENA/form_nuevo_plan_ordenamiento_territorial";

    var URL_ACTUALIZAR_PLANOS_CATASTRADOS_TRAMITES_EN_LINEA_SETENA = SNITHOST + "/TramitesSETENA/form_actualizar_planos_catastrados_mapa_tramites_en_linea";



    var URL_ALL_TOOLTIPS = SNITHOST + "/TramitesSETENA/get_tooltips";

    var CONSULTA_PROYECTOS_BANCO_IMAGENES = SNITHOST + "/BancoImagenes/consultas_proyectos";

    var CONSULTA_RADIO_BANCO_IMAGENES = SNITHOST + "/Visor/services/consultabancoimagenes";

    var URL_APLICAR_FILTROS_BANCO_IMAGENES = SNITHOST + "/Visor/aplicarFiltrosConsultaBancoImagenes";

    var URL_GET_DOCX_TRAMITES_EN_LINEA = SNITHOST + "/TramitesSETENA/get_docx_tramites_en_linea";

    var URL_GET_DOCX_NUEVO_PLAN_ORDENAMIENTO_TERRITORIAL = SNITHOST + "/TramitesSETENA/get_docx_nuevo_plan_ordenamiento_territorial";

    var URL_GET_DOCX_FORMULARIO_D1 = SNITHOST + "/TramitesSETENA/get_docx_formulario_D1";

    var URL_GET_DOCX_FORMULARIO_D2 = SNITHOST + "/TramitesSETENA/get_docx_formulario_D2";

    var URL_GET_ACTIVIDADES_FORMULARIO_D1 = SNITHOST + "/TramitesSETENA/get_actividades_formulario_d1";

    var URL_GET_DIVISION_ACTIVIDADES_FORMULARIO_D1 = SNITHOST + "/TramitesSETENA/get_divison_actividades_formulario_d1";

    var URL_REVISAR_ACCESO_GNSS = SNITHOST + "/revisar_acceso_gnss";

    var URL_SOLICITAR_ACCESO_GNSS = SNITHOST + "/GNSS/dar_acceso_caster";


    var URL_PERMISOS_CATALOGO_OBJETOS = SNITHOST + "/Tramites/obtener_permisos_catalogo_objetos"; //TODO MOVERLO A GESTIONCATALOGOOBJETOS
    var URL_DOCUMENTOS_NOMBRES_GEOGRAFICOS = SNITHOST  + '/documentos_nombres_geograficos'

    var URL_GET_DOCUMENTOS_NOMBRES_GEOGRAFICOS = SNITHOST  + '/get_documentos_nombres_geograficos'
    var URL_AGREGAR_DOCUMENTOS_NOMBRES_GEOGRAFICOS = SNITHOST + "/agregar_documento_nombres_geograficos";//"/DTAlegal_agregar2";
    var URL_GUARDAR_DOCUMENTOS_NOMBRES_GEOGRAFICOS = SNITHOST + "/guardar_documentos_nombre_geograficos";
    var URL_CONSULTAR_DOCUMENTOS_NOMBRES_GEOGRAFICOS   = SNITHOST + "/consultar_documentos_nombres_geograficos";
    /** METADATOS **/

    var INSTITUCIONES = [
        {'titulo' : 'RN-IGN', 'tooltip' : 'Registro Nacional'},
        {'titulo' : 'Academia e Investigación', 'tooltip' : 'Academia e Investigación'},
        {'titulo' : 'ARESEP', 'tooltip' : 'Autoridad Reguladora de los Servicios Públicos'},
        {'titulo' : 'AyA', 'tooltip' : 'Instituto Costarricense de Acueductos y Alcantarillados'},
        {'titulo' : 'Bomberos CR', 'tooltip' : 'Benemérito Cuerpo de Bomberos de Costa Rica'},
        {'titulo' : 'CNE', 'tooltip' : 'Comisión Nacional de Emergencias'},
        {'titulo' : 'CONAVI', 'tooltip' : 'Consejo Nacional de Vialidad'},
        {'titulo' : 'ICAFE', 'tooltip' : 'Instituto del Café de Costa Rica'},
        {'titulo' : 'ICE', 'tooltip' : 'Instituto Costarricense de Electricidad'},
        {'titulo' : 'ICT', 'tooltip' : 'Instituto Costarricense de Turismo'},
        {'titulo' : 'INEC', 'tooltip' : 'Instituto Nacional de Estadística y Censos'},
        {'titulo' : 'INVU', 'tooltip' : 'Instituto Nacional de Vivienda y Urbanismo'},
        {'titulo' : 'MAG', 'tooltip' : 'Magisterio de Agricultura y Ganadería'},
        //{'titulo' : 'MCJ', 'tooltip' : 'Ministerio de Cultura y Juventud'},
        {'titulo' : 'MEP', 'tooltip' : 'Ministerio de Educación Pública'},
        {'titulo' : 'MH-ONT', 'tooltip' : 'Ministerio de Hacienda - Órgano de Normalización Técnical'},
        {'titulo' : 'MINAE', 'tooltip' : 'Ministerio de Ambiente y Energía'},
        {'titulo' : 'MIVAH', 'tooltip' : 'Ministerio de Vivienda y Asentamientos Humanos'},
        {'titulo' : 'MOPT', 'tooltip' : 'Ministerio de Obras Públicas y Transportes'},
        {'titulo' : 'Municipalidades', 'tooltip' : 'Municipalidades'},
        {'titulo' : 'RECOPE', 'tooltip' : 'Refinadora Costarricense de Petróleo'},
        {'titulo' : 'SENARA', 'tooltip' : 'Servicio Nacional de Aguas Subterráneas Riego y Avenamiento'},
        {'titulo' : 'CNFL', 'tooltip' : 'Comisión Nacional de Fuerza y Luz'},
        {'titulo' : 'instituto_alcoholismo_farmacodependencia', 'tooltip' : 'Instituto sobre Alcoholismo y Farmacodependencia (IAFA)'},
        {'titulo' : 'simocute', 'tooltip' : 'Sistema Nacional de Monitoreo de la Cobertura y Uso de la Tierra y Ecosistemas'},
    ];


    thisObject.getMaxCsvSize= function (){
        return MAX_CSV_SIZE ;
    }

    thisObject.getVisorTabName = function (){
        return VISOR_TAB_NAME;
    }

    thisObject.getSnitHost = function (){
        return SNITHOST;
    }

    thisObject.getWSVisor = function (){
        return URL_WEBSOCKET_VISOR;
    }

    thisObject.getUrlPersonalWFS = function (){
        return PERSONAL_WFS_URL;
    }

    thisObject.getUrlPersonalWMS = function (){
        return PERSONAL_WMS_URL;
    }

    thisObject.getUrlTematicas = function (){
        return URL_TEMATICAS;
    }

    thisObject.getUrlOrtomapasInteres = function (){
        return URL_ORTOMAPAS_INTERES;
    }

    thisObject.getUrlCapasRecientes = function (){
        return URL_CAPAS_RECIENTES;
    }

    thisObject.getUrlCapasFundamentales = function (){
        return URL_CAPAS_FUNDAMENTALES;
    }

    thisObject.getUrlCapasPopulares = function (){
        return URL_CAPAS_POPULARES;
    }

    thisObject.getUrlConsumoDatos = function (){
        return URL_CONSUMO_DATOS;
    }

    thisObject.getUrlBusqueda = function (){
        return URL_BUSQUEDA;
    }

    thisObject.getUrlBusquedaCapas = function (){
        return URL_BUSQUEDA_CAPAS;
    }

    thisObject.getUrlDatosUsuario = function (){
        return URL_DATOS_USUARIO;
    }

    thisObject.getUrlDatosProfile = function (){
        return URL_DATOS_PROFILE;
    }

    thisObject.getUrlUsersPdfs = function (){
        return URL_USERS_PDFS;
    }


    thisObject.getUrlNoticias = function (){
        return URL_NOTICIAS;
    }

    thisObject.getUrlDetalleNoticias = function (){
        return URL_DETALLE_NOTICIAS;
    }

    thisObject.getUrlDatosNodo = function (){
        return URL_DATOS_NODO;
    }

    thisObject.getUrlAvisosDatosNodo = function (){
        return URL_AVISOS_DATOS_NODO;
    }

    thisObject.getUrlAgregarVisor = function (){
        return URL_AGREGAR_VISOR;
    }

    thisObject.getUrlDetalleCapa = function (){
        return URL_DETALLE_CAPA;
    }

    thisObject.getVisorDefaultUrl = function () {
        return URL_VISOR_DEFAULT;
    }

    thisObject.getUrlEliminarVisor = function (){
        return URL_ELIMINAR_VISOR;
    }

    thisObject.getUrlAgregarWFS = function (){
        return URL_AGREGAR_WFS;
    }

    thisObject.getUrlAgregarWMS = function (){
        return URL_AGREGAR_WMS;
    }

    thisObject.getUrlExploradorCapas = function (){
        return URL_EXPLORADOR_CAPAS;
    }

    thisObject.getUrlListaCapasExploradorCapas = function (){
        return URL_LISTA_CAPAS_EXPLORADOR;
    }

    thisObject.getUrlSugerenciaCapas = function (){
        return URL_SUGERENCIACAPAS;
    }

    thisObject.getUrlD3CapasExplorador = function (){
        return URL_D3_CAPAS_EXPLORADOR;
    }

    thisObject.getUrlD3Nodos = function (){
        return URL_D3_NODOS;
    }

    thisObject.getUrlAgregarCapasNodos = function (){
        return URL_GET_AGREGAR_CAPAS;
    }

    thisObject.getUrlPrevisualizarCapa = function (){
        return URL_PREVISUALIZAR_CAPA;
    }

    thisObject.getUrlDocumentosManuales = function (){
        return URL_DOCUMENTOS_MANUALES;
    }

    thisObject.getUrlListaTutorialesPresentaciones = function (){
        return URL_TUTORIALES_PRESENTACIONES;
    }

    thisObject.getUrlListaCharlas = function (){
        return URL_CHARLAS;
    }

    thisObject.getUrlListaGuias = function (){
        return URL_GUIAS;
    }


    thisObject.getUrlTramitesOtrasInstituciones = function (){
        return URL_TRAMITES_OTRAS_INSTITUCIONES;
    }

    thisObject.getUrlServiciosOGC = function (){
        return URL_SERVICIOS_OGC;
    }

    thisObject.getUrlDocumentosLegal = function (){
        return URL_DOCUMENTOS_LEGAL;
    };

    thisObject.getUrlDocumentosDecretos = function (){
        return URL_DOCUMENTOS_DECRETOS;
    };

    thisObject.getUrlInformesSemestrales = function (){
        return URL_INFORMES_SEMESTRALES;
    };

    thisObject.getUrlGeoportalLimitesDocumentos = function (){
        return URL_GEOPORTAL_LIMITES_DOCUMENTOS;
    };


    thisObject.getUrlAvisos = function (){
        return URL_AVISOS;
    };
    thisObject.getUrlPresentaciones = function (){
        return URL_PRESENTACIONES;
    };

    thisObject.getUrlUtilidades = function (){
        return URL_UTILIDADES;
    };

    thisObject.getUrlRepositorioDocumentos = function (){
        return URL_REPOSITORIO_DOCUMENTOS;
    };

    thisObject.getUrlConsultarDTALegal = function (){
        return URL_CONSULTAR_DTA_LEGAL;
    }

    thisObject.getUrlConsultarDTADocumentosGenerales = function (){
        return URL_CONSULTAR_DTA_DOCUMENTOS_GENERALES;
    }

    thisObject.getUrlConsultarNGLegal = function (){
        return URL_CONSULTAR_NG_LEGAL;
    }

    thisObject.getUrlGuardarDTALegal = function (){
        return URL_GUARDAR_DTA_LEGAL;
    }

    thisObject.getUrlGuardarNGLegal = function (){
        return URL_GUARDAR_NG_LEGAL;
    }

    thisObject.getUrlHomeUpload = function (){
        return URL_HOME_UPLOAD;
    }

    thisObject.getUrlHomeDownload = function (){
        return URL_HOME_DOWNLOAD;
    }

    thisObject.getUrlAgregarDTALegalDoc = function (){
        return URL_AGREGAR_DTA_LEGAL_DOC;
    };
    thisObject.getUrlAgregarDTALegalDoc2 = function (){
        return URL_AGREGAR_DTA_LEGAL_DOC2;
    };

    thisObject.getUrlAgregarNGLegalDoc = function (){
        return URL_AGREGAR_NG_LEGAL_DOC;
    }

    thisObject.getUrlBorrarDTALegalDoc = function (){
        return URL_BORRAR_DTA_LEGAL_DOC;
    }

    thisObject.getUrlBorrarNGLegalDoc = function (){
        return URL_BORRAR_NG_LEGAL_DOC;
    }

    thisObject.getUrlDTALegal = function (){
        return URL_DTA_LEGAL;
    }

    thisObject.getUrlDTALegal2 = function (){
        return URL_DTA_LEGAL2;
    };

    thisObject.getUrlNGLegal = function (){
        return URL_NG_LEGAL;
    }

    thisObject.getUrlAnios = function (){
        return URL_GET_ANIOS;
    }

    thisObject.getUrlVisorPointQuery = function ()
    {
        return URL_VISOR_POINT_QUERY;
    }

    thisObject.getUrlFullMetadata = function (){
        return URL_FULLMETADATA;
    }

    thisObject.getUrlXmlMetadata = function (){
        return URL_XML_CAPA_FULLMETADATOS_METADATA;
    }
    thisObject.getUrlDocxMetadata = function (){
        return URL_GETDOCXMETADATA;
    };
    thisObject.getUrlPdfMetadata = function (){
        return URL_GETPDFMETADATA;
    };

    thisObject.getUrlGuardarMetadata_V_101 = function (){
        return URL_GUARDARMETADATA_V_101;
    }

    thisObject.getUrlGuardarMetadata = function (){
        return URL_GUARDARMETADATA;
    }

    thisObject.getUrlEditarMetadata = function (){
        return URL_EDITARMETADATA;
    }

    thisObject.getUrlEditarMetadata2 = function (){
        return URL_EDITARMETADATA2;
    }

    thisObject.getUrlCrearMetadata = function (){
        return URL_CREARMETADATA;
    }

    thisObject.getUrlCrearMetadata2 = function (){
        return URL_CREARMETADATA2
    }

    thisObject.getUrlCopiarMetadata = function (){
        return URL_COPIARMETADATO;
    }

    thisObject.getUrlEliminarMetadata = function (){
        return URL_ELIMINARMETADATO;
    }



    thisObject.getUrlCambiarEstadoMetadata = function (){
        return URL_CAMBIARESTADOMETADATA;
    }



    thisObject.getUrlListadoMetadata = function (){
        return URL_LISTADOMETADATA;
    }


    thisObject.getUrlFormMetadata = function (){
        return URL_GETFORMMETADATA;
    }

    thisObject.getUrlFormMetadata_V_101 = function (){
        return URL_GETFORMMETADATA_V_101;
    }

    thisObject.getUrlFormMetadata_V_101_2 = function (){
        return URL_GETFORMMETADATA_V_101_2;
    }

    thisObject.getUrlTooltipsMetadata = function (){
        return URL_TOOLTIPS_METADATA;
    }

    thisObject.getUrlXmlCapaMetadata = function (){
        return URL_XML_CAPA_METADATOS_METADATA;
    }

    thisObject.getUrlXmlCapaFullMetadata = function (){
        return URL_XML_CAPA_FULLMETADATOS_METADATA;
    }
    thisObject.getUrlDocxCapaMetadata = function (){
        return URL_DOCX_CAPA_METADATOS_METADATA;
    }
    thisObject.getUrlPdfCapaMetadata = function (){
        return URL_PDF_CAPA_METADATOS_METADATA;
    }

    thisObject.getUrlAllMetadata = function (){
        return URL_ALLMETADATA;
    }

    thisObject.getUrlVerMetadata = function (){

        return URL_VERMETADATA;
    }

    thisObject.getUrlVerMetadata2 = function (){

        return URL_VERMETADATA2;
    }

    thisObject.getUrlVerMetadataPublico = function (){

        return URL_VERMETADATAPUBLICO;
    }

    thisObject.getUrlVerMetadataPublico2 = function (){

        return URL_VERMETADATAPUBLICO2;
    }

    thisObject.getUrlDisplayFullMetadata = function (){
        return URL_DISPLAYFULLMETADATA;
    }

    thisObject.getUrlDisplayFullMetadata2 = function (){
        return URL_DISPLAYFULLMETADATA2;
    }

    thisObject.getUrlUploadMetadata = function (){
        return URL_METADATOS_UPLOAD;
    }

    thisObject.getUrlDownloadMetadata = function (){
        return URL_METADATOS_DOWNLOAD;
    }

    thisObject.getUrlDescargarPlantillaXMLMetadatos = function (){
        return URL_METADATOS_DESCARGAR_PLANTILLA_XML_METADATOS;
    }

    thisObject.getCantidadTematicas = function (){
        return CANTIDAD_TEMATICAS;
    }

    thisObject.getCantidadTematicasMobile = function (){
        return CANTIDAD_TEMATICAS_MOBILE;
    }

    thisObject.getCantidadOrtomapasInteres = function (){
        return CANTIDAD_ORTOMAPAS_INTERES;
    }

    thisObject.getCantidadOrtomapasInteresMobile = function (){
        return CANTIDAD_ORTOMAPAS_INTERES_MOBILE;
    }

    thisObject.getCantidadCapasActualizadas = function (){
        return CANTIDAD_CAPAS_ACTUALIZADAS;
    }

    thisObject.getCantidadCapasActualizadasMobile = function (){
        return CANTIDAD_CAPAS_ACTUALIZADAS_MOBILE;
    }

    thisObject.getCantidadCapasFundamentales = function (){
        return CANTIDAD_CAPAS_FUNDAMENTALES;
    }

    thisObject.getCantidadCapasFundamentalesMobile = function (){
        return CANTIDAD_CAPAS_FUNDAMENTALES_MOBILE;
    }

    thisObject.getCantidadCapasPopulares = function (){
        return CANTIDAD_CAPAS_POPULARES;
    }

    thisObject.getCantidadNoticias = function (){
        return CANTIDAD_NOTICIAS;
    }

    thisObject.getCantidadTramitesOtrasInstituciones = function (){
        return CANTIDAD_TRAMITES_OTRAS_INSTITUCIONES;
    }

    thisObject.getCantidadTramitesOtrasInstitucionesMobile = function (){
        return CANTIDAD_TRAMITES_OTRAS_INSTITUCIONES_MOBILE;
    }

    thisObject.getUrlCapasNodo = function (){
        return URL_CAPAS_DE_NODO;
    }

    thisObject.getRevisarAccesoGNSS = function (){
        return URL_REVISAR_ACCESO_GNSS;
    }

    thisObject.solicitarAccesoGNSS = function (){
        return URL_SOLICITAR_ACCESO_GNSS;
    }


    thisObject.getUrlProyectos = function (){
        return URL_PROYECTOS;
    }

    thisObject.getUrlResultadosBusquedaNomenclator = function (){
        return URL_RESULTADOS_BUSQUEDA_NOMENCLATOR;
    }

    thisObject.setProyectoActual = function (proyecto){
        this.PROYECTO_ACTUAL = proyecto;
    }

    thisObject.getProyectoActual = function (){
        return PROYECTO_ACTUAL;
    }

    thisObject.getUrlMetadatosCapa = function (){
        return URL_METADATOS_CAPA;
    }

    thisObject.getUrlCambiarProyecto = function (){
        return URL_CAMBIAR_PROYECTO;
    }

    thisObject.getUrlBancoImagenes = function (){
        return URL_SERVICIOS_BANCOIMAGENES;
    };

    thisObject.getUrlGuardarProyecto = function (){
        return URL_GUARDAR_PROYECTO;
    }
    thisObject.getUrlRedGeodesica= function (){
        return URL_RED_GEODESICA;
    }
    thisObject.getUrlNombreGeografico= function (){
        return URL_NOMBRE_GEOGRAFICO;
    }
    thisObject.getUrlFileManager= function (){
        return URL_FILE_MANAGER;
    }
    thisObject.getUrlCatalogoMapaFotos1= function (){
        return URL_GET_CATALOGO_MAPA_FOTOS1;
    }
    thisObject.getUrlCatalogoMapaFotosTERRA= function (){
        return URL_GET_CATALOGO_MAPA_FOTOSTERRA;
    }
    thisObject.getUrlCatalogoMapaFotosCWA= function (){
        return URL_GET_CATALOGO_MAPA_FOTOSCWA;
    }
    thisObject.getUrlCatalogoMapaFotosJICA= function (){
        return URL_GET_CATALOGO_MAPA_FOTOSJICA;
    }
    thisObject.getUrlCatalogoMapaFotosINFORMACION= function (){
        return URL_GET_CATALOGO_MAPA_FOTOSINFORMATION;
    }
    thisObject.getUrlProyectosLista = function (){
        return URL_PROYECTOSLISTA;
    }
    thisObject.getUrlVisorUpload = function (){
        return URL_VISOR_UPLOAD;
    }
    thisObject.getUrlVisorPlantilla = function (){
        return URL_VISOR_PLANTILLAS;
    }
    thisObject.getUrlProyectosListaDetallada = function (){
        return URL_PROYECTOSLISTADETALLADA;
    }



    thisObject.getUrlEditarProyectos = function (){
        return URL_EDITARPROYECTOS;
    }

    thisObject.getUrlGetProyectosEdicion = function (){
        return URL_GETPROYECTOSEDICION;
    }

    thisObject.getUrlBaseGeop= function (){
        return URL_BASE_GEOP;
    }

    thisObject.getUrlCapaUsuario= function (){
        return URL_RECIBIR_CAPA_USUARIO;
    }

    thisObject.getUrlGetCapaUsuario= function (){
        return URL_CARGAR_CAPA_USUARIO;
    }

    thisObject.getMaxShapefileZipSize= function (){
        return MAX_SHAPEFILE_ZIP_SIZE;
    }

    thisObject.getMaxZipSize= function (){
        return MAX_ZIP_SIZE;
    }

    thisObject.getMaxPdfSize= function (){
        return MAX_PDF_SIZE;
    }
    thisObject.getMaxImagesSize= function (){
        return MAX_IMAGENES_SIZE;
    }

    thisObject.getMaxPlantillaDocSize= function (){
        return MAX_PLANTILLA_DOC_SIZE;
    }

    thisObject.getRadioRangoNombresGeograficos= function (){
        return RADIO_RANGO_NOMBRES_GEOGRAFICOS;
    }

    thisObject.getUrlBaseGeopMap= function (){
        return URL_BASE_GEOP_MAP;
    }

    thisObject.getUrlDatosProyecto = function (){
        return URL_DATOS_PROYECTO;
    }

    thisObject.getUrlCheckFiles = function (){
        return URL_CHECKFILES;
    }

    thisObject.getUrlBasePDFHojas = function (){
        return URL_PDF_HOJAS_BASE;
    }

    thisObject.getUrlBasePDFZIPFULL = function (){
        return URL_PDF_HOJAS_TIPOS_ZIPFULL;
    }

    thisObject.getUrlBasePDFZIPREC = function (){
        return URL_PDF_HOJAS_TIPOS_ZIPREC;
    }

    thisObject.getUrlBasePDFRARFULL = function (){
        return URL_PDF_HOJAS_TIPOS_RARFULL;
    }

    thisObject.getUrlBasePDFRARREC = function (){
        return URL_PDF_HOJAS_TIPOS_RARREC;
    }
    thisObject.getUrlBasePDFLimitesMaritimos= function (){
        return URL_PDF_LIMITES_MARITIMOS;
    }
    thisObject.getUrlBaseBancosNivel = function (){
        return URL_BANCOSNIVEL;
    }

    thisObject.getUrlContProyecto= function (){
        return URL_CONT_PROYECTO;
    }

    thisObject.getUrlProyecto = function (){
        return URL_PROYECTOACTUAL;
    }

    thisObject.getUrlVisorVerFile = function (){
        return URL_VISOR_VERFILE;
    }

    thisObject.getUrlEliminarCapa = function (){
        return URL_ELIMINAR_CAPA;
    }

    thisObject.getUrlCapasAdministrarWFS = function (){
        return URL_CAPAS_ADMINISTRAR_WFS;
    }

    thisObject.getUrlCapasAdministrarWMS = function (){
        return URL_CAPAS_ADMINISTRAR_WMS;
    }

    thisObject.getUrlEliminarCapaEnServidorWFS = function (){
        return URL_ELIMINAR_CAPA_EN_SERVIDOR_WFS;
    }

    thisObject.getUrlEliminarCapaEnServidorWMS = function (){
        return URL_ELIMINAR_CAPA_EN_SERVIDOR_WMS;
    }

    thisObject.getUrlTipoUsuario = function (){
        return URL_TIPO_USUARIO;
    }

    thisObject.getUrlTemasInteres = function (){
        return URL_TEMAS_INTERES;
    }

    thisObject.getUrlInstitucionUsuario = function (){
        return URL_INSTITUCION_USUARIO;
    }

    thisObject.getUrlActualizarUsuario = function (){
        return URL_ACTUALIZAR_USUARIO;
    }

    thisObject.getUrlCambiarClaveUsuario = function (){
        return URL_CAMBIAR_CLAVE_USUARIO;
    }

    thisObject.getUrlRegistrarUsuario = function (){
        return URL_REGISTRAR_USUARIO;
    }

    thisObject.getUrlNoticiasRelevantes = function (){
        return URL_NOTICIAS_RELEVANTES;
    }

    thisObject.getCantidadNoticiasRelevantes = function (){
        return CANTIDAD_NOTICIAS_RELEVANTES;
    }

    thisObject.getUrlLogin = function (){
        return URL_LOGIN;
    }

    thisObject.getUrlLogOut = function (){
        return URL_LOGOUT;
    }

    thisObject.getUrlLogged = function (){
        return URL_LOGGED;
    }

    thisObject.getUrlRegistrationPaso1 = function (){
        return URL_USUARIO_REGISTRATION_PASO1;
    }

    thisObject.getUrlRegistrationPaso2 = function (){
        return URL_USUARIO_REGISTRATION_PASO2;
    }

    thisObject.getUrlCambiarPass = function (){
        return URL_USUARIO_CAMBIAR_PASS;
    }

    thisObject.getUrlActualizarPass = function (){
        return URL_USUARIO_ACTUALIZAR_PASS;
    }

    thisObject.getUrlForgot = function (){
        return URL_USUARIO_FORGOT;
    }

    thisObject.getNodosSnit = function (){
        return URL_GET_NODOS_SNIT;
    }

    thisObject.getUrlFormReproyeccionAvanzada = function (){
        return FORM_REPROYECCION_AVANZADA;
    }

    thisObject.getUrlFormReproyeccionAvanzada2 = function (){
        return FORM_REPROYECCION_AVANZADA2;
    }

    thisObject.getUrlReproyeccionAvanzada = function (){
        return REPROYECCION_AVANZADA;
    }


    thisObject.getUrlHomeCsvs = function (){
        return URL_HOME_CSVS;
    }

    thisObject.getUrlFormRegistroPaso1 = function (){
        return URL_GET_FORM_REGISTRO_PASO1;
    }

    thisObject.getUrlUserActualizarProyecto = function (){
        return URL_GETUSERACTUALIZARPROYECTO;
    }
    thisObject.getUrlUserBorrarProyecto = function (){
        return URL_GETUSERBORRARPROYECTO;
    }
    thisObject.getUrlUserCompartirProyecto = function (){
        return URL_GETUSERCOMPARTIRPROYECTO;
    }

    thisObject.getUrlUserCompartirProyectoAceptar = function (){
        return URL_GETUSERCOMPARTIRPROYECTOACEPTAR;
    };
    thisObject.getUrlUserCompartirProyectoNegar = function (){
        return URL_GETUSERCOMPARTIRPROYECTONEGAR;
    };

    thisObject.getUrlUserPasswordRecover = function ()
    {
        return URL_PASSWORD_RECOVER;
    }

    thisObject.getUrlUserChangePassword = function ()
    {
        return URL_USER_CHANGE_PASSWORD;
    }

    thisObject.getUrlUserCompartidosByProjectKey = function ()
    {
        return URL_GET_COMPARTIDOS_BY_PROJECT_KEY;
    }

    thisObject.getUrlUserProyectoEditarCompartidos = function ()
    {
        return URL_EDITARPROYECTOUSUARIOSCOMPARTIDOS;
    }

    thisObject.getUrlConsultasRPNHome = function ()
    {
        return URL_CONSULTAS_RPN;
    }

    thisObject.getUrlConsultasFODESAF = function ()
    {
        return URL_CONSULTAS_FODESAF;
    }

    thisObject.getUrlConsultasCCSS = function ()
    {
        return URL_CONSULTAS_CCSS;
    }

    thisObject.getUrlConsultasColegioAbogados = function ()
    {
        return URL_CONSULTAS_COLEGIO_ABOGADOS;
    }

    thisObject.getUrlNoticiasDownload = function ()
    {
        return URL_NOTICIAS_DOWNLOAD;
    }
    thisObject.getUrlNoticiasUpload = function ()
    {
        return URL_NOTICIAS_UPLOAD;
    }
    thisObject.getUrlGuardarNoticia = function ()
    {
        return URL_GUARDAR_NOTICIAS;
    }

    thisObject.getUrlGetNoticias = function ()
    {
        return URL_GET_NOTICIAS;
    }
    thisObject.getUrlBorrarNoticia = function ()
    {
        return URL_GET_BORRAR_NOTICIAS;
    }

    thisObject.getUrlEditarNoticia = function ()
    {
        return URL_GET_EDITAR_NOTICIAS;
    }

    thisObject.getUrlBanner = function ()
    {
        return URL_BANNER;
    }

    thisObject.getUrlNoticiasBanner = function ()
    {
        return URL_NOTICIAS_BANNER;
    }

    thisObject.getUrlFormularioCoordenadasXY = function()
    {
        return URL_FORMULARIO_COORDENADAS_XY;
    }


    /** TRAMITES DGM **/

    thisObject.getUrlConsultasRPN = function ()
    {
        return URL_CONSULTAS_RPN_DGM;
    }

    thisObject.getUrlConsultasFODESAF = function ()
    {
        return URL_CONSULTAS_FODESAF_DGM;
    }

    thisObject.getUrlConsultasCCSS = function ()
    {
        return URL_CONSULTAS_CCSS_DGM;
    }


    thisObject.getUrlDatosPrueba = function ()
    {
        return URL_DATOS_PRUEBA;
    }

    thisObject.getUrlDatosConcesionMinera = function ()
    {
        return URL_DATOS_TRAMITE_CONCESION_MINERA;
    }

    thisObject.getUrlDatosPrueba2 = function ()
    {
        return URL_DATOS_PRUEBA_2;
    }

    thisObject.getUrlGetFormHashes = function ()
    {
        return URL_GET_FORM_HASHES;
    }

    thisObject.getUrlDatosConcesionMineraCNE = function ()
    {
        return URL_DATOS_TRAMITE_CONCESION_MINERA_CNE;
    }
    thisObject.getUrlDatosConcesionMineraEstado = function ()
    {
        return URL_DATOS_TRAMITE_CONCESION_MINERA_ESTADO;
    }

    thisObject.getUrlDatosConcesionMineraAutonomas = function ()
    {
        return URL_DATOS_TRAMITE_CONCESION_MINERA_AUTONOMAS;
    }
    thisObject.getUrlDatosConcesionMineraPrivado = function ()
    {
        return URL_DATOS_TRAMITE_CONCESION_MINERA_PRIVADO;
    }
    thisObject.getUrlDatosConcesionMineraArtesanal = function ()
    {
        return URL_DATOS_TRAMITE_CONCESION_MINERA_ARTESANAL;
    }
    thisObject.getUrlDatosConcesionMineraMunicipalidad = function ()
    {
        return URL_DATOS_TRAMITE_CONCESION_MINERA_MUNICIPALIDAD;
    }

    thisObject.getUrlDatosTramitesEnLinea = function ()
    {
        return URL_DATOS_TRAMITES_EN_LINEA_DGM;
    }

    thisObject.getUrlDatosFormalizacionTramitesDGM = function ()
    {
        return URL_DATOS_FORMALIZACION_TRAMITES_DGM;
    }

    thisObject.getUrlDatosFormalizacionCNETramitesDGM = function ()
    {
        return URL_DATOS_FORMALIZACION_CNE_TRAMITES_DGM;
    }

    thisObject.getUrlDatosFormalizacionEstadoTramitesDGM = function ()
    {
        return URL_DATOS_FORMALIZACION_ESTADO_TRAMITES_DGM;
    }
    thisObject.getUrlDatosFormalizacionMunicipalidadTramitesDGM = function ()
    {
        return URL_DATOS_FORMALIZACION_MUNICIPALIDAD_TRAMITES_DGM;
    }

    thisObject.getUrlDatosFormalizacionAutonomasTramitesDGM = function ()
    {
        return URL_DATOS_FORMALIZACION_AUTONOMAS_TRAMITES_DGM;
    }

    thisObject.getUrlFormConcesionMinera = function ()
    {
        return URL_FORM_TRAMITE_CONCESION_MINERA;
    }

    thisObject.getUrlFormConcesionMineraCNE = function ()
    {
        return URL_FORM_TRAMITE_CONCESION_MINERA_CNE;
    }

    thisObject.getUrlFormFormalizacion = function ()
    {
        return URL_FORM_FORMALIZACION;
    }

    thisObject.getUrlFormFormalizacionEstado = function ()
    {
        return URL_FORM_FORMALIZACION_ESTADO;
    }
    thisObject.getUrlFormFormalizacionMunicipalidad = function ()
    {
        return URL_FORM_FORMALIZACION_MUNICIPALIDAD;
    }
    thisObject.getUrlFormFormalizacionAutonomas = function ()
    {
        return URL_FORM_FORMALIZACION_AUTONOMAS;
    }

    thisObject.getUrlFormInformacionGeoespacialConcesionMinera = function ()
    {
        return URL_FORM_INFORMACION_GEOESPACIAL_CONCESION_MINERA;
    }

    thisObject.getUrlFormInformacionGeoespacialConcesionMineraCNE = function ()
    {
        return URL_FORM_INFORMACION_GEOESPACIAL_CONCESION_MINERA_CNE;
    }
    thisObject.getUrlFormInformacionGeoespacialConcesionMineraPrivado = function ()
    {
        return URL_FORM_INFORMACION_GEOESPACIAL_CONCESION_MINERA_PRIVADO;
    }
    thisObject.getUrlFormInformacionGeoespacialConcesionMineraMunicipalidad = function ()
    {
        return URL_FORM_INFORMACION_GEOESPACIAL_CONCESION_MINERA_MUNICIPALIDAD;
    }
    thisObject.getUrlFormInformacionGeoespacialConcesionMineraEstado = function ()
    {
        return URL_FORM_INFORMACION_GEOESPACIAL_CONCESION_MINERA_ESTADO;
    }
    thisObject.getUrlFormInformacionGeoespacialConcesionMineraArtesanal = function ()
    {
        return URL_FORM_INFORMACION_GEOESPACIAL_CONCESION_MINERA_ARTESANAL;
    }
    thisObject.getUrlFormInformacionGeoespacialConcesionMineraAutonomas = function ()
    {
        return URL_FORM_INFORMACION_GEOESPACIAL_CONCESION_MINERA_AUTONOMAS;
    }

    thisObject.getUrlFormResultadoTramiteConcesionMinera = function ()
    {
        return URL_FORM_RESULTADO_TRAMITE_CONCESION_MINERA;
    }

    thisObject.getUrlFormTramiteConcesionMineraMunicipalidad = function ()
    {
        return URL_FORM_TRAMITE_CONCESION_MINERA_MUNICIPALIDAD;
    }
    thisObject.getUrlFormTramiteConcesionMineraCNE = function ()
    {
        return URL_FORM_TRAMITE_CONCESION_MINERA_CNE;
    }
    thisObject.getUrlFormTramiteConcesionMineraAutonomas = function ()
    {
        return URL_FORM_TRAMITE_CONCESION_MINERA_AUTONOMAS;
    }
    thisObject.getUrlFormTramiteConcesionMineraEstado = function ()
    {
        return URL_FORM_TRAMITE_CONCESION_MINERA_ESTADO;
    }

    thisObject.getUrlFormPuntosFormalizacion = function ()
    {
        return URL_FORM_PUNTOS_FORMALIZACION;
    }

    thisObject.getUrlFormPuntosFormalizacionMunicipalidad = function ()
    {
        return URL_FORM_PUNTOS_FORMALIZACION_MUNICIPALIDAD;
    }

    thisObject.getUrlFormPuntosFormalizacionAutonomas = function ()
    {
        return URL_FORM_PUNTOS_FORMALIZACION_AUTONOMAS;
    }

    thisObject.getUrlFormPuntosFormalizacionEstado = function ()
    {
        return URL_FORM_PUNTOS_FORMALIZACION_ESTADO;
    }

    thisObject.getUrlMisTramitesDGM = function ()
    {
        return URL_MIS_TRAMITES_DGM;
    }

    thisObject.getUrlMisTramitesSNIT = function ()
    {
        return URL_MIS_TRAMITES_IGN;
    }



    thisObject.getUrlFormTramitesEnLineaDGM = function ()
    {
        return URL_FORMN_TRAMITES_EN_LINEA_DGM;
    }

    thisObject.getUrlFormSeleccionarMapaTramitesEnLineaDGM = function ()
    {
        return URL_FORM_SELECCIONAR_MAPA_TRAMITES_EN_LINEA_DGM;
    }

    thisObject.getUrlFormGetDocxTramiteConcesionMineraDGM = function ()
    {
        return URL_GET_DOCX_TRAMITE_CONCESION_MINERA;
    }

    thisObject.getUrlFormGetDocxFormalizacionDGM = function ()
    {
        return URL_GET_DOCX_FORMALIZACION;
    }

    /**SETENA**/


    thisObject.getUrlDatosNuevoProyectoSetena = function ()
    {
        return URL_DATOS_NUEVO_PROYECTO_SETENA;
    }

    thisObject.getUrlDatosFormularioD1Setena = function ()
    {
        return URL_DATOS_FORMULARIO_D1_SETENA;
    }

    thisObject.getUrlDatosRegistroConsultoresSetena = function ()
    {
        return URL_DATOS_REGISTRO_CONSULTORES_SETENA;
    }

    thisObject.getUrlDatosFormularioD2Setena = function ()
    {
        return URL_DATOS_FORMULARIO_D2_SETENA;
    }

    thisObject.getUrlDatosTramitesEnLineaSetena = function ()
    {
        return URL_DATOS_TRAMITES_EN_LINEA_SETENA;
    }

    thisObject.getUrlDatosNuevoPlanOrdenamientoTerritorialSetena = function ()
    {
        return URL_DATOS_NUEVO_PLAN_ORDENAMIENTO_TERRITORIAL_SETENA;
    }

    thisObject.getUrlConsultasCCSSSETENA = function ()
    {
        return URL_CONSULTAS_CCSS_SETENA;
    }

    thisObject.getUrlConsultasRPNSETENA = function ()
    {
        return URL_CONSULTAS_RPN_SETENA;
    }

    thisObject.getUrlFormUbicacionPreliminarNuevoProyecto = function ()
    {
        return URL_FORM_UBICACION_PRELIMINAR_NUEVO_PROYECTO;
    }

    thisObject.getUrlFormUbicacionDetalladaFormularioD1_3 = function ()
    {
        return URL_FORM_UBICACION_DETALLADA_FORMULARIO_D1_3;
    }

    thisObject.getUrlFormNuevoProyectoSETENA = function ()
    {
        return URL_FORM_NUEVO_PROYECTO_SETENA;
    }

    thisObject.getUrlFormFormularioD1SETENA = function ()
    {
        return URL_FORM_FORMULARIO_D1;
    }
    thisObject.getUrlFormFormularioD2SETENA = function ()
    {
        return URL_FORM_FORMULARIO_D2;
    }

    thisObject.getUrlSelecionarMapaTramitesEnLineaSETENA = function ()
    {
        return URL_SELECCIONAR_MAPA_TRAMITES_EN_LINEA_SETENA;
    }

    thisObject.getUrlFormTramitesEnLineaSETENA = function ()
    {
        return URL_TRAMITES_EN_LINEA_SETENA;
    }

    thisObject.getUrlFormPlanOrdenamientoTerritorialSETENA = function ()
    {
        return URL_NUEVO_PLAN_ORDENAMIENTO_TERRITORIAL_SETENA;
    }

    thisObject.getUrlActualizarPlanosCatastradosTramitesEnLineaSETENA = function ()
    {
        return URL_ACTUALIZAR_PLANOS_CATASTRADOS_TRAMITES_EN_LINEA_SETENA;
    }

    thisObject.getUrlGetDocxTramitesEnLlineaSETENA = function ()
    {
        return URL_GET_DOCX_TRAMITES_EN_LINEA;
    }

    thisObject.getUrlGetDocxNuevoPlanOrdenamientoTerritorialSETENA = function ()
    {
        return URL_GET_DOCX_NUEVO_PLAN_ORDENAMIENTO_TERRITORIAL;
    }

    thisObject.getUrlGetDocxFormularioD1SETENA = function ()
    {
        return URL_GET_DOCX_FORMULARIO_D1;
    }

    thisObject.getUrlGetDocxFormularioD2SETENA = function ()
    {
        return URL_GET_DOCX_FORMULARIO_D2;
    }

    thisObject.getUrlGetActividadesFormularioD1SETENA = function ()
    {
        return URL_GET_ACTIVIDADES_FORMULARIO_D1;
    }

    thisObject.getUrlGetDivisionActividadesFormularioD1SETENA = function ()
    {
        return URL_GET_DIVISION_ACTIVIDADES_FORMULARIO_D1;
    }



    thisObject.getUrlVisorPointQuery = function ()
    {
        return URL_VISOR_POINT_QUERY;
    }


    thisObject.getUrlGetTooltips = function ()
    {
        return URL_ALL_TOOLTIPS;
    }

    thisObject.getUrlConsultaProyectosBancoImagenes = function ()
    {
        return CONSULTA_PROYECTOS_BANCO_IMAGENES;
    }

    thisObject.getUrlConsultaBancoImagenesPorRadio = function ()
    {
        return CONSULTA_RADIO_BANCO_IMAGENES;
    }

    thisObject.getUrlAplicarFiltrosBancoImagenes = function ()
    {
        return URL_APLICAR_FILTROS_BANCO_IMAGENES;
    }

    thisObject.getIntituciones = function ()
    {
        return INSTITUCIONES;
    }

    thisObject.getUrlBibliotecaDTA = function ()
    {
        return URL_BIBLIOTECA_DTA;
    }

    thisObject.getUrlSolicitudesModificacionCatalogoObjetos = function (){
        return URL_PERMISOS_CATALOGO_OBJETOS;
    }

    thisObject.getDocumentosNombresGeograficos = function (){
        return URL_GET_DOCUMENTOS_NOMBRES_GEOGRAFICOS;
    }
    thisObject.getUrlAgregarDocumentoNombresGeograficos = function (){
        return URL_AGREGAR_DOCUMENTOS_NOMBRES_GEOGRAFICOS;
    };

    thisObject.getUrGuardarDocumentosNombresGeograficos = function (){
        return URL_GUARDAR_DOCUMENTOS_NOMBRES_GEOGRAFICOS;
    }
    thisObject.getUrlDocumentosNombresGeograficos = function ()
    {
        return URL_DOCUMENTOS_NOMBRES_GEOGRAFICOS;
    }

    thisObject.getUrlConsultarDocumentosNombresGeograficos = function ()
    {
        return URL_CONSULTAR_DOCUMENTOS_NOMBRES_GEOGRAFICOS;
    }

    return thisObject;
})();
