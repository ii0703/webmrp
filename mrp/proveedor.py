from flask import Blueprint, render_template, request, redirect, url_for, g, abort
from mrp.auth import login_required
from .models import Proveedor, Lugar, Unidad
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

        proveedor = Proveedor(identificacion=identificacion,
                          lugar_id=lugar_id,
                          nombre=nombre,
                          correo_electronico=correo_electronico,
                          telefono = telefono,
                          es_persona_fisica = es_persona_fisica,
                          esta_activo=esta_activo
                          )

        db.session.add(proveedor)
        id: int = -1
        # db.session.commit()

        try:
            db.session.commit()
            id = proveedor.id
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

        return redirect(url_for('proveedor.view', id=id))

    return render_template('proveedor/create.html', lugares=lugares)


@bp.route('/update/<int:id>', methods=['GET', 'POST'])
@login_required
def update(id):
    proveedor = get(id)
    lugares = (Lugar
               .query.filter_by(esta_activo=True)
               .order_by(Lugar.nombre).all())

    if request.method == 'POST':
        proveedor.identificacion = request.form['identificacion']
        proveedor.lugar_id = request.form['lugar']
        proveedor.nombre = request.form['nombre']
        proveedor.correo_electronico = request.form['correo-electronico']
        proveedor.telefono = request.form['telefono']
        proveedor.es_persona_fisica = request.form.get('es-persona-fisica') == 'on'
        proveedor.esta_activo = request.form.get('esta-activo') == 'on'

        db.session.commit()

        return redirect(url_for('proveedor.view', id=id))

    return render_template('proveedor/update.html', dato=proveedor, lugares=lugares)


@bp.route('/view/<int:id>')
@login_required
def view(id):
    proveedor = get(id)
    return render_template('proveedor/view.html', dato=proveedor)


@bp.route('/delete/<int:id>', methods=['GET', 'POST'])
def delete(id):
    proveedor = get(id)

    if request.method == 'POST':
        proveedor = get(id)
        db.session.delete(proveedor)
        db.session.commit()
        return redirect(url_for('proveedor.index'))

    return render_template('proveedor/delete.html', dato=proveedor)
