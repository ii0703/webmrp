from flask import Blueprint, render_template, request, redirect, url_for, g, abort
from flask import (send_file, stream_with_context, Response, flash)
from io import BytesIO, StringIO
from datetime import datetime, timedelta, date
import csv
from mrp.auth import login_required
from .models import PlanMaestroProduccion, Producto, PlanMaestroProduccionProductos
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
        inicio_y, inicio_w = inicio_str.split('-')
        inicio_iso_week_str = f"{inicio_y}-{inicio_w}-1"
        inicio = date.fromisoformat(inicio_iso_week_str)

        final_str: str = request.form['final']
        final_y, final_w = final_str.split('-')
        final_iso_week_str = f"{final_y}-{final_w}-1"
        final = date.fromisoformat(final_iso_week_str)

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

    now = datetime.now()
    hoy_str = now.strftime('%Y-%m-%d')
    hoyw_str = f"{now.year}-{now.isocalendar()[1]}"
    final = now + timedelta(days=28)
    final_str = final.strftime('%Y-%m-%d')
    finalw_str = f"{final.year}-{final.isocalendar()[1]}"

    return render_template('mps/create.html', inicio=hoyw_str, final=finalw_str)


@bp.route('/update/<int:id>', methods=['GET', 'POST'])
@login_required
def update(id):
    mps = get(id)

    if request.method == 'POST':
        mps.nombre: str = request.form['nombre']

        inicio_str: str = request.form['inicio']
        inicio_y, inicio_w = inicio_str.split('-')
        inicio_iso_week_str = f"{inicio_y}-{inicio_w}-1"
        inicio = date.fromisoformat(inicio_iso_week_str)
        mps.inicio: inicio

        final_str: str = request.form['final']
        final_y, final_w = final_str.split('-')
        final_iso_week_str = f"{final_y}-{final_w}-1"
        final = date.fromisoformat(final_iso_week_str)
        mps.fin: final

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

    inicio = f'{mps.inicio.year}-W{mps.inicio.isocalendar()[1]}'
    final = f'{mps.fin.year}-W{mps.fin.isocalendar()[1]}'

    return render_template('mps/update.html', dato=mps, inicio=inicio, final=final)


@bp.route('/view/<int:id>')
@login_required
def view(id):
    mps = get(id)

    productos_relacionado_subquery = (db.session
                                      .query(PlanMaestroProduccionProductos.producto_id)
                                      .filter(PlanMaestroProduccionProductos.mps_id == id))
    productos_relacionados = Producto.query.filter(Producto.id.in_(productos_relacionado_subquery)).all()

    inicio = f'{mps.inicio.year}-W{mps.inicio.isocalendar()[1]}'
    final = f'{mps.fin.year}-W{mps.fin.isocalendar()[1]}'

    return render_template('mps/view.html', dato=mps, productos_relacionados=productos_relacionados, inicio=inicio, final=final)


@bp.route('/product_add/<int:id>', methods=['GET', 'POST'])
@login_required
def product_add(id):
    mps = get(id)


    productos = None
    codigo = ''
    nombre = ''
    # flash(request.form.getlist('selected_items'))
    if request.method == 'POST':
        if request.form.get('type') == 'add':
            productos_seleccionado = request.form.getlist('selected_items')
            if productos_seleccionado:
                for producto in productos_seleccionado:
                    pmpp = PlanMaestroProduccionProductos()
                    pmpp.mps = mps
                    pmpp.producto_id = int(producto)
                    db.session.add(pmpp)

            try:
                db.session.commit()
            except Exception as err:
                db.session.rollback()
                abort(409, err)
            # except IntegrityError as err:
            #     db.session.rollback()
            #     abort(409, err.orig)
            # except Exception as err:
            #     db.session.rollback()
            #     abort(500, err)
            # finally:
            #     db.session.close()

        if request.form.get('type') == 'search':
            nombre = request.form['nombre']
            codigo = request.form['codigo']

            productos_registrados_subquery = (db.session
                                              .query(PlanMaestroProduccionProductos.producto_id)
                                              .filter(PlanMaestroProduccionProductos.mps_id == id))

            query = Producto.query

            query = query.filter(~Producto.id.in_(productos_registrados_subquery))

            if codigo:
                query = query.filter(Producto.sku.ilike(f'%{codigo}%'))
            if nombre:
                query = query.filter(Producto.nombre.ilike(f'%{nombre}%'))

            productos = query.limit(50).all()

    productos_relacionado_subquery = (db.session
                                      .query(PlanMaestroProduccionProductos.producto_id)
                                      .filter(PlanMaestroProduccionProductos.mps_id == id))
    productos_relacionados = Producto.query.filter(Producto.id.in_(productos_relacionado_subquery)).all()

    return render_template('mps/product_add.html', dato=mps, codigo=codigo, nombre=nombre, productos=productos, productos_relacionados=productos_relacionados)

@bp.route('/product_demand/<int:id>')
@login_required
def product_demand(id):
    mps = get(id)
    dia_inicio = mps.inicio
    dia_final = mps.fin
    dias:timedelta = dia_final - dia_inicio
    semanas = int(dias.days/7) + 1
    dias_semana_iso = [dia_inicio+timedelta(days=i*7) for i in range(0, semanas)]
    semanas_iso = [f'{fecha.year}-W{fecha.isocalendar()[1]}' for fecha in dias_semana_iso]

    productos_registrados_subquery = (db.session
                                      .query(PlanMaestroProduccionProductos.producto_id)
                                      .filter(PlanMaestroProduccionProductos.mps_id == id))

    query = Producto.query

    query = query.filter(Producto.id.in_(productos_registrados_subquery))

    productos = query.all()

    # flash(semanas_iso)
    # flash(productos)
    return render_template('mps/product_demand.html', dato=mps, semanas=semanas_iso, productos=productos)

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
