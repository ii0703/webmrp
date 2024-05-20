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
        identificacion = request.form['identificacion']
        lugar_id = request.form['lugar']
        nombre = request.form['nombre']
        correo_electronico = request.form['correo-electronico']
        telefono = request.form['telefono']
        es_persona_fisica = request.form.get('es-persona-fisica') == 'on'
        esta_activo = request.form.get('esta-activo') == 'on'

        cliente = Cliente(identificacion=identificacion,
                          lugar_id=lugar_id,
                          nombre=nombre,
                          correo_electronico=correo_electronico,
                          telefono = telefono,
                          es_persona_fisica = es_persona_fisica,
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

        return redirect(url_for('cliente.view', id=id))

    return render_template('cliente/create.html', lugares=lugares)


@bp.route('/update/<int:id>', methods=['GET', 'POST'])
@login_required
def update(id):
    cliente = get(id)
    lugares = (Lugar
               .query.filter_by(esta_activo=True)
               .order_by(Lugar.nombre).all())

    if request.method == 'POST':
        cliente.identificacion = request.form['identificacion']
        cliente.lugar_id = request.form['lugar']
        cliente.nombre = request.form['nombre']
        cliente.correo_electronico = request.form['correo-electronico']
        cliente.telefono = request.form['telefono']
        cliente.es_persona_fisica = request.form.get('es-persona-fisica') == 'on'
        cliente.esta_activo = request.form.get('esta-activo') == 'on'

        db.session.commit()

        return redirect(url_for('cliente.view', id=id))

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
