def interpolacion_newton(xs, ys, valor):
    n = len(xs)

    if n != len(ys):
        raise ValueError("xs y ys deben tener la misma cantidad de datos.")

    # La primera columna de la tabla son los valores de y
    tabla = [ys[:]]

    # Calcular las diferencias divididas, columna por columna
    for orden in range(1, n):
        columna_anterior = tabla[orden - 1]
        columna_nueva = []

        for i in range(n - orden):
            numerador = columna_anterior[i + 1] - columna_anterior[i]
            denominador = xs[i + orden] - xs[i]

            if denominador == 0:
                raise ValueError("Hay valores de x repetidos.")

            columna_nueva.append(numerador / denominador)

        tabla.append(columna_nueva)

    # Los coeficientes son el primer valor de cada columna
    coeficientes = []
    for columna in tabla:
        coeficientes.append(columna[0])

    # Evaluar el polinomio en el valor pedido
    resultado = coeficientes[0]
    producto = 1

    for k in range(1, n):
        producto = producto * (valor - xs[k - 1])
        resultado = resultado + coeficientes[k] * producto

    return resultado, coeficientes, tabla


# Prueba de interpolación de Newton
# Usamos puntos de la misma función x^3 - 2x - 5

def funcion(x):
    return x**3 - 2*x - 5

xs = [1, 2, 3, 4]
ys = [ funcion (x) for x in xs]

valor, coef, tabla_dd = interpolacion_newton(xs, ys, 2.5)

print("\nInterpolación de Newton")
print("Coeficientes:", coef)
print("Valor interpolado en x = 2.5:", valor)
print("Valor real:", funcion(2.5))

print("\nTabla de diferencias divididas:")
for numero, columna in enumerate(tabla_dd):
    print("Orden", numero, ":", columna)