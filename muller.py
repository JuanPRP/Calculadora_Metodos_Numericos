import math

def metodo_muller(f, x0, x1, x2, tolerancia = 0.01, max_iteraciones = 100):
    resultados = []

    for i in range(1, max_iteraciones + 1):

#Evalua la funcion de las 3 aproximaciones
        f0 = f(x0)
        f1 = f(x1)
        f2 = f(x2)

#Calcular diferencias

        h1 = x1 - x0
        h2 = x2 - x1

        if h1 == 0 or h2 == 0 or h1 + h2 == 0:
            raise ValueError("Las aproximaciones iniciales no son validas.") 

#Calcular deltas

        delta1 = (f1 - f0) / h1
        delta2 = (f2 - f1) / h2

#Calcular coeficientes de la parabola

        CoefA = (delta2 - delta1) / (h2 + h1)
        CoefB = (CoefA * h2) + delta2
#Coefc = f2

#Calcular el discriminante
        discriminante = CoefB**2 - 4 * CoefA * f2

        if discriminante < 0:
            raise ValueError(
                "El discriminante es negativo. "
                "Esta versión trabaja con aproximaciones reales."
            )

        raiz_discriminante = math.sqrt(discriminante)

#Escoger el demonimador con mayor valor absoluto

        if CoefB >= 0:
            denominador = CoefB + raiz_discriminante

        else:
            denominador = CoefB - raiz_discriminante

        if denominador == 0:
            raise ValueError("No se puede continuar porque el denominador es igual a cero.")

        #Cacular la nueva aproximacion

        x3 = x2 - (2 * f2 / denominador)

#Calculamos el error aproximado porcentual

        if x3 != 0:
            error = abs((x3 - x2) / x3) * 100
        else:
            error = 0 if x2 == x3 else None 

#Guardar los resultados de la iteracion

        resultados.append({
            "iteracion": i,
            "x0": x0,
            "x1": x1,
            "x2": x2,
            "f(x2)": f2,
            "a": CoefA,
            "b": CoefB,
            "discriminante": discriminante,
            "x3": x3,
            "error": error,
        })

#Verificar si se llego a la tolerancia

        if error is not None and error <= tolerancia:
            return x3, resultados

#actualizamos las aproximaciones 

        x0 = x1
        x1 = x2
        x2 = x3

    return x2, resultados

# Primera prueba del método de Muller

def funcion(x):
    return x**3 - 2*x - 5

raiz, tabla = metodo_muller(
    funcion,
    x0=1,
    x1=2,
    x2=3,
    tolerancia=0.01,
    max_iteraciones=100
)

print("Raiz aproximada:", raiz)
print("\nResultados por iteracion:")

for fila in tabla:
    print(fila)
