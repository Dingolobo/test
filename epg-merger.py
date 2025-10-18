import requests
import xml.etree.ElementTree as ET
from xml.dom import minidom
import os
import json
from datetime import datetime

# Array de URLs de ejemplo (reemplaza con tus URLs reales)
EPG_URLS = [
    'https://raw.githubusercontent.com/matthuisman/i.mjh.nz/refs/heads/master/Plex/mx.xml',
    'https://raw.githubusercontent.com/luisms123/tdt/master/guiacanales.xml',
    'https://raw.githubusercontent.com/acidjesuz/EPGTalk/master/guide.xml',
    'https://raw.githubusercontent.com/Dingolobo/test/refs/heads/main/mvshub.xml',
    'https://raw.githubusercontent.com/Dingolobo/test/refs/heads/main/dish.xml',
    'https://raw.githubusercontent.com/Dingolobo/test/refs/heads/main/openepg.xml'
]

# Diccionario de filtros: clave = URL, valor = lista de IDs de canales permitidos.
# Si una URL no está en este diccionario, NO se aplica filtrado (se incluyen todos los canales y programas).
# Para agregar un filtro nuevo:
# 1. Agrega la URL como clave en este diccionario.
# 2. Proporciona una lista de IDs de canales que quieres mantener (solo esos canales y sus programas se incluirán).
#    - Obtén los IDs inspeccionando el XML de esa URL (busca <channel id="...">).
#    - Ejemplo: Si quieres filtrar solo canales con IDs específicos, lista solo esos.
#    - Si la lista está vacía [], se incluirán todos (equivalente a no filtrar).
# Filtros actuales:
FILTERS = {
    # Filtro para mx.xml: solo estos IDs
    'https://raw.githubusercontent.com/matthuisman/i.mjh.nz/refs/heads/master/Plex/mx.xml': [
        "608049aefa2b8ae93c2c3a63-688d3402a6fe30698ab42007", #ITV deportes
        "608049aefa2b8ae93c2c3a63-63f0ca427b78030ed9990309", #Curiosity
        "608049aefa2b8ae93c2c3a63-66633339ebeb02ee8bd1597c"  #fifa+
    ],
    # Filtro para guiacanales.xml: solo estos IDs
    'https://raw.githubusercontent.com/luisms123/tdt/master/guiacanales.xml': [
        "Sky Sports 1",  # sky sports 1
        "Sky Sports 16",   # sky sports 16
        "Sky Sports 24",  #sky sports 24
        "4 de Monterrey",
        "Canal De Las Estrellas -1 Hora",
        "Canal De Las Estrellas -2 Hora"
    ],
    # Filtro para acidjesuz
    'https://raw.githubusercontent.com/acidjesuz/EPGTalk/master/guide.xml': [
        "I108.18101.schedulesdirect.org",
        "I111.89542.schedulesdirect.org",
        "I112.72801.schedulesdirect.org",
        "I129.20742.schedulesdirect.org",
        "I16.83162.schedulesdirect.org",
        "I191.58780.schedulesdirect.org",
        "I193.58646.schedulesdirect.org",
        "I205.95679.schedulesdirect.org",
        "I207.19736.schedulesdirect.org",
        "I208.16288.schedulesdirect.org",
        "I210.74016.schedulesdirect.org",
        "I23.111165.schedulesdirect.org",
        "I235.55980.schedulesdirect.org",
        "I272.79318.schedulesdirect.org",
        "I273.64230.schedulesdirect.org",
        "I278.95630.schedulesdirect.org",
        "I304.16574.schedulesdirect.org",
        "I305.40704.schedulesdirect.org",
        "I337.60179.schedulesdirect.org",
        "I353.71799.schedulesdirect.org",
        "I361.17672.schedulesdirect.org",
        "I373.16298.schedulesdirect.org",
        "I374.16423.schedulesdirect.org",
        "I376.19737.schedulesdirect.org",
        "I377.68317.schedulesdirect.org",
        "I378.80804.schedulesdirect.org",
        "I381.80805.schedulesdirect.org",
        "I414.111249.schedulesdirect.org",
        "I425.113876.schedulesdirect.org",
        "I438.98718.schedulesdirect.org",
        "I448.67632.schedulesdirect.org",
        "I488.99621.schedulesdirect.org",
        "I513.59155.schedulesdirect.org",
        "I551.33629.schedulesdirect.org",
        "I554.75785.schedulesdirect.org",
        "I560.109786.schedulesdirect.org",
        "I561.50798.schedulesdirect.org",
        "I562.82446.schedulesdirect.org",
        "I575.50367.schedulesdirect.org",
        "I681.19246.schedulesdirect.org",
        "I684.16189.schedulesdirect.org",
        "I687.15211.schedulesdirect.org",
        "I689.73070.schedulesdirect.org",
        "I699.37232.schedulesdirect.org",
        "I711.63109.schedulesdirect.org",
        "I718.65129.schedulesdirect.org",
        "I739.84425.schedulesdirect.org",
        "I754.11118.schedulesdirect.org",
        "I298.30392.schedulesdirect.org",
        "I299.79923.schedulesdirect.org",
        "I300.47374.schedulesdirect.org"
    ],
    # Filtro para dish
    'https://raw.githubusercontent.com/Dingolobo/test/refs/heads/main/dish.xml': [
        "12712",
        "15178",
        "15192",
        "15232",
        "15296",
        "15384",
        "15688",
        "15969",
        "16141",
        "16213",
        "16435",
        "16464",
        "16707",
        "16794",
        "16795",
        "16799",
        "16800",
        "17484",
        "18169",
        "18329",
        "18955",
        "19158",
        "19234",
        "19384",
        "19385",
        "20548",
        "24519",
        "25615",
        "25788",
        "25793",
        "27741",
        "27773",
        "29017",
        "32749",
        "34344",
        "34412",
        "34710",
        "34863",
        "34879",
        "37747",
        "40137",
        "45831",
        "45955",
        "46442",
        "46608",
        "47403",
        "48293",
        "50577",
        "52762",
        "56036",
        "56727",
        "57580",
        "59582",
        "60295",
        "60801",
        "61033",
        "61311",
        "61404",
        "61719",
        "62043",
        "64835",
        "65940",
        "66419",
        "66488",
        "67787",
        "68119",
        "68134",
        "68140",
        "71621",
        "72625",
        "74420",
        "74450",
        "75537",
        "77783",
        "78763",
        "79402",
        "79968",
        "80199",
        "82970",
        "83458",
        "84532",
        "87915",
        "88305",
        "88533",
        "89128",
        "89260",
        "89610",
        "90209",
        "90653",
        "90682",
        "90917",
        "91029",
        "92197",
        "95687",
        "96445",
        "97501",
        "98192",
        "100602,"
        "101111",
        "101734",
        "102301",
        "106112",
        "107366",
        "109817",
        "109982",
        "115713",
        "118698",
        "119198",
        "120767",
        "121144",
        "123193",
        "123604",
        "124934",
        "140026",
        "141773",
        "144778",
        "148503",
        "186893"
    ]
    
    # Para agregar otra URL y filtro:
    # 'https://ejemplo.com/otra-epg.xml': ["id1", "id2", "id3"]
}

def cargar_mappings(archivo_mapping='mappings.json'):
    """Carga el archivo de mappings desde JSON."""
    try:
        with open(archivo_mapping, 'r', encoding='utf-8') as f:
            mappings = json.load(f)
            print(f"Mappings cargados: {len(mappings)} entradas.")
            return mappings
    except FileNotFoundError:
        print(f"Advertencia: No se encontró {archivo_mapping}. Usando nombres originales.")
        return {}
    except json.JSONDecodeError:
        print(f"Error: {archivo_mapping} no es un JSON válido. Usando nombres originales.")
        return {}

def aplicar_mappings(root, mappings):
    """Aplica los mappings a los canales: elimina todos los <display-name> y agrega solo uno nuevo por ID."""
    canales = root.findall('channel')
    mappings_aplicados = 0
    for canal in canales:
        canal_id = canal.get('id')
        if canal_id and canal_id in mappings:
            nombre_deseado = mappings[canal_id]
            # Eliminar TODOS los display-name existentes
            display_names = canal.findall('display-name')
            for dn in display_names:
                canal.remove(dn)
            # Agregar SOLO uno nuevo
            display_name = ET.SubElement(canal, 'display-name')
            display_name.text = nombre_deseado
            mappings_aplicados += 1
            print(f"Mapping aplicado (solo uno): {canal_id} -> {nombre_deseado}")
        elif canal_id:
            print(f"Advertencia: No hay mapping para {canal_id}. Manteniendo nombres originales.")
    print(f"Total mappings aplicados: {mappings_aplicados}/{len(canales)} canales.")

def download_and_parse_xml(url, local_filename=None):
    """Descarga y parsea un XML desde una URL, priorizando archivo local si existe (modificación para workflow)."""
    # Modificación: Intenta leer archivo local primero si se proporciona
    if local_filename and os.path.exists(local_filename):
        try:
            print(f"Leyendo XML local: {local_filename}")
            with open(local_filename, 'r', encoding='utf-8') as f:
                content = f.read()
            root = ET.fromstring(content)
            return root
        except ET.ParseError as e:
            print(f"Error parseando XML local {local_filename}: {e}. Fallback a URL.")
        except Exception as e:
            print(f"Error leyendo local {local_filename}: {e}. Fallback a URL.")
    
    # Fallback original: Descarga de URL
    try:
        print(f"Descargando de URL: {url} (fuente externa o fallback)")
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        root = ET.fromstring(response.content)
        return root
    except requests.RequestException as e:
        print(f"Error descargando {url}: {e}")
        return None
    except ET.ParseError as e:
        print(f"Error parseando XML de {url}: {e}")
        return None

def merge_epg_feeds(urls):
    """Mergea múltiples feeds EPG en uno solo, aplicando filtros por URL si están definidos en FILTERS."""
    all_channels = {}  # Diccionario para evitar duplicados por ID de canal
    all_programmes = []

    for url in urls:
        print(f"Procesando {url}...")
        
        # Modificación: Detecta si es una fuente local y pasa el filename para priorizar local
        local_filename = None
        if 'mvshub.xml' in url:
            local_filename = 'mvshub.xml'
        elif 'dish.xml' in url:
            local_filename = 'dish.xml'
        elif 'openepg.xml' in url:
            local_filename = 'openepg.xml'
        
        root = download_and_parse_xml(url, local_filename)
        if root is None or root.tag != 'tv':
            print(f"Saltando {url}: XML inválido o vacío.")
            continue

        canales_procesados = 0
        programas_procesados = 0

        # Obtener la lista de IDs permitidos para esta URL (si existe en FILTERS)
        # Si no hay filtro (None o lista vacía), no filtrar (incluir todo)
        ids_permitidos = FILTERS.get(url, None)
        filtrar = (ids_permitidos is not None and len(ids_permitidos) > 0)
        if filtrar:
            print(f"Aplicando filtrado solo para IDs: {ids_permitidos} en {url}")

        # Extraer canales (evitar duplicados por 'id'), con filtrado si aplica
        for channel in root.findall('channel'):
            channel_id = channel.get('id')
            if channel_id:
                # Si hay filtro, solo incluir si el ID está en la lista permitida
                if filtrar and channel_id not in ids_permitidos:
                    continue  # Salta canales no deseados
                if channel_id not in all_channels:
                    all_channels[channel_id] = channel
                    canales_procesados += 1

        # Extraer programas, con filtrado si aplica
        for programme in root.findall('programme'):
            programme_channel = programme.get('channel')
            if filtrar and programme_channel not in ids_permitidos:
                continue  # Salta programas no deseados (solo aquellos de canales filtrados)
            all_programmes.append(programme)
            programas_procesados += 1

        print(f"  - Canales agregados: {canales_procesados}, Programas: {programas_procesados}")

    # Crear nuevo XML raíz
    tv = ET.Element('tv')
    tv.set('generator-info-name', 'Merged EPG Script')
    tv.set('generator-info-url', 'https://github.com/tu-usuario/tu-repo')

    # Agregar canales mergeados
    for channel in all_channels.values():
        tv.append(channel)

    # Agregar todos los programas
    for programme in all_programmes:
        tv.append(programme)

    return tv

def pretty_xml(element):
    """Formatea el XML para que sea legible, eliminando líneas vacías extras."""
    rough_string = ET.tostring(element, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    pretty_xml = reparsed.toprettyxml(indent="  ")
    
    # Filtrar líneas vacías extras (solo espacios o \n)
    lines = pretty_xml.split('\n')
    clean_lines = []
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped or i == 0:  # Mantener la primera línea (XML declaration) aunque esté vacía
            clean_lines.append(line.rstrip())  # Remover trailing spaces
    return '\n'.join(clean_lines) + '\n'  # Agregar un \n final para cierre limpio

def main():
    """Función principal: mergea y guarda el XML."""
    if not EPG_URLS:
        print("No hay URLs configuradas.")
        return

    print(f"Iniciando merge de {len(EPG_URLS)} feeds EPG a las {datetime.now()}")
    
    # Cargar mappings al inicio
    mappings = cargar_mappings()
    
    merged_tv = merge_epg_feeds(EPG_URLS)
    if merged_tv is None:
        print("No se pudo mergear ningún feed.")
        return

    # Aplicar mappings después del merge
    aplicar_mappings(merged_tv, mappings)

    xml_content = pretty_xml(merged_tv)
    
    # Guardar en archivo
    output_file = 'mxepg.xml'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(xml_content)
    
    print(f"Archivo mergeado guardado: {output_file}")
    print(f"Tamaño aproximado: {len(xml_content)} caracteres")
    print("Merge completado exitosamente.")

if __name__ == "__main__":
    main()
