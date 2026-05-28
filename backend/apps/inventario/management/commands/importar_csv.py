import csv
import re
from datetime import datetime
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.usuarios.models import Usuario
from apps.catalogo.models import Categoria, Producto
from apps.inventario.models import Lote, Movimiento

class Command(BaseCommand):
    help = 'Importa y reestructura datos desde INVENTARIO.csv'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Ruta al archivo INVENTARIO.csv (ej: ../INVENTARIO.csv)')

    def handle(self, *args, **kwargs):
        csv_path = kwargs['csv_file']

        try:
            # We assume ';' delimiter based on typical Excel CSV output in Spanish locales
            with open(csv_path, newline='', encoding='utf-8-sig') as csvfile:
                reader = csv.reader(csvfile, delimiter=';')
                
                # Busca la cabecera (ignora filas vacías o basura al inicio)
                headers = None
                for row in reader:
                    if len(row) > 0 and 'MATERIALES' in row[0].upper():
                        headers = row
                        break
                
                if not headers:
                    self.stderr.write(self.style.ERROR('No se encontró la cabecera "MATERIALES". Verifica que el archivo no esté corrupto.'))
                    return

                # Crear usuario del sistema para que quede el registro de que él hizo la migración
                user, _ = Usuario.objects.get_or_create(
                    rut='00.000.000-0',
                    defaults={
                        'username': 'migracion',
                        'first_name': 'Sistema',
                        'last_name': 'Migración',
                        'rol': Usuario.Rol.GESTOR,
                        'is_active': False
                    }
                )

                # Procesar todo dentro de una transacción para que si falla, no deje la base de datos a medias
                with transaction.atomic():
                    for i, row in enumerate(reader, start=1):
                        # Saltar filas vacías
                        if not row or not row[0].strip():
                            continue
                        
                        try:
                            material = row[0].strip()
                            tipo = row[1].strip()
                            ano_str = row[2].strip()
                            oc_str = row[3].strip()
                            cantidad_str = row[4].strip()
                            
                            # La columna 6 en adelante es la ubicación, entregas, y el historial de texto libre.
                            historial = " | ".join([c.strip() for c in row[6:] if c.strip()])

                            # 1. CATEGORÍA
                            categoria, _ = Categoria.objects.get_or_create(
                                nombre=tipo or "Sin Categoría",
                                defaults={'descripcion': 'Generado automáticamente por migración CSV'}
                            )

                            # 2. PRODUCTO
                            producto, _ = Producto.objects.get_or_create(
                                nombre=material,
                                defaults={
                                    'categoria': categoria,
                                    'codigo': f'PROD-{Categoria.objects.count()}-{i}',
                                    'unidad_medida': 'unidad'
                                }
                            )

                            # 3. EXTRACCIÓN MATEMÁTICA DE CANTIDADES (Ej: "41 quedan 7")
                            cant_inicial = 0
                            cant_disp = 0
                            
                            nums = re.findall(r'\d+', cantidad_str)
                            if len(nums) >= 2:
                                cant_inicial = int(nums[0])
                                cant_disp = int(nums[1])
                            elif len(nums) == 1:
                                cant_inicial = int(nums[0])
                                cant_disp = int(nums[0])
                            else:
                                # Si no hay números (ej: "?"), asumimos 1 para no quebrar la base de datos
                                cant_inicial = 1
                                cant_disp = 1
                                historial = f"CANTIDAD DUDOSA ({cantidad_str}) - " + historial

                            # 4. FECHA DE INGRESO
                            year = datetime.now().year
                            try:
                                yr_match = re.search(r'20\d\d', ano_str)
                                if yr_match:
                                    year = int(yr_match.group(0))
                            except:
                                pass
                            fecha_ingreso = datetime(year, 1, 1).date()

                            # 5. CREACIÓN DEL LOTE
                            lote = Lote.objects.create(
                                producto=producto,
                                orden_compra=oc_str[:100] if oc_str and oc_str.upper() != 'SIN INFORMACIÓN' else f"MIG-{year}-{i}",
                                costo_unitario=0,
                                cantidad_inicial=cant_inicial,
                                cantidad_disponible=cant_inicial, # Empezamos full
                                cantidad_reservada=0,
                                fecha_ingreso=fecha_ingreso,
                            )

                            # 6. MOVIMIENTO: INGRESO INICIAL
                            Movimiento.objects.create(
                                lote=lote,
                                ejecutado_por=user,
                                tipo=Movimiento.Tipo.INGRESO,
                                cantidad=cant_inicial,
                                stock_anterior=0,
                                stock_posterior=cant_inicial,
                                motivo="Carga inicial por migración"
                            )

                            # 7. MOVIMIENTO: AJUSTE POR CONSUMO HISTÓRICO
                            if cant_disp < cant_inicial:
                                diff = cant_inicial - cant_disp
                                Movimiento.objects.create(
                                    lote=lote,
                                    ejecutado_por=user,
                                    tipo=Movimiento.Tipo.DESPACHO,
                                    cantidad=diff,
                                    stock_anterior=cant_inicial,
                                    stock_posterior=cant_disp,
                                    motivo=f"Respaldo histórico de entregas: {historial}"
                                )
                                # Actualizar estado del lote a su realidad actual
                                lote.cantidad_disponible = cant_disp
                                lote.actualizar_estado()
                                lote.save(update_fields=['cantidad_disponible', 'estado'])

                            self.stdout.write(self.style.SUCCESS(f'OK: {material} (Disponible: {cant_disp} de {cant_inicial})'))
                        
                        except Exception as e:
                            self.stderr.write(self.style.ERROR(f'Error procesando la fila {i} ({row[0]}): {e}'))

            self.stdout.write(self.style.SUCCESS('\n¡Migración completada exitosamente! Base de datos inicializada.'))
            
        except FileNotFoundError:
            self.stderr.write(self.style.ERROR(f'No se encontró el archivo: {csv_path}'))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Error crítico al abrir el archivo: {e}'))
