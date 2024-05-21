from flask import Blueprint, render_template, request, redirect, url_for, g, abort
from mrp.auth import login_required
from .models import CategoriaMateriaPrima
from mrp import db
from sqlite3 import IntegrityError

bp = Blueprint('categoria_materia_prima', __name__, url_prefix='/categoria_materia_prima')


def get(id):
    dato = CategoriaMateriaPrima.query.get_or_404(id)
    return dato


@bp.route('/list')
@login_required
def index():
    p = request.args.get('p', 1, type=int)
    datos = db.paginate(db.select(CategoriaMateriaPrima).order_by(CategoriaMateriaPrima.nombre.desc()),
                        per_page=5, page=p)
    return render_template('categoria_materia_prima/index.html', datos=datos)


@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    if request.method == 'POST':
        codigo: str = request.form['codigo']
        nombre: str = request.form['nombre']
        esta_activo: bool = request.form.get('esta-activo', '') == 'on'

        categoria_materia_prima = CategoriaMateriaPrima(codigo=codigo,
                      nombre=nombre,
                      esta_activo=esta_activo
                      )

        db.session.add(categoria_materia_prima)
        id:int = -1
        try:
            db.session.commit()
            id = categoria_materia_prima.id
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

        return redirect(url_for('categoria_materia_prima.view',id=id))

    return render_template('categoria_materia_prima/create.html')


@bp.route('/update/<int:id>', methods=['GET', 'POST'])
@login_required
def update(id):
    categoria_materia_prima = get(id)

    if request.method == 'POST':
        categoria_materia_prima.codigo = request.form['codigo']
        categoria_materia_prima.nombre = request.form['nombre']

        categoria_materia_prima.esta_activo = request.form.get('esta-activo') == 'on'

        id:int = categoria_materia_prima.id

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

        return redirect(url_for('categoria_materia_prima.view',id=id))

    return render_template('categoria_materia_prima/update.html', dato=categoria_materia_prima)


@bp.route('/view/<int:id>')
@login_required
def view(id):
    categoria_materia_prima = get(id)
    return render_template('categoria_materia_prima/view.html', dato=categoria_materia_prima)


@bp.route('/delete/<int:id>', methods=['GET', 'POST'])
def delete(id):
    categoria_materia_prima = get(id)

    if request.method == 'POST':
        categoria_materia_prima = get(id)
        db.session.delete(categoria_materia_prima)
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
        return redirect(url_for('categoria_materia_prima.index'))

    return render_template('categoria_materia_prima/delete.html', dato=categoria_materia_prima)
