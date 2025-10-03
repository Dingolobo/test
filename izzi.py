name: iptv detodotv to XML

on:
  schedule:
    - cron: '0 11 * * *'  # Ejecuta a medianoche UTC todos los días
  workflow_dispatch:      # Permite ejecución manual desde GitHub

jobs:
  update-xml:
    runs-on: ubuntu-latest

    steps:
    - name: Checkout repo
      uses: actions/checkout@v3

    - name: Descargar guia XML
      run: |
        wget --user-agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.96 Safari/537.36" -O epg.xml http://live.detodotvplay.com/xmltv.php?username=Risario8&password=Pineda13

    - name: Configurar git para push con token personal
      run: |
        git remote set-url origin https://x-access-token:${{ secrets.PERSONAL_ACCESS_TOKEN }}@github.com/Dingolobo/xmldata.git

    - name: Commit y push cambios
      run: |
        git config user.name "github-actions"
        git config user.email "actions@github.com"
        git add epg.xml
        git commit -m "Actualizar guía EPG procesada" || echo "No hay cambios para commitear"
        git push origin main
