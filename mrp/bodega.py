from flask import Blueprint, render_template, request, redirect, url_for, g, abort
from mrp.auth import login_required
from .models import Lugar, Bodega
from mrp import db
from sqlite3 import IntegrityError

bp = Blueprint('bodega', __name__, url_prefix='/bodega')


def get(id):
    dato = Bodega.query.get_or_404(id)
    return dato


@bp.route('/list')
@login_required
def index():
    p = request.args.get('p', 1, type=int)
    datos = db.paginate(db.select(Bodega).order_by(Bodega.nombre.desc()),
                        per_page=5, page=p)
    return render_template('bodega/index.html', datos=datos)


@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    lugares = Lugar.query.where(Lugar.esta_activo == True).order_by(Lugar.nombre.asc()).all()
    if request.method == 'POST':
        codigo: str = request.form['codigo']
        nombre: str = request.form['nombre']
        esta_activo: bool = request.form.get('esta-activo', '') == 'on'
        lugar_id: int = request.form['lugar']
        bodega = Bodega(codigo=codigo,
                        nombre=nombre,
                        esta_activo=esta_activo,
                        lugar_id=lugar_id)

        db.session.add(bodega)
        id: int = -1
        try:
            db.session.commit()
            id = bodega.id
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

        return redirect(url_for('bodega.view', id=id))

    return render_template('bodega/create.html', lugares=lugares)


@bp.route('/update/<int:id>', methods=['GET', 'POST'])
@login_required
def update(id):
    bodega = get(id)
    lugares = Lugar.query.where(Lugar.esta_activo == True).order_by(Lugar.nombre.asc()).all()
    if request.method == 'POST':
        bodega.codigo = request.form['codigo']
        bodega.nombre = request.form['nombre']
        bodega.esta_activo = request.form.get('esta_activo') == 'on'
        bodega.lugar_id = request.form['lugar']

        id: int = bodega.id

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

        return redirect(url_for('bodega.view', id=id))

    return render_template('bodega/update.html', dato=bodega, lugares=lugares)


@bp.route('/view/<int:id>')
@login_required
def view(id):
    bodega = get(id)
    return render_template('bodega/view.html', dato=bodega)


@bp.route('/delete/<int:id>', methods=['GET', 'POST'])
def delete(id):
    bodega = get(id)

    if request.method == 'POST':
        bodega = get(id)
        db.session.delete(bodega)
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
        return redirect(url_for('bodega.index'))

    return render_template('bodega/delete.html', dato=bodega)
