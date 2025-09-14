from ortools.linear_solver import pywraplp

# ==== DATOS DE ENTRADA ====
meses = ["Ene","Feb","Mar","Abr","May","Jun","Jul","Ago","Sep"]
demanda_cm = [10, 20, 13, 25, 11, 3, 27, 16, 23]   # Demanda en cm
cm_a_unid = 100   # 1 cm -> 100 unidades
cinv = 5.0        # costo inventario (u.m./unidad/mes)
catr = 12.0       # costo atraso (u.m./unidad/mes)
cprod = 0.0       # costo producción regular (u.m./unidad)
inv0 = 0.0
atr0 = 0.0

# Mezcla nivelador-perseguidor
usar_tope_por_periodo = True
delta_cm = 3.0

# ==== PARÁMETROS DE OPERARIOS ====
cap_por_operario = 500     # unidades que un operario puede producir por mes
c_contratacion = 100.0      # costo por contratar un operario
c_despido = 80.0            # costo por despedir un operario
operarios_iniciales = 4    # nuevos operarios iniciales

# ==== SOLVER ====
solver = pywraplp.Solver.CreateSolver('SCIP')
T = len(meses)

# ==== VARIABLES ====
prod_cm = [solver.NumVar(0, solver.infinity(), f'prod_cm[{t}]') for t in range(T)]
inv = [solver.NumVar(0, solver.infinity(), f'inv[{t}]') for t in range(T)]
atr = [solver.NumVar(0, solver.infinity(), f'atr[{t}]') for t in range(T)]
diff_pos = [solver.NumVar(0, solver.infinity(), f'diff_pos[{t}]') for t in range(T)]
diff_neg = [solver.NumVar(0, solver.infinity(), f'diff_neg[{t}]') for t in range(T)]
num_operarios = [solver.NumVar(0, solver.infinity(), f'operarios[{t}]') for t in range(T)]
contrataciones = [solver.NumVar(0, solver.infinity(), f'contrataciones[{t}]') for t in range(T)]
despidos = [solver.NumVar(0, solver.infinity(), f'despidos[{t}]') for t in range(T)]

# ==== RESTRICCIONES ====
# Balance de inventario y atraso
solver.Add(inv[0] - atr[0] == (inv0 - atr0) + cm_a_unid*(prod_cm[0] - demanda_cm[0]))
for t in range(1, T):
    solver.Add(inv[t] - atr[t] == (inv[t-1] - atr[t-1]) + cm_a_unid*(prod_cm[t] - demanda_cm[t]))

# Suavizado de producción
solver.Add(diff_pos[0] == 0)
solver.Add(diff_neg[0] == 0)
for t in range(1, T):
    solver.Add(prod_cm[t] - prod_cm[t-1] == diff_pos[t] - diff_neg[t])
    if usar_tope_por_periodo:
        solver.Add(diff_pos[t] + diff_neg[t] <= delta_cm)

# Producción limitada por capacidad de operarios
for t in range(T):
    solver.Add(cm_a_unid * prod_cm[t] <= num_operarios[t] * cap_por_operario)

# Contrataciones y despidos según necesidad, con 4 operarios iniciales
solver.Add(contrataciones[0] >= num_operarios[0] - operarios_iniciales)
solver.Add(despidos[0] >= operarios_iniciales - num_operarios[0])
for t in range(1, T):
    solver.Add(contrataciones[t] >= num_operarios[t] - num_operarios[t-1])
    solver.Add(despidos[t] >= num_operarios[t-1] - num_operarios[t])

# ==== FUNCIÓN OBJETIVO ====
cost_terms = []
for t in range(T):
    unidades_t = cm_a_unid * prod_cm[t]
    cost_terms.append(
        cinv * inv[t] +
        catr * atr[t] +
        cprod * unidades_t +
        c_contratacion * contrataciones[t] +
        c_despido * despidos[t]
    )

solver.Minimize(solver.Sum(cost_terms))

# ==== RESOLVER ====
status = solver.Solve()

# ==== IMPRESIÓN DE RESULTADOS ====
def imprime_resultados(tag_status):
    print(f"\nEstado del solver: {tag_status}")
    print(f"Costo total: {solver.Objective().Value():.2f}")
    header = '|{:^3}|{:^5}|{:^10}|{:^10}|{:^10}|{:^10}|{:^10}|{:^10}|{:^10}|{:^10}|{:^10}|{:^10}|'.format(
        't','Mes','Dem (cm)','Dem (unid)','Prod (cm)','Prod (unid)',
        'Inv (unid)','Atr (unid)','Operarios','Contrat','Despidos','Costo Inv','Costo Atr')
    print('\n' + header)
    print('-'*len(header))

    tot_inv_cost = tot_atr_cost = tot_prod_cost = tot_contrat = tot_despido = 0.0
    for t in range(T):
        dcm = demanda_cm[t]
        dunid = dcm * cm_a_unid
        pcm = prod_cm[t].solution_value()
        punid = pcm * cm_a_unid
        i   = inv[t].solution_value()
        a   = atr[t].solution_value()
        n_op = num_operarios[t].solution_value()
        cont = contrataciones[t].solution_value()
        desp = despidos[t].solution_value()
        cinv_t = cinv * i
        catr_t = catr * a
        ctotal_t = cinv_t + catr_t + cprod*punid + c_contratacion*cont + c_despido*desp
        tot_inv_cost += cinv_t
        tot_atr_cost += catr_t
        tot_prod_cost += cprod*punid
        tot_contrat += c_contratacion*cont
        tot_despido += c_despido*desp
        print('|{:>3}|{:^5}|{:>10.0f}|{:>10.0f}|{:>10.2f}|{:>10.0f}|{:>10.0f}|{:>10.0f}|{:>10.0f}|{:>10.0f}|{:>10.0f}|{:>10.2f}|{:>10.2f}|'.format(
            t, meses[t], dcm, dunid, pcm, punid, i, a, n_op, cont, desp, cinv_t, catr_t))

    print('\nDesglose de costos:')
    print(f'  Costo Inventario : {tot_inv_cost:.2f}')
    print(f'  Costo Atraso     : {tot_atr_cost:.2f}')
    print(f'  Costo Producción : {tot_prod_cost:.2f}')
    print(f'  Costo Contratacion: {tot_contrat:.2f}')
    print(f'  Costo Despido    : {tot_despido:.2f}')
    print(f'  TOTAL            : {solver.Objective().Value():.2f}')

if status in [pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE]:
    imprime_resultados("ÓPTIMA" if status == pywraplp.Solver.OPTIMAL else "FACTIBLE")
else:
    print("No se encontró solución factible (status =", status, ").")


