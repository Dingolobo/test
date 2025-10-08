import requests
import xml.etree.ElementTree as ET
from xml.dom import minidom
import os
import json
from datetime import datetime

# Array de URLs de ejemplo (reemplaza con tus URLs reales)
EPG_URLS = [
    'https://raw.githubusercontent.com/Dingolobo/xmldata/refs/heads/main/schdirect.xml',
    'https://raw.githubusercontent.com/Dingolobo/xmldata/refs/heads/main/openepg.xml',
    'https://raw.githubusercontent.com/matthuisman/i.mjh.nz/refs/heads/master/Plex/mx.xml',
    'https://raw.githubusercontent.com/Dingolobo/xmldata/main/mvshub.xml',
    'https://raw.githubusercontent.com/serviciovodflex/nxt-guide/refs/heads/main/epg.xml'  # Nueva URL agregada
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
    # Filtro para mx.xml: solo estos dos IDs
    'https://raw.githubusercontent.com/matthuisman/i.mjh.nz/refs/heads/master/Plex/mx.xml': [
        "608049aefa2b8ae93c2c3a63-688d3402a6fe30698ab42007", #ITV deportes
        "608049aefa2b8ae93c2c3a63-63f0ca427b78030ed9990309", #Curiosity
        "608049aefa2b8ae93c2c3a63-66633339ebeb02ee8bd1597c"  #fifa+
    ],
    # Ejemplo de filtro para la nueva URL nxt-guide: reemplaza con IDs reales de canales que quieras.
    # Por ahora, está vacío (no filtra nada). Para filtrar, agrega IDs como en el ejemplo de mx.xml.
    'https://raw.githubusercontent.com/serviciovodflex/nxt-guide/refs/heads/main/epg.xml': [
        "SkySports1.mx",  # Ejemplo: descomenta y agrega IDs reales, e.g., "canal1.example.com"
        "SkySports16.mx",   # Agrega tantos como necesites
        "SkySports24.mx"
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

def download_and_parse_xml(url):
    """Descarga y parsea un XML desde una URL."""
    try:
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
        root = download_and_parse_xml(url)
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
