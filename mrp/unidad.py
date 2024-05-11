from flask import Blueprint, render_template, request, redirect, url_for, g
from .models import Unidad, TipoUnidad
from mrp import db
from mrp.auth import login_required

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
    tipos = TipoUnidad.query.order_by(TipoUnidad.nombre.asc()).all()

    if request.method == 'POST':
        simbolo = request.form['simbolo']
        nombre = request.form['nombre']
        esta_activo = request.form.get('esta_activo') == 'on'
        tipo_unidad_id = request.form['tipo-unidad']
        # tipo_unidad = TipoUnidad.query.get_or_404(tipo_unidad_id)


        unidad = Unidad(simbolo=simbolo, nombre=nombre, esta_activo=esta_activo, tipo_unidad_id= tipo_unidad_id)

        db.session.add(unidad)
        db.session.commit()

        return redirect(url_for('unidad.index'))

    return render_template('unidad/create.html', tipos=tipos)


@bp.route('/update/<int:id>', methods=['GET', 'POST'])
@login_required
def update(id):
    unidad = get(id)
    tipos = TipoUnidad.query.order_by(TipoUnidad.nombre.asc()).all()

    if request.method == 'POST':
        unidad.simbolo = request.form['simbolo']
        unidad.nombre = request.form['nombre']
        unidad.esta_activo = request.form.get('esta_activo') == 'on'
        unidad.tipo_unidad_id = request.form['tipo-unidad']

        db.session.commit()

        return redirect(url_for('unidad.index'))

    return render_template('unidad/update.html', unidad=unidad, tipos=tipos)


@bp.route('/delete/<int:id>')
@login_required
def delete(id):
    unidad = get(id)
    db.session.delete(unidad)
    db.session.commit()
    return redirect(url_for('unidad.index'))
