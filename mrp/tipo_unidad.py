from flask import Blueprint, render_template, request, redirect, url_for, g, abort
from mrp.auth import login_required
from .models import TipoUnidad
from mrp import db
from sqlite3 import IntegrityError

bp = Blueprint('tipo_unidad', __name__, url_prefix='/tipo_unidad')


def get(id):
    dato = TipoUnidad.query.get_or_404(id)
    return dato


@bp.route('/list')
@login_required
def index():
    p = request.args.get('p', 1, type=int)
    datos = db.paginate(db.select(TipoUnidad).order_by(TipoUnidad.nombre.desc()),
                        per_page=5, page=p)
    return render_template('tipo_unidad/index.html', datos=datos)


@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    if request.method == 'POST':
        codigo: str = request.form['codigo']
        nombre: str = request.form['nombre']
        esta_activo: bool = request.form.get('esta-activo', '') == 'on'

        tipo_unidad = TipoUnidad(codigo=codigo,
                      nombre=nombre,
                      esta_activo=esta_activo
                      )

        db.session.add(tipo_unidad)
        id:int = -1
        try:
            db.session.commit()
            id = tipo_unidad.id
            print(id)
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

        return redirect(url_for('tipo_unidad.view',id=id))

    return render_template('tipo_unidad/create.html')


@bp.route('/update/<int:id>', methods=['GET', 'POST'])
@login_required
def update(id):
    tipo_unidad = get(id)

    if request.method == 'POST':
        tipo_unidad.codigo = request.form['codigo']
        tipo_unidad.nombre = request.form['nombre']

        tipo_unidad.esta_activo = request.form.get('esta-activo') == 'on'

        id:int = tipo_unidad.id

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

        return redirect(url_for('tipo_unidad.view',id=id))

    return render_template('tipo_unidad/update.html', dato=tipo_unidad)


@bp.route('/view/<int:id>')
@login_required
def view(id):
    tipo_unidad = get(id)
    return render_template('tipo_unidad/view.html', dato=tipo_unidad)


@bp.route('/delete/<int:id>', methods=['GET', 'POST'])
def delete(id):
    tipo_unidad = get(id)

    if request.method == 'POST':
        tipo_unidad = get(id)
        db.session.delete(tipo_unidad)
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
        return redirect(url_for('tipo_unidad.index'))

    return render_template('tipo_unidad/delete.html', dato=tipo_unidad)
