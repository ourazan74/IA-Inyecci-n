import math
import streamlit as st
import pandas as pd
import numpy as np
from PIL import Image

# ---------------------------------------------------------
# Funciones auxiliares
# ---------------------------------------------------------

def calcular_area_proyectada(tipo, largo=None, ancho=None, diametro=None, area_manual=None):
    """Calcula el área proyectada en cm² según la geometría básica."""
    try:
        if tipo == "Rectangular":
            return float(largo) * float(ancho) / 100.0  # mm² → cm²
        elif tipo == "Cilíndrica":
            radio = float(diametro) / 2.0
            return (math.pi * radio * radio) / 100.0    # mm² → cm²
        else:
            return float(area_manual)
    except:
        return 0.0


def calcular_area_irregular_desde_imagen(largo_max_mm, ancho_max_mm, imagen):
    """
    Calcula un área proyectada aproximada en cm² para figura irregular
    usando:
      - largo máximo real (mm)
      - ancho máximo real (mm)
      - foto de la pieza o cavidad
    """
    try:
        img = Image.open(imagen).convert("L")  # escala de grises
        arr = np.array(img)

        # Umbral simple: asumimos pieza más oscura que el fondo
        thresh = np.mean(arr)
        mask = arr < thresh  # True donde está la pieza

        # Si no se detecta nada, devolvemos 0
        if not np.any(mask):
            return 0.0

        # Bounding box de la pieza en píxeles
        ys, xs = np.where(mask)
        min_x, max_x = xs.min(), xs.max()
        min_y, max_y = ys.min(), ys.max()

        width_px = max_x - min_x + 1
        height_px = max_y - min_y + 1

        # Escala en mm/px según largo y ancho máximos reales
        mm_per_px_x = float(largo_max_mm) / float(width_px)
        mm_per_px_y = float(ancho_max_mm) / float(height_px)

        # Área en píxeles de la pieza
        pixel_count = mask.sum()

        # Área real en mm²
        area_mm2 = pixel_count * mm_per_px_x * mm_per_px_y

        # Convertimos a cm²
        area_cm2 = area_mm2 / 100.0
        return area_cm2
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

altura_pieza = None
diametro = None

if geo == "Rectangular":
    largo = st.number_input("Largo (mm)", min_value=0.1)
    ancho = st.number_input("Ancho (mm)", min_value=0.1)
    altura_pieza = st.number_input("Altura (mm)", min_value=0.1)
    area = calcular_area_proyectada("Rectangular", largo=largo, ancho=ancho)

elif geo == "Cilíndrica":
    diametro = st.number_input("Diámetro (mm)", min_value=0.1)
    altura_pieza = st.number_input("Altura (mm)", min_value=0.1)
    area = calcular_area_proyectada("Cilíndrica", diametro=diametro)

else:  # Irregular
    st.markdown("### Datos para figura irregular")
    largo_max = st.number_input("Largo máximo (mm)", min_value=0.1)
    ancho_max = st.number_input("Ancho máximo (mm)", min_value=0.1)
    altura_pieza = st.number_input("Altura (mm)", min_value=0.1)

    imagen = st.file_uploader("Sube una foto de la pieza o cavidad (vista superior)", type=["png", "jpg", "jpeg"])

    area = 0.0
    if imagen is not None and largo_max > 0 and ancho_max > 0:
        st.info("Calculando área proyectada aproximada a partir de la imagen…")
        area = calcular_area_irregular_desde_imagen(largo_max, ancho_max, imagen)
        st.write(f"Área proyectada estimada desde imagen: **{area:.2f} cm²**")
    else:
        st.warning("Si no subes imagen, ingresa un valor manual de área proyectada.")
        area_manual = st.number_input("Área proyectada manual (cm²)", min_value=0.1)
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

    alertas = []

    # -------- Tonelaje y uso de husillo --------
    tonelaje_req = round(calcular_tonelaje(area_total), 2)
    uso_husillo = round((float(peso_total) / float(cap_inyeccion)) * 100.0, 1)

    # -------- Tiempos base --------
    t_iny, t_sost_base, t_enf_base = calcular_tiempos_base(peso_total, espesor)
    t_sost = t_sost_base
    t_enf = t_enf_base

    # -------- Ajustes por relación altura/espesor (h/e) --------
    if altura_pieza is not None and espesor > 0:
        relacion_he = float(altura_pieza) / float(espesor)

        # Ajuste de sostenimiento según h/e
        factor_sost_he = 1.0 + 0.03 * max(relacion_he - 5.0, 0)  # a partir de h/e > 5
        factor_sost_he = min(factor_sost_he, 1.5)                # máx +50%
        t_sost = round(t_sost * factor_sost_he, 2)

        # Ajuste de enfriamiento según h/e
        factor_enf_he = 1.0 + 0.05 * max(relacion_he - 5.0, 0)
        factor_enf_he = min(factor_enf_he, 2.0)                  # máx x2
        t_enf = round(t_enf * factor_enf_he, 2)

        # Riesgos por h/e
        if relacion_he >= 20:
            alertas.append(
                f"Relación altura/espesor h/e = {relacion_he:.1f}. Riesgo de deformación (pieza muy esbelta)."
            )
        if relacion_he >= 30 and espesor <= 1.0:
            alertas.append(
                f"h/e = {relacion_he:.1f} con espesor {espesor} mm. Alto riesgo de colapso en paredes delgadas."
            )

    # -------- Ajustes adicionales para cilíndricas (h/D) --------
    if geo == "Cilíndrica" and diametro is not None and altura_pieza is not None and diametro > 0:
        relacion_hd = float(altura_pieza) / float(diametro)

        # Ajuste extra de sostenimiento por h/D
        factor_sost_hd = 1.0 + 0.05 * max(relacion_hd - 1.0, 0)
        factor_sost_hd = min(factor_sost_hd, 1.5)
        t_sost = round(t_sost * factor_sost_hd, 2)

        # Ajuste extra de enfriamiento por h/D
        factor_enf_hd = 1.0 + 0.1 * max(relacion_hd - 1.0, 0)
        factor_enf_hd = min(factor_enf_hd, 2.0)
        t_enf = round(t_enf * factor_enf_hd, 2)

        if relacion_hd >= 3.0:
            alertas.append(
                f"Pieza cilíndrica esbelta (h/D = {relacion_hd:.2f}). Riesgo de deformación, refuerce sostenimiento y enfriamiento."
            )
        if relacion_hd >= 4.0 and espesor <= 1.0:
            alertas.append(
                f"h/D = {relacion_hd:.2f} con espesor {espesor} mm. Alto riesgo de colapso en paredes delgadas."
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
    st.subheader("Alertas de proceso")
    if alertas:
        for a in alertas:
            st.warning(a)
    else:
        st.info("Sin alertas críticas según los parámetros ingresados.")
