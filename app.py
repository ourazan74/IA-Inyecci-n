import math
import streamlit as st
import pandas as pd

# ---------------------------------------------------------
# Funciones auxiliares
# ---------------------------------------------------------

def calcular_area_proyectada(tipo, largo=None, ancho=None, diametro=None, area_manual=None):
    """Calcula el área proyectada en cm² según la geometría."""
    try:
        if tipo == "Rectangular":
            return float(largo) * float(ancho) / 100.0
        elif tipo == "Cilíndrica":
            radio = float(diametro) / 2.0
            return (math.pi * radio * radio) / 100.0
        else:
            return float(area_manual)
    except:
        return 0.0


def calcular_tonelaje(area_cm2, presion_cavidad=450):
    """Tonelaje requerido según área proyectada."""
    try:
        return (float(area_cm2) * float(presion_cavidad)) / 1000.0
    except:
        return 0.0


def calcular_tiempos_base(peso_g, espesor_mm):
    """Tiempos térmicos base (antes de ajustes por geometría)."""
    try:
        t_iny = round(0.008 * float(peso_g) + 0.5, 2)
        t_sost = round(0.6 * float(espesor_mm)**2 + 0.3 * float(espesor_mm), 2)
        t_enf = round(2.5 * float(espesor_mm)**2, 2)
        return t_iny, t_sost, t_enf
    except:
        return 0, 0, 0


def temperaturas(material, reciclado, carga):
    """Temperaturas recomendadas por zonas."""
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
st.write("Optimizada para Android. Agrega esta página a tu pantalla de inicio para usarla como app.")

# ------------------ MATERIAL ------------------
st.header("1. Material")
material = st.selectbox("Tipo de material", ["PP", "PEAD", "Mezcla PP/PE"])
reciclado = st.checkbox("Material reciclado")
carga = st.checkbox("Con CaCO₃")

# ------------------ PIEZA ------------------
st.header("2. Pieza y Molde")
peso_total = st.number_input("Peso total de inyección (g)", min_value=0.1)
espesor = st.number_input("Espesor máximo de pared (mm)", min_value=0.1)
cavidades = st.number_input("Número de cavidades", min_value=1)

geo = st.selectbox("Geometría principal", ["Rectangular", "Cilíndrica", "Irregular"])

altura = None
diametro = None

if geo == "Rectangular":
    largo = st.number_input("Largo (mm)", min_value=0.1)
    ancho = st.number_input("Ancho (mm)", min_value=0.1)
    area = calcular_area_proyectada("Rectangular", largo=largo, ancho=ancho)

elif geo == "Cilíndrica":
    diametro = st.number_input("Diámetro (mm)", min_value=0.1)
    altura = st.number_input("Altura (mm)", min_value=0.1)
    area = calcular_area_proyectada("Cilíndrica", diametro=diametro)

else:
    area_manual = st.number_input("Área proyectada (cm²)", min_value=0.1)
    area = calcular_area_proyectada("Irregular", area_manual=area_manual)

area_total = float(area) * float(cavidades)

# ------------------ MÁQUINA ------------------
st.header("3. Máquina")
tonelaje_maquina = st.number_input("Tonelaje de la máquina (t)", min_value=0.1)
cap_inyeccion = st.number_input("Capacidad máxima de inyección (g)", min_value=0.1)
diametro_husillo = st.number_input("Diámetro del husillo (mm)", min_value=10.0)

# ------------------ TIEMPOS MECÁNICOS ------------------
st.header("4. Tiempos mecánicos (sugeridos pero editables)")
tiempo_cierre = st.number_input("Tiempo de cierre (s)", value=2.0, min_value=0.1)
tiempo_apertura = st.number_input("Tiempo de apertura (s)", value=2.0, min_value=0.1)
tiempo_expulsion = st.number_input("Tiempo de expulsión (s)", value=1.0, min_value=0.1)

# ---------------------------------------------------------
# Cálculo
# ---------------------------------------------------------

if st.button("Calcular parámetros"):

    # -------- Tonelaje y uso de husillo --------
    tonelaje_req = round(calcular_tonelaje(area_total), 2)
    uso_husillo = round((float(peso_total) / float(cap_inyeccion)) * 100.0, 1)

    # -------- Tiempos base --------
    t_iny, t_sost_base, t_enf_base = calcular_tiempos_base(peso_total, espesor)
    t_sost = t_sost_base
    t_enf = t_enf_base

    alertas = []

    # -------- Ajustes por relación altura/diámetro (solo cilíndrica) --------
    if geo == "Cilíndrica" and diametro and altura:
        relacion_hd = float(altura) / float(diametro)

        # Ajuste de sostenimiento según altura/diámetro
        # A mayor relación, más tiempo de sostenimiento para evitar colapso interno
        factor_sost = 1.0 + 0.05 * max(relacion_hd - 1.0, 0)   # +5% por cada unidad sobre 1
        factor_sost = min(factor_sost, 1.5)                    # Máx +50%
        t_sost = round(t_sost_base * factor_sost, 2)

        # Ajuste de enfriamiento según altura/diámetro
        factor_enf = 1.0 + 0.1 * max(relacion_hd - 1.0, 0)     # +10% por cada unidad sobre 1
        factor_enf = min(factor_enf, 2.0)                      # Máx x2
        t_enf = round(t_enf_base * factor_enf, 2)

        # Riesgo de deformación (pieza muy esbelta)
        if relacion_hd >= 3.0:
            alertas.append(
                f"Pieza cilíndrica esbelta (h/D = {relacion_hd:.2f}). Riesgo de deformación, recomienda refuerzo en sostenimiento y enfriamiento."
            )

        # Riesgo de colapso en paredes delgadas
        if relacion_hd >= 4.0 and espesor <= 1.0:
            alertas.append(
                f"Relación h/D = {relacion_hd:.2f} con espesor {espesor} mm. Alto riesgo de colapso en paredes delgadas."
            )

    # -------- Tiempos mecánicos y ciclo total --------
    t_mecanico = float(tiempo_cierre) + float(tiempo_apertura) + float(tiempo_expulsion)
    t_ciclo = round(t_iny + t_sost + t_enf + t_mecanico, 2)

    # -------- Temperaturas --------
    zona_post, zona_trans, zona_ant, boquilla = temperaturas(material, reciclado, carga)
    temp_molde = "20–30 °C (frío) / 30–40 °C (templado)"

    # -------- Tabla de resultados --------
    tabla = [
        ["Temperatura zona posterior", f"{zona_post} °C"],
        ["Temperatura zona transición", f"{zona_trans} °C"],
        ["Temperatura zona anterior", f"{zona_ant} °C"],
        ["Temperatura boquilla", f"{boquilla} °C"],
        ["Temperatura molde", temp_molde],
        ["Área proyectada total", f"{round(area_total,2)} cm²"],
        ["Tonelaje requerido", f"{tonelaje_req} t"],
        ["Tonelaje disponible", f"{tonelaje_maquina} t"],
        ["Uso del husillo", f"{uso_husillo} %"],
        ["Tiempo de inyección", f"{t_iny} s"],
        ["Tiempo de sostenimiento (ajustado)", f"{t_sost} s"],
        ["Tiempo de enfriamiento (ajustado)", f"{t_enf} s"],
        ["Tiempo cierre", f"{tiempo_cierre} s"],
        ["Tiempo apertura", f"{tiempo_apertura} s"],
        ["Tiempo expulsión", f"{tiempo_expulsion} s"],
        ["Tiempo de ciclo total", f"{t_ciclo} s"],
    ]

    df = pd.DataFrame(tabla, columns=["Parámetro", "Valor"])
    st.subheader("Resultados")
    st.dataframe(df, use_container_width=True)

    # -------- Alertas de proceso --------
    if alertas:
        st.subheader("Alertas de proceso")
        for a in alertas:
            st.warning(a)
    else:
        st.info("Sin alertas críticas según los parámetros ingresados.")
