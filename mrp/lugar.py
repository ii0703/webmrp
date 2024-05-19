from flask import Blueprint, render_template, request, redirect, url_for, g, abort
from mrp.auth import login_required
from .models import Lugar, Unidad
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
    if request.method == 'POST':
        codigo: str = request.form['codigo']
        nombre: str = request.form['nombre']
        esta_activo: bool = request.form.get('esta-activo', '') == 'on'

        lugar = Lugar(codigo=codigo,
                      nombre=nombre,
                      esta_activo=esta_activo
                      )

        db.session.add(lugar)

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

    if request.method == 'POST':
        lugar.codigo = request.form['codigo']
        lugar.nombre = request.form['nombre']

        lugar.esta_activo = request.form.get('esta-activo') == 'on'

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

    return render_template('lugar/update.html', dato=lugar)


@bp.route('/view/<int:id>')
@login_required
def view(id):
    lugar = get(id)
    return render_template('lugar/view.html', dato=lugar)


@bp.route('/delete/<int:id>', methods=['GET', 'POST'])
def delete(id):
    lugar = get(id)

    if request.method == 'POST':
        lugar = get(id)
        db.session.delete(lugar)
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

    return render_template('lugar/delete.html', lugar=lugar)
