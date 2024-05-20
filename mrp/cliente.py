from flask import Blueprint, render_template, request, redirect, url_for, g, abort
from mrp.auth import login_required
from .models import Cliente, Lugar, Unidad
from mrp import db
from sqlite3 import IntegrityError

bp = Blueprint('cliente', __name__, url_prefix='/cliente')


def get(id):
    dato = Cliente.query.get_or_404(id)
    return dato


@bp.route('/list')
@login_required
def index():
    p = request.args.get('p', 1, type=int)
    datos = db.paginate(db.select(Cliente).order_by(Cliente.nombre.desc()),
                        per_page=5, page=p)
    return render_template('cliente/index.html', datos=datos)


@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    lugares = (Lugar
                           .query.filter_by(esta_activo=True)
                           .order_by(Lugar.nombre).all())

    if request.method == 'POST':
        sku = request.form['sku']
        categoria_cliente_id = request.form['categoria-cliente']
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

        cliente = Cliente(sku=sku,
                            nombre=nombre,
                            categoria_cliente_id=categoria_cliente_id,
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

        db.session.add(cliente)
        id: int = -1
        # db.session.commit()

        try:
            db.session.commit()
            id = cliente.id
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

        return redirect(url_for('cliente.view',id=id))

    return render_template('cliente/create.html', lugares=lugares)


@bp.route('/update/<int:id>', methods=['GET', 'POST'])
@login_required
def update(id):
    cliente = get(id)
    lugares = (Lugar
                           .query.filter_by(esta_activo=True)
                           .order_by(Lugar.nombre).all())

    if request.method == 'POST':
        cliente.sku = request.form['sku']
        cliente.categoria_cliente_id = request.form['categoria-cliente']
        cliente.nombre = request.form['nombre']
        cliente.unidad_id = request.form['unidad']
        cliente.cantidad_total = request.form['cantidad-total']
        cliente.costo = request.form['costo']
        cliente.porcentaje_impuesto = request.form['porcentaje-impuesto']
        cliente.redondeo = request.form['redondeo']
        modo_utilidad = request.form['modo-utilidad']
        utilidad_monto = 0
        utilidad_porcentaje = 0
        utilildad_es_porcentaje = True

        id: int = cliente.id

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

        cliente.utilidad_porcentaje = utilidad_porcentaje
        cliente.utilidad_monto = utilidad_monto
        cliente.utilildad_es_porcentaje = utilildad_es_porcentaje

        cliente.esta_activo = request.form.get('esta-activo') == 'on'

        db.session.commit()

        return redirect(url_for('cliente.view',id=id))

    return render_template('cliente/update.html', dato=cliente, lugares=lugares)


@bp.route('/view/<int:id>')
@login_required
def view(id):
    cliente = get(id)
    return render_template('cliente/view.html', dato=cliente)


@bp.route('/delete/<int:id>', methods=['GET', 'POST'])
def delete(id):
    cliente = get(id)

    if request.method == 'POST':
        cliente = get(id)
        db.session.delete(cliente)
        db.session.commit()
        return redirect(url_for('cliente.index'))

    return render_template('cliente/delete.html', dato=cliente)
