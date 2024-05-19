from flask import Blueprint, render_template, request, redirect, url_for, g, abort
from mrp.auth import login_required
from .models import TipoUnidad, Unidad
from mrp import db
from sqlite3 import IntegrityError

bp = Blueprint('unidad', __name__, url_prefix='/unidad')


def get(id):
    dato = Unidad.query.get_or_404(id)
    return dato


@bp.route('/list')
@login_required
def index():
    p = request.args.get('p', 1, type=int)
    datos = db.paginate(db.select(Unidad).order_by(Unidad.nombre.desc()),
                        per_page=5, page=p)
    return render_template('unidad/index.html', datos=datos)


@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    tipos = TipoUnidad.query.where(TipoUnidad.esta_activo == True).order_by(TipoUnidad.nombre.asc()).all()
    if request.method == 'POST':
        simbolo: str = request.form['simbolo']
        nombre: str = request.form['nombre']
        esta_activo: bool = request.form.get('esta-activo', '') == 'on'
        tipo_unidad_id: int = request.form['tipo-unidad']
        unidad = Unidad(simbolo=simbolo,
                        nombre=nombre,
                        esta_activo=esta_activo,
                        tipo_unidad_id=tipo_unidad_id)

        db.session.add(unidad)
        id: int = -1
        try:
            db.session.commit()
            id = unidad.id
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

        return redirect(url_for('unidad.view', id=id))

    return render_template('unidad/create.html', tipos=tipos)


@bp.route('/update/<int:id>', methods=['GET', 'POST'])
@login_required
def update(id):
    unidad = get(id)
    tipos = TipoUnidad.query.where(TipoUnidad.esta_activo == True).order_by(TipoUnidad.nombre.asc()).all()
    if request.method == 'POST':
        unidad.simbolo = request.form['simbolo']
        unidad.nombre = request.form['nombre']
        unidad.esta_activo = request.form.get('esta_activo') == 'on'
        unidad.tipo_unidad_id = request.form['tipo-unidad']

        id: int = unidad.id

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

        return redirect(url_for('unidad.view', id=id))

    return render_template('unidad/update.html', dato=unidad, tipos=tipos)


@bp.route('/view/<int:id>')
@login_required
def view(id):
    unidad = get(id)
    return render_template('unidad/view.html', dato=unidad)


@bp.route('/delete/<int:id>', methods=['GET', 'POST'])
def delete(id):
    unidad = get(id)

    if request.method == 'POST':
        unidad = get(id)
        db.session.delete(unidad)
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
        return redirect(url_for('unidad.index'))

    return render_template('unidad/delete.html', dato=unidad)
