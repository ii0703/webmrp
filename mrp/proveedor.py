from flask import Blueprint, render_template, request, redirect, url_for, g, abort
from mrp.auth import login_required
from .models import Proveedor,Unidad
from mrp import db
from sqlite3 import IntegrityError

bp = Blueprint('proveedor', __name__, url_prefix='/proveedor')


def get(id):
    dato = Proveedor.query.get_or_404(id)
    return dato


@bp.route('/list')
@login_required
def index():
    p = request.args.get('p', 1, type=int)
    datos = db.paginate(db.select(Proveedor).order_by(Proveedor.nombre.desc()),
                        per_page=5, page=p)
    return render_template('proveedor/index.html', datos=datos)


@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    # categorias_proveedor = (CategoriaProveedor
    #                        .query.filter_by(esta_activo=True)
    #                        .order_by(CategoriaProveedor.nombre).all())
    # unidades = (Unidad.query
    #             .filter_by(esta_activo=True)
    #             .order_by(Unidad.nombre).all())

    if request.method == 'POST':
        sku = request.form['sku']
        categoria_proveedor_id = request.form['categoria-proveedor']
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

        proveedor = Proveedor(sku=sku,
                            nombre=nombre,
                            categoria_proveedor_id=categoria_proveedor_id,
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

        db.session.add(proveedor)

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

        return redirect(url_for('proveedor.index'))

    return render_template('proveedor/create.html')


@bp.route('/update/<int:id>', methods=['GET', 'POST'])
@login_required
def update(id):
    proveedor = get(id)
    # categorias_proveedor = (CategoriaProveedor
    #                        .query.filter_by(esta_activo=True)
    #                        .order_by(CategoriaProveedor.nombre).all())
    unidades = (Unidad.query
                .filter_by(esta_activo=True)
                .order_by(Unidad.nombre).all())

    if request.method == 'POST':
        proveedor.sku = request.form['sku']
        proveedor.categoria_proveedor_id = request.form['categoria-proveedor']
        proveedor.nombre = request.form['nombre']
        proveedor.unidad_id = request.form['unidad']
        proveedor.cantidad_total = request.form['cantidad-total']
        proveedor.costo = request.form['costo']
        proveedor.porcentaje_impuesto = request.form['porcentaje-impuesto']
        proveedor.redondeo = request.form['redondeo']
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

        proveedor.utilidad_porcentaje = utilidad_porcentaje
        proveedor.utilidad_monto = utilidad_monto
        proveedor.utilildad_es_porcentaje = utilildad_es_porcentaje

        proveedor.esta_activo = request.form.get('esta-activo') == 'on'

        db.session.commit()

        return redirect(url_for('proveedor.index'))

    # return render_template('proveedor/update.html', proveedor=proveedor, categorias_proveedor=categorias_proveedor,
    #                        unidades=unidades)


@bp.route('/view/<int:id>')
@login_required
def view(id):
    proveedor = get(id)
    return render_template('proveedor/view.html', proveedor=proveedor)


@bp.route('/delete/<int:id>', methods=['GET', 'POST'])
def delete(id):
    proveedor = get(id)

    if request.method == 'POST':
        proveedor = get(id)
        db.session.delete(proveedor)
        db.session.commit()
        return redirect(url_for('proveedor.index'))

    return render_template('proveedor/delete.html', proveedor=proveedor)
