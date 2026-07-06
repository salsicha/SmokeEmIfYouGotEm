/*
 * Copyright (c) 2016. Addax Software Development, S.A.
 */



var objectMap = {};
var urlWFS = "";
var nombreTabla = "";
let table;
var total_capas_ocultas = 0;
function show_info(title, html){
    var titulo = "Atributos para la capa " + title;
    nombreTabla = title;
    $('#modalResumenTramite').modal()

    /*
    $("#tituloAtributo").text(titulo);
    $("#modal").iziModal('setTitle',title);



    $('#modalContent').html(html);


    var modalPrincipal = $("#modal-container").clone().removeAttr('id');
    $("#modal .iziModal-content").html(modalPrincipal);
    $('#modal').iziModal('setFullscreen', true);
    $('#modal').iziModal('setHeader', false)
    $('#modal').iziModal('open');
*/
}

function exportarAtributos() {

    table.download("xlsx", nombreTabla+".xlsx");
/*
    var tableName =
    TableToExcel.convert(document.getElementById("tablaresultados-busqueda-html"), {
        name: nombreTabla + `.xlsx`,
        sheet: {
            name: 'Sheet 1'
        }
    });*/
}



function abrirTablaAtributos(typeName, title){
    $('#attr.modal').show();
    $('#atributos').html('');

    $('#loadingIndicator').css('display', 'flex');

    let format = 'csv';
    var url,data,separator,utf8_encode;
    var descarga_interna =false;

    if(typeof capas_descarga_interna[typeName] !== 'undefined' && typeof capas_descarga_interna[typeName][format] !== 'undefined'){ // DESCARGA DE CARPETA DE ADDAX
        var datos_descarga = capas_descarga_interna[typeName];

        var document_name;
        var base_path =  datos_descarga['base_path'];

        if(typeof datos_descarga[format] === 'string'){
            document_name =datos_descarga[format];
        } if(typeof datos_descarga[format] === 'object'){
            var datos_descarga_formato = datos_descarga[format];
            document_name =datos_descarga_formato['documento'];
            separator =datos_descarga_formato['separator'];
            utf8_encode = datos_descarga_formato['utf8_encode'];
        }


        descarga_interna = true;

         url = '/descarga_contenido_geoservicios';
         data = {
             base_path: base_path,
             document_name: document_name,
             separator : "",
             utf8_encode: ''
         };

         if(typeof separator ==='string'){
             data['separator']= separator;
         }
        if(typeof utf8_encode ==='string'){
            data['utf8_encode']= utf8_encode;
        }
    }else{
         url = '/get_atributos_capas';
         data = {"typeName": typeName, "baseUrl": urlWFS.replace(/\?$/, '')};
    }

    if(descarga_interna){
        console.log('descarga nueva');
    }else{
        console.log('descarga antigua');

    }
    console.log('url',url)
    console.log('data',data)

    $.ajax({
        type: "get",
        dataType: "json",
        url: url,
        data: data
    }).done(function(data) {
        $('#loadingIndicator').hide();
        console.log("Data: " + JSON.stringify(data));


        if (data.resultado) {

            var html = crearTabla(data.data,descarga_interna);
            show_info(title, html);
        }
    }).fail(function() {
        $('#loadingIndicator').hide();
        alert('Error loading data.');
    });
}




function crearTabla(listaResultados,descarga_interna){

    var columnas = listaResultados.columns;
    var resultados = listaResultados.features;

    console.log('columnas',columnas)
    console.log('resultados',resultados)
   // return 0;
    var headers = '';
    var tabulator_columnas =  [];

    var lista_columnas;
    if(descarga_interna){
        lista_columnas = columnas;
    }else {
        lista_columnas = Object.keys(columnas)
    }
    lista_columnas.forEach(key =>{
        if(key != 'SHAPE') {
            headers += `<th>${key}</th>`;
            tabulator_columnas.push(  {title:key, field:key, formatter:"textarea", headerFilter:"input", headerFilterPlaceholder:"Digite para filtrar"})
        }
    });
 /*//20-06-2024  ANDRES GOMEZ: esta forma de crear tablas es muy inefiente para la pagina, se va a usar tabulator.
    var filas = "";
    for(var i in resultados){
        var filaactual = "<tr class='f-"+i+"'>";

        for(var valor in resultados[i]){
            filaactual += `<td class="title" style="margin-left: 2px">${resultados[i][valor]}</td>`;
        }

        filaactual +="</tr>";
        filas += filaactual;
    }

    var thead = '<thead> <tr>  '+headers+'</tr> </thead>' ;
    var tbody = '<tbody> '+filas+' </tbody>' ;
    var htmlfinal = "<table id='tablaresultados-busqueda-html'>" +thead+tbody+ "</table>";
*/



    $('#tablaResultadoTabulator').show();
     table = new Tabulator("#tablaResultadoTabulator", {
        initialSort:[
        ],
        height:"auto",
        width : "auto",
        data: resultados, //assign data to table
        layout:"fitColumns", //fit columns to width of table (optional)
        pagination:"local",
        paginationSize:15,
        movableColumns:true,
        paginationSizeSelector:true,
        columns:tabulator_columnas,

    });


     return '';
  //  return htmlfinal;
}


function abrirMetadato(key){
    var obj = objectMap[key];

    window.open(CONFIG.getUrlDisplayFullMetadata2() +  "?k=" + (obj.id), '_blank');

}

function agregarVisor(key){
    var obj = objectMap[key];
    //window.open("/Visor/indexver2?k=" + (obj.id), '_blank');
    AgregarAbrirVisor(obj.id, true);
}

function previsualizarCapa(key) {
    var obj = objectMap[key];
    window.open(obj.url, '_blank');
}



function KMLNoDisponible(typeName){ // 28/04/2026 esto es temporal ya que estas capas dio problemas al generar el kml

    let capas_kml_no_disponble = [
"curvas_5000_2017",
"RE_120102",
"forestal2017_5k",
"pastos2017_5k",
"vias_5000",
    ]

  return   capas_kml_no_disponble.includes(typeName)


}

function descargarCapas(typeName, modelos ){
    console.log('typeName',typeName)
    if(modelos){
     //   showLoader();
        let downloadUrl = ''
        if(typeName === "IGN_MDE_2017"){
        //    window.location.href = "https://files.snitcr.go.cr/modelos/MDE_5k.zip";

            const params = new URLSearchParams({
                base_path: 'DOCUMENTOS_DESCARGA_GEOSERVICIOS__MODELOS',
                document_name: 'MDE_5k.zip',
                download_name : 'MDE_5k.zip',
                format: 'zip'
            });

            downloadUrl = `/descarga_documentos_geoservicios?${params.toString()}`;
        }else{
            const params = new URLSearchParams({
                base_path: 'DOCUMENTOS_DESCARGA_GEOSERVICIOS__MODELOS',
                document_name: 'Modelo_Sombras.zip',
                download_name : 'Modelo_Sombras.zip',
                format: 'zip'
            });

            downloadUrl = `/descarga_documentos_geoservicios?${params.toString()}`;
         //   window.location.href = "https://files.snitcr.go.cr/modelos/Modelo_Sombras.zip";
        }

        window.location.href =downloadUrl
        return;
    }

    let kml_no_disponible = KMLNoDisponible(typeName);
    let option_kml =  kml_no_disponible ? "": "<option value=\"kml\">KML</option>" ;
    swal({
        title: "Descarga",
        text: "Escoge el formato de descarga:",
        icon: "info",
        content: {
            element: "select",
            attributes: {
                innerHTML: `
                <option value="json">GeoJSON</option>
                <option value="shape-zip">Shapefile</option>
                <option value="excel">Excel</option>
                ${option_kml}
            `,
            },
        },
        buttons: ["Cancelar", "Descargar"],
    }).then((value) => {
        if (value) {

            const format = document.querySelector(".swal-content__select").value;
            descargarNodos(urlWFS, typeName, format);
        }
    });

}


function showLoader() {
    document.getElementById('loadingIndicator').style.display = 'flex';
}

function hideLoader() {
    document.getElementById('loadingIndicator').style.display = 'none';
}


const capas_descarga_interna =
    {
        'curvas_5000_2017': {
            "base_path" : "DOCUMENTOS_DESCARGA_GEOSERVICIOS__CURVAS_5K_2017",
            "xlsx": "Curvas_5K_2017.xlsx",
            "json" :"Curvas 5K_2017.geojson",
            "zip" : "Curvas_5K_2017.zip",
            "csv" : "Curvas_5K_2017.csv",
            "download_name" : ''
        },
        "caucedrenaje_25k":{
            "base_path" : "DOCUMENTOS_DESCARGA_GEOSERVICIOS__Capas_SNIT",
            "xlsx": "caucedrenaje_25k.xlsx",
            "kml":"caucedrenaje_25k.kml"
        },
        "RE_120101":{
            "base_path" : "DOCUMENTOS_DESCARGA_GEOSERVICIOS__Capas_SNIT",
            "xlsx": "RE_120101.xlsx",
            'csv': 'RE_120101.csv',
            "kml":"RE_120101.kml"
        },
        "RE_120102":{
            "base_path" : "DOCUMENTOS_DESCARGA_GEOSERVICIOS__Capas_SNIT",
            "xlsx": "RE_120102.xlsx",
            "csv" : "RE_120102.csv"
        },
        "ec140101_25k":{
            "base_path" : "DOCUMENTOS_DESCARGA_GEOSERVICIOS__Capas_SNIT",
            "xlsx": "ec140101_25k.xlsx",
            "csv": "ec140101_25k.csv",
            "kml":"ec140101_25k.kml"

        },
        "transporteterrestre_25k":{
            "base_path" : "DOCUMENTOS_DESCARGA_GEOSERVICIOS__Capas_SNIT",
            "xlsx": "transporteterrestre_25k.xlsx",
            "kml":"transporteterrestre_25k.kml"
        },

        "forestal2017_5k":{
            "base_path" : "DOCUMENTOS_DESCARGA_GEOSERVICIOS__Capas_SNIT",
            "xlsx": "IGN_5forestal2017_5k.xlsx",
            "json" :  {
                "documento":"forestal2017_5k.zip", // para un caso especial en el que el documento original pesa mucho lo comprimimos
                "formato" : "zip"
            },
            "zip" : "IGN_5forestal2017_5k.zip",
            "csv" : "IGN_5forestal2017_5k.csv"
        },
        "cultivos2017_5k":{
            "base_path" : "DOCUMENTOS_DESCARGA_GEOSERVICIOS__Capas_SNIT",
            "xlsx": "cultivos2017_5k.xlsx",
            "json" : {
                "documento":"cultivos2017_5kgeojson.zip", // para un caso especial en el que el documento original pesa mucho lo comprimimos
                "formato" : "zip"
            },
            "zip" : "cultivos2017_5k.zip",
            "csv" : "cultivos2017_5k.csv",
            "kml": "cultivos2017_5k.kml"

        },
        "edificaciones2017_5k":{
            "base_path" : "DOCUMENTOS_DESCARGA_GEOSERVICIOS__Capas_SNIT",
            "xlsx": "IGN_5edificaciones2017_5k.xlsx",
            "kml":"edificaciones2017_5k.kml"
        },
        "hidrografia_5000":{
            "base_path" : "DOCUMENTOS_DESCARGA_GEOSERVICIOS__Capas_SNIT",
            "xlsx": "hidrografia_5000.xlsx",
            "kml":"hidrografia_5000.kml"
        },
        "pastos2017_5k":{
            "base_path" : "DOCUMENTOS_DESCARGA_GEOSERVICIOS__Capas_SNIT",
            "xlsx": "IGN_5pastos2017_5k.xlsx",
            "json":{
                "documento":"IGN_5pastos2017_5kgeojson.zip", // para un caso especial en el que el documento original pesa mucho lo comprimimos
                "formato" : "zip"
            },
            "zip" : "IGN_5pastos2017_5k.zip",
            "csv" : "IGN_5pastos2017_5k.csv"

        },
        "urbano_5000" :{
            "base_path" : "DOCUMENTOS_DESCARGA_GEOSERVICIOS__Capas_SNIT",
            "csv" :{
                "documento":"urbano_5000.csv", // para un caso especial en el que el documento original pesa mucho lo comprimimos
                'separator' : ',',
                'utf8_encode': "true"

            },
            "kml":"urbano_5000.kml"

        },
        "vias_5000":{
            "base_path" : "DOCUMENTOS_DESCARGA_GEOSERVICIOS__Capas_SNIT",
            "xlsx": "IGN_5vias_5000.xlsx",
            "csv" : {
                "documento":"IGN_5vias_5000.csv", // para un caso especial en el que el documento original pesa mucho lo comprimimos
                'separator' : ',',
                'utf8_encode': "true"

            }
        }


};
async function descargarNodos(wfsBaseUrl, featureTypeName, format) {


    if (format == 'excel') {
        format = 'xlsx';
    } else if (format == 'shape-zip') {
        format = 'zip';

    }

    let  downloadUrl;
    let descargaModoNuevo = false;
    if(typeof capas_descarga_interna[featureTypeName] !== 'undefined' && typeof capas_descarga_interna[featureTypeName][format] !== 'undefined'){ // DESCARGA DE CARPETA DE ADDAX

        //todo, esta config deberia guardarse junto a la config de la capa


        console.log('descarga nueva')
        let datos_descarga = capas_descarga_interna[featureTypeName];
        let base_path =  datos_descarga['base_path'];
        let document_name;

        if(typeof datos_descarga[format] === 'string'){
            document_name =datos_descarga[format];
        } if(typeof datos_descarga[format] === 'object'){
            document_name =datos_descarga[format]['documento'];
            format = datos_descarga[format]['formato'];
        }


        let download_name = ''

        if(datos_descarga['download_name']){
             download_name =datos_descarga['download_name'];
        }else{
            download_name =document_name.split(".").slice(0, -1).join(".");
        }

        const params = new URLSearchParams({
            base_path: base_path,
            document_name: document_name,
            download_name : download_name,
            format: format
        });



         downloadUrl = `/descarga_documentos_geoservicios?${params.toString()}`;
        descargaModoNuevo = true;

    /*    if(format === 'kml'){
            swal('Descarga de datos', 'Por el momento esta capa no cuenta con la descarga de KML disponible, intentelo más tarde', 'error');
            console.log(downloadUrl)
            return
        }*/
    }else { // DESCARGA NORMAL
        console.log('descarga antigua')

        const params = new URLSearchParams({
            typeName: featureTypeName,
            baseUrl: wfsBaseUrl.replace(/\?$/, ''),
            format: format
        });
         downloadUrl = `/obtener_datos_nodo?${params.toString()}`;

    }
    console.log('downloadUrl',downloadUrl)

    console.log('inicio icono descarga')
    showLoader();

    if (format === 'zip' && !descargaModoNuevo) {
        $.get(downloadUrl, {}, function(response){
            if(response.success){
                hideLoader();

                iframe = document.createElement("iframe");
                iframe.style.display = "none";
                iframe.src = `/descargar_shp_generadonodo?res=${response.res}`;
                registrarDescarga(iframe.src, true,featureTypeName);

                iframe.onload = () => {
                    // If it loads, download started
                    setTimeout(() => iframe.remove(), 2000);
              //      registrarDescarga(iframe.src, true,featureTypeName);  // 20/03/2026 esto esta dando un erro de las politicas del navegador, ver con julio
                };

                iframe.onerror = () => {
                    iframe.remove();
              //      registrarDescarga(iframe.src, false,featureTypeName);   // 20/03/2026 esto esta dando un erro de las politicas del navegador, ver con julio
                };

                document.body.appendChild(iframe);

            } else {
                hideLoader();
                swal('Descarga de datos', 'No se pudo generar correctamente la descarga del zip de shapefiles.', 'error');
                registrarDescarga(downloadUrl, false,featureTypeName);
            }
        }, 'json');
    } else {
        try {
         //   hideLoader();

            iframe = document.createElement("iframe");
            iframe.style.display = "none";
            iframe.src = downloadUrl;
            registrarDescarga(downloadUrl,featureTypeName, true);
            // 20/03/2026 esto esta dando un erro de las politicas del navegador, ver con julio
/*
            iframe.onload = () => {
                setTimeout(() => iframe.remove(), 2000);
                registrarDescarga(downloadUrl,featureTypeName, true);
            };

            iframe.onerror = () => {
                iframe.remove();
                registrarDescarga(downloadUrl, false,featureTypeName);
            };

            document.body.appendChild(iframe);
            */
            // Si además quieres usar fetch para validar:
            const response = await fetch(downloadUrl);
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }

            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = url;
            a.download = `${featureTypeName}.${format}`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);

            registrarDescarga(downloadUrl, true,featureTypeName);

        } catch (error) {
            console.error('There was a problem with the fetch operation:', error);
            registrarDescarga(downloadUrl, false,featureTypeName,error);
        } finally {
            hideLoader();
        }
    }

}
function registrarDescarga(endpoint, exito,featureTypeName, error = '') {
    const payload = {
        url_descarga: endpoint,
        descarga_exitosa: exito,
        error:error,
        capa:featureTypeName


    };

    $.ajax({
        url: '/guardar_registro_descarga_capa',
        type:"post",
        dataType:"json",
        data: payload,
        success: function (response) {
            console.log('Registro guardado correctamente:', response);
        },
        error: function (xhr, status, err) {
            console.error('Error registrando la descarga:', err);
        }
    });
}






function dispatchFunction(funcName, key) {
    const functionMap = {
        abrirTablaAtributos: abrirTablaAtributos,
        descargarCapas: descargarCapas,
        abrirMetadato: abrirMetadato,
        agregarVisor: agregarVisor,
        previsualizarCapa: previsualizarCapa
    };

    if (functionMap[funcName]) {
        functionMap[funcName](key);
    } else {
        console.error("Function not found:", funcName);
    }
}

function getInstitucion(institucion){
    var institucionActual = "";
    switch (institucion){
        case "Dirección de Agua, MINAE":
            institucionActual = "DA";
            break;
        case "IGN":
            institucionActual = "IGN";
            break;
        case "Instituto Nacional de Vivienda":
        case "Instituto Nacional de Vivienda y Urbanismo y el Programa de las Naciones Unidas para Costa Rica":
        case "INVU-Urbanismo":
            institucionActual = "INVU";
            break;
        case "Ministerio de Educación Pública (MEP)":
            institucionActual = "MEP";
            break;
        case "Sistema Nacional de Áreas de Conservación":
            institucionActual = "SINAC";
            break;
        case "Servicio Nacional de Aguas Subterráneas, Riego y Avenamiento - ESTACIONES METEOROLÓGICAS":
        case "Servicio Nacional de Aguas Subterráneas, Riego y Avenamiento - RECARGA":
        case "Servicio Nacional de Aguas Subterráneas, Riego y Avenamiento - VULNERABILIDAD":
            institucionActual = "SENARA";
            break;
        case "Benemérito Cuerpo de Bomberos de Costa Rica":
            institucionActual = "BOMBEROS_CR";
            break;
        case "Instituto Costarricense de Turismo":
            institucionActual = "ICT";
            break;
        case "Instituto Costarricense de Electricidad (ICE)":
            institucionActual = "ICE";
            break;
        case "MOPT - Secretaría de Planificación Sectorial":
            institucionActual = "MOPT";
            break;
        case "Municipalidad de Barva":
            institucionActual = "MUNIBARVA";

            break;
        case "Consejo de Transporte Público":
            institucionActual = "CTP";
            break;
        case "Consejo de Seguridad Vial (COSEVI)":
            institucionActual = 'COSEVI'
            break

        case "Municipalidad de Escazú":
            institucionActual = 'MUNIESCAZU'
            break

        case "Registro Inmobiliario":
            institucionActual = 'REGISTRO_INMOBILIARIO'
            break


        case "Tribunal Supremo de Elecciones (TSE)":
            institucionActual = 'TSE'
            break

        case "Instituto Nacional de Estadística y Censos (INEC)":
            institucionActual = 'INEC'
            break

        case "Municipalidad de Liberia":
            institucionActual = 'MUNILIBERIA'
            break
        default:
            institucionActual = "";
    }
    return institucionActual;
}







function esCapaOCulta(nombre_capa){

    console.log('revisando si es capa oculta:',nombre_capa)
    //13/01/2026
    //todo esto es temporal hay que preguntarle a julio como quitarlos de la consulta
    const capoasOcultas = [
        "Y2FwYTo6UFZUWkgrJUUyJTgwJTkzK1pvbmFzK0hvbW9nJUMzJUE5bmVhcytPTlQ6OkNhcGFfWm9uYXNfaG9tb2dlbmVhcyUzQVpvbmFzX2hvbW9nJUMzJUE5bmVhcw==", //Zonas_homogéneas son del nodo Zonas Homogéneas ONT
        "Y2FwYTo6UFZUWkgrJUUyJTgwJTkzK1pvbmFzK0hvbW9nJUMzJUE5bmVhcytPTlQ6OkNhcGFfWm9uYXNfaG9tb2dlbmVhcyUzQUxvdGV0aXBvX3pvbmFzX2hvbW9nJUMzJUE5bmVhcw==", // Lotetipo_zonas_homogéneas son del nodo Zonas Homogéneas ONT
        "Y2FwYTo6UFZBKyVFMiU4MCU5Mytab25hcytBZ3JvcGVjdWFyaWFzK09OVDo6Q2FwYV9ab25hc19hZ3JvcGVjdWFyaWFzJTNBWm9uYXNfYWdyb3BlY3Vhcmlhcw==", //Zonas_agropecuarias
        "Y2FwYTo6UFZBKyVFMiU4MCU5Mytab25hcytBZ3JvcGVjdWFyaWFzK09OVDo6Q2FwYV9ab25hc19hZ3JvcGVjdWFyaWFzJTNBTG90ZXRpcG9fQWdyb3BlY3Vhcmlv" //Lotetipo_Agropecuario
    ];
    if (capoasOcultas.includes(nombre_capa)) {
        total_capas_ocultas +=1;
        console.log('es capa oculta:',nombre_capa)

        return true
    } else {
        return  false
    }
}


function cargarCapas(){


    const icons = [
        { title: "Atributos", imagePath: "/gimgs/buscar.png" },
        { title: "Descargar capa", imagePath: "/gimgs/descarga.png" },
        { title: "Abrir metadato", imagePath: "/gimgs/documento.png" },
        { title: "Agregar visor", imagePath:"/gimgs/mas.png" },
        { title: "Previsualizar", imagePath: "/gimgs/ojo.png" }
    ];

    $('#examplewms').remove();
    var param = getParameterByNameNoLowerCase("k");

    var dataString = { nk: param };
    var url = CONFIG.getUrlCapasNodo();
    console.log('urllllll',url)
    $.ajax({
        type:"post", dataType:"json", url:url, data:dataString, async: false
    }).done(function(data) {
        console.log("Datos: " + JSON.stringify(data.data));
        if(data.resultado != false && data.data.length>0){
            var arr = data.data;
            var institucion = getInstitucion(arr[0]['institucion']);

            console.log(institucion);
            var htmltabla = '<table id="examplewms" class="table table-striped">';
            htmltabla +=    '<thead class="text-center"><tr id="titulo_tabla" style="margin-bottom: 2%;">';
            htmltabla +=    '<td colspan="5">Directorio de Capas</td>';
            htmltabla +=    '</tr>';
            htmltabla +=    '<tr><td>Título de la Capa</td>';
            if(institucion === "IGN"){
                htmltabla +=    '<td>Nombre de la Capa</td>';
            }

            htmltabla +=    '<td>Descripción</td>';
            htmltabla +=    '<td>Capa Oficial</td>';
            htmltabla +=    '<td>Acciones</td>';
            htmltabla +=    '</tr></thead><tbody>';


            var dataString = { institucion: institucion };


            var url = "../get_capas_oficiales";

            console.log('institucion consultada":',dataString)
            $.ajax({
                type:"post", dataType:"json", url:url, data:dataString
            }).done(function(data) {

                var capasOficiales = data.data;


                console.log("capasOficiales",capasOficiales)
                var htmldocumentos = '';
                for(var i=0; i<arr.length; i++) {


                    var obj = arr[i];
                    if(!esCapaOCulta(obj.id)) {


                        var key = "obj_" + i;
                        objectMap[key] = obj;

                        var oficial = false;
                        let botones_activos = false;
                        if (capasOficiales != null) {
                            console.log("capasOficiales", capasOficiales)
                            //   oficial = capasOficiales.some(element => element.nombre_nodo === obj.layer);

                            for (let capasIndice = 0; capasIndice < capasOficiales.length; capasIndice++) {
                                let element = capasOficiales[capasIndice];
                                console.log("element.nombre_nodo ", element.nombre_nodo);
                                console.log("obj.layer ", obj.layer);
                                if (element.nombre_nodo === obj.layer || element.nombre === obj.layer) {
                                    console.log("element ", element);
                                    oficial = true;
                                    if (element.botones_activos) {
                                        botones_activos = element.botones_activos;
                                    }
                                }
                            }

                        }


                        var esOficial = oficial ? "SÍ" : "NO";
                        var abstracto = obj.Abstract == null || obj.Abstract === "" ? "No tiene" : obj.Abstract;
                        var htmldocumento = '<tr><td class="text-left nombre_capa" title ="' + obj.nombre + '" >' + obj.nombre + '</td>';
                        if (institucion === "IGN") {
                            htmldocumento += '<td class="text-center nombre_de_capa">' + obj.layer + '</td>';
                        }

                        if (abstracto == "No tiene") {
                            htmldocumento += '<td class="text-center descripcion_capa">' + abstracto + '</td>';
                        } else {
                            htmldocumento += '<td class="text-justify descripcion_capa">' + abstracto + '</td>';
                        }

                        htmldocumento += '<td class="text-center oficial_capa">' + esOficial + '</td>';
                        htmldocumento += '<td class="text-center">';
                        htmldocumento += '<div class="row row-actions-buttons" >';
                        var modelos = false;
                        //Este es un caso especial donde es requerido poder descargar el WMTS para la capa de Modelos.
                        if (obj.id === "Y2FwYTo6TW9kZWxvczo6SUdOX01ERV8yMDE3" || obj.id === "Y2FwYTo6TW9kZWxvczo6SUdOX01PREVMT19TT01CUkFTXzIwMTc=") {
                            modelos = true;
                        }

                        var counter = 0;
                        /*  if(!oficial || modelos){
                              if(obj.wfs && institucion === "IGN" || modelos){
                                  counter = 0;
                              }else{
                                  counter = 2;
                              }
                          }*/

                        if (!modelos && (!obj.wfs || institucion !== "IGN")) {
                            counter = 2;
                        } else {
                            if (modelos) {
                                counter = 1;
                            }
                        }
                        if (obj.id === "Y2FwYTo6SUdOKzElM0E1bWlsK0NPOjpjdXJ2YXNfNTAwMF8yMDE3") {
                            counter = 0;
                        }

                        for (counter; counter < 5; counter++) {
                            var src = icons[counter].imagePath;
                            var title = icons[counter].title;
                            var layer = obj.layer;
                            var nombre = obj.nombre;
                            var funcName = ['abrirTablaAtributos', 'descargarCapas', 'abrirMetadato', 'agregarVisor', 'previsualizarCapa'][counter];

                            let mostrar_boton = false;

                            //TODO 07/06/2024 es un pequelo parche para hacerlo mas bonito, toca hacer un refactor para que esto del counter no sea tan ambiguo

                            console.log(botones_activos, 'botones activos')
                            if (typeof botones_activos !== "object" || typeof botones_activos === "object" && botones_activos.includes(counter)) {
                                mostrar_boton = true;
                            }
                            if (mostrar_boton) {
                                if (counter === 1) {
                                    htmldocumento += '<div class="col-1"><div class="actions-buttons" onclick="descargarCapas(\'' + layer + '\', ' + (modelos ? 'true' : 'false') + ')" ><img src="' + src + '" title="' + title + '"></div></div>';
                                } else if (counter === 0) {
                                    htmldocumento += '<div class="col-1"><div class="actions-buttons" onclick="abrirTablaAtributos(\'' + layer + '\', \'' + nombre + '\')" ><img src="' + src + '" title="' + title + '"></div></div>';
                                } else {
                                    htmldocumento += '<div class="col-1"><div class="actions-buttons" onclick="dispatchFunction(\'' + funcName + '\', \'' + key + '\')" data-key="' + key + '"><img src="' + src + '" title="' + title + '"></div></div>';
                                }
                            }


                        }

                        htmldocumento += '</div></td></tr>';
                        htmldocumentos += htmldocumento;
                    }
                }

                htmltabla += htmldocumentos + '</tbody></table>';
                $('#contenedorTabla').append(htmltabla);
                if(institucion === "IGN"){
                $('#examplewms').DataTable({
                    "dom": 'frtp',
                    "info": false,
                    "width": "100%",
                    "pageLength": 10,
                    "columns": [
                        { "width": "20%" },
                        { "width": "15%" },
                        { "width": "35%" },
                        { "width": "5%" },
                        { "width": "25%" }
                    ],
                    "language": {
                        "sProcessing":     "Procesando...",
                        "sLengthMenu":     "Mostrar _MENU_ registros",
                        "sZeroRecords":    "No se encontraron resultados",
                        "sEmptyTable":     "Ningún dato disponible en esta tabla",
                        "sInfo":           "Mostrando registros del _START_ al _END_ de un total de _TOTAL_ registros",
                        "sInfoEmpty":      "Mostrando registros del 0 al 0 de un total de 0 registros",
                        "sInfoFiltered":   "(filtrado de un total de _MAX_ registros)",
                        "sInfoPostFix":    "",
                        "sSearch":         "<span class='search-icon'><img src='gimgs/icono_buscar_gris.png'></span>",
                        "searchPlaceholder": "Búsqueda en directorio de capas",
                        "sUrl":            "",
                        "sInfoThousands":  ",",
                        "sLoadingRecords": "Cargando...",
                        "oPaginate": {
                            "sFirst":    "Primero",
                            "sLast":     "Último",
                            "sNext":     "siguiente",
                            "sPrevious": "anterior"
                        },
                        "oAria": {
                            "sSortAscending":  ": Activar para ordenar la columna de manera ascendente",
                            "sSortDescending": ": Activar para ordenar la columna de manera descendente"
                        }
                    }
                });}else{
                    $('#examplewms').DataTable({
                        "dom": 'frtp',
                        "info": false,
                        "width": "100%",
                        "pageLength": 10,
                        "columns": [
                            { "width": "25%" },
                            { "width": "40%" },
                            { "width": "5%" },
                            { "width": "30%" }
                        ],
                        "language": {
                            "sProcessing":     "Procesando...",
                            "sLengthMenu":     "Mostrar _MENU_ registros",
                            "sZeroRecords":    "No se encontraron resultados",
                            "sEmptyTable":     "Ningún dato disponible en esta tabla",
                            "sInfo":           "Mostrando registros del _START_ al _END_ de un total de _TOTAL_ registros",
                            "sInfoEmpty":      "Mostrando registros del 0 al 0 de un total de 0 registros",
                            "sInfoFiltered":   "(filtrado de un total de _MAX_ registros)",
                            "sInfoPostFix":    "",
                            "sSearch":         "<span class='search-icon'><img src='gimgs/icono_buscar_gris.png'></span>",
                            "searchPlaceholder": "Búsqueda en directorio de capas",
                            "sUrl":            "",
                            "sInfoThousands":  ",",
                            "sLoadingRecords": "Cargando...",
                            "oPaginate": {
                                "sFirst":    "Primero",
                                "sLast":     "Último",
                                "sNext":     "siguiente",
                                "sPrevious": "anterior"
                            },
                            "oAria": {
                                "sSortAscending":  ": Activar para ordenar la columna de manera ascendente",
                                "sSortDescending": ": Activar para ordenar la columna de manera descendente"
                            }
                        }
                    });
                }
            });
        }
    });
}

function cargarDatosTablawms() {// se encarga de hacer el llamado a la funcion que devuelve la informacion de las capas recientes en un json

    var param = getParameterByNameNoLowerCase("k");


    var dataString = {
        nk: param
    };
    var url = CONFIG.getUrlCapasNodo();
    $.ajax({
        type:"post", dataType:"json", url:url, data:dataString
    }).done(function( data ) {

        var fullmetadata_url = "/Metadatos/full_metadata2"; //CONFIG.getUrlDisplayFullMetadata();

        if(data.resultado != false){
            var arr = data.data;
            var htmltabla;
            htmltabla  = '<table id="examplewms" class="table table-striped">';
            htmltabla +=   '<thead class="text-center">';

            htmltabla +=     '<tr id="titulo_tabla" style="margin-bottom: 2%;">';
            htmltabla +=       '<td colspan="4">Directorio de Capas</td>';
            htmltabla +=     '</tr>';

            htmltabla +=     '<tr>';
            htmltabla +=       '<td>Título de la Capa</td>';
            htmltabla +=       '<td>Descripción</td>';
            htmltabla +=       '<td>Metadatos</td>';
            htmltabla +=       '<td>Previsualización</td>';
            htmltabla +=     '</tr>';
            htmltabla +=   '</thead>';
            htmltabla +=   '<tbody>';

            var htmldocumentos = '';
            for(var i=0;i<arr.length;i++){
                var obj = arr[i];
                var metadatos;
                var abstracto;
                var htmldocumento;

                if(obj.TieneMetadatos==false){
                    metadatos="NO";
                }else{
                    metadatos=`<a href="${fullmetadata_url}?k=${obj.id}" target="_blank">SÍ</a>`;
                }
                if(obj.Abstract==null)
                {
                    abstracto="No tiene";
                }
                else
                {
                    abstracto = obj.Abstract;
                }
                htmldocumento = '<tr>';
                htmldocumento += '<td class="text-left nombre_capa" title ="'+ obj.nombre+'" >' + obj.nombre + '</td>';
                htmldocumento += '<td class="text-justify">' + abstracto + '</td>';
                htmldocumento += '<td class="text-center">' + metadatos + '</td>';
                htmldocumento += '<td class="text-center"><a href="' + obj.url + '" target="_blank"> Ver en Web </a></td>';
                htmldocumento += '</tr>';
                htmldocumentos += htmldocumento;

            }

            htmltabla +=     htmldocumentos;
            htmltabla +=   '</tbody>';
            htmltabla += '</table>';

            $('#contenedorTabla').append(htmltabla);

            $('#examplewms').DataTable( {
                "dom": 'frtp',
                "info": false,
                "width": "100%",
                "pageLength": 10,
                "columns": [
                    { "width": "25%" },
                    { "width": "45%" },
                    { "width": "10%" },
                    { "width": "20%" }
                ],
                "language": {
                    "sProcessing":     "Procesando...",
                    "sLengthMenu":     "Mostrar _MENU_ registros",
                    "sZeroRecords":    "No se encontraron resultados",
                    "sEmptyTable":     "Ningún dato disponible en esta tabla",
                    "sInfo":           "Mostrando registros del _START_ al _END_ de un total de _TOTAL_ registros",
                    "sInfoEmpty":      "Mostrando registros del 0 al 0 de un total de 0 registros",
                    "sInfoFiltered":   "(filtrado de un total de _MAX_ registros)",
                    "sInfoPostFix":    "",
                    "sSearch":         "<span class='search-icon'><img src='gimgs/icono_buscar_gris.png'></span>",
                    "searchPlaceholder": "Búsqueda en directorio de capas",
                    "sUrl":            "",
                    "sInfoThousands":  ",",
                    "sLoadingRecords": "Cargando...",
                    "oPaginate": {
                        "sFirst":    "Primero",
                        "sLast":     "Último",
                        "sNext":     "siguiente",
                        "sPrevious": "anterior"
                    },
                    "oAria": {
                        "sSortAscending":  ": Activar para ordenar la columna de manera ascendente",
                        "sSortDescending": ": Activar para ordenar la columna de manera descendente"
                    }
                }
            } );
        }
    });
}

function setTitulo()
{
    var nombre = getParameterByNameNoLowerCase("nombre");

    $("#nombre_nodo").text(nombre);
}

function cargar_detalle_nodo()
{
    var param = getParameterByNameNoLowerCase("k");


    var dataString = {
        nk: param
    };
    var url = CONFIG.getUrlDatosNodo();

    $.ajax(
        {type: "post", url:url, dataType:"json", data:dataString}
    ).done(function(data){

            if(data.resultado)
            {

                var data = data.data;
                var datos = "";
                var descripcion = "Sin descripción";

                if(data.descripcion  && data.descripcion != "")
                {
                    descripcion = data.descripcion;
                }

                datos = "<strong>Descripción: </strong>"+descripcion+"";

                let nodeName =  getParameterByNameNoLowerCase("nombre")
                let dataString = {nodeName:nodeName};
                $.ajax({
                    type:"post", dataType:"json", url:CONFIG.getUrlAvisosDatosNodo(), data:dataString, async:false
                }).done(function( data ) {
                    let textoAviso = data.resultado? data.data : "";
                    if(nodeName === 'IGN Cartografía 1:5mil CO'){ //caso especial, quieren que sea punto y seguido...
                        datos += `${textoAviso}<br><br>`;

                    }else{
                        datos += `<p> ${textoAviso}</p><br><br>`;

                    }
                });
                $("#detalle_nodo").html(datos);
                cargarDatosDelNodo(data);

                datos = "";

                if(data.url_wfs != "" && data['public_url_wfs'] != null)
                {
                    urlWFS = data.public_url_wfs;
                    datos += "<div class='input-group mb-4'><input class ='form-control' value = '"+ data.public_url_wfs+"' id='url-wfs' ><div class='input-group-append'><button class='clipboard-btn btn btn-outline-secondary' data-clipboard-target='#url-wfs' id='url-wfs-btn'>Copiar WFS</button></div></div>";
                }

                if(data.url_wms != "" && data['public_url_wms'] != null)
                {
                    datos += "<div class='input-group mb-4'><input class ='form-control' value = '"+data.public_url_wms+"' id='url-wms'><div class='input-group-append'><button class='clipboard-btn btn btn-outline-secondary' data-clipboard-target='#url-wms' data-original-title ='Copiar' id='url-wms-btn'>Copiar WMS</button></div></div>";
                }
                if(data.url_wmts != "" && data['public_url_wmts'] != null)
                {
                    datos += "<div class='input-group mb-4'><input class = 'form-control' value = '"+data.public_url_wmts+"' id='url-wmts'><div class='input-group-append'><span class='input-group-button'><button class='clipboard-btn btn btn-outline-secondary' data-clipboard-target='#url-wmts' data-original-title ='Copiar' id='url-wmts-btn'>Copiar WMTS</button></span></div></div>";
                }

                if(data.public_url_rest != "" && data.public_url_rest != null ){
                    let rest =data.public_url_rest
                    datos+=   "<div class='input-group mb-4'><input class = 'form-control' value = '"+rest+"' id='url-wmts'><div class='input-group-append'><span class='input-group-button'><button class='clipboard-btn btn btn-outline-secondary' data-clipboard-target='#url-wmts' data-original-title ='Copiar' id='url-wmts-btn'>Copiar REST</button></span></div></div>";

                }
             //   datos += agregarCampoRest(nombre)

                let nombre =getParameterByNameNoLowerCase("nombre");

              /*  let rest = 'https://services8.arcgis.com/cB2sgNg281ELTjnP/arcgis/rest/services/Nodo_Puntarenas_vista/FeatureServer';
                if(nombre === 'Municipalidad de Puntarenas')
                {
                    datos += "<div class='input-group mb-4'><input class = 'form-control' value = '"+rest+"' id='url-wmts'><div class='input-group-append'><span class='input-group-button'><button class='clipboard-btn btn btn-outline-secondary' data-clipboard-target='#url-wmts' data-original-title ='Copiar' id='url-wmts-btn'>Copiar REST</button></span></div></div>";
                }
                */




                $("#url_nodo").html(datos);

            }
        }

    );

}

//22/04/2026 esto es algo temporal, si ya se añande muchos hay que ponerlos en el nodo populator como campo nuevo
function agregarCampoRest(nombre){

    let htmi = '' ;
    let listaNodosConREST = {
        'Municipalidad de Puntarenas' : {"rest":'https://services8.arcgis.com/cB2sgNg281ELTjnP/arcgis/rest/services/Nodo_Puntarenas_vista/FeatureServer'},
        'ICAFE' : {"rest":'https://services5.arcgis.com/LF48CxpifRE4aglv/arcgis/rest/services/Cobertura_Cafe_Costa_Rica_vista/FeatureServer'}

    };


    if(listaNodosConREST[nombre]){
        let rest = listaNodosConREST[nombre]['rest'];
        htmi =   "<div class='input-group mb-4'><input class = 'form-control' value = '"+rest+"' id='url-wmts'><div class='input-group-append'><span class='input-group-button'><button class='clipboard-btn btn btn-outline-secondary' data-clipboard-target='#url-wmts' data-original-title ='Copiar' id='url-wmts-btn'>Copiar REST</button></span></div></div>";

    }

return htmi;

}


function cargarDatosDelNodo(datos){
    console.log(datos);
    console.log(datos.institucion);
    $("#nombre_nodo").text(datos.title);
    $('#nombreEncargado').text(datos['nombre_encargado']);

    console.log("Total capas ocultas:",total_capas_ocultas);

    $('#capasPublicadas').text(parseInt(datos['capas_publicadas'])-total_capas_ocultas);
    $('#correoDatos').text(datos['correo_encargado']);
    $('#cantidadMetadatos').text(datos['capas_con_metadatos']);
    $('#telefonoDatos').text(datos['telefono_encargado']);

    if(datos['url_sitio'] != ""){
        $('#sitioWebDatos').text(datos['url_sitio']);
        $('#sitioWebDatos').attr('href', datos['url_sitio']);
    }else{
        $('#datosSitio').hide();
    }


   if(datos['url_visor_principal'] != ""){
        $('#visorExternoDatos').text(datos['url_visor_principal']);
       $('#visorExternoDatos').attr('href', datos['url_visor_principal']);
    }else{
        $('#datosExterno').hide();

    }


}




function setTooltip(message, object) {
    object = object + "-btn";
    $(object).tooltip('hide')
        .attr('data-original-title', message)
        .tooltip('show');
}

function hideTooltip(object) {
    object = object+"-btn";
    setTimeout(function() {
        $(object).tooltip('hide'); $(object).removeAttr("data-original-title");
    }, 1000);
}



function iniciarClipboard() {

    var clipboard = new Clipboard('.clipboard-btn');
    clipboard.on('success', function (e) {
            var target = e.trigger.getAttribute("data-clipboard-target");

            setTooltip("Copiado", target);
            hideTooltip(target);

        }

    );

    setTooltip("Copiar", '.clipboard-btn');
}

function IniciarPagina()
{
    mostrarMensajeInformativo('Se le recomienda a la persona usuaria consultar el metadato, para que su búsqueda sea más asertiva.',false)

    iniciarClipboard();

    //initBusquedaBox();

    //var isMobile = isMobileUser();

    //cargarCapasPopulares(CONFIG.getCantidadCapasPopulares());
    //cargarNoticias(CONFIG.getCantidadNoticias());

    //initBotonesGeneralesCapas();

    $(function () {
        $('[data-toggle="tooltip"]').tooltip()
    });

    //cargarDatosUsuario();

    //adjustToOrientation();

    $("#botonIngresar").click(function(){
        $(".contenedor-formulario-ingresar-usuario").show();
    });

    //cargarDatosTablawms();
    cargarCapas();
    //setTitulo();

    cargar_detalle_nodo();

    scroll();
    //readEnterLogin();

    //efectoNoticias();

}








function mostrarMensajeInformativo(mensaje, error)
{
    $('.__notify_msg').remove(); //Se borran todas las notificaciones

    if(error)
    {
        $.notify.error(mensaje, 10);
    }
    else
    {
        $.notify.success(mensaje, 10);
    }
}


function scroll(x) {

    $('a[href="#cap"]').bind('click', function (event) {
        event.preventDefault();
        $.smoothScroll({
            scrollElement: $('body'),
            scrollTarget: '#c'+x
        });
    });
}

$( document ).ready(function() {

    try{
        $('#elementos').hide();
      //  $('#tablaResultadoTabulator').hide();


        $('#modal').iziModal({
            top: 0,
            bodyOverflow: true,
        });
    }catch (error){

    }



    IniciarPagina();

});
