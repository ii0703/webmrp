from flask import Blueprint, render_template, request, redirect, url_for, g, abort
from mrp.auth import login_required
from .models import Producto, CategoriaProducto, Unidad
from mrp import db
from sqlite3 import IntegrityError

bp = Blueprint('producto', __name__, url_prefix='/producto')


def get(id):
    dato = Producto.query.get_or_404(id)
    return dato


@bp.route('/list')
@login_required
def index():
    p = request.args.get('p', 1, type=int)
    datos = db.paginate(db.select(Producto).order_by(Producto.nombre.desc()),
                        per_page=5, page=p)
    return render_template('producto/index.html', datos=datos)


@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    categorias_producto = (CategoriaProducto
                           .query.filter_by(esta_activo=True)
                           .order_by(CategoriaProducto.nombre).all())
    unidades = (Unidad.query
                .filter_by(esta_activo=True)
                .order_by(Unidad.nombre).all())

    if request.method == 'POST':
        sku = request.form['sku']
        categoria_producto_id = request.form['categoria-producto']
        nombre = request.form['nombre']
        unidad_id = request.form['unidad']
        cantidad_total = request.form['cantidad-total']
        costo = request.form['costo']
        porcentaje_impuesto = request.form['porcentaje-impuesto']
        redondeo = request.form['redondeo']
        modo_utilidad = request.form['modo-utilidad']
        utilidad_monto = 0
        utilidad_porcentaje = 0
        utilildad_es_porcentaje = True
        if modo_utilidad == 'porcentaje':
            utilidad_porcentaje = request.form['utilidad-porcentaje']
            utilildad_es_porcentaje = True
        else:
            utilidad_porcentaje = 0
        if utilidad_monto == 'monto':
            utilidad_monto = request.form['utilidad-monto']
            utilildad_es_porcentaje = False
        else:
            utilidad_porcentaje = 0
        esta_activo = request.form.get('esta-activo') == 'on'

        producto = Producto(sku=sku,
                            nombre=nombre,
                            categoria_producto_id=categoria_producto_id,
                            unidad_id=unidad_id,
                            cantidad_total=cantidad_total,
                            costo=costo,
                            porcentaje_impuesto=porcentaje_impuesto,
                            redondeo=redondeo,
                            utilildad_es_porcentaje=utilildad_es_porcentaje,
                            porcentaje_utilidad=utilidad_porcentaje,
                            monto_utilidad=utilidad_monto,
                            esta_activo=esta_activo
                            )

        db.session.add(producto)

        # db.session.commit()

        try:
            db.session.commit()
        except AssertionError as err:
            db.session.rollback()
            abort(409, err)
        except IntegrityError as err:
            db.session.rollback()
            abort(409, err.orig)
        except Exception as err:
            db.session.rollback()
            abort(500, err)
        finally:
            db.session.close()

        return redirect(url_for('producto.index'))

    return render_template('producto/create.html', categorias_producto=categorias_producto, unidades=unidades)


@bp.route('/update/<int:id>', methods=['GET', 'POST'])
@login_required
def update(id):
    producto = get(id)
    categorias_producto = (CategoriaProducto
                           .query.filter_by(esta_activo=True)
                           .order_by(CategoriaProducto.nombre).all())
    unidades = (Unidad.query
                .filter_by(esta_activo=True)
                .order_by(Unidad.nombre).all())

    if request.method == 'POST':
        producto.sku = request.form['sku']
        producto.categoria_producto_id = request.form['categoria-producto']
        producto.nombre = request.form['nombre']
        producto.unidad_id = request.form['unidad']
        producto.cantidad_total = request.form['cantidad-total']
        producto.costo = request.form['costo']
        producto.porcentaje_impuesto = request.form['porcentaje-impuesto']
        producto.redondeo = request.form['redondeo']
        modo_utilidad = request.form['modo-utilidad']
        utilidad_monto = 0
        utilidad_porcentaje = 0
        utilildad_es_porcentaje = True
        if modo_utilidad == 'porcentaje':
            utilidad_porcentaje = request.form['utilidad-porcentaje']
            utilildad_es_porcentaje = True
        else:
            utilidad_porcentaje = 0

        if utilidad_monto == 'monto':
            utilidad_monto = request.form['utilidad-monto']
            utilildad_es_porcentaje = False
        else:
            utilidad_porcentaje = 0

        producto.utilidad_porcentaje = utilidad_porcentaje
        producto.utilidad_monto = utilidad_monto
        producto.utilildad_es_porcentaje = utilildad_es_porcentaje

        producto.esta_activo = request.form.get('esta-activo') == 'on'

        db.session.commit()

        return redirect(url_for('producto.index'))

    return render_template('producto/update.html', producto=producto, categorias_producto=categorias_producto,
                           unidades=unidades)


@bp.route('/delete/<int:id>')
@login_required
def delete(id):
    producto = get(id)
    db.session.delete(producto)
    db.session.commit()
    return redirect(url_for('producto.index'))


@bp.route('/view/<int:id>')
@login_required
def view(id):
    producto = get(id)
    return render_template('producto/view.html', producto=producto)
