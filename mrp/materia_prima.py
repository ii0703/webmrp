from flask import Blueprint, render_template, request, redirect, url_for, g, abort
from mrp.auth import login_required
from .models import MateriaPrima, CategoriaMateriaPrima, Unidad
from mrp import db
from sqlite3 import IntegrityError

bp = Blueprint('materia_prima', __name__, url_prefix='/materia_prima')


def get(id):
    dato = MateriaPrima.query.get_or_404(id)
    return dato


@bp.route('/list')
@login_required
def index():
    p = request.args.get('p', 1, type=int)
    datos = db.paginate(db.select(MateriaPrima).order_by(MateriaPrima.nombre.desc()),
                        per_page=5, page=p)
    return render_template('materia_prima/index.html', datos=datos)


@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    categorias_materia_prima = (CategoriaMateriaPrima
                           .query.filter_by(esta_activo=True)
                           .order_by(CategoriaMateriaPrima.nombre).all())
    unidades = (Unidad.query
                .filter_by(esta_activo=True)
                .order_by(Unidad.nombre).all())

    if request.method == 'POST':
        sku = request.form['sku']
        nombre = request.form['nombre']
        categoria_materia_prima_id = request.form['categoria-materia-prima']
        unidad_id = request.form['unidad']
        cantidad_total = request.form['cantidad-total']
        costo = request.form['costo']
        porcentaje_impuesto = request.form['porcentaje-impuesto']
        esta_activo = request.form.get('esta-activo') == 'on'


        materia_prima = MateriaPrima(sku=sku,
                            nombre=nombre,
                            categoria_materia_prima_id=categoria_materia_prima_id,
                            unidad_id=unidad_id,
                            cantidad_total=cantidad_total,
                            costo=costo,
                            porcentaje_impuesto=porcentaje_impuesto,
                            esta_activo=esta_activo
                            )

        db.session.add(materia_prima)
        id: int = -1
        # db.session.commit()

        try:
            db.session.commit()
            id = materia_prima.id
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

        return redirect(url_for('materia_prima.view',id=id))

    return render_template('materia_prima/create.html', categorias_materia_prima=categorias_materia_prima, unidades=unidades)


@bp.route('/update/<int:id>', methods=['GET', 'POST'])
@login_required
def update(id):
    materia_prima = get(id)
    categorias_materia_prima = (CategoriaMateriaPrima
                           .query.filter_by(esta_activo=True)
                           .order_by(CategoriaMateriaPrima.nombre).all())
    unidades = (Unidad.query
                .filter_by(esta_activo=True)
                .order_by(Unidad.nombre).all())

    if request.method == 'POST':
        materia_prima.sku = request.form['sku']
        materia_prima.categoria_materia_prima_id = request.form['categoria-materia-prima']
        materia_prima.nombre = request.form['nombre']
        materia_prima.unidad_id = request.form['unidad']
        materia_prima.cantidad_total = request.form['cantidad-total']
        materia_prima.costo = request.form['costo']
        materia_prima.porcentaje_impuesto = request.form['porcentaje-impuesto']
        materia_prima.esta_activo = request.form.get('esta-activo') == 'on'

        id: int = materia_prima.id

        db.session.commit()

        return redirect(url_for('materia_prima.view',id=id))

    return render_template('materia_prima/update.html', dato=materia_prima, categorias_materia_prima=categorias_materia_prima,
                           unidades=unidades)


@bp.route('/view/<int:id>')
@login_required
def view(id):
    materia_prima = get(id)
    return render_template('materia_prima/view.html', dato=materia_prima)


@bp.route('/delete/<int:id>', methods=['GET', 'POST'])
def delete(id):
    materia_prima = get(id)

    if request.method == 'POST':
        materia_prima = get(id)
        db.session.delete(materia_prima)
        db.session.commit()
        return redirect(url_for('materia_prima.index'))

    return render_template('materia_prima/delete.html', dato=materia_prima)
