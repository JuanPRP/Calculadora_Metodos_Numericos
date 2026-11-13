import math
from io import BytesIO
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from muller import metodo_muller
from newton import interpolacion_newton

st.set_page_config(page_title="Calculadora de métodos numéricos", layout="wide")

# Colores de las gráficas (solo cuatro para que se vea ordenado)
AZUL = "#1C83E1"
ROJO = "#FF4B4B"
OSCURO = "#31333F"
GRIS = "#808495"


# ---------- Funciones de ayuda ----------

def fmt(numero):
    # Muestra un número con máximo 6 cifras significativas
    if numero is None:
        return "-"
    return f"{numero:.6g}"



def crear_funcion(texto):
    import ast
    import operator

    texto = texto.replace("^", "**").strip()

    if not texto or len(texto) > 200:
        raise ValueError("La función está vacía o es demasiado larga.")

    funciones = {
        "sin": math.sin,
        "cos": math.cos,
        "tan": math.tan,
        "exp": math.exp,
        "log": math.log,
        "sqrt": math.sqrt,
    }

    constantes = {
        "pi": math.pi,
        "e": math.e,
    }

    operadores = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Pow: operator.pow,
        ast.Mod: operator.mod,
    }

    try:
        arbol = ast.parse(texto, mode="eval")
    except SyntaxError:
        raise ValueError("La expresión matemática no es válida.")

    if len(list(ast.walk(arbol))) > 50:
        raise ValueError("La expresión es demasiado compleja.")

    def calcular(nodo, x):
        if isinstance(nodo, ast.Expression):
            return calcular(nodo.body, x)

        elif isinstance(nodo, ast.Constant):
            if isinstance(nodo.value, (int, float)) and not isinstance(nodo.value, bool):
                return nodo.value
            raise ValueError("Solo se permiten números.")

        elif isinstance(nodo, ast.Name):
            if nodo.id == "x":
                return x
            if nodo.id in constantes:
                return constantes[nodo.id]
            raise ValueError(f"Nombre no permitido: {nodo.id}")

        elif isinstance(nodo, ast.BinOp):
            tipo = type(nodo.op)

            if tipo not in operadores:
                raise ValueError("Operación no permitida.")

            izquierda = calcular(nodo.left, x)
            derecha = calcular(nodo.right, x)

            if tipo == ast.Pow:
                if abs(derecha) > 100 or abs(izquierda) > 1e50:
                    raise ValueError("Potencia demasiado grande.")

            resultado = operadores[tipo](izquierda, derecha)

        elif isinstance(nodo, ast.UnaryOp):
            valor = calcular(nodo.operand, x)

            if isinstance(nodo.op, ast.USub):
                resultado = -valor
            elif isinstance(nodo.op, ast.UAdd):
                resultado = valor
            else:
                raise ValueError("Operador no permitido.")

        elif isinstance(nodo, ast.Call):
            if not isinstance(nodo.func, ast.Name):
                raise ValueError("Función no permitida.")

            nombre = nodo.func.id

            if nombre not in funciones or len(nodo.args) != 1 or nodo.keywords:
                raise ValueError("Función matemática no permitida.")

            argumento = calcular(nodo.args[0], x)
            resultado = funciones[nombre](argumento)

        else:
            raise ValueError("Expresión matemática no permitida.")

        if not isinstance(resultado, (int, float)) or not math.isfinite(resultado):
            raise ValueError("El resultado no es un número finito.")

        return resultado

    def f(x):
        return calcular(arbol, x)

    return f


def columna_num(titulo, ayuda=None):
    # Columna numérica: se ordena bien y muestra hasta 6 cifras
    return st.column_config.NumberColumn(titulo, help=ayuda, format="%.6g")


def convertir_a_excel(dataframe, nombre_hoja="Resultados"):
    # Convierte una tabla de pandas en un archivo Excel descargable.
    archivo = BytesIO()
    with pd.ExcelWriter(archivo, engine="openpyxl") as escritor:
        dataframe.to_excel(escritor, index=False, sheet_name=nombre_hoja)
    archivo.seek(0)
    return archivo.getvalue()


def resaltar_coeficientes(tabla_df):
    # Pinta la primera fila (menos la columna x): son los coeficientes del polinomio
    estilos = pd.DataFrame("", index=tabla_df.index, columns=tabla_df.columns)
    estilos.iloc[0, 1:] = "background-color: rgba(255, 75, 75, 0.2); font-weight: bold"
    return estilos


def evaluar(f, valores):
    # Calcula f(v) para cada valor de la lista
    resultados = []
    for v in valores:
        resultados.append(f(v))
    return resultados


def puntos_curva(f, izq, der):
    # Calcula 200 puntos de la curva para poder dibujarla
    xs = []
    ys = []
    for i in range(201):
        x = izq + (der - izq) * i / 200
        try:
            y = float(f(x))
            xs.append(x)
            ys.append(y)
        except Exception:
            pass  # si f no existe en ese x, se salta ese punto
    return xs, ys


def factor(c):
    # Escribe (x - c) cuidando el signo
    if c >= 0:
        return f"(x - {fmt(c)})"
    return f"(x + {fmt(-c)})"


def limpiar_ejes(ax):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(alpha=0.2)
    ax.set_xlabel("x")
    ax.legend(fontsize=8)


# ---------- Encabezado y selección del método ----------

st.title("Calculadora de métodos numéricos")
st.caption("Elige un método, escribe tus datos a la izquierda y revisa el resultado paso a paso.")

metodo = st.sidebar.radio("Método", ["Müller", "Interpolación de Newton"])
st.sidebar.header("Datos")


# ---------- MÉTODO DE MÜLLER ----------

if metodo == "Müller":
    # Los datos se envían juntos al pulsar el botón del formulario.
    with st.sidebar.form("formulario_muller"):
        texto_f = st.text_input("Función f(x)", "x**3 - 2*x - 5")
        x0 = st.number_input("x0", value=1.0, format="%g")
        x1 = st.number_input("x1", value=2.0, format="%g")
        x2 = st.number_input("x2", value=3.0, format="%g")
        tolerancia = st.number_input("Tolerancia (error %)", value=0.01, min_value=0.0, format="%g")
        maximo = st.number_input("Máximo de iteraciones", value=20, min_value=1, max_value=100, step=1)
        ejecutar_muller = st.form_submit_button("Ejecutar método")

    # El cálculo solo se realiza cuando se pulsa el botón.
    if ejecutar_muller:
        try:
            funcion_muller = crear_funcion(texto_f)
            raiz_calculada, tabla_calculada = metodo_muller(
                funcion_muller, x0, x1, x2, tolerancia, int(maximo)
            )
            st.session_state["resultado_muller"] = {
                "raiz": raiz_calculada,
                "tabla": tabla_calculada,
                "texto_f": texto_f,
                "x0": x0,
                "x1": x1,
                "x2": x2,
                "tolerancia": tolerancia,
                "maximo": int(maximo),
                "error": None,
            }
        except Exception as error:
            st.session_state["resultado_muller"] = {"error": str(error)}

    datos_muller = st.session_state.get("resultado_muller")
    if datos_muller is None:
        st.info("Ingresa los datos y pulsa **Ejecutar método** para obtener los resultados.")
        st.stop()

    if datos_muller.get("error"):
        st.error(f"No se pudo calcular: {datos_muller['error']}")
        st.caption("Revisa que la función esté escrita así: x**3 - 2*x - 5 (usa ** para potencias).")
        st.stop()

    # Se muestran los últimos resultados calculados, aunque Streamlit actualice la página.
    raiz = datos_muller["raiz"]
    tabla = datos_muller["tabla"]
    texto_f = datos_muller["texto_f"]
    x0 = datos_muller["x0"]
    x1 = datos_muller["x1"]
    x2 = datos_muller["x2"]
    tolerancia = datos_muller["tolerancia"]
    maximo = datos_muller["maximo"]
    f = crear_funcion(texto_f)

    error_final = tabla[-1]["error"]
    col1, col2, col3 = st.columns(3)
    col1.metric("Raíz aproximada", fmt(raiz))
    col2.metric("Iteraciones", len(tabla))
    col3.metric("Error final", fmt(error_final) + " %")

    if error_final is None or error_final > tolerancia:
        st.warning("No se alcanzó la tolerancia con las iteraciones indicadas. Prueba con más iteraciones u otros valores iniciales.")

    tab_grafica, tab_tabla, tab_pasos = st.tabs(["Gráfica", "Tabla de iteraciones", "Paso a paso"])

    # --- Gráfica: se elige la iteración y se ve su parábola ---
    with tab_grafica:
        n = len(tabla)
        if n > 1:
            k = st.slider("Iteración", 1, n, 1)
        else:
            k = 1
        fila = tabla[k - 1]

        # Rango del eje x: cubre todos los puntos por donde pasa el método
        todos = [x0, x1, x2]
        for una_fila in tabla:
            todos.append(una_fila["x3"])
        margen = (max(todos) - min(todos)) * 0.3
        if margen == 0:
            margen = 1
        izq = min(todos) - margen
        der = max(todos) + margen

        def parabola(x):
            dx = x - fila["x2"]
            return fila["f(x2)"] + fila["b"] * dx + fila["a"] * dx ** 2

        cx, cy = puntos_curva(f, izq, der)
        px, py = puntos_curva(parabola, izq, der)
        usados = [fila["x0"], fila["x1"], fila["x2"]]
        x3 = fila["x3"]

        fig, ax = plt.subplots(figsize=(8, 4.5))
        ax.axhline(0, color=GRIS, linewidth=1)
        ax.plot(cx, cy, color=OSCURO, label="f(x)")
        ax.plot(px, py, "--", color=ROJO, label="Parábola de esta iteración")
        ax.scatter(usados, evaluar(f, usados), color=AZUL, zorder=3, label="Puntos usados (x0, x1, x2)")
        ax.plot([x3, x3], [0, f(x3)], ":", color=ROJO)
        ax.scatter([x3], [f(x3)], color=ROJO, zorder=3)
        ax.scatter([x3], [0], color=ROJO, marker="D", zorder=4, label=f"Nueva aproximación x3 = {fmt(x3)}")

        ymin = min(min(cy), 0)
        ymax = max(max(cy), 0)
        espacio = (ymax - ymin) * 0.1
        ax.set_ylim(ymin - espacio, ymax + espacio)
        ax.set_ylabel("f(x)")
        limpiar_ejes(ax)
        st.pyplot(fig)
        plt.close(fig)
        st.caption("La línea roja punteada es la parábola que pasa por los tres puntos azules. "
                   "Donde cruza el eje x aparece la nueva aproximación (rombo rojo).")

    # --- Tabla con todas las iteraciones y su error ---
    with tab_tabla:
        filas = []
        mayor_error = 0
        for una_fila in tabla:
            filas.append({
                "Iteración": una_fila["iteracion"],
                "x0": una_fila["x0"],
                "x1": una_fila["x1"],
                "x2": una_fila["x2"],
                "f(x2)": una_fila["f(x2)"],
                "a": una_fila["a"],
                "b": una_fila["b"],
                "Discriminante": una_fila["discriminante"],
                "x3 (nueva)": una_fila["x3"],
                "Error %": una_fila["error"],
            })
            if una_fila["error"] is not None and una_fila["error"] > mayor_error:
                mayor_error = una_fila["error"]
        if mayor_error == 0:
            mayor_error = 1

        # Formato de cada columna (al pasar el mouse sobre el nombre sale su explicación)
        columnas = {
            "x0": columna_num("x0", "Primer punto usado en esta iteración"),
            "x1": columna_num("x1", "Segundo punto usado en esta iteración"),
            "x2": columna_num("x2", "Tercer punto usado (el más reciente)"),
            "f(x2)": columna_num("f(x2)", "Valor de la función en x2"),
            "a": columna_num("a", "Coeficiente a de la parábola"),
            "b": columna_num("b", "Coeficiente b de la parábola"),
            "Discriminante": columna_num("Discriminante", "b² - 4ac"),
            "x3 (nueva)": columna_num("x3 (nueva)", "Nueva aproximación a la raíz"),
            "Error %": st.column_config.ProgressColumn(
                "Error %", help="|x3 - x2| / |x3| × 100", format="%.4g",
                min_value=0, max_value=mayor_error),
        }
        tabla_excel = pd.DataFrame(filas)
        st.dataframe(tabla_excel, hide_index=True, column_config=columnas)
        st.download_button(
            label="Descargar tabla en Excel",
            data=convertir_a_excel(tabla_excel, "Iteraciones Muller"),
            file_name="resultados_muller.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="descargar_excel_muller",
        )
        st.caption("Error % = |x3 - x2| / |x3| × 100. El método se detiene cuando es menor o igual a la tolerancia. "
                   "Haz clic en el nombre de una columna para ordenarla.")

    # --- Paso a paso de cada iteración ---
    with tab_pasos:
        st.write("Cada iteración usa tres puntos para armar una parábola y buscar dónde cruza el eje x.")
        st.caption("El signo (+ o -) del denominador se elige para que quede lo más grande posible.")
        for una_fila in tabla:
            p0 = una_fila["x0"]
            p1 = una_fila["x1"]
            p2 = una_fila["x2"]
            f0 = f(p0)
            f1 = f(p1)
            f2 = una_fila["f(x2)"]
            h1 = p1 - p0
            h2 = p2 - p1
            delta1 = (f1 - f0) / h1
            delta2 = (f2 - f1) / h2
            raiz_d = math.sqrt(una_fila["discriminante"])
            if una_fila["b"] >= 0:
                signo = "+"
                denominador = una_fila["b"] + raiz_d
            else:
                signo = "-"
                denominador = una_fila["b"] - raiz_d

            texto = (
                f"h1 = x1 - x0 = {fmt(p1)} - {fmt(p0)} = {fmt(h1)}\n"
                f"h2 = x2 - x1 = {fmt(p2)} - {fmt(p1)} = {fmt(h2)}\n"
                f"δ1 = (f(x1) - f(x0)) / h1 = ({fmt(f1)} - {fmt(f0)}) / {fmt(h1)} = {fmt(delta1)}\n"
                f"δ2 = (f(x2) - f(x1)) / h2 = ({fmt(f2)} - {fmt(f1)}) / {fmt(h2)} = {fmt(delta2)}\n"
                f"a = (δ2 - δ1) / (h2 + h1) = {fmt(una_fila['a'])}\n"
                f"b = a·h2 + δ2 = {fmt(una_fila['b'])}\n"
                f"c = f(x2) = {fmt(f2)}\n"
                f"D = b² - 4ac = {fmt(una_fila['discriminante'])}\n"
                f"denominador = b {signo} √D = {fmt(denominador)}\n"
                f"x3 = x2 - 2c / denominador = {fmt(una_fila['x3'])}\n"
                f"error = |x3 - x2| / |x3| × 100 = {fmt(una_fila['error'])} %"
            )
            titulo = f"Iteración {una_fila['iteracion']}  →  x3 = {fmt(una_fila['x3'])}  (error {fmt(una_fila['error'])} %)"
            with st.expander(titulo, expanded=(una_fila["iteracion"] == 1)):
                st.code(texto, language=None)


# ---------- INTERPOLACIÓN DE NEWTON ----------

else:
    # Los datos de Newton se envían juntos al pulsar el botón del formulario.
    with st.sidebar.form("formulario_newton"):
        st.caption("Puntos conocidos: edita las celdas o agrega filas con el + al final de la tabla.")
        puntos = st.data_editor(
            pd.DataFrame({"x": [1.0, 2.0, 3.0, 4.0], "y": [-6.0, -1.0, 16.0, 51.0]}),
            num_rows="dynamic",
            column_config={"x": st.column_config.NumberColumn("x", format="%g"),
                           "y": st.column_config.NumberColumn("y", format="%g")},
            key="editor_puntos_newton",
        )
        valor = st.number_input("Valor de x a estimar", value=2.5, format="%g", key="valor_newton")
        texto_real = st.text_input("Valor real de y (opcional)", "5.625", key="real_newton")
        ejecutar_newton = st.form_submit_button("Ejecutar método")

    # El cálculo solo se realiza cuando se pulsa el botón.
    if ejecutar_newton:
        try:
            # Se pasan los puntos de la tabla a dos listas, saltando las filas incompletas.
            xs_calculados = []
            ys_calculados = []
            for i in range(len(puntos)):
                px = puntos["x"].iloc[i]
                py = puntos["y"].iloc[i]
                if not (pd.isna(px) or pd.isna(py)):
                    xs_calculados.append(float(px))
                    ys_calculados.append(float(py))
            if len(xs_calculados) < 2:
                raise ValueError("Agrega al menos 2 puntos completos a la tabla.")

            resultado_calculado, coeficientes_calculados, tabla_calculada = interpolacion_newton(
                xs_calculados, ys_calculados, valor
            )
            real_calculado = None
            if texto_real.strip() != "":
                real_calculado = float(texto_real)

            st.session_state["resultado_newton"] = {
                "xs": xs_calculados,
                "ys": ys_calculados,
                "valor": valor,
                "texto_real": texto_real,
                "resultado": resultado_calculado,
                "coeficientes": coeficientes_calculados,
                "tabla_dd": tabla_calculada,
                "real": real_calculado,
                "error": None,
            }
        except Exception as error:
            st.session_state["resultado_newton"] = {"error": str(error)}

    datos_newton = st.session_state.get("resultado_newton")
    if datos_newton is None:
        st.info("Ingresa los puntos y pulsa **Ejecutar método** para obtener los resultados.")
        st.stop()

    if datos_newton.get("error"):
        st.error(f"No se pudo calcular: {datos_newton['error']}")
        st.caption("Revisa que cada punto tenga x e y, que no haya x repetidos y que el valor real sea un número.")
        st.stop()

    # Se muestran los últimos resultados calculados, aunque Streamlit actualice la página.
    xs = datos_newton["xs"]
    ys = datos_newton["ys"]
    valor = datos_newton["valor"]
    resultado = datos_newton["resultado"]
    coeficientes = datos_newton["coeficientes"]
    tabla_dd = datos_newton["tabla_dd"]
    real = datos_newton["real"]
    texto_real = datos_newton["texto_real"]

    n = len(xs)
    error_t = None
    if real is not None and real != 0:
        error_t = abs((real - resultado) / real) * 100

    col1, col2, col3 = st.columns(3)
    col1.metric(f"Valor estimado P({fmt(valor)})", fmt(resultado))
    col2.metric("Grado del polinomio", n - 1)
    if error_t is not None:
        col3.metric("Error porcentual verdadero", fmt(error_t) + " %")
    elif real == 0:
        st.info("El error porcentual no se puede calcular cuando el valor real es 0.")

    tab_grafica, tab_tabla, tab_pasos = st.tabs(["Gráfica", "Tabla de diferencias divididas", "Paso a paso"])

    # --- Gráfica del polinomio y los puntos ---
    with tab_grafica:
        todos = xs + [valor]
        margen = (max(todos) - min(todos)) * 0.1
        if margen == 0:
            margen = 1
        izq = min(todos) - margen
        der = max(todos) + margen

        gx = []
        gy = []
        for i in range(201):
            x = izq + (der - izq) * i / 200
            gx.append(x)
            gy.append(interpolacion_newton(xs, ys, x)[0])

        fig, ax = plt.subplots(figsize=(8, 4.5))
        ax.plot(gx, gy, color=OSCURO, label="Polinomio P(x)")
        ax.scatter(xs, ys, color=AZUL, zorder=3, label="Puntos dados")
        ax.scatter([valor], [resultado], color=ROJO, marker="D", zorder=4,
                   label=f"Estimado: P({fmt(valor)}) = {fmt(resultado)}")
        if real is not None:
            ax.scatter([valor], [real], color=GRIS, marker="x", zorder=4, label=f"Valor real: {fmt(real)}")
        ax.set_ylabel("y")
        limpiar_ejes(ax)
        st.pyplot(fig)
        plt.close(fig)
        st.caption("La curva es el polinomio que pasa por todos los puntos azules. El rombo rojo es el valor estimado.")

    # --- Tabla de diferencias divididas ---
    with tab_tabla:
        filas = []
        for i in range(n):
            una_fila = {"x": fmt(xs[i]), "f[xi]": fmt(ys[i])}
            for orden in range(1, n):
                if i < n - orden:
                    una_fila["Orden " + str(orden)] = fmt(tabla_dd[orden][i])
                else:
                    una_fila["Orden " + str(orden)] = ""
            filas.append(una_fila)
        tabla_df = pd.DataFrame(filas)
        st.dataframe(tabla_df.style.apply(resaltar_coeficientes, axis=None), hide_index=True)

        # Para Excel se conservan los valores numéricos, no el formato redondeado de pantalla.
        filas_excel = []
        for i in range(n):
            una_fila_excel = {"x": xs[i], "f[xi]": ys[i]}
            for orden in range(1, n):
                una_fila_excel["Orden " + str(orden)] = (
                    tabla_dd[orden][i] if i < n - orden else None
                )
            filas_excel.append(una_fila_excel)
        tabla_excel = pd.DataFrame(filas_excel)
        st.download_button(
            label="Descargar tabla en Excel",
            data=convertir_a_excel(tabla_excel, "Diferencias divididas"),
            file_name="resultados_newton.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="descargar_excel_newton",
        )
        st.caption("Cada columna sale de la anterior: (valor siguiente - valor actual) / (x más lejano - x más cercano). "
                   "Las celdas rojas de la primera fila son los coeficientes del polinomio.")

    # --- Paso a paso ---
    with tab_pasos:
        st.markdown("**1. Coeficientes** (primer valor de cada columna)")
        texto = ""
        for k in range(n):
            texto += f"c{k} = {fmt(coeficientes[k])}\n"
        st.code(texto, language=None)

        st.markdown("**2. Polinomio**")
        polinomio = f"P(x) = {fmt(coeficientes[0])}"
        for k in range(1, n):
            polinomio += f" + ({fmt(coeficientes[k])})"
            for j in range(k):
                polinomio += factor(xs[j])
        st.code(polinomio, language=None)

        st.markdown(f"**3. Evaluar en x = {fmt(valor)}**")
        texto = f"P = c0 = {fmt(coeficientes[0])}\n"
        suma = coeficientes[0]
        producto = 1
        for k in range(1, n):
            producto = producto * (valor - xs[k - 1])
            suma = suma + coeficientes[k] * producto
            texto += f"c{k} · producto = {fmt(coeficientes[k])} · {fmt(producto)}  →  suma = {fmt(suma)}\n"
        st.code(texto, language=None)

        if error_t is not None:
            st.markdown("**4. Error porcentual verdadero**")
            st.code(f"error = |(real - estimado) / real| × 100 = |({fmt(real)} - {fmt(resultado)}) / {fmt(real)}| × 100 = {fmt(error_t)} %",
                    language=None)
