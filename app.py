import math
import streamlit as st
from tabulate import tabulate

# ---------------------------------------------------------
# Funciones auxiliares
# ---------------------------------------------------------

def calcular_area_proyectada(tipo, largo=None, ancho=None, diametro=None, area_manual=None):
    if tipo == "Rectangular":
        return (largo * ancho) / 100  # mm² → cm²
    elif tipo == "Cilíndrica":
        radio = diametro / 2
        return (math.pi * radio * radio) / 100  # mm² → cm²
    else:
        return area_manual

def calcular_tonelaje(area_cm2, presion_cavidad=450):
    return (area_cm2 * presion_cavidad) / 1000

def calcular_tiempos(peso_g, espesor_mm):
    t_iny = round(0.008 * peso_g + 0.5, 2)
    t_sost = round(0.6 * espesor_mm**2 + 0.3 * espesor_mm, 2)
    t_enf = round(2.5 * espesor_mm**2, 2)
    return t_iny, t_sost, t_enf

def temperaturas(material, reciclado, carga):
    if material == "PP":
        base = [200, 210, 220, 215]
    elif material == "PEAD":
        base = [180, 190, 200, 195]
    else:
        base = [190, 200, 210, 205]

    if reciclado:
        base = [t + 5 for t in base]
    if carga:
        base = [t + 5 for t in base]

    return base

# ---------------------------------------------------------
# Interfaz Streamlit
# ---------------------------------------------------------

st.title("🧠 Calculadora de Parámetros Iniciales de Inyección")
st.write("Versión optimizada para Android vía navegador")

st.header("1. Material")
material = st.selectbox("Tipo de material", ["PP", "PEAD", "Mezcla PP/PE"])
reciclado = st.checkbox("Material reciclado")
carga = st.checkbox("Con CaCO₃")

st.header("2. Pieza y Molde")
peso_total = st.number_input("Peso total de inyección (g)", min_value=1.0)
espesor = st.number_input("Espesor máximo de pared (mm)", min_value=0.1)
cavidades = st.number_input("Número de cavidades", min_value=1)

geo = st.selectbox("Geometría principal", ["Rectangular", "Cilíndrica", "Irregular"])

if geo == "Rectangular":
    largo = st.number_input("Largo (mm)", min_value=1.0)
    ancho = st.number_input("Ancho (mm)", min_value=1.0)
    area = calcular_area_proyectada("Rectangular", largo=largo, ancho=ancho)
elif geo == "Cilíndrica":
    diametro = st.number_input("Diámetro (mm)", min_value=1.0)
    area = calcular_area_proyectada("Cilíndrica", diametro=diametro)
else:
    area_manual = st.number_input("Área proyectada (cm²)", min_value=0.1)
    area = area_manual

area_total = area * cavidades

st.header("3. Máquina")
tonelaje_maquina = st.number_input("Tonelaje de la máquina (t)", min_value=1.0)
cap_inyeccion = st.number_input("Capacidad máxima de inyección (g)", min_value=1.0)
diametro_husillo = st.number_input("Diámetro del husillo (mm)", min_value=10.0)

st.header("4. Tiempos mecánicos (sugeridos pero editables)")
tiempo_cierre = st.number_input("Tiempo de cierre (s)", value=2.0)
tiempo_apertura = st.number_input("Tiempo de apertura (s)", value=2.0)
tiempo_expulsion = st.number_input("Tiempo de expulsión (s)", value=1.0)

# ---------------------------------------------------------
# Cálculo
# ---------------------------------------------------------

if st.button("Calcular parámetros"):
    tonelaje_req = calcular_tonelaje(area_total)
    uso_husillo = round((peso_total / cap_inyeccion) * 100, 1)
    t_iny, t_sost, t_enf = calcular_tiempos(peso_total, espesor)
    t_mecanico = tiempo_cierre + tiempo_apertura + tiempo_expulsion
    t_ciclo = round(t_iny + t_sost + t_enf + t_mecanico, 2)

    zona_post, zona_trans, zona_ant, boquilla = temperaturas(material, reciclado, carga)
    temp_molde = "20–30 °C (frío) / 30–40 °C (templado)"

    tabla = [
        ["Temperatura zona posterior", f"{zona_post} °C"],
        ["Temperatura zona transición", f"{zona_trans} °C"],
        ["Temperatura zona anterior", f"{zona_ant} °C"],
        ["Temperatura boquilla", f"{boquilla} °C"],
        ["Temperatura molde", temp_molde],
        ["Tonelaje requerido", f"{round(tonelaje_req,2)} t"],
        ["Tonelaje disponible", f"{tonelaje_maquina} t"],
        ["Uso del husillo", f"{uso_husillo} %"],
        ["Tiempo de inyección", f"{t_iny} s"],
        ["Tiempo de sostenimiento", f"{t_sost} s"],
        ["Tiempo de enfriamiento", f"{t_enf} s"],
        ["Tiempo cierre", f"{tiempo_cierre} s"],
        ["Tiempo apertura", f"{tiempo_apertura} s"],
        ["Tiempo expulsión", f"{tiempo_expulsion} s"],
        ["Tiempo de ciclo total", f"{t_ciclo} s"],
    ]

    st.subheader("Resultados")
    st.table(tabla)
