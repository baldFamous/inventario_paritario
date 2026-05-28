import pytest
from apps.usuarios.models import Usuario
from apps.catalogo.models import Categoria, Producto
from apps.inventario.models import Lote, Movimiento


class TestUsuarioModel:
    def test_crear_usuario_solicitante(self, solicitante):
        assert solicitante.rol == Usuario.Rol.SOLICITANTE
        assert solicitante.es_solicitante is True
        assert solicitante.es_gestor is False

    def test_crear_usuario_gestor(self, gestor):
        assert gestor.rol == Usuario.Rol.GESTOR
        assert gestor.es_gestor is True
        assert gestor.es_solicitante is False

    def test_str_usuario(self, gestor):
        assert gestor.rut in str(gestor)

    def test_rut_unico(self, db, gestor):
        with pytest.raises(Exception):
            Usuario.objects.create_user(
                username='otro', password='Test1234!',
                rut=gestor.rut, rol=Usuario.Rol.SOLICITANTE,
            )


class TestCategoriaModel:
    def test_crear_categoria(self, categoria):
        assert categoria.nombre == 'Higiene'
        assert str(categoria) == 'Higiene'

    def test_nombre_unico(self, db, categoria):
        with pytest.raises(Exception):
            Categoria.objects.create(nombre='Higiene')


class TestProductoModel:
    def test_crear_producto(self, producto):
        assert producto.codigo == 'HIG-001'
        assert producto.is_active is True

    def test_relacion_categoria(self, producto, categoria):
        assert producto.categoria == categoria
        assert producto in categoria.productos.all()

    def test_codigo_unico(self, db, producto, categoria):
        with pytest.raises(Exception):
            Producto.objects.create(
                categoria=categoria, codigo='HIG-001',
                nombre='Otro', unidad_medida='unidad',
            )


class TestLoteModel:
    def test_crear_lote(self, lote):
        assert lote.estado == Lote.Estado.ACTIVO
        assert lote.cantidad_disponible == 100
        assert lote.cantidad_reservada == 0

    def test_costo_total(self, lote):
        assert lote.costo_total == 100 * 3500

    def test_actualizar_estado_agotado(self, lote):
        lote.cantidad_disponible = 0
        lote.cantidad_reservada = 0
        lote.actualizar_estado()
        assert lote.estado == Lote.Estado.AGOTADO


class TestMovimientoInmutabilidad:
    def test_no_permite_update(self, db, lote, gestor):
        mov = Movimiento.objects.create(
            lote=lote, ejecutado_por=gestor,
            tipo=Movimiento.Tipo.INGRESO, cantidad=100,
            stock_anterior=0, stock_posterior=100,
        )
        with pytest.raises(ValueError, match='inmutables'):
            mov.motivo = 'Cambio'
            mov.save()

    def test_no_permite_delete(self, db, lote, gestor):
        mov = Movimiento.objects.create(
            lote=lote, ejecutado_por=gestor,
            tipo=Movimiento.Tipo.INGRESO, cantidad=100,
            stock_anterior=0, stock_posterior=100,
        )
        with pytest.raises(ValueError, match='inmutables'):
            mov.delete()
