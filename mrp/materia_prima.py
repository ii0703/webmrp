from flask import Blueprint, render_template, request, redirect, url_for, g, abort
from flask import (send_file, stream_with_context, Response)
from io import BytesIO, StringIO
import csv
from mrp.auth import login_required
from .models import MateriaPrima, CategoriaMateriaPrima, Unidad
from mrp import db
from sqlite3 import IntegrityError

bp = Blueprint('materia_prima', __name__, url_prefix='/materia_prima')


def get(id):
    dato = MateriaPrima.query.get_or_404(id)
    return dato


@bp.route('/list', methods=['GET'])
@login_required
def index():
    pagina = request.args.get('pagina', 1, type=int)
    busqueda = request.args.get('busqueda', '', type=str)
    if busqueda == '':
        datos = db.paginate(db.select(MateriaPrima).order_by(MateriaPrima.nombre.desc()), per_page=5, page=pagina)
    else:
        datos = db.paginate(db.select(MateriaPrima).filter(MateriaPrima.nombre.ilike(f'%{busqueda}%')), per_page=5,
                            page=pagina)
    return render_template('materia_prima/index.html', datos=datos, pagina=pagina, busqueda=busqueda)


def decode_utf8(input_iterator):
    for l in input_iterator:
        yield l.decode('utf-8')


@bp.route('/csv_import_all', methods=['GET', 'POST'])
def csv_import_all():
    if request.method == 'POST':
        file = request.files['file']
        reader = csv.DictReader(decode_utf8(file))
        for row in reader:
            print(row)
        return redirect(url_for('materia_prima.index'))
    return '''
<!DOCTYPE html>
<html lang="en">
<head>
	<meta charset="UTF-8">
	<meta http-equiv="X-UA-Compatible" content="IE=edge">
	<meta name="viewport" content="width=device-width, initial-scale=1.0">
	<title>File Upload Example</title>
	<style>
	.ok{

		font-size: 20px;
	}
	.op{
		font-size: 20px;
		margin-left: -70px;
		font-weight: bold;
		background-color: yellow;
		border-radius: 5px;
		cursor: pointer;
	}


	</style>
</head>
<body>
	<div class="center">
		<h1> Uploading and Returning Files With a Database in Flask </h1>
		<form method="POST" enctype="multipart/form-data">
			<input class="ok" type="file" name="file">
			<button class="op">Submit</button>
		</form>
	</div>

</body>
</html>

    '''


@bp.route('/csv_export_all')
def csv_export_all():
    file_output = StringIO()
    csv_writer = csv.writer(file_output, delimiter=',',
                            quoting=csv.QUOTE_ALL)
    csv_writer.writerow(['Identificación', 'Nombre', 'Tipo'])
    datos = MateriaPrima.query.order_by(MateriaPrima.nombre.desc()).all()
    csv_items = [[dato.identificacion, dato.nombre, dato.lugar.nombre, dato.correo_electronico, dato.telefono,
                  'Persona física' if dato.es_persona_fisica else 'Empresa',
                  'Activo' if dato.esta_activo else 'Inactivo'] for dato in datos]
    for item in csv_items:
        csv_writer.writerow(item)
    file_output.seek(0)
    response = Response(file_output)
    response.headers['Content-Type'] = 'text/csv; charset=utf-8'
    response.headers['Content-Disposition'] = 'attachment; filename="materia_prima_export_all.csv"'
    return response


@bp.route('/csv_template')
def csv_template():
    # @stream_with_context
    # def generate():
    #     yield str.encode('Identificación', 'Nombre', 'Tipo', 'utf-8')

    # response = Response(generate())
    ##
    file_output = StringIO()
    csv_writer = csv.writer(file_output, delimiter=',',
                            quoting=csv.QUOTE_ALL)
    csv_writer.writerow(['Identificación', 'Nombre', 'Tipo'])
    csv_items = [['Identificación', 'Nombre', 'Tipo']]
    for item in csv_items:
        csv_writer.writerow(item)
    file_output.seek(0)
    ##
    response = Response(file_output)
    response.headers['Content-Type'] = 'text/csv; charset=utf-8'
    response.headers['Content-Disposition'] = 'attachment; filename="materia_prima_template.csv"'
    return response


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

        return redirect(url_for('materia_prima.view', id=id))

    return render_template('materia_prima/create.html', categorias_materia_prima=categorias_materia_prima,
                           unidades=unidades)


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

        return redirect(url_for('materia_prima.view', id=id))

    return render_template('materia_prima/update.html', dato=materia_prima,
                           categorias_materia_prima=categorias_materia_prima,
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
