import xml.etree.ElementTree as ET

# Lista de IDs que quieres filtrar
CANAL_IDS = [
    "skymas/edye",
    "otro/canal1",
    "otro/canal2"
]

INPUT_FILE = "openepg.xml"
OUTPUT_FILE = "openepg_filtered.xml"

def filtrar_canales():
    try:
        tree = ET.parse(INPUT_FILE)
        root = tree.getroot()

        # Crear nuevo XML raíz
        tv = ET.Element('tv')
        tv.set('generator-info-name', 'Filtered EPG Script')
        tv.set('generator-info-url', 'https://github.com/tu-usuario/tu-repo')

        # Agregar canales que estén en la lista CANAL_IDS
        canales_encontrados = 0
        for canal_id in CANAL_IDS:
            canal = root.find(f"./channel[@id='{canal_id}']")
            if canal is not None:
                tv.append(canal)
                canales_encontrados += 1
            else:
                print(f"Canal con id '{canal_id}' no encontrado en el XML.")

        print(f"Canales encontrados y agregados: {canales_encontrados}/{len(CANAL_IDS)}")

        # Agregar programas que correspondan a cualquiera de los canales en CANAL_IDS
        programas = root.findall("./programme")
        programas_agregados = 0
        for prog in programas:
            if prog.get('channel') in CANAL_IDS:
                tv.append(prog)
                programas_agregados += 1

        print(f"Programas agregados: {programas_agregados}")

        # Guardar XML filtrado con declaración y encoding UTF-8
        tree_filtrado = ET.ElementTree(tv)
        tree_filtrado.write(OUTPUT_FILE, encoding='utf-8', xml_declaration=True)
        print(f"Archivo filtrado guardado en {OUTPUT_FILE}")

    except ET.ParseError as e:
        print(f"Error al parsear XML: {e}")
    except FileNotFoundError:
        print(f"Archivo {INPUT_FILE} no encontrado.")

if __name__ == "__main__":
    filtrar_canales()

