import xml.etree.ElementTree as ET

CANAL_ID = "skymas/edye"
INPUT_FILE = "openepg.xml"
OUTPUT_FILE = "openepg_filtered.xml"

def filtrar_canal():
    try:
        tree = ET.parse(INPUT_FILE)
        root = tree.getroot()

        # Crear nuevo XML raíz
        tv = ET.Element('tv')
        tv.set('generator-info-name', 'Filtered EPG Script')
        tv.set('generator-info-url', 'https://github.com/tu-usuario/tu-repo')

        # Buscar y agregar solo el canal con id CANAL_ID
        canal = root.find(f"./channel[@id='{CANAL_ID}']")
        if canal is not None:
            tv.append(canal)
        else:
            print(f"Canal con id '{CANAL_ID}' no encontrado en el XML.")

        # Agregar solo los programas que correspondan a ese canal
        programas = root.findall(f"./programme[@channel='{CANAL_ID}']")
        for prog in programas:
            tv.append(prog)

        # Guardar XML filtrado con declaración y encoding UTF-8
        tree_filtrado = ET.ElementTree(tv)
        tree_filtrado.write(OUTPUT_FILE, encoding='utf-8', xml_declaration=True)
        print(f"Archivo filtrado guardado en {OUTPUT_FILE}")

    except ET.ParseError as e:
        print(f"Error al parsear XML: {e}")
    except FileNotFoundError:
        print(f"Archivo {INPUT_FILE} no encontrado.")

if __name__ == "__main__":
    filtrar_canal()
