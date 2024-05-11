from flask import Blueprint, render_template, request, redirect, url_for, g
from .models import CategoriaProducto
from mrp import db
from mrp.auth import login_required

bp = Blueprint('categoria_producto', __name__, url_prefix='/categoria-producto')

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
        codigo = request.form['codigo']
        nombre = request.form['nombre']
        esta_activo = request.form.get('esta_activo') == 'on'

        categoria_producto = CategoriaProducto(codigo=codigo, nombre=nombre, esta_activo=esta_activo)

        db.session.add(categoria_producto)
        db.session.commit()

        return redirect(url_for('categoria_producto.index'))

    return render_template('categoria_producto/create.html')


@bp.route('/update/<int:id>', methods=['GET', 'POST'])
@login_required
def update(id):
    categoria_producto = get(id)

    if request.method == 'POST':
        categoria_producto.codigo = request.form['codigo']
        categoria_producto.nombre = request.form['nombre']
        categoria_producto.esta_activo = request.form.get('esta_activo') == 'on'

        db.session.commit()

        return redirect(url_for('categoria_producto.index'))

    return render_template('categoria_producto/update.html', categoria_producto = categoria_producto)

@bp.route('/delete/<int:id>')
@login_required
def delete(id):
    categoria_producto = get(id)
    db.session.delete(categoria_producto)
    db.session.commit()
    return redirect(url_for('categoria_producto.index'))
