from flask import Blueprint, render_template, request, redirect, url_for, g, abort
from flask import (send_file, stream_with_context, Response, flash)
from io import BytesIO, StringIO
from datetime import datetime, timedelta, date
import csv
from mrp.auth import login_required
from .models import PlanMaestroProduccion, Producto, PlanMaestroProduccionProductos, PlanMaestroProduccionDemandas
from mrp import db
from sqlite3 import IntegrityError
import numpy as np
import pandas as pd
import io
import matplotlib.pyplot as plt
import seaborn as sns
import base64
import matplotlib.ticker as mticker


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


def calcular_inventario_inicial_neto(inventario_inicial_bruto,
                                     porcentaje_desperdicio):  # esta función es para calcular el inventario inicial neto con el % de desperdicio respectivo
    return inventario_inicial_bruto * (1 - porcentaje_desperdicio)


def ajustar_plan_produccion_nivelado(total_demanda, inventario_inicial, inventario_seguridad, N,
                                     gamma):  # esta función es para calcular el plan de producción con la estrategia nivelador
    demanda_total = sum(total_demanda)
    plan_produccion_nivelado = (demanda_total - inventario_inicial + inventario_seguridad) / N
    plan_produccion_nivelado_con_scrap = np.ceil(
        plan_produccion_nivelado * gamma)  # aquí el np.ceil se utiliza para redondear al siguiente número entero más alto
    return [plan_produccion_nivelado_con_scrap] * N


def calcular_disponible(inventario_inicial_neto,
                        plan_produccion):  # esta función es para calcular el disponible con su respectiva fórmula
    return inventario_inicial_neto + plan_produccion


def calcular_inventario_final(disponible,
                              demanda):  # esta función es para calcular el disponible con su respectiva fórmula
    return disponible - demanda


def mps_nivelador(productos, capacidad_actual,
                  N):  # aquí la función mps_nivelador solo acepta esos 3 argumentos y se crea un diccionario llamado tablas
    tablas = {}

    for producto, datos in productos.items():  # aquí se está agregando los valores de demanda, inventarios y % de desperdicio y scrap en el diccionario de tablas en la parte de productos
        demanda = datos['demanda']
        inventario_inicial_bruto = datos['inventario_inicial_bruto']
        inventario_seguridad = datos['inventario_seguridad']
        porcentaje_desperdicio = datos['porcentaje_desperdicio']
        scrap = datos['scrap']

        gamma = 1 / (1 - scrap)  # define que es gamma
        inventario_inicial_neto = calcular_inventario_inicial_neto(inventario_inicial_bruto, porcentaje_desperdicio)

        tabla = pd.DataFrame(index=['Inventario Inicial Bruto', 'Porcentaje Desperdicio', 'Inventario Inicial Neto',
                                    # esto es para poder formar una tabla al final
                                    'Plan Producción (sin scrap)', 'Scrap Plan Producción',
                                    'Plan Producción (con scrap)',
                                    'Disponible', 'Demanda', 'Inventario Final'],
                             columns=[f'Periodo {i + 1}' for i in range(N)])

        tabla.loc[
            'Inventario Inicial Bruto', 'Periodo 1'] = inventario_inicial_bruto  # aquí tabla.loc es para acceder a las filas y columnas que se definieron anteriormente para la tabla
        tabla.loc['Porcentaje Desperdicio'] = porcentaje_desperdicio
        tabla.loc['Scrap Plan Producción'] = scrap
        tabla.loc['Demanda'] = demanda

        plan_produccion_nivelado = ajustar_plan_produccion_nivelado(demanda, inventario_inicial_neto,
                                                                    inventario_seguridad, N, gamma)

        for i in range(N):  #
            if i == 0:
                inventario_inicial_neto_periodo = inventario_inicial_neto
            else:
                inventario_inicial_neto_periodo = tabla.loc['Inventario Final', f'Periodo {i}']

            plan_con_scrap = plan_produccion_nivelado[i]
            plan_sin_scrap = plan_con_scrap / gamma

            disponible = calcular_disponible(inventario_inicial_neto_periodo, plan_con_scrap)
            inventario_final_periodo = calcular_inventario_final(disponible, demanda[i])

            tabla.loc['Inventario Inicial Neto', f'Periodo {i + 1}'] = inventario_inicial_neto_periodo
            tabla.loc['Plan Producción (sin scrap)', f'Periodo {i + 1}'] = plan_sin_scrap
            tabla.loc['Plan Producción (con scrap)', f'Periodo {i + 1}'] = plan_con_scrap
            tabla.loc['Disponible', f'Periodo {i + 1}'] = disponible
            tabla.loc['Inventario Final', f'Periodo {i + 1}'] = inventario_final_periodo

        tablas[producto] = tabla

    plan_produccion_total_general = sum(tabla.loc['Plan Producción (con scrap)'].sum() for tabla in tablas.values())
    if plan_produccion_total_general > capacidad_actual:  # aquí se presenta la posibilidad de que si el plan de producción es mayor a la capacidad actual definir un factor de ajsute DUDA CON EL PROFE
        print(
            f"Advertencia: la capacidad total de producción {plan_produccion_total_general} excede la capacidad actual de {capacidad_actual}.")
    else:
        print(f"Plan de producción total general: {plan_produccion_total_general}")

    return tablas


@bp.route('/mps_nivelado/<int:id>', methods=['GET', 'POST'])
@login_required
def calcular_nivelado(id):
    mps = get(id)

    inventario_inicio = {}
    for producto_mps in mps.productos:
        # poner porcentaja inventario de seguridad en producto
        inventario_inicio[producto_mps.producto] = calcular_inventario_inicial_neto(
            producto_mps.producto.cantidad_total, producto_mps.producto.scrap_almacenamiento / 100)

    query_demandas = PlanMaestroProduccionDemandas.query
    query_demandas = query_demandas.filter(PlanMaestroProduccionDemandas.mps_id == id)
    demandas = query_demandas.all()

    dict_productos = {}

    for demanda in demandas:
        if demanda.producto in dict_productos:
            dict_productos[demanda.producto].append((demanda.semana, demanda.cantidad))
        else:
            dict_productos[demanda.producto] = [(demanda.semana, demanda.cantidad)]

    lista_plan_produccion_nivelado = {}
    for k, lista_semana_demandas in dict_productos.items():
        valores_demandas = [x[1] for x in lista_semana_demandas]
        # falta inventario de seguridad
        lista_plan_produccion_nivelado[k] = ajustar_plan_produccion_nivelado(valores_demandas,
                                                                             inventario_inicio[k],
                                                                             100,
                                                                             len(valores_demandas),
                                                                             1 - (k.scrap_produccion / 100))


    query_semanas = (db.session.query(PlanMaestroProduccionDemandas.semana)
                     .filter(PlanMaestroProduccionDemandas.mps_id == id)
                     .order_by(PlanMaestroProduccionDemandas.semana.asc())
                     .distinct())
    semanas = [semana[0] for semana in query_semanas.all()]


    limite = 60*8*5

    # Crear figura y definir estilo de gráfico
    datos_grafico = {}
    for producto, demandas in lista_plan_produccion_nivelado.items():
        datos_grafico[producto.nombre] = [ producto.minutos_produccion * d for d in demandas]
    fig, ax = plt.subplots()

    ax.stackplot(semanas, datos_grafico.values(),
                 labels=datos_grafico.keys(), alpha=0.8)
    ax.axhline(limite, color='red', linestyle='--', label='Capacidad máxima')
    ax.legend(loc='upper left', reverse=True)
    ax.set_title('MPS Nivelados en minutos')
    ax.set_xlabel('Semanas')
    ax.set_ylabel('Minutos')
    # add tick at every 200 million people
    ax.yaxis.set_minor_locator(mticker.MultipleLocator(5000))
    buf = BytesIO()
    fig.savefig(buf, format="png")

    data = base64.b64encode(buf.getbuffer()).decode("ascii")


    return render_template('mps/leveled_mps.html',
                           mps=mps,
                           lista_plan_produccion_nivelado=lista_plan_produccion_nivelado,
                           semanas=semanas,
                           data=data)


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

def ordernar_diccionario(dicc):
    dicco = sorted(dicc.items(), key=lambda x: x[0])
    return dict(dicco)

def ordenar_diccionarios_internos(dicc):
    for k, v in dicc.items():
        dicc[k] = ordernar_diccionario(v)

    return dicc

@bp.route('/view/<int:id>')
@login_required
def view(id):
    mps = get(id)

    productos_relacionado_subquery = (db.session
                                      .query(PlanMaestroProduccionProductos.producto_id)
                                      .filter(PlanMaestroProduccionProductos.mps_id == id))
    productos_relacionados = Producto.query.filter(Producto.id.in_(productos_relacionado_subquery)).all()

    query_demandas = PlanMaestroProduccionDemandas.query
    query_demandas = query_demandas.filter(PlanMaestroProduccionDemandas.mps_id == id)
    demandas = query_demandas.all()


    dict_demandas = {(demanda.producto_id, demanda.semana): demanda for demanda in demandas}

    dict_prod_semana_demandas = {}
    for demanda in demandas:
        if demanda.producto in dict_prod_semana_demandas:
            dict_semana_demandas = dict_prod_semana_demandas[demanda.producto]
            dict_semana_demandas[demanda.semana] = demanda.cantidad
        else:
            dict_prod_semana_demandas[demanda.producto] = {demanda.semana: demanda.cantidad}

    # flash(dict_prod_semana_demandas)

    ordenar_diccionarios_internos(dict_prod_semana_demandas)

    # flash(dict_prod_semana_demandas)


    query_semanas = (db.session.query(PlanMaestroProduccionDemandas.semana)
                     .filter(PlanMaestroProduccionDemandas.mps_id == id)
                     .order_by(PlanMaestroProduccionDemandas.semana.asc())
                     .distinct())

    semanas = [semana[0] for semana in query_semanas.all()]

    # Crear figura y definir estilo de gráfico
    limite = 8 * 60 * 5
    datos_grafico = {}
    for producto, semanas_demandas in dict_prod_semana_demandas.items():
        datos_grafico[producto.nombre] = [ producto.minutos_produccion * demanda for semana, demanda in semanas_demandas.items()]

    # flash(datos_grafico)
    fig, ax = plt.subplots()

    ax.stackplot(semanas, datos_grafico.values(),
                 labels=datos_grafico.keys(), alpha=0.8)
    ax.axhline(limite, color='red', linestyle='--', label='Capacidad máxima')
    ax.legend(loc='upper left', reverse=True)
    ax.set_title('Demandas en minutos')
    ax.set_xlabel('Semanas')
    ax.set_ylabel('Minutos')
    # add tick at every 200 million people
    ax.yaxis.set_minor_locator(mticker.MultipleLocator(5000))
    buf = BytesIO()
    fig.savefig(buf, format="png")

    chart_data = base64.b64encode(buf.getbuffer()).decode("ascii")

    inicio = f'{mps.inicio.year}-W{mps.inicio.isocalendar()[1]}'
    final = f'{mps.fin.year}-W{mps.fin.isocalendar()[1]}'

    return render_template('mps/view.html', dato=mps, productos_relacionados=productos_relacionados, inicio=inicio,
                           final=final, semanas=semanas, demandas=dict_demandas, chart_data= chart_data)


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

    return render_template('mps/product_add.html', dato=mps, codigo=codigo, nombre=nombre, productos=productos,
                           productos_relacionados=productos_relacionados)


@bp.route('/product_demand/<int:id>', methods=['GET', 'POST'])
@login_required
def product_demand(id):
    mps = get(id)
    dia_inicio = mps.inicio
    dia_final = mps.fin
    dias: timedelta = dia_final - dia_inicio
    semanas = int(dias.days / 7) + 1
    dias_semana_iso = [dia_inicio + timedelta(days=i * 7) for i in range(0, semanas)]
    semanas_iso = [f'{fecha.year}-W{fecha.isocalendar()[1]}' for fecha in dias_semana_iso]

    productos_registrados_subquery = (db.session
                                      .query(PlanMaestroProduccionProductos.producto_id)
                                      .filter(PlanMaestroProduccionProductos.mps_id == id))

    query = Producto.query
    query = query.filter(Producto.id.in_(productos_registrados_subquery))
    productos = query.all()

    query_demandas = PlanMaestroProduccionDemandas.query
    query_demandas = query_demandas.filter(PlanMaestroProduccionDemandas.mps_id == id)
    demandas = query_demandas.all()

    dict_demandas = {(demanda.producto_id, demanda.semana): demanda for demanda in demandas}

    form_data = {}
    for demanda in demandas:
        form_data['d-{}-{}'.format(demanda.producto_id, demanda.semana)] = demanda.cantidad

    if request.method == 'POST':
        form_data = request.form
        for key in form_data:
            if key.startswith('d-'):
                k, producto_id, year, week = key.split('-')
                producto_id = int(producto_id)
                week_iso = '{}-{}'.format(year, week)
                key_dict = (producto_id, week_iso)
                # flash(dict_demandas)
                if key_dict in dict_demandas:
                    demanda = dict_demandas.get(key_dict)
                    demanda.cantidad = float(form_data.get(key))
                else:
                    demanda = PlanMaestroProduccionDemandas()
                    demanda.mps_id = id
                    demanda.producto_id = producto_id
                    demanda.semana = week_iso
                    demanda.cantidad = float(form_data.get(key))
                    db.session.add(demanda)

        db.session.commit()
    return render_template('mps/product_demand.html', dato=mps, semanas=semanas_iso, productos=productos,
                           form_data=form_data)


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
