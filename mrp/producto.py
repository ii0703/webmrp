from flask import Blueprint, render_template, request, redirect, url_for, g, abort
from flask import (send_file, stream_with_context, Response)
from io import BytesIO, StringIO
import csv
from mrp.auth import login_required
from .models import Producto, CategoriaProducto, Unidad
from mrp import db
from sqlite3 import IntegrityError

bp = Blueprint('producto', __name__, url_prefix='/producto')


def get(id):
    dato = Producto.query.get_or_404(id)
    return dato


@bp.route('/list', methods=['GET'])
@login_required
def index():
    pagina = request.args.get('pagina', 1, type=int)
    busqueda = request.args.get('busqueda', '', type=str)
    if busqueda == '':
        datos = db.paginate(db.select(Producto).order_by(Producto.nombre.desc()), per_page=5, page=pagina)
    else:
        datos = db.paginate(db.select(Producto).filter(Producto.nombre.ilike(f'%{busqueda}%')), per_page=5, page=pagina)
    return render_template('producto/index.html', datos=datos, pagina=pagina, busqueda=busqueda)


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
        return redirect(url_for('producto.index'))
    return '''
<!DOCTYPE html>
<html lang="en">
<head>
	<meta charset="UTF-8">
	<meta http-equiv="X-UA-Compatible" content="IE=edge">
	<meta name="viewport" content="width=device-width, initial-scale=1.0">
	<title>Importar productos</title>
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
		<h1>Importar productos</h1>
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
    csv_writer.writerow(
        ['SKU', 'Nombre', 'Categoría', 'Unidad', 'Cantidad total', 'Cantidad disponible', 'Cantidad reservado', 'Costo',
         'Porcentaje impuesto', 'Redondeo', 'Modo de cálculo de utilidad', 'Porcentaje utilidad', 'Monto utilidad',
         'Minutos producción', 'Scrap producción', 'Scrap almacenamiento', 'Estado'])
    datos = Producto.query.order_by(Producto.nombre.desc()).all()
    csv_items = [[dato.identificacion, dato.nombre, dato.lugar.nombre, dato.correo_electronico, dato.telefono,
                  'Persona física' if dato.es_persona_fisica else 'Empresa',
                  'Activo' if dato.esta_activo else 'Inactivo'] for dato in datos]
    for item in csv_items:
        csv_writer.writerow(item)
    file_output.seek(0)
    response = Response(file_output)
    response.headers['Content-Type'] = 'text/csv; charset=utf-8'
    response.headers['Content-Disposition'] = 'attachment; filename="producto_export_all.csv"'
    return response


@bp.route('/csv_template')
def csv_template():
    # @stream_with_context
    # def generate():
    #     yield str.encode('Identificación', 'Nombre', 'Tipo', 'Estado', 'utf-8')

    # response = Response(generate())
    ##
    file_output = StringIO()
    csv_writer = csv.writer(file_output, delimiter=',',
                            quoting=csv.QUOTE_ALL)
    csv_writer.writerow(
        ['SKU', 'Nombre', 'Categoría', 'Unidad', 'Cantidad total', 'Cantidad disponible', 'Cantidad reservado', 'Costo',
         'Porcentaje impuesto', 'Redondeo', 'Modo de cálculo de utilidad', 'Porcentaje utilidad', 'Monto utilidad',
         'Minutos producción', 'Scrap producción', 'Scrap almacenamiento', 'Estado'])
    csv_items = [
        ['SKU', 'Nombre', 'Categoría', 'Unidad', 'Cantidad total', 'Cantidad disponible', 'Cantidad reservado', 'Costo',
         'Porcentaje impuesto', 'Redondeo', 'Modo de cálculo de utilidad', 'Porcentaje utilidad', 'Monto utilidad',
         'Minutos producción', 'Scrap producción', 'Scrap almacenamiento', 'Estado']]
    for item in csv_items:
        csv_writer.writerow(item)
    file_output.seek(0)
    ##
    response = Response(file_output)
    response.headers['Content-Type'] = 'text/csv; charset=utf-8'
    response.headers['Content-Disposition'] = 'attachment; filename="producto_template.csv"'
    return response


@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    categorias_producto = (CategoriaProducto
                           .query.filter_by(esta_activo=True)
                           .order_by(CategoriaProducto.nombre).all())
    unidades = (Unidad.query
                .filter_by(esta_activo=True)
                .order_by(Unidad.nombre).all())

    if request.method == 'POST':
        sku = request.form['sku']
        nombre = request.form['nombre']
        categoria_producto_id = request.form['categoria-producto']
        unidad_id = request.form['unidad']
        cantidad_total = request.form['cantidad-total']
        costo = request.form['costo']
        porcentaje_impuesto = request.form['porcentaje-impuesto']
        redondeo = request.form['redondeo']
        utilildad_es_porcentaje = request.form.get('modo-utilidad') == 'porcentaje'
        esta_activo = request.form.get('esta-activo') == 'on'
        porcentaje_utilidad = request.form['utilidad-porcentaje']
        monto_utilidad = request.form['utilidad-monto']
        minutos_produccion = request.form['minutos-produccion']
        scrap_produccion = request.form['scrap-produccion']
        scrap_almacenamiento = request.form['scrap-almacenamiento']

        producto = Producto(sku=sku,
                            nombre=nombre,
                            categoria_producto_id=categoria_producto_id,
                            unidad_id=unidad_id,
                            cantidad_total=cantidad_total,
                            costo=costo,
                            porcentaje_impuesto=porcentaje_impuesto,
                            redondeo=redondeo,
                            utilildad_es_porcentaje=utilildad_es_porcentaje,
                            porcentaje_utilidad=porcentaje_utilidad,
                            monto_utilidad=monto_utilidad,
                            esta_activo=esta_activo,
                            minutos_produccion=minutos_produccion,
                            scrap_produccion=scrap_produccion,
                            scrap_almacenamiento=scrap_almacenamiento
                            )

        db.session.add(producto)
        id: int = -1
        # db.session.commit()

        try:
            db.session.commit()
            id = producto.id
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

        return redirect(url_for('producto.view', id=id))

    return render_template('producto/create.html', categorias_producto=categorias_producto, unidades=unidades)


@bp.route('/update/<int:id>', methods=['GET', 'POST'])
@login_required
def update(id):
    producto = get(id)
    categorias_producto = (CategoriaProducto
                           .query.filter_by(esta_activo=True)
                           .order_by(CategoriaProducto.nombre).all())
    unidades = (Unidad.query
                .filter_by(esta_activo=True)
                .order_by(Unidad.nombre).all())

    if request.method == 'POST':
        producto.sku = request.form['sku']
        producto.categoria_producto_id = request.form['categoria-producto']
        producto.nombre = request.form['nombre']
        producto.unidad_id = request.form['unidad']
        producto.cantidad_total = request.form['cantidad-total']
        producto.costo = request.form['costo']
        producto.porcentaje_impuesto = request.form['porcentaje-impuesto']
        producto.redondeo = request.form['redondeo']
        utilildad_es_porcentaje = request.form.get('modo-utilidad') == 'porcentaje'
        producto.utilildad_es_porcentaje = utilildad_es_porcentaje
        producto.esta_activo = request.form.get('esta-activo') == 'on'
        producto.porcentaje_utilidad = request.form['utilidad-porcentaje']
        producto.monto_utilidad = request.form['utilidad-monto']
        producto.minutos_produccion = request.form['minutos-produccion']
        producto.scrap_produccion = request.form['scrap-produccion']
        producto.scrap_almacenamiento = request.form['scrap-almacenamiento']

        id: int = producto.id

        db.session.commit()

        return redirect(url_for('producto.view', id=id))

    return render_template('producto/update.html', dato=producto, categorias_producto=categorias_producto,
                           unidades=unidades)


@bp.route('/view/<int:id>')
@login_required
def view(id):
    producto = get(id)
    return render_template('producto/view.html', dato=producto)


@bp.route('/delete/<int:id>', methods=['GET', 'POST'])
def delete(id):
    producto = get(id)

    if request.method == 'POST':
        producto = get(id)
        db.session.delete(producto)
        db.session.commit()
        return redirect(url_for('producto.index'))

    return render_template('producto/delete.html', dato=producto)
