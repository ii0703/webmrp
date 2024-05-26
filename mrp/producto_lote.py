from flask import Blueprint, render_template, request, redirect, url_for, g, abort
from mrp.auth import login_required
from .models import ProductoLote, Unidad, Bodega
from mrp import db
from sqlite3 import IntegrityError

bp = Blueprint('producto_lote', __name__, url_prefix='/producto_lote')


def get(id):
    dato = ProductoLote.query.get_or_404(id)
    return dato


@bp.route('/list')
@login_required
def index():
    p = request.args.get('p', 1, type=int)
    datos = db.paginate(db.select(ProductoLote).order_by(ProductoLote.nombre.desc()),
                        per_page=5, page=p)
    return render_template('producto_lote/index.html', datos=datos)


@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():

    unidades = (Unidad.query
                .filter_by(esta_activo=True)
                .order_by(Unidad.nombre).all())

    if request.method == 'POST':
        sku = request.form['sku']
        nombre = request.form['nombre']
        categoria_producto_lote_id = request.form['categoria-producto_lote']
        unidad_id = request.form['unidad']
        cantidad_total = request.form['cantidad-total']
        costo = request.form['costo']
        porcentaje_impuesto = request.form['porcentaje-impuesto']
        redondeo = request.form['redondeo']
        utilildad_es_porcentaje = request.form.get('modo-utilidad') == 'porcentaje'
        esta_activo = request.form.get('esta-activo') == 'on'
        porcentaje_utilidad = request.form['utilidad-porcentaje']
        monto_utilidad = request.form['utilidad-monto']



        producto_lote = ProductoLote(sku=sku,
                            nombre=nombre,
                            categoria_producto_lote_id=categoria_producto_lote_id,
                            unidad_id=unidad_id,
                            cantidad_total=cantidad_total,
                            costo=costo,
                            porcentaje_impuesto=porcentaje_impuesto,
                            redondeo=redondeo,
                            utilildad_es_porcentaje=utilildad_es_porcentaje,
                            porcentaje_utilidad=porcentaje_utilidad,
                            monto_utilidad=monto_utilidad,
                            esta_activo=esta_activo
                            )

        db.session.add(producto_lote)
        id: int = -1
        # db.session.commit()

        try:
            db.session.commit()
            id = producto_lote.id
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

        return redirect(url_for('producto_lote.view',id=id))

    return render_template('producto_lote/create.html', unidades=unidades)


@bp.route('/update/<int:id>', methods=['GET', 'POST'])
@login_required
def update(id):
    producto_lote = get(id)

    unidades = (Unidad.query
                .filter_by(esta_activo=True)
                .order_by(Unidad.nombre).all())

    if request.method == 'POST':
        producto_lote.sku = request.form['sku']
        producto_lote.categoria_producto_lote_id = request.form['categoria-producto_lote']
        producto_lote.nombre = request.form['nombre']
        producto_lote.unidad_id = request.form['unidad']
        producto_lote.cantidad_total = request.form['cantidad-total']
        producto_lote.costo = request.form['costo']
        producto_lote.porcentaje_impuesto = request.form['porcentaje-impuesto']
        producto_lote.redondeo = request.form['redondeo']
        utilildad_es_porcentaje = request.form.get('modo-utilidad') == 'porcentaje'
        producto_lote.utilildad_es_porcentaje = utilildad_es_porcentaje
        producto_lote.esta_activo = request.form.get('esta-activo') == 'on'
        producto_lote.porcentaje_utilidad = request.form['utilidad-porcentaje']
        producto_lote.monto_utilidad = request.form['utilidad-monto']

        id: int = producto_lote.id

        db.session.commit()

        return redirect(url_for('producto_lote.view',id=id))

    return render_template('producto_lote/update.html', dato=producto_lote,
                           unidades=unidades)


@bp.route('/view/<int:id>')
@login_required
def view(id):
    producto_lote = get(id)
    return render_template('producto_lote/view.html', dato=producto_lote)


@bp.route('/delete/<int:id>', methods=['GET', 'POST'])
def delete(id):
    producto_lote = get(id)

    if request.method == 'POST':
        producto_lote = get(id)
        db.session.delete(producto_lote)
        db.session.commit()
        return redirect(url_for('producto_lote.index'))

    return render_template('producto_lote/delete.html', dato=producto_lote)
