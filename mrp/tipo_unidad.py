from flask import Blueprint, render_template, request, redirect, url_for, g, abort
from flask import (send_file, stream_with_context, Response, flash)
from io import BytesIO, StringIO
import csv
from mrp.auth import login_required
from .models import TipoUnidad
from mrp import db
from sqlite3 import IntegrityError

bp = Blueprint('tipo_unidad', __name__, url_prefix='/tipo_unidad')


def get(id):
    dato = TipoUnidad.query.get_or_404(id)
    return dato


@bp.route('/list', methods=['GET'])
@login_required
def index():
    pagina = request.args.get('pagina', 1, type=int)
    busqueda = request.args.get('busqueda', '', type=str)
    if busqueda == '':
        datos = db.paginate(db.select(TipoUnidad).order_by(TipoUnidad.nombre.desc()), per_page=5, page=pagina)
    else:
        datos = db.paginate(db.select(TipoUnidad).filter(TipoUnidad.nombre.ilike(f'%{busqueda}%')), per_page=5, page=pagina)
    return render_template('tipo_unidad/index.html', datos=datos, pagina=pagina, busqueda=busqueda)


def decode_utf8(input_iterator):
    for l in input_iterator:
        yield l.decode('utf-8')


@bp.route('/csv_import_all', methods=['GET', 'POST'])
def csv_import_all():
    if request.method == 'POST':
        file = request.files['file']
        reader = csv.DictReader(decode_utf8(file),
                                fieldnames=['codigo', 'nombre', 'estado'],
                                delimiter=';')
        # para saltar la primera línea del encabezado, dado que yo le mando los nombre
        next(reader)
        # Cargo todos los lugares existentes, por si existe un código previamente ignoralo
        lista_tipo_unidades = TipoUnidad.query.all()
        # convierto la lista en un diccionario (el código debe ser único)
        dict_tipo_unidades = {tipo_unidad.codigo: tipo_unidad for tipo_unidad in lista_tipo_unidades}

        nuevos = 0
        existentes = 0

        for row in reader:
            if row['codigo'] in dict_tipo_unidades:
                existentes = existentes + 1
            else:
                lugar = TipoUnidad(codigo=row['codigo'], nombre=row['nombre'],
                              esta_activo=row['estado'].lstrip().lower() == 'activo')
                db.session.add(lugar)

                nuevos = nuevos + 1

        if nuevos > 0:
            db.session.commit()
            flash('Datos nuevos {}'.format(nuevos))
        if existentes > 0:
            flash('Datos existentes: {}'.format(existentes))
        return redirect(url_for('tipo_unidad.index'))
    return '''
<!DOCTYPE html>
<html lang="en">
<head>
	<meta charset="UTF-8">
	<meta http-equiv="X-UA-Compatible" content="IE=edge">
	<meta name="viewport" content="width=device-width, initial-scale=1.0">
	<title>Importar tipos de unidades</title>
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
		<h1>Importar tipos de unidades</h1>
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
    csv_writer.writerow(['Identificación', 'Nombre', 'Lugar', 'Correo electrónico', 'Teléfono', 'Tipo', 'Estado'])
    datos = TipoUnidad.query.order_by(TipoUnidad.nombre.desc()).all()
    csv_items = [[dato.identificacion, dato.nombre, dato.lugar.nombre, dato.correo_electronico, dato.telefono,
                  'Persona física' if dato.es_persona_fisica else 'Empresa',
                  'Activo' if dato.esta_activo else 'Inactivo'] for dato in datos]
    for item in csv_items:
        csv_writer.writerow(item)
    file_output.seek(0)
    response = Response(file_output)
    response.headers['Content-Type'] = 'text/csv; charset=utf-8'
    response.headers['Content-Disposition'] = 'attachment; filename="tipo_unidad_export_all.csv"'
    return response


@bp.route('/csv_template')
def csv_template():
    # @stream_with_context
    # def generate():
    #     yield str.encode('Identificación, Nombre, Lugar, Correo electrónico, Teléfono, Tipo, Estado', 'utf-8')

    # response = Response(generate())
    ##
    file_output = StringIO()
    csv_writer = csv.writer(file_output, delimiter=',',
                            quoting=csv.QUOTE_ALL)
    csv_writer.writerow(['Identificación', 'Nombre', 'Lugar', 'Correo electrónico', 'Teléfono', 'Tipo', 'Estado'])
    csv_items = [['Identificación', 'Nombre', 'Lugar', 'Correo electrónico', 'Teléfono', 'Tipo', 'Estado']]
    for item in csv_items:
        csv_writer.writerow(item)
    file_output.seek(0)
    ##
    response = Response(file_output)
    response.headers['Content-Type'] = 'text/csv; charset=utf-8'
    response.headers['Content-Disposition'] = 'attachment; filename="tipo_unidad_template.csv"'
    return response


@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    if request.method == 'POST':
        codigo: str = request.form['codigo']
        nombre: str = request.form['nombre']
        esta_activo: bool = request.form.get('esta-activo', '') == 'on'

        tipo_unidad = TipoUnidad(codigo=codigo,
                      nombre=nombre,
                      esta_activo=esta_activo
                      )

        db.session.add(tipo_unidad)
        id:int = -1
        try:
            db.session.commit()
            id = tipo_unidad.id
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

        return redirect(url_for('tipo_unidad.view',id=id))

    return render_template('tipo_unidad/create.html')


@bp.route('/update/<int:id>', methods=['GET', 'POST'])
@login_required
def update(id):
    tipo_unidad = get(id)

    if request.method == 'POST':
        tipo_unidad.codigo = request.form['codigo']
        tipo_unidad.nombre = request.form['nombre']

        tipo_unidad.esta_activo = request.form.get('esta-activo') == 'on'

        id:int = tipo_unidad.id

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

        return redirect(url_for('tipo_unidad.view',id=id))

    return render_template('tipo_unidad/update.html', dato=tipo_unidad)


@bp.route('/view/<int:id>')
@login_required
def view(id):
    tipo_unidad = get(id)
    return render_template('tipo_unidad/view.html', dato=tipo_unidad)


@bp.route('/delete/<int:id>', methods=['GET', 'POST'])
def delete(id):
    tipo_unidad = get(id)

    if request.method == 'POST':
        tipo_unidad = get(id)
        db.session.delete(tipo_unidad)
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
        return redirect(url_for('tipo_unidad.index'))

    return render_template('tipo_unidad/delete.html', dato=tipo_unidad)
