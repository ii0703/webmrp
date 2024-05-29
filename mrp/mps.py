from flask import Blueprint, render_template, request, redirect, url_for, g, abort
from flask import (send_file, stream_with_context, Response)
from io import BytesIO, StringIO
from datetime import datetime, timedelta
import csv
from mrp.auth import login_required
from .models import PlanMaestroProduccion
from mrp import db
from sqlite3 import IntegrityError

bp = Blueprint('mps', __name__, url_prefix='/mps')


def get(id):
    dato = PlanMaestroProduccion.query.get_or_404(id)
    return dato


@bp.route('/list', methods=['GET'])
@login_required
def index():
    pagina = request.args.get('pagina', 1, type=int)
    busqueda = request.args.get('busqueda', '', type=str)
    if busqueda == '':
        datos = db.paginate(db.select(PlanMaestroProduccion), per_page=5, page=pagina)
    else:
        datos = db.paginate(db.select(PlanMaestroProduccion), per_page=5, page=pagina)
    return render_template('mps/index.html', datos=datos, pagina=pagina, busqueda=busqueda)


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
        return redirect(url_for('mps.index'))
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
    csv_writer.writerow(['Identificación', 'Nombre', 'Lugar', 'Correo electrónico', 'Teléfono', 'Tipo', 'Estado'])
    datos = PlanMaestroProduccion.query.order_by(PlanMaestroProduccion.nombre.desc()).all()
    csv_items = [[dato.identificacion, dato.nombre, dato.lugar.nombre, dato.correo_electronico, dato.telefono,
                  'Persona física' if dato.es_persona_fisica else 'Empresa',
                  'Activo' if dato.esta_activo else 'Inactivo'] for dato in datos]
    for item in csv_items:
        csv_writer.writerow(item)
    file_output.seek(0)
    response = Response(file_output)
    response.headers['Content-Type'] = 'text/csv; charset=utf-8'
    response.headers['Content-Disposition'] = 'attachment; filename="mps_export_all.csv"'
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
    response.headers['Content-Disposition'] = 'attachment; filename="mps_template.csv"'
    return response


@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    if request.method == 'POST':
        nombre: str = request.form['nombre']
        inicio_str: str = request.form['inicio']
        inicio:datetime = datetime.strptime(inicio_str, '%Y-%m-%d')
        final_str: str = request.form['final']
        final:datetime = datetime.strptime(final_str, '%Y-%m-%d')
        esta_finalizado: bool = request.form.get('esta-finalizado', '') == 'on'
        mps = PlanMaestroProduccion(nombre=nombre,
                                    inicio=inicio,
                                    fin=final,
                                    esta_finalizado=esta_finalizado)

        db.session.add(mps)
        id: int = -1
        try:
            db.session.commit()
            id = mps.id
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

        return redirect(url_for('mps.view', id=id))

    hoy_str = datetime.now().strftime('%Y-%m-%d')
    final = datetime.now() + timedelta(days=28)
    final_str = final.strftime('%Y-%m-%d')

    return render_template('mps/create.html', inicio=hoy_str, final=final_str)


@bp.route('/update/<int:id>', methods=['GET', 'POST'])
@login_required
def update(id):
    mps = get(id)

    if request.method == 'POST':
        mps.nombre: str = request.form['nombre']
        inicio_str: str = request.form['inicio']
        mps.inicio:datetime = datetime.strptime(inicio_str, '%Y-%m-%d')
        final_str: str = request.form['final']
        mps.final:datetime = datetime.strptime(final_str, '%Y-%m-%d')
        mps.esta_finalizado: bool = request.form.get('esta-finalizado', '') == 'on'

        id: int = mps.id

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

        return redirect(url_for('mps.view', id=id))

    return render_template('mps/update.html', dato=mps)


@bp.route('/view/<int:id>')
@login_required
def view(id):
    mps = get(id)
    return render_template('mps/view.html', dato=mps)


@bp.route('/delete/<int:id>', methods=['GET', 'POST'])
def delete(id):
    mps = get(id)

    if request.method == 'POST':
        mps = get(id)
        db.session.delete(mps)
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
        return redirect(url_for('mps.index'))

    return render_template('mps/delete.html', dato=mps)
