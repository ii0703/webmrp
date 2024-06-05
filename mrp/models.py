from mrp import db
from sqlalchemy import (BLOB, Table, Column, String, Boolean, Integer, DateTime, ForeignKey, Text, UniqueConstraint,
                        Index, Date, Numeric, Double, func, CheckConstraint)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import datetime, date
from typing import Optional


class Usuario(db.Model):
    __tablename__ = 'usuarios'

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    password: Mapped[str] = mapped_column(Text)
    nombre: Mapped[str] = mapped_column(String(60))

    def __repr__(self):
        return f'<Usuario: "{self.username} - {self.nombre}">'


class Lugar(db.Model):
    __tablename__ = 'lugares'

    id: Mapped[int] = mapped_column(primary_key=True)
    codigo: Mapped[str] = mapped_column(String(6), unique=True, index=True)
    nombre: Mapped[str] = mapped_column(String(100))
    esta_activo: Mapped[bool] = mapped_column(Boolean, default=True)
    bodegas: Mapped[list['Bodega']] = relationship(back_populates='lugar')
    clientes: Mapped[list['Cliente']] = relationship(back_populates='lugar')
    proveedores: Mapped[list['Proveedor']] = relationship(back_populates='lugar')

    def __repr__(self):
        return f'<Lugar: "{self.codigo} - {self.nombre}">'


class Bodega(db.Model):
    __tablename__ = 'bodegas'

    id: Mapped[int] = mapped_column(primary_key=True)
    codigo: Mapped[str] = mapped_column(String(6), unique=True, index=True)
    nombre: Mapped[str] = mapped_column(String(100))
    esta_activo: Mapped[bool] = mapped_column(Boolean, default=True)
    lugar_id: Mapped[int] = mapped_column(Integer, ForeignKey('lugares.id'))
    lugar: Mapped['Lugar'] = relationship(back_populates='bodegas')

    def __repr__(self):
        return f'<Bodega: "{self.codigo} - {self.nombre}">'


class Cliente(db.Model):
    __tablename__ = 'clientes'

    id: Mapped[int] = mapped_column(primary_key=True)
    identificacion: Mapped[str] = mapped_column(String(6), unique=True, index=True)
    nombre: Mapped[str] = mapped_column(String(100))
    correo_electronico: Mapped[Optional[str]] = mapped_column(String(100), unique=True, index=True)
    telefono: Mapped[Optional[str]] = mapped_column(String(100), unique=True, index=True)
    es_persona_fisica: Mapped[bool] = mapped_column(Boolean, default=True)
    esta_activo: Mapped[bool] = mapped_column(Boolean, default=True)
    lugar_id: Mapped[int] = mapped_column(Integer, ForeignKey('lugares.id'))
    lugar: Mapped['Lugar'] = relationship(back_populates='clientes')

    def __repr__(self):
        return f'<Cliente: "{self.identificacion} - {self.nombre}">'


class Proveedor(db.Model):
    __tablename__ = 'proveedores'

    id: Mapped[int] = mapped_column(primary_key=True)
    identificacion: Mapped[str] = mapped_column(String(6), unique=True, index=True)
    nombre: Mapped[str] = mapped_column(String(100))
    correo_electronico: Mapped[Optional[str]] = mapped_column(String(100), unique=True, index=True)
    telefono: Mapped[Optional[str]] = mapped_column(String(100), unique=True, index=True)
    es_persona_fisica: Mapped[bool] = mapped_column(Boolean, default=True)
    esta_activo: Mapped[bool] = mapped_column(Boolean, default=True)
    lugar_id: Mapped[int] = mapped_column(Integer, ForeignKey('lugares.id'))
    lugar: Mapped['Lugar'] = relationship(back_populates='proveedores')

    def __repr__(self):
        return f'<Proveedor: "{self.identificacion} - {self.nombre}">'


class TipoUnidad(db.Model):
    __tablename__ = 'tipos_unidades'

    id: Mapped[int] = mapped_column(primary_key=True)
    codigo: Mapped[str] = mapped_column(String(6), unique=True, index=True)
    nombre: Mapped[str] = mapped_column(String(100))
    esta_activo: Mapped[bool] = mapped_column(Boolean, default=True)
    unidades: Mapped[list['Unidad']] = relationship(back_populates='tipo_unidad')

    def __repr__(self):
        return f'<TipoUnidad: "{self.codigo} - {self.nombre}">'


class Unidad(db.Model):
    __tablename__ = 'unidades'

    id: Mapped[int] = mapped_column(primary_key=True)
    simbolo: Mapped[str] = mapped_column(String(6), unique=True, index=True)
    nombre: Mapped[str] = mapped_column(String(100))
    esta_activo: Mapped[bool] = mapped_column(Boolean, default=True)
    tipo_unidad_id: Mapped[int] = mapped_column(Integer, ForeignKey('tipos_unidades.id'))
    tipo_unidad: Mapped['TipoUnidad'] = relationship(back_populates='unidades')

    def __repr__(self):
        return f'<Unidad: "{self.simbolo} - {self.nombre}">'


class CategoriaProducto(db.Model):
    __tablename__ = 'categorias_productos'

    id: Mapped[int] = mapped_column(primary_key=True)
    codigo: Mapped[str] = mapped_column(String(6), unique=True, index=True)
    nombre: Mapped[str] = mapped_column(String(100))
    esta_activo: Mapped[bool] = mapped_column(Boolean, default=True)
    productos: Mapped[list['Producto']] = relationship(back_populates='categoria_producto')

    def __repr__(self):
        return f'<CategoriaProducto: "{self.codigo} - {self.nombre}">'


class Producto(db.Model):
    __tablename__ = 'productos'

    id: Mapped[int] = mapped_column(primary_key=True)
    sku: Mapped[str] = mapped_column(String(13), unique=True, index=True)
    nombre: Mapped[str] = mapped_column(String(100))
    categoria_producto_id: Mapped[int] = mapped_column(Integer, ForeignKey('categorias_productos.id'))
    categoria_producto: Mapped['CategoriaProducto'] = relationship(back_populates='productos')
    unidad_id: Mapped[int] = mapped_column(Integer, ForeignKey('unidades.id'))
    unidad: Mapped['Unidad'] = relationship()
    cantidad_total: Mapped[float] = mapped_column(Double, default=0.0)
    cantidad_disponible: Mapped[float] = mapped_column(Double, default=0.0)
    cantidad_reservado: Mapped[float] = mapped_column(Double, default=0.0)
    costo: Mapped[float] = mapped_column(Numeric(12, 2), default=0.0)
    porcentaje_impuesto: Mapped[float] = mapped_column(Double, default=0.0)
    redondeo: Mapped[float] = mapped_column(Double, default=0.0)
    utilildad_es_porcentaje: Mapped[bool] = mapped_column(Boolean, default=True)
    porcentaje_utilidad: Mapped[float] = mapped_column(Double, default=0.0)
    monto_utilidad: Mapped[float] = mapped_column(Double, default=0.0)
    fecha_registro: Mapped[date] = mapped_column(Date, default=datetime.now())
    esta_activo: Mapped[bool] = mapped_column(Boolean, default=True)
    lotes: Mapped[list['ProductoLote']] = relationship(back_populates='producto')

    def __repr__(self):
        return f'<Producto: "{self.sku} - {self.nombre}">'


class ProductoLote(db.Model):
    __tablename__ = 'productos_lotes'

    id: Mapped[int] = mapped_column(primary_key=True)
    bodega_id: Mapped[int] = mapped_column(Integer, ForeignKey('bodegas.id'))
    bodega: Mapped['Bodega'] = relationship()
    producto_id: Mapped[int] = mapped_column(Integer, ForeignKey('productos.id'))
    producto: Mapped['Producto'] = relationship(back_populates='lotes')
    unidad_id: Mapped[int] = mapped_column(Integer, ForeignKey('unidades.id'))
    unidad: Mapped['Unidad'] = relationship()
    cantidad_total: Mapped[float] = mapped_column(Double, default=0.0)
    cantidad_disponible: Mapped[float] = mapped_column(Double, default=0.0)
    cantidad_reservado: Mapped[float] = mapped_column(Double, default=0.0)
    costo: Mapped[float] = mapped_column(Numeric(12, 2), default=0.0)
    porcentaje_impuesto: Mapped[float] = mapped_column(Double, default=0.0)
    redondeo: Mapped[float] = mapped_column(Double, default=0.0)
    utilildad_es_porcentaje: Mapped[bool] = mapped_column(Boolean, default=True)
    porcentaje_utilidad: Mapped[float] = mapped_column(Double, default=0.0)
    monto_utilidad: Mapped[float] = mapped_column(Double, default=0.0)
    fecha_registro: Mapped[date] = mapped_column(Date, server_default=func.now())
    esta_activo: Mapped[bool] = mapped_column(Boolean, default=True)
    fecha_vencimiento: Mapped[Optional[datetime]] = mapped_column(DateTime)
    __table_args__ = (
        Index("idx_producto_lote_bp", bodega_id, producto_id, unique=False),
        # UniqueConstraint(bodega_id, producto_id, name='uq_producto_lote_bp'),
    )

    def __repr__(self):
        return f'<ProductoLote: "{self.simbolo} - {self.nombre}">'


class Tiempo(db.Model):
    __tablename__ = 'tiempos'

    id: Mapped[int] = mapped_column(primary_key=True)
    codigo: Mapped[str] = mapped_column(String(6), unique=True, index=True)
    nombre: Mapped[str] = mapped_column(String(100))
    esta_activo: Mapped[bool] = mapped_column(Boolean, default=True)
    equivalente_en_dias: Mapped[float] = mapped_column(Double, default=1)

    def __repr__(self):
        return f'<Tiempo: "{self.codigo} - {self.nombre}">'


class CategoriaMateriaPrima(db.Model):
    __tablename__ = 'categorias_materias_primas'

    id: Mapped[int] = mapped_column(primary_key=True)
    codigo: Mapped[str] = mapped_column(String(6), unique=True, index=True)
    nombre: Mapped[str] = mapped_column(String(100))
    esta_activo: Mapped[bool] = mapped_column(Boolean, default=True)
    materias: Mapped[list['MateriaPrima']] = relationship(back_populates='categoria_materia_prima')

    def __repr__(self):
        return f'<CategoriaProducto: "{self.codigo} - {self.nombre}">'


class MateriaPrima(db.Model):
    __tablename__ = 'materias_primas'

    id: Mapped[int] = mapped_column(primary_key=True)
    sku: Mapped[str] = mapped_column(String(13), unique=True, index=True)
    nombre: Mapped[str] = mapped_column(String(100))
    categoria_materia_prima_id: Mapped[int] = mapped_column(Integer, ForeignKey('categorias_materias_primas.id'))
    categoria_materia_prima: Mapped['CategoriaMateriaPrima'] = relationship(back_populates='materias')
    unidad_id: Mapped[int] = mapped_column(Integer, ForeignKey('unidades.id'))
    unidad: Mapped['Unidad'] = relationship()
    cantidad_total: Mapped[float] = mapped_column(Double, default=0.0)
    cantidad_disponible: Mapped[float] = mapped_column(Double, default=0.0)
    cantidad_reservado: Mapped[float] = mapped_column(Double, default=0.0)
    costo: Mapped[float] = mapped_column(Numeric(12, 2), default=0.0)
    porcentaje_impuesto: Mapped[float] = mapped_column(Double, default=0.0)
    fecha_registro: Mapped[date] = mapped_column(Date, default=datetime.now())
    esta_activo: Mapped[bool] = mapped_column(Boolean, default=True)
    lotes: Mapped[list['MateriaPrimaLote']] = relationship(back_populates='materia_prima')

    def __repr__(self):
        return f'<MateriaPrima: "{self.simbolo} - {self.nombre}">'


class MateriaPrimaLote(db.Model):
    __tablename__ = 'materias_primas_lotes'

    id: Mapped[int] = mapped_column(primary_key=True)
    bodega_id: Mapped[int] = mapped_column(Integer, ForeignKey('bodegas.id'))
    bodega: Mapped['Bodega'] = relationship()
    materia_prima_id: Mapped[int] = mapped_column(Integer, ForeignKey('materias_primas.id'))
    materia_prima: Mapped['MateriaPrima'] = relationship(back_populates='lotes')
    unidad_id: Mapped[int] = mapped_column(Integer, ForeignKey('unidades.id'))
    unidad: Mapped['Unidad'] = relationship()
    cantidad_total: Mapped[float] = mapped_column(Double, default=0.0)
    cantidad_disponible: Mapped[float] = mapped_column(Double, default=0.0)
    cantidad_reservado: Mapped[float] = mapped_column(Double, default=0.0)
    costo: Mapped[float] = mapped_column(Numeric(12, 2), default=0.0)
    porcentaje_impuesto: Mapped[float] = mapped_column(Double, default=0.0)
    redondeo: Mapped[float] = mapped_column(Double, default=0.0)
    utilildad_es_porcentaje: Mapped[bool] = mapped_column(Boolean, default=True)
    porcentaje_utilidad: Mapped[float] = mapped_column(Double, default=0.0)
    monto_utilidad: Mapped[float] = mapped_column(Double, default=0.0)
    fecha_registro: Mapped[date] = mapped_column(Date, server_default=func.now())
    esta_activo: Mapped[bool] = mapped_column(Boolean, default=True)
    fecha_vencimiento: Mapped[Optional[date]] = mapped_column(Date)


class MateriaPrimaProveedor(db.Model):
    __tablename__ = 'materias_primas_proveedores'

    id: Mapped[int] = mapped_column(primary_key=True)
    materia_prima_id: Mapped[int] = mapped_column(Integer, ForeignKey('materias_primas.id'))
    materia_prima: Mapped['MateriaPrima'] = relationship()
    proveedor_id: Mapped[int] = mapped_column(Integer, ForeignKey('proveedores.id'))
    proveedor: Mapped['Proveedor'] = relationship()
    unidad_id: Mapped[int] = mapped_column(Integer, ForeignKey('unidades.id'))
    unidad: Mapped['Unidad'] = relationship()
    tiempo_id: Mapped[int] = mapped_column(Integer, ForeignKey('tiempos.id'))
    tiempo: Mapped['Tiempo'] = relationship()
    tiempo_entrega: Mapped[float] = mapped_column(Double, default=0.0)
    cantidad_minima: Mapped[float] = mapped_column(Double, default=0.0)
    costo: Mapped[float] = mapped_column(Numeric(12, 2), default=0.0)
    esta_activo: Mapped[bool] = mapped_column(Boolean, default=True)

    def __repr__(self):
        return f'<MateriaPrimaProveedor: "{self.simbolo} - {self.nombre}">'


class ListaMateriales(db.Model):
    __tablename__ = 'listas_materiales'

    id: Mapped[int] = mapped_column(primary_key=True)
    producto_id: Mapped[int] = mapped_column(Integer, ForeignKey('productos.id'))
    producto: Mapped['Producto'] = relationship()
    unidad_id: Mapped[int] = mapped_column(Integer, ForeignKey('unidades.id'))
    unidad: Mapped['Unidad'] = relationship()
    es_receta_principal: Mapped[bool] = mapped_column(Boolean, default=True)
    costo_componentes: Mapped[float] = mapped_column(Numeric(12, 2), default=0.0)
    costo_materia_prima: Mapped[float] = mapped_column(Numeric(12, 2), default=0.0)
    costo_operativo: Mapped[float] = mapped_column(Numeric(12, 2), default=0.0)
    tiempo_fabricacion_en_minutos: Mapped[float] = mapped_column(Double, default=0.0)
    comentario: Mapped[Optional[str]] = mapped_column(String[100])
    fecha_registro: Mapped[date] = mapped_column(Date, server_default=func.now())
    esta_activo: Mapped[bool] = mapped_column(Boolean, default=True)
    fecha_vencimiento: Mapped[Optional[date]] = mapped_column(Date)
    componentes: Mapped[list['ListaMaterialesComponentes']] = relationship(back_populates='lista_materiales')
    materias_primas: Mapped[list['ListaMaterialesMateriasPrimas']] = relationship(back_populates='lista_materiales')

    def __repr__(self):
        principal: str = 'Principal' if self.es_receta_principal else 'Alternativo'
        return f'<ListaMateriales: "{self.producto.nombre} - {principal}">'


class ListaMaterialesComponentes(db.Model):
    __tablename__ = 'listas_materiales_componentes'

    id: Mapped[int] = mapped_column(primary_key=True)
    lista_materiales_id: Mapped[int] = mapped_column(Integer, ForeignKey('listas_materiales.id'))
    lista_materiales: Mapped['ListaMateriales'] = relationship()
    componente_id: Mapped[int] = mapped_column(Integer, ForeignKey('productos.id'))
    componente: Mapped['Producto'] = relationship()
    cantidad: Mapped[float] = mapped_column(Double, default=0.0)
    costo_unitario: Mapped[Optional[float]] = mapped_column(Numeric(12, 2))
    costo_total: Mapped[Optional[float]] = mapped_column(Numeric(12, 2))
    tiempo_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('tiempos.id'))
    tiempo: Mapped['Tiempo'] = relationship()
    tiempo_fabricacion: Mapped[Optional[float]] = mapped_column(Double, default=0.0)

    def __repr__(self):
        return f'<ListaMaterialesComponentes: "{self.producto.nombre}">'


class ListaMaterialesMateriasPrimas(db.Model):
    __tablename__ = 'listas_materiales_materias_primas'

    id: Mapped[int] = mapped_column(primary_key=True)
    lista_materiales_id: Mapped[int] = mapped_column(Integer, ForeignKey('listas_materiales.id'))
    lista_materiales: Mapped['ListaMateriales'] = relationship()
    materia_prima_id: Mapped[int] = mapped_column(Integer, ForeignKey('materias_primas.id'))
    materia_prima: Mapped['MateriaPrima'] = relationship()
    cantidad: Mapped[float] = mapped_column(Double, default=0.0)
    costo_unitario: Mapped[Optional[float]] = mapped_column(Numeric(12, 2))
    costo_total: Mapped[Optional[float]] = mapped_column(Numeric(12, 2))
    tiempo_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('tiempos.id'))
    tiempo: Mapped['Tiempo'] = relationship()
    tiempo_fabricacion: Mapped[Optional[float]] = mapped_column(Double, default=0.0)
    __table_args__ = (UniqueConstraint('lista_materiales_id', 'materia_prima_id', name='uq_lista_materiales_mp'),
                      CheckConstraint('cantidad > 0', name='ck_lista_materiales_cantidad'))

    def __repr__(self):
        return f'<ListaMaterialesMateriasPrimas: "{self.producto.nombre}">'


class PlanMaestroProduccion(db.Model):
    __tablename__ = 'planes_maestros_producciones'

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(100))
    inicio: Mapped[Optional[datetime]] = mapped_column(DateTime)
    fin: Mapped[Optional[datetime]] = mapped_column(DateTime)
    esta_finalizado: Mapped[bool] = mapped_column(Boolean, default=False)
    productos: Mapped[list['PlanMaestroProduccionProductos']] = relationship(back_populates='mps')

    def __repr__(self):
        return f'<PlanMaestroProduccion: "{self.nombre}">'


class PlanMaestroProduccionProductos(db.Model):
    __tablename__ = 'planes_maestros_producciones_productos'

    id: Mapped[int] = mapped_column(primary_key=True)
    mps_id: Mapped[int] = mapped_column(Integer, ForeignKey('planes_maestros_producciones.id'))
    mps: Mapped['PlanMaestroProduccion'] = relationship()
    producto_id: Mapped[int] = mapped_column(Integer, ForeignKey('productos.id'))
    producto: Mapped['Producto'] = relationship()

    def __repr__(self):
        return f'<PlanMaestroProduccionProductos: "{self.id}">'


class PlanMaestroProduccionDemandas(db.Model):
    __tablename__ = 'planes_maestros_producciones_demandas'

    id: Mapped[int] = mapped_column(primary_key=True)
    mps_id: Mapped[int] = mapped_column(Integer, ForeignKey('planes_maestros_producciones.id'))
    mps: Mapped['PlanMaestroProduccion'] = relationship()
    producto_id: Mapped[int] = mapped_column(Integer, ForeignKey('productos.id'))
    producto: Mapped['Producto'] = relationship()
    semana: Mapped['str'] = mapped_column(String(10))
    cantidad: Mapped[float] = mapped_column(Double, default=0.0)

    def __repr__(self):
        return f'<PlanMaestroProduccionDemandas: "{self.id}">'
