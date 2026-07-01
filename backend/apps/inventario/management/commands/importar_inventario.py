import csv
import os
import re
from datetime import date
from django.core.management.base import BaseCommand
from apps.catalogo.models import Categoria, Producto
from apps.inventario.models import Lote

class Command(BaseCommand):
    help = 'Importa inventario inicial desde INVENTARIO.csv'

    def extract_first_number(self, text):
        if not text:
            return 0
        match = re.search(r'\d+', str(text))
        if match:
            return int(match.group())
        return 0

    def handle(self, *args, **kwargs):
        # El archivo debe estar en /app (que es la carpeta backend local)
        file_path = '/app/INVENTARIO.csv'
        
        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(
                'No se encontró INVENTARIO.csv en /app/.\n'
                'Por favor, mueve o copia INVENTARIO.csv dentro de la carpeta "backend" y vuelve a ejecutar este comando.'
            ))
            return

        self.stdout.write(f'Leyendo archivo {file_path}...')

        count_cat = 0
        count_prod = 0
        count_lote = 0

        # Usar utf-8-sig para lidiar con el BOM de Excel, o latin1 si falla
        try:
            csvfile = open(file_path, newline='', encoding='utf-8-sig')
            csvfile.read(1)
            csvfile.seek(0)
        except UnicodeDecodeError:
            csvfile = open(file_path, newline='', encoding='latin1')

        with csvfile:
            reader = csv.reader(csvfile, delimiter=';')
            headers = []
            
            # Buscar la fila de encabezados
            for row in reader:
                if not row:
                    continue
                # Limpiar espacios
                clean_row = [str(h).strip().upper() for h in row]
                if 'MATERIALES' in clean_row or any('MATERIALES' in h for h in clean_row):
                    headers = clean_row
                    break
            
            if not headers:
                self.stdout.write(self.style.ERROR('No se encontró la fila de encabezados (buscando "MATERIALES").'))
                return
            
            # Encontrar índices de las columnas, permitiendo ligeras variaciones
            def find_idx(keywords):
                for i, h in enumerate(headers):
                    for kw in keywords:
                        if kw in h:
                            return i
                return -1

            idx_material = find_idx(['MATERIALES'])
            idx_tipo = find_idx(['TIPO'])
            idx_anio = find_idx(['AÑO DE COMPRA', 'AÑO'])
            idx_oc = find_idx(['ORDEN DE COMPRA', 'ORDEN'])
            idx_cant = find_idx(['CANTIDAD TOTAL', 'CANTIDAD'])
            idx_asignado = find_idx(['ENTREGA A FUNCIONARIO'])

            for row_num, row in enumerate(reader, start=1):
                if not row or len(row) <= max(idx_material, idx_tipo, idx_cant):
                    continue
                
                material = row[idx_material].strip() if idx_material != -1 else ""
                if not material:
                    continue

                tipo = row[idx_tipo].strip() if idx_tipo != -1 else "Sin Categoría"
                if not tipo: tipo = "Sin Categoría"

                anio_str = row[idx_anio].strip() if idx_anio != -1 and idx_anio < len(row) else ""
                oc_str = row[idx_oc].strip() if idx_oc != -1 and idx_oc < len(row) else ""
                cant_str = row[idx_cant].strip() if idx_cant != -1 and idx_cant < len(row) else ""
                asignado_str = row[idx_asignado].strip() if idx_asignado != -1 and idx_asignado < len(row) else ""

                # 1. Categoria
                categoria, created = Categoria.objects.get_or_create(nombre=tipo)
                if created: count_cat += 1

                # 2. Producto
                producto = Producto.objects.filter(nombre=material, categoria=categoria).first()
                if not producto:
                    # Generar código único PRD-XXXX
                    base_code = 'PRD-' + ''.join(filter(str.isalnum, material[:6])).upper()
                    if not base_code.strip('PRD-'):
                        base_code = 'PRD-MISC'
                    
                    code = base_code
                    suffix = 1
                    while Producto.objects.filter(codigo=code).exists():
                        code = f"{base_code}-{suffix}"
                        suffix += 1
                    
                    asignado = asignado_str if asignado_str.lower() != 'no aplica' else ''
                    
                    producto = Producto.objects.create(
                        categoria=categoria,
                        codigo=code,
                        nombre=material,
                        asignado_a=asignado
                    )
                    count_prod += 1

                # 3. Lote
                cantidad = self.extract_first_number(cant_str)
                if cantidad > 0:
                    fecha_ingreso = date.today()
                    anio = self.extract_first_number(anio_str)
                    if anio > 2000 and anio <= date.today().year + 1:
                        fecha_ingreso = date(anio, 1, 1)

                    if 'sin' in oc_str.lower() or not oc_str:
                        oc_str = f"S/N-{fecha_ingreso.year}"

                    lote_exists = Lote.objects.filter(producto=producto, orden_compra=oc_str).exists()
                    if not lote_exists:
                        Lote.objects.create(
                            producto=producto,
                            orden_compra=oc_str,
                            costo_unitario=0,
                            cantidad_inicial=cantidad,
                            cantidad_disponible=cantidad,
                            fecha_ingreso=fecha_ingreso
                        )
                        count_lote += 1

        self.stdout.write(self.style.SUCCESS(f'Importación finalizada. Creados: {count_cat} Categorías, {count_prod} Productos, {count_lote} Lotes.'))
