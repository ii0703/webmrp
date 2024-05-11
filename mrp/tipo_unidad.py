from flask import Blueprint, render_template, request, redirect, url_for, g
from .models import TipoUnidad
from mrp import db
from mrp.auth import login_required

bp = Blueprint('tipo_unidad', __name__, url_prefix='/tipo-unidad')

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
        codigo = request.form['codigo']
        nombre = request.form['nombre']
        esta_activo = request.form.get('esta_activo') == 'on'

        tipo_unidad = TipoUnidad(codigo=codigo, nombre=nombre, esta_activo=esta_activo)

        db.session.add(tipo_unidad)
        db.session.commit()

        return redirect(url_for('tipo_unidad.index'))

    return render_template('tipo_unidad/create.html')


@bp.route('/update/<int:id>', methods=['GET', 'POST'])
@login_required
def update(id):
    tipo_unidad = get(id)

    if request.method == 'POST':
        tipo_unidad.codigo = request.form['codigo']
        tipo_unidad.nombre = request.form['nombre']
        tipo_unidad.esta_activo = request.form.get('esta_activo') == 'on'

        db.session.commit()

        return redirect(url_for('tipo_unidad.index'))

    return render_template('tipo_unidad/update.html', tipo_unidad = tipo_unidad)

@bp.route('/delete/<int:id>')
@login_required
def delete(id):
    tipo_unidad = get(id)
    db.session.delete(tipo_unidad)
    db.session.commit()
    return redirect(url_for('tipo_unidad.index'))
