from flask import Blueprint, render_template, request, redirect, url_for, g, abort
from mrp.auth import login_required
from .models import CategoriaProducto
from mrp import db
from sqlite3 import IntegrityError

bp = Blueprint('categoria_producto', __name__, url_prefix='/categoria_producto')


def get(id):
    dato = CategoriaProducto.query.get_or_404(id)
    return dato


@bp.route('/list')
@login_required
def index():
    p = request.args.get('p', 1, type=int)
    datos = db.paginate(db.select(CategoriaProducto).order_by(CategoriaProducto.nombre.desc()),
                        per_page=5, page=p)
    return render_template('categoria_producto/index.html', datos=datos)


@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    if request.method == 'POST':
        codigo: str = request.form['codigo']
        nombre: str = request.form['nombre']
        esta_activo: bool = request.form.get('esta-activo', '') == 'on'

        categoria_producto = CategoriaProducto(codigo=codigo,
                      nombre=nombre,
                      esta_activo=esta_activo
                      )

        db.session.add(categoria_producto)
        id:int = -1
        try:
            db.session.commit()
            id = categoria_producto.id
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

        return redirect(url_for('categoria_producto.view',id=id))

    return render_template('categoria_producto/create.html')


@bp.route('/update/<int:id>', methods=['GET', 'POST'])
@login_required
def update(id):
    categoria_producto = get(id)

    if request.method == 'POST':
        categoria_producto.codigo = request.form['codigo']
        categoria_producto.nombre = request.form['nombre']

        categoria_producto.esta_activo = request.form.get('esta-activo') == 'on'

        id:int = categoria_producto.id

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

        return redirect(url_for('categoria_producto.view',id=id))

    return render_template('categoria_producto/update.html', dato=categoria_producto)


@bp.route('/view/<int:id>')
@login_required
def view(id):
    categoria_producto = get(id)
    return render_template('categoria_producto/view.html', dato=categoria_producto)


@bp.route('/delete/<int:id>', methods=['GET', 'POST'])
def delete(id):
    categoria_producto = get(id)

    if request.method == 'POST':
        categoria_producto = get(id)
        db.session.delete(categoria_producto)
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
        return redirect(url_for('categoria_producto.index'))

    return render_template('categoria_producto/delete.html', dato=categoria_producto)
