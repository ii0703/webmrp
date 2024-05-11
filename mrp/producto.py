from flask import Blueprint, render_template, request, redirect, url_for, g
from mrp.auth import login_required
from .models import Producto
from mrp import db

bp = Blueprint('producto', __name__, url_prefix='/producto')

def get(id):
    dato = Producto.query.get_or_404(id)
    return dato

@bp.route('/list')
@login_required
def index():
    p = request.args.get('p', 1, type=int)
    datos = db.paginate(db.select(Producto).order_by(Producto.nombre.desc()),
                        per_page=5, page=p)
    return render_template('producto/index.html', datos=datos)


@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    if request.method == 'POST':
        codigo = request.form['codigo']
        nombre = request.form['nombre']
        precio = request.form['precio']

        producto = Producto(codigo=codigo, nombre=nombre, precio=precio)

        db.session.add(producto)
        db.session.commit()

        return redirect(url_for('producto.index'))

    return render_template('producto/create.html')


@bp.route('/update/<int:id>', methods=['GET', 'POST'])
@login_required
def update(id):
    producto = get(id)

    if request.method == 'POST':
        producto.codigo = request.form['codigo']
        producto.nombre = request.form['nombre']
        producto.precio = request.form['precio']

        db.session.commit()

        return redirect(url_for('producto.index'))

    return render_template('producto/update.html', producto = producto)

@bp.route('/delete/<int:id>')
@login_required
def delete(id):
    producto = get(id)
    db.session.delete(producto)
    db.session.commit()
    return redirect(url_for('producto.index'))
