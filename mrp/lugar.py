from flask import Blueprint, render_template, request, redirect, url_for, g, abort
from mrp.auth import login_required
from .models import Lugar,Unidad
from mrp import db
from sqlite3 import IntegrityError

bp = Blueprint('lugar', __name__, url_prefix='/lugar')


def get(id):
    dato = Lugar.query.get_or_404(id)
    return dato


@bp.route('/list')
@login_required
def index():
    p = request.args.get('p', 1, type=int)
    datos = db.paginate(db.select(Lugar).order_by(Lugar.nombre.desc()),
                        per_page=5, page=p)
    return render_template('lugar/index.html', datos=datos)


@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    # categorias_lugar = (CategoriaLugar
    #                        .query.filter_by(esta_activo=True)
    #                        .order_by(CategoriaLugar.nombre).all())
    # unidades = (Unidad.query
    #             .filter_by(esta_activo=True)
    #             .order_by(Unidad.nombre).all())

    if request.method == 'POST':
        sku = request.form['sku']
        categoria_lugar_id = request.form['categoria-lugar']
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

        lugar = Lugar(sku=sku,
                            nombre=nombre,
                            categoria_lugar_id=categoria_lugar_id,
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

        db.session.add(lugar)

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

        return redirect(url_for('lugar.index'))

    return render_template('lugar/create.html')


@bp.route('/update/<int:id>', methods=['GET', 'POST'])
@login_required
def update(id):
    lugar = get(id)
    # categorias_lugar = (CategoriaLugar
    #                        .query.filter_by(esta_activo=True)
    #                        .order_by(CategoriaLugar.nombre).all())
    unidades = (Unidad.query
                .filter_by(esta_activo=True)
                .order_by(Unidad.nombre).all())

    if request.method == 'POST':
        lugar.sku = request.form['sku']
        lugar.categoria_lugar_id = request.form['categoria-lugar']
        lugar.nombre = request.form['nombre']
        lugar.unidad_id = request.form['unidad']
        lugar.cantidad_total = request.form['cantidad-total']
        lugar.costo = request.form['costo']
        lugar.porcentaje_impuesto = request.form['porcentaje-impuesto']
        lugar.redondeo = request.form['redondeo']
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

        lugar.utilidad_porcentaje = utilidad_porcentaje
        lugar.utilidad_monto = utilidad_monto
        lugar.utilildad_es_porcentaje = utilildad_es_porcentaje

        lugar.esta_activo = request.form.get('esta-activo') == 'on'

        db.session.commit()

        return redirect(url_for('lugar.index'))

    # return render_template('lugar/update.html', lugar=lugar, categorias_lugar=categorias_lugar,
    #                        unidades=unidades)


@bp.route('/view/<int:id>')
@login_required
def view(id):
    lugar = get(id)
    return render_template('lugar/view.html', lugar=lugar)


@bp.route('/delete/<int:id>', methods=['GET', 'POST'])
def delete(id):
    lugar = get(id)

    if request.method == 'POST':
        lugar = get(id)
        db.session.delete(lugar)
        db.session.commit()
        return redirect(url_for('lugar.index'))

    return render_template('lugar/delete.html', lugar=lugar)
