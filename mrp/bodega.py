from flask import Blueprint, render_template, request, redirect, url_for, g, abort
from flask import (send_file, stream_with_context, Response, flash)
from io import BytesIO, StringIO
import csv
from mrp.auth import login_required
from .models import Lugar, Bodega
from mrp import db
from sqlite3 import IntegrityError

bp = Blueprint('bodega', __name__, url_prefix='/bodega')


def get(id):
    dato = Bodega.query.get_or_404(id)
    return dato


@bp.route('/list', methods=['GET'])
@login_required
def index():
    pagina = request.args.get('pagina', 1, type=int)
    busqueda = request.args.get('busqueda', '', type=str)
    if busqueda == '':
        datos = db.paginate(db.select(Bodega).order_by(Bodega.nombre.desc()), per_page=5, page=pagina)
    else:
        datos = db.paginate(db.select(Bodega).filter(Bodega.nombre.ilike(f'%{busqueda}%')), per_page=5, page=pagina)
    return render_template('bodega/index.html', datos=datos, pagina=pagina, busqueda=busqueda)


def decode_utf8(input_iterator):
    for l in input_iterator:
        yield l.decode('utf-8')


@bp.route('/csv_import_all', methods=['GET', 'POST'])
def csv_import_all():
    if request.method == 'POST':
        file = request.files['file']
        reader = csv.DictReader(decode_utf8(file),
                                fieldnames=['codigo', 'nombre', 'lugar', 'estado'],
                                delimiter=';')
        # para saltar la primera línea del encabezado, dado que yo le mando los nombre
        next(reader)
        # Cargo todos los lugares existentes, por si existe un código previamente ignoralo
        lista_lugares = Lugar.query.all()
        # convierto la lista en un diccionario (el código debe ser único)
        dict_lugares = {lugar.codigo: lugar for lugar in lista_lugares}

        # Cargo todos los lugares existentes, por si existe un código previamente ignoralo
        lista_bodegas = Bodega.query.all()
        # convierto la lista en un diccionario (el código debe ser único)
        dict_bodegas = {bodega.codigo: bodega for bodega in lista_bodegas}

        nuevos = 0
        existentes = 0
        sin_lugar = 0



        for row in reader:
            if row['lugar'] in dict_lugares:
                lugar = dict_lugares[row['lugar']]
                if row['codigo'] in dict_bodegas:
                    existentes = existentes + 1
                else:
                    nuevos = nuevos + 1
                    codigo = str(row['codigo'].strip())
                    nombre = row['nombre']
                    esta_activo = row['estado'].lstrip().lower() == 'activo'
                    # flash('{} {} {}'.format(codigo, nombre, esta_activo))
                    bodega = Bodega(codigo=codigo,
                                    nombre=nombre,
                                    esta_activo=esta_activo,
                                    lugar=lugar)

                    db.session.add(bodega)
            else:
                sin_lugar = sin_lugar + 1

        if nuevos > 0:
            db.session.commit()
            flash('Datos nuevos {}'.format(nuevos))
        if existentes > 0:
            flash('Datos existentes: {}'.format(existentes))
        if sin_lugar > 0:
            flash('Datos que no se pudieron registrar porque no tenían sitio registrado: {}'.format(existentes))

        return redirect(url_for('bodega.index'))

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
    csv_writer.writerow(['Código', 'Nombre', 'Lugar', 'Estado'])
    datos = Bodega.query.order_by(Bodega.nombre.desc()).all()
    csv_items = [[dato.codigo, dato.nombre, dato.lugar.codigo,
                  'Activo' if dato.esta_activo else 'Inactivo'] for dato in datos]
    for item in csv_items:
        csv_writer.writerow(item)
    file_output.seek(0)
    response = Response(file_output)
    response.headers['Content-Type'] = 'text/csv; charset=utf-8'
    response.headers['Content-Disposition'] = 'attachment; filename="bodega_export_all.csv"'
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
    csv_writer.writerow(['Código', 'Nombre', 'Lugar', 'Estado'])
    csv_items = [['', '', '', '']]
    for item in csv_items:
        csv_writer.writerow(item)
    file_output.seek(0)
    ##
    response = Response(file_output)
    response.headers['Content-Type'] = 'text/csv; charset=utf-8'
    response.headers['Content-Disposition'] = 'attachment; filename="bodega_template.csv"'
    return response


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
