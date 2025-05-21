import pandas as pd, os, numpy as np, matplotlib.pyplot as plt, tkinter as tk, pathlib as Path; from scipy import integrate; import re
## Funciones generales
def menu():
    print("\n🔹 Menú de Procesos 🔹")
    print("1. GRAFICAR CICLOS")
    print("2. PROCESO AUTOMATICO INICIAL")
    print("3. PROCESO AUTOMATICO GENERACION SUBGRUPOS")
    print("4. PROCESO AUTOMATICO ANALISIS FINAL")
    print("5. GRAFICA DE PRESION Y FLUJO")
    print("0 - EXIT")
def continuar_proceso():
    while True:
        respuesta = input("¿Deseas continuar? (S para sí, N para no): ").strip().upper()
        
        if respuesta == "S":
            return True  # Continuar con el proceso
        elif respuesta == "N":
            return False  # Detener el proceso
        else:
            print("⚠️ Entrada inválida. Ingresa 'S' para sí o 'N' para no.")
def leer_excel_con_ruta(ruta):
    return pd.read_excel(ruta)
## Procesamiento inicial
# A.PROCEDIMIENTO INICAL PARA DETERMINACION DE CICLOS Y FASES DE CADA CICLO RESPIRATORIO
def procesar_dataframe(df):
    # 1. Eliminar las columnas no deseadas
    columnas_a_eliminar = ["flow_1", "flow_2", "p0"]
    df = df.drop(columns=columnas_a_eliminar, errors="ignore")  # Evita errores si las columnas no existen

    # 2. Renombrar las columnas
    columnas_a_renombrar = {
        "flow": "flujo",
        "p1": "presion",
        "v": "volumen"
    }
    df = df.rename(columns=columnas_a_renombrar)

    # 3. Crear nuevas columnas "ciclo" y "fase" con valores iniciales en blanco
    df["ciclo"] = 0  
    df["fase"] = ""
    df = df.round(2)

    # 4. Identificación de ciclos
    ciclo_actual = 0
    inicio_ciclo = False

    # 5. Identificar ciclos basados en la columna "volumen"
    for i in range(len(df)):
        if df.iloc[i]['volumen'] == 0.00:
            if not inicio_ciclo:
                ciclo_actual += 1
                inicio_ciclo = True
        else:
            inicio_ciclo = False
        if ciclo_actual > 0:
            df.at[i, 'ciclo'] = ciclo_actual
    return df
def deltas(df):
    # Calcular la diferencia de presión entre la fila actual y la siguiente
    df['delta_Presion'] = df['presion'] - df['presion'].shift(-1)

    # Redondear la nueva columna a dos cifras decimales
    df['delta_Presion'] = df['delta_Presion'].round(2)

    # Calcular la diferencia de VOLUMEN entre la fila actual y dos filas siguientes
    df['delta_Volumen'] = df['volumen'].shift(-2) - df['volumen']

    # Redondear la nueva columna a dos cifras decimales
    df['delta_Volumen'] = df['delta_Volumen'].round(2)

    df['delta_flujo'] = df['flujo'] - df['flujo'].shift(1)
    return df
def fases_ciclos(df):
    df_copy = df.copy()
    df_copy['fase'] = ''

    ciclos = df_copy['ciclo'].unique()

    for ciclo in ciclos:
        mask_ciclo = df_copy['ciclo'] == ciclo
        indices_ciclo = df_copy[mask_ciclo].index

        if len(indices_ciclo) == 0:
            continue

        # Encontrar el inicio de la fase I (primer flujo > 1)
        inicio_i = indices_ciclo[df_copy.loc[indices_ciclo, 'flujo'] > 0.1].min()
        
        # Determinar el volumen máximo del ciclo
        volumen_max = df_copy.loc[indices_ciclo, 'volumen'].max()
        umbral_volumen = volumen_max * 0.5

        # Encontrar el fin de la fase I (flujo < 4 y volumen > 50% del volumen máximo)
        fin_i = indices_ciclo[(indices_ciclo > inicio_i) &
                              (df_copy.loc[indices_ciclo, 'flujo'] < 4) &
                              (df_copy.loc[indices_ciclo, 'volumen'] > umbral_volumen)].min() 
        
        if pd.notna(inicio_i) and pd.notna(fin_i):
            df_copy.loc[inicio_i:fin_i-1, 'fase'] = 'I'
            
            # Inicio de la pausa (justo después del fin de la fase I)
            inicio_p = fin_i
            
            # Fin de la pausa (flujo fuera del rango [-4, 4] y delta de presión < 1)
            fin_p = indices_ciclo[(indices_ciclo > inicio_p) &
                                  (~df_copy.loc[indices_ciclo, 'flujo'].between(-4, 4)) &
                                  (df_copy.loc[indices_ciclo, 'delta_Presion'] < 3)].min() #Para el flujo, entonces el rango es de 4 a -4 para la pausa, y verificar mientras el delta de presión es mayor que 1
            
            # Si el flujo en fin_p es menor que -10, tomar el valor anterior
            if pd.notna(fin_p) and df_copy.loc[fin_p, 'flujo'] < -10:
                fin_p_alternativo = indices_ciclo[(indices_ciclo < fin_p) & (df_copy.loc[indices_ciclo, 'flujo'] < -4)].max()
                if pd.notna(fin_p_alternativo):
                    fin_p = fin_p_alternativo
            
            if pd.notna(fin_p):
                df_copy.loc[inicio_p:fin_p-1, 'fase'] = 'P'
                
                # Inicio de la fase E (flujo < -4 y delta de presión > 1)
                inicio_e = indices_ciclo[(indices_ciclo >= fin_p) &
                                         (df_copy.loc[indices_ciclo, 'flujo'] < -4.00) &
                                         (df_copy.loc[indices_ciclo, 'delta_Volumen'] < -2.00)].min()
                
                # Si no se encuentra inicio_e, tomar el valor justo después de fin_p
                if pd.isna(inicio_e):
                    print(f"El ciclo {ciclo} Es nan para el inicio de e, se toma cuando acaba la pausa")
                    inicio_e = fin_p + 1
                
                if pd.notna(inicio_e):
                    df_copy.loc[inicio_e:indices_ciclo[-1], 'fase'] = 'E'
                # print(f"Proceso de identificación de fases para el ciclo {ciclo}.")
                # print(f"Fase I empieza en: {inicio_i} y termina en: {fin_i}")
                # print(f"Fase P empieza en: {inicio_p} y termina en: {fin_p}")
                # print(f"Fase E empieza en: {inicio_e} y termina en: {indices_ciclo[-1]}")
                # print(f"flujo y volumen en inicio de la i {df_copy.loc[inicio_i, 'flujo']} y {df_copy.loc[inicio_i, 'volumen']}")
                # print(f"flujo y volumen en fin de la i {df_copy.loc[fin_i, 'flujo']} y {df_copy.loc[fin_i, 'volumen']}")
                # print(f"flujo y volumen en inicio de la p {df_copy.loc[inicio_p, 'flujo']} y {df_copy.loc[inicio_p, 'volumen']}")
                # print(f"flujo y volumen en fin de la p {df_copy.loc[fin_p, 'flujo']} y {df_copy.loc[fin_p, 'volumen']}")
                # print(f"flujo y volumen en inicio de la e {df_copy.loc[inicio_e, 'flujo']} y {df_copy.loc[inicio_e, 'volumen']}")
                # print(f"flujo y volumen en fin de la e {df_copy.loc[indices_ciclo[-1], 'flujo']} y {df_copy.loc[indices_ciclo[-1], 'volumen']}")
                # breakpoint()
    
    return df_copy
 #Agregar las lineas para guardar el archivo
def guardar_ciclos_inicio_fin(df,paciente):
    print("\nGuardando el resultado en un archivo de Excel...")
    ciclos_min = df["ciclo"].min()
    ciclos_max = df["ciclo"].max()

    directorio_resultados = os.path.join(os.getcwd(), f"Paciente_{paciente}")
    os.makedirs(directorio_resultados, exist_ok=True)
    nombre_archivo = os.path.join(directorio_resultados, f"Paciente_{paciente}_proceso_ciclos y fases_ciclo inicio({ciclos_min})_ciclo final({ciclos_max}).xlsx")
    df.to_excel(nombre_archivo, index=False, engine="openpyxl")
    ruta_completa = os.path.join(os.getcwd(), f"Paciente_{paciente}_proceso_ciclos y fases_ciclo inicio({ciclos_min})_ciclo final({ciclos_max}).xlsx")
    print("¡Proceso finalizado! 🎉")
    print(f"✅ Archivo guardado en: {ruta_completa}")
# B.PROCESO DE SINCRONIZACION Y AJUSTE DE ARCHIVOS
#Ojo con el automatico 1, recordar ponerle el imput a los retrasos
def retrasoO2(df, retraso):
    #columnas_principales = ['t', 'presion', 'flujo', 'volumen', 'ciclo', 'delta_presion', 'delta_volumen', 'fase'] # para retrasar los gases
    columnas_principales = ['o2', 'co2'] # para adelantar los gases
    retraso = int(float(retraso)/10)
     # Aplicar retraso principal
    for col in columnas_principales:
        if col in df.columns:
            df[col] = df[col].shift(retraso)
    return df
def retrasoCO2(df,retraso):
    retraso = int(float(retraso)/10)
    # Aplicar retraso al CO2
    if 'co2' in df.columns:
        df['co2'] = df['co2'].shift(retraso)
    return df
def eliminar_filas(df,retrasoO,retrasoCO):
    retrasoO =int(float(retrasoO)/10)
    retrasoCO =int(float(retrasoCO)/10)
    max_retraso = max(retrasoO,retrasoCO)
    df = df.iloc[max_retraso:].reset_index(drop=True)
    return df
def grafica(df):
    ciclo_inicio = int(input("Ingrese el ciclo de inicio: "))
    ciclo_fin = int(input("Ingrese el ciclo de fin: "))

    # Filtrar datos por los ciclos seleccionados
    df_filtrado = df[(df["ciclo"] >= ciclo_inicio) & (df["ciclo"] < ciclo_fin+1)]

    # Crear la figura y ejes
    fig, ax1 = plt.subplots(figsize=(10, 5))

    # Eje Y izquierdo (Presión, O2, CO2, Flujo)
    ax1.set_xlabel("Tiempo (s)")
    ax1.set_ylabel("Presión (cmH2O) / Concentraciones (%) / Flujo (ml/s)")
    ax1.plot(df_filtrado["t"], df_filtrado["presion"], label="Presión", color="orange", linestyle="-", linewidth=0.6)
    ax1.plot(df_filtrado["t"], df_filtrado["o2"], label="O2", color="green", linestyle="-", linewidth=0.6)
    ax1.plot(df_filtrado["t"], df_filtrado["co2"], label="CO2", color="gray", linestyle=":", linewidth=0.6)
    ax1.plot(df_filtrado["t"], df_filtrado["flujo"], label="Flujo", color="red", linestyle="--", linewidth=0.6)
    ax1.tick_params(axis='y')

    # Crear un segundo eje Y para Volumen
    ax2 = ax1.twinx()
    ax2.set_ylabel("Volumen (ml)")
    ax2.plot(df_filtrado["t"], df_filtrado["volumen"], label="Volumen", color="blue", linestyle=":", linewidth=0.6)
    ax2.tick_params(axis='y', colors="blue")

    # Agregar leyendas
    ax1.legend(loc="upper left")
    ax2.legend(loc="upper right")

    # Título y mostrar la gráfica
    plt.title(f"Evolución de Presión, O2, CO2, Flujo y Volumen - Ciclos {ciclo_inicio} al {ciclo_fin}")
    plt.grid(True)
    plt.show()
def grafica_comp(df):
    ciclo_inicio = int(input("Ingrese el ciclo de inicio: "))
    ciclo_fin = int(input("Ingrese el ciclo de fin: "))

    # Filtrar datos por los ciclos seleccionados
    df_filtrado = df[(df["ciclo"] >= ciclo_inicio) & (df["ciclo"] < ciclo_fin+1)]

    # Crear la figura y ejes
    fig, ax1 = plt.subplots(figsize=(10, 5))

    # Eje Y izquierdo (Presión y Flujo)
    ax1.set_xlabel("Tiempo (s)")
    ax1.set_ylabel("Presión (cmH2O) / Flujo (ml/s)")
    ax1.plot(df_filtrado["t"], df_filtrado["presion"], label="Presión", color="orange", linestyle="-", linewidth=0.6)
    ax1.plot(df_filtrado["t"], df_filtrado["flujo"], label="Flujo", color="red", linestyle="--", linewidth=0.6)
    ax1.tick_params(axis='y')

    # Agregar leyenda
    ax1.legend(loc="upper left")

    # Título y mostrar la gráfica
    plt.title(f"Evolución de Presión y Flujo - Ciclos {ciclo_inicio} al {ciclo_fin}")
    plt.grid(True)
    plt.show()
def guardar_correcion_retraso(df,paciente):
    print("\nGuardando el resultado en un archivo de Excel...")
    directorio_resultados = os.path.join(os.getcwd(), f"Paciente_{paciente}")
    os.makedirs(directorio_resultados, exist_ok=True)
    nombre_archivo = os.path.join(directorio_resultados, f"Paciente_{paciente}_correcion_retraso.xlsx")
    df.to_excel(nombre_archivo, index=False, engine="openpyxl")
    ruta_completa = os.path.join(os.getcwd(), f"Paciente_{paciente}_correcion_retraso.xlsx")
    print("¡Proceso finalizado! 🎉")
    print(f"✅ Archivo guardado en: {ruta_completa}")
# C. PROCEDIMIENTO PARA DETERMINAR VARIABLES MODIFICAFAS A CADA PACIENTE
def crear_resumen_ciclos(df):
    resultados = []
    ciclos = sorted(df['ciclo'].unique())
    for ciclo in ciclos:
        # Filtrar datos del ciclo actual
        datos_ciclo = 0
        datos_ciclo = df[df['ciclo'] == ciclo]
        
        # Obtener t inicio y t final
        t_inicio = datos_ciclo['t'].iloc[0]
        t_final = datos_ciclo['t'].iloc[-1]
        
        # Filtrar fases I y P para cálculos
        datos_I_P = datos_ciclo[datos_ciclo['fase'].isin(['I', 'P'])]
        
        # Filtrar fase E
        datos_E = datos_ciclo[datos_ciclo['fase'] == 'E']
        
        # Calcular estadísticas
        promedio_o2_I_P = datos_I_P['o2'].mean()
        promedio_presion_E = datos_ciclo['presion'].iloc[-30:].mean()
        # print(f"el promedio de la presion es {promedio_presion_E} para el ciclo {ciclo}")
        vol_max_I_P = datos_I_P['volumen'].max()
        t_total_ciclo = t_final - t_inicio
        frecuencia = 60 / (t_total_ciclo / 1000)  # Convertir ms a segundos
        
        # Agregar resultados
        resultados.append({
            'ciclo': ciclo,
            't_inicio': t_inicio,
            'promedio_o2_I': promedio_o2_I_P,
            'promedio_presion_E': promedio_presion_E,
            'vol_max_I_P': vol_max_I_P,
            't_total_ciclo': t_total_ciclo,
            'frecuencia': frecuencia
        })
    
    # Crear DataFrame con los resultados
    df_resumen = pd.DataFrame(resultados)
    df_resumen = df_resumen.round(2)
    return df_resumen
def guardar_promedios_por_ciclos(df,paciente):
    print("Guardando el resultado en un archivo de Excel...")
    directorio_resultados = os.path.join(os.getcwd(), f"Paciente_{paciente}")
    os.makedirs(directorio_resultados, exist_ok=True)
    nombre_archivo = os.path.join(directorio_resultados, f"Paciente_{paciente}_Promedios_por_Ciclos_PEEP_Vt_F.xlsx")
    df.to_excel(nombre_archivo, index=False, engine="openpyxl")
    ruta_completa = os.path.join(os.getcwd(), f"Paciente_{paciente}_Promedios_por_Ciclos_PEEP_Vt_F.xlsx")
    print("¡Proceso finalizado! 🎉")
    print(f"✅ Archivo guardado en: {ruta_completa}")
def dividir_archivo_por_ciclos(df, rangos_ciclos, num_paciente):
    if "ciclo" not in df.columns:
        raise ValueError("⚠️ Error: La columna 'ciclo' no se encontró en el DataFrame.")
    
    df = df.drop(columns=["delta_Presion", "delta_Volumen"], errors='ignore')  # Elimina columnas si existen
    
    # Crear directorios
    directorio_resultados = os.path.join(os.getcwd(), f"Paciente_{num_paciente}")
    os.makedirs(directorio_resultados, exist_ok=True)
    subcarpeta = os.path.join(directorio_resultados, f"Subsets_Crudos_Paciente_{num_paciente}")
    os.makedirs(subcarpeta, exist_ok=True)
    
    # Generar subsets
    for i, (ciclo_inicio, ciclo_fin) in enumerate(rangos_ciclos, 1):
        subset = df[df['ciclo'].between(ciclo_inicio, ciclo_fin)].copy()
        
        if subset.empty:
            print(f"⚠️ Advertencia: El rango {ciclo_inicio}-{ciclo_fin} no tiene datos en 'ciclo'.")
            continue
        
        nombre_archivo = os.path.join(subcarpeta, f"paciente_{num_paciente}_set_{i}_de_{len(rangos_ciclos)}.xlsx")
        subset.to_excel(nombre_archivo, index=False)
        
        print(f"\nSet {i} guardado:")
        print(f"- Ciclos: {ciclo_inicio} a {ciclo_fin}")
        print(f"- Archivo guardado como: {nombre_archivo}")
        print(f"- Número de ciclos en el set: {len(subset['ciclo'].unique())}")
        print(f"- Número de filas en el set: {len(subset)}")
# D. PROCEDIMIENTO PARA DETERMINAR ESPACIO MUERTO Y CICLOS ASINCRÓNICOS
def VolE_and_VDana(df):
    # Crear columna para el volumen espiratorio corregido (Vol_E)
    # Reset index for easier processing during grouping
    df.reset_index(drop=True, inplace=True)
    # Initialize the new column with NaN values
    df['vol_E'] = np.nan
    # Group the data by "Ciclo" and process each group
    for cycle, group in df.groupby('ciclo'):
        # Find rows with Fase == "E" within the current cycle
        phase_e_rows = group[group['fase'] == "E"]
        if not phase_e_rows.empty:
            # Take the first "volumen" value of the Fase == "E" rows
            reference_volume = phase_e_rows.iloc[0]['volumen']
            # Update "vol_E" for rows where Fase == "E"
            df.loc[phase_e_rows.index, 'vol_E'] = (reference_volume - df.loc[phase_e_rows.index, 'volumen']).round(2)
    return df
def Columnas_para_fase_E(df):
    # Initialize new columns
    df['CA'] = np.nan
    df['delta_V(iE)'] = np.nan
    df['Factor_(1-co2/CA)'] = np.nan
    df['VD_parcial'] = np.nan

    # Group by 'Ciclo'
    for cycle, group in df.groupby('ciclo'):
        # Filter rows for phase 'E'
        phase_e_rows = group[group['fase'] == "E"]
        
        # Skip processing if no rows for phase 'E'
        if phase_e_rows.empty:
            continue
        
        # Calculate CA: Average of last 100 CO2 values in phase 'E'
        ca_value = phase_e_rows['co2'].iloc[-100:].mean()
        df.loc[phase_e_rows.index, 'CA'] = ca_value

        # Calculate delta_V(iE)
        delta_v = [0]  # First row in phase 'E' gets 0
        delta_v.extend(np.diff(phase_e_rows['vol_E'].fillna(0)))  # Difference between consecutive vol_E values
        df.loc[phase_e_rows.index, 'delta_V(iE)'] = np.round(delta_v, 1)

        # Calculate Factor_(1-co2/CA)
        df.loc[phase_e_rows.index, 'Factor_(1-co2/CA)'] = (
            1 - (phase_e_rows['co2'] / ca_value)
        ).round(4)

        # Calculate VD_parcial
        df.loc[phase_e_rows.index, 'VD_parcial'] = (
            df.loc[phase_e_rows.index, 'Factor_(1-co2/CA)'] * df.loc[phase_e_rows.index, 'delta_V(iE)']
        ).round(4)

    df = df
    # Round the specified columns to 2 decimal places
    columns_to_round = ['CA', 'Factor_(1-co2/CA)', 'VD_parcial']
    df[columns_to_round] = df[columns_to_round].round(2)

        # Create the "VDana" column by summing up "VD_parcial" for each cycle
    df['VDana'] = df.groupby('ciclo')['VD_parcial'].transform('sum')

    # Round "VDana" to 2 decimal places
    df['VDana'] = df['VDana'].round(2)

    return df
def det_asincronias(data_updated):      
    data_updated['delta_V(iI)'] = np.nan 

    for cycle, group in data_updated.groupby('ciclo'):

        filtered_rows = group[(group['fase'] == "I") | (group['fase'] == "P")]

        if filtered_rows.empty:
            continue
        delta_v_ii = [0]  
        delta_v_ii.extend(np.diff(filtered_rows['volumen'].fillna(0))) 
        data_updated.loc[filtered_rows.index, 'delta_V(iI)'] = np.round(delta_v_ii, 2) 

    data_updated['delta_V(iE)'] = np.nan

    for cycle, group in data_updated.groupby('ciclo'):
        phase_e_rows = group[group['fase'] == "E"]
        if phase_e_rows.empty:
            continue
        delta_v_ie = [0]  
        delta_v_ie.extend(np.diff(phase_e_rows['vol_E'].fillna(0)))
        data_updated.loc[phase_e_rows.index, 'delta_V(iE)'] = np.round(delta_v_ie, 2) 

    data_updated['sum_delta_V(iI)'] = np.nan

    for cycle, group in data_updated.groupby('ciclo'):
        filtered_rows = group[(group['fase'] == "I") | (group['fase'] == "P")]
        if filtered_rows.empty:
            continue
        sum_delta_vi = filtered_rows['delta_V(iI)'].sum()
        first_index = group.index[0]
        data_updated.loc[first_index, 'sum_delta_V(iI)'] = np.round(sum_delta_vi, 2)

    data_updated['sum_delta_V(iE)'] = np.nan

    for cycle, group in data_updated.groupby('ciclo'):
        phase_e_rows = group[group['fase'] == "E"]
        if phase_e_rows.empty:
            continue
        sum_delta_ve = phase_e_rows['delta_V(iE)'].sum()
        first_index = group.index[0]
        data_updated.loc[first_index, 'sum_delta_V(iE)'] = np.round(sum_delta_ve, 2)

    data_updated['Dif_vol I_E'] = np.nan

    for cycle, group in data_updated.groupby('ciclo'):
        first_row = group.iloc[0]
        sum_delta_vi = first_row['sum_delta_V(iI)']
        sum_delta_ve = first_row['sum_delta_V(iE)']
        if not pd.isna(sum_delta_vi) and not pd.isna(sum_delta_ve):
            difference = sum_delta_vi - sum_delta_ve
            data_updated.loc[group.index[0], 'Dif_vol I_E'] = np.round(difference, 1)

    filtered_data = data_updated[data_updated['Dif_vol I_E'].notna() & (data_updated['Dif_vol I_E'] != 0)]

    median_dif_vol_ie = filtered_data['Dif_vol I_E'].median()
    mean_dif_vol_ie = filtered_data['Dif_vol I_E'].mean()

    summary_row = {
        't': 'Summary',
        'Dif_vol I_E': f"Median: {round(median_dif_vol_ie, 1)}, Mean: {round(mean_dif_vol_ie, 1)}"
    }

    data_updated = pd.concat([data_updated, pd.DataFrame([summary_row])], ignore_index=True)

    data_updated['Dif_vol I_E'] = pd.to_numeric(data_updated['Dif_vol I_E'], errors='coerce')

    filtered_data = data_updated.dropna(subset=['Dif_vol I_E'])
    filtered_data = filtered_data[filtered_data['Dif_vol I_E'] != 0]
    median_dif_vol_ie = filtered_data['Dif_vol I_E'].median()

    lower_bound = median_dif_vol_ie - 40
    upper_bound = median_dif_vol_ie + 40

    first_indices = data_updated.groupby('ciclo')['t'].idxmin()

    data_updated['tipo de ciclo'] = ""
    for index in first_indices:
        row = data_updated.loc[index]
        if not pd.isna(row['Dif_vol I_E']) and row['Dif_vol I_E'] != 0:
            tipo = "SINC" if lower_bound <= row['Dif_vol I_E'] <= upper_bound else "ASCR"
            data_updated.at[index, 'tipo de ciclo'] = tipo
    data_updated = data_updated

    data_updated['VDana_new'] = data_updated['VDana']

    last_sinc_vdana = None
    for index, row in data_updated.iterrows():
        if row['tipo de ciclo'] == "SINC":
            # Update the last "VDana_new" value for "SINC" cycles
            last_sinc_vdana = row['VDana']
        elif row['tipo de ciclo'] == "ASCR" and last_sinc_vdana is not None:
            # Assign the last "SINC" VDana_new value to "ASCR" cycles
            data_updated.at[index, 'VDana_new'] = last_sinc_vdana
    data_updated = data_updated
    return data_updated
def VO2_CO2_Real(df):
    df["delta_VO2_INS/ESP"] = df.apply(lambda row: round((row["o2"] / 100) * row["delta_V(iI)"], 3) 
    if row["fase"] in ["I", "P"] 
    else round((row["o2"] / 100) * row["delta_V(iE)"], 3), axis=1)

    suma_ip = df[df["fase"].isin(["I", "P"])].groupby("ciclo")["delta_VO2_INS/ESP"].sum()

    suma_e = df[df["fase"] == "E"].groupby("ciclo")["delta_VO2_INS/ESP"].sum()

    vo2_ciclo_values = (suma_ip - suma_e).round(3)

    df["VO2_ciclo"] = df["ciclo"].map(vo2_ciclo_values)

    df["VO2_ciclo"] = df["VO2_ciclo"].round(1)

    df["delta_VCO2_INS/ESP"] = df.apply(lambda row: round((row["co2"] / 100) * row["delta_V(iI)"], 3) 
                                    if row["fase"] in ["I", "P"] 
                                    else round((row["co2"] / 100) * row["delta_V(iE)"], 3), axis=1)

    suma_e = df[df["fase"] == "E"].groupby("ciclo")["delta_VCO2_INS/ESP"].sum()

    suma_ip = df[df["fase"].isin(["I", "P"])].groupby("ciclo")["delta_VCO2_INS/ESP"].sum()

    vco2_ciclo_values = (suma_e - suma_ip).round(3)

    df["VCO2_ciclo"] = df["ciclo"].map(vco2_ciclo_values)

    df["VCO2_ciclo"] = df["VCO2_ciclo"].round(1)

    def encontrar_dif_vol_ie_apropiado(ciclo_idx, ciclo_tipo, dif_vol_ie):
        # Si es un ciclo sincrónico con Dif_vol_I_E positivo, usar su propio valor
        if ciclo_tipo == "SINC" and dif_vol_ie > 0:
            return dif_vol_ie
            
        ciclos_df = df.drop_duplicates('ciclo')[['ciclo', 'tipo de ciclo', 'Dif_vol I_E']].reset_index()
        ciclos_df = ciclos_df.sort_values('ciclo')
        
        current_idx = ciclos_df[ciclos_df['ciclo'] == ciclo_idx].index[0]
        
        for i in range(current_idx - 1, -1, -1):
            if ciclos_df.iloc[i]['tipo de ciclo'] == "SINC" and ciclos_df.iloc[i]['Dif_vol I_E'] > 0:
                return ciclos_df.iloc[i]['Dif_vol I_E']
        
        for i in range(current_idx + 1, len(ciclos_df)):
            if ciclos_df.iloc[i]['tipo de ciclo'] == "SINC" and ciclos_df.iloc[i]['Dif_vol I_E'] > 0:
                return ciclos_df.iloc[i]['Dif_vol I_E']
                
        return dif_vol_ie

    df["VO2_ciclo_correcion_fuga"] = np.nan
    
    for ciclo in df["ciclo"].dropna().unique():
        ciclo_mask = df["ciclo"] == ciclo
        
        ciclo_tipo = df.loc[ciclo_mask, "tipo de ciclo"].iloc[0] if "tipo de ciclo" in df.columns else "SINC"
        dif_vol_ie_original = df.loc[ciclo_mask, "Dif_vol I_E"].iloc[0] if not df.loc[ciclo_mask, "Dif_vol I_E"].isna().all() else 0
        
        dif_vol_ie_apropiado = encontrar_dif_vol_ie_apropiado(ciclo, ciclo_tipo, dif_vol_ie_original)
        
        avg_o2 = df.loc[ciclo_mask, "o2"].mean()
        correction = (avg_o2 / 100) * dif_vol_ie_apropiado
        
        vo2_ciclo = df.loc[ciclo_mask, "VO2_ciclo"].iloc[0]
        df.loc[ciclo_mask, "VO2_ciclo_correcion_fuga"] = round(vo2_ciclo - correction, 2)

    df["VCO2_ciclo_correcion_fuga"] = np.nan
    
    for ciclo in df["ciclo"].dropna().unique():
        ciclo_mask = df["ciclo"] == ciclo
        
        ciclo_tipo = df.loc[ciclo_mask, "tipo de ciclo"].iloc[0] if "tipo de ciclo" in df.columns else "SINC"
        dif_vol_ie_original = df.loc[ciclo_mask, "Dif_vol I_E"].iloc[0] if not df.loc[ciclo_mask, "Dif_vol I_E"].isna().all() else 0
        
        dif_vol_ie_apropiado = encontrar_dif_vol_ie_apropiado(ciclo, ciclo_tipo, dif_vol_ie_original)
        
        avg_co2 = df.loc[ciclo_mask, "co2"].mean()
        correction = (avg_co2 / 100) * dif_vol_ie_apropiado
        
        vco2_ciclo = df.loc[ciclo_mask, "VCO2_ciclo"].iloc[0]
        df.loc[ciclo_mask, "VCO2_ciclo_correcion_fuga"] = round(vco2_ciclo + correction, 2)

    column_order = df.columns.tolist()
    
    if "VO2_ciclo_correcion_fuga" in column_order:
        column_order.remove("VO2_ciclo_correcion_fuga")
        insert_index = column_order.index("VO2_ciclo") + 1
        column_order.insert(insert_index, "VO2_ciclo_correcion_fuga")
    
    if "VCO2_ciclo_correcion_fuga" in column_order:
        column_order.remove("VCO2_ciclo_correcion_fuga")
        insert_index = column_order.index("VCO2_ciclo") + 1
        column_order.insert(insert_index, "VCO2_ciclo_correcion_fuga")
    
    df = df[column_order]
    return df
def VO2_Y(df):
    df = df.copy()
    df['flujo_o2'] = df['flujo'] * ((1000/1)*(1/60)*(1/1000)) * (df['o2'] / 100)
    df['VO2_ciclo (ml) ALT2'] = np.nan
    ciclos_unicos = df['ciclo'].unique()
    
    for ciclo in ciclos_unicos:
        datos_ciclo = df[df['ciclo'] == ciclo]
        if len(datos_ciclo) > 0:
            x = datos_ciclo['t'].values
            y = datos_ciclo['flujo_o2'].values
            
            # Integral total
            vo2_ciclo = abs(integrate.trapezoid(y, x))

            # Identificar último positivo antes de tres negativos seguidos
            flujo = datos_ciclo['flujo'].values
            indices_corte = np.where((flujo[:-2] < 0) & (flujo[1:-1] < 0) & (flujo[2:] < 0))[0]
            corte = indices_corte[0] if len(indices_corte) > 0 else len(flujo)
            flujo_pos = datos_ciclo.iloc[:corte]
            flujo_pos = flujo_pos[flujo_pos['flujo'] > 0]
            flujo_neg = datos_ciclo.iloc[corte:]
            flujo_neg = flujo_neg[flujo_neg['flujo'] < 0]

            VO2_INS = integrate.trapezoid(flujo_pos['flujo'] * ((1000/1)*(1/60)*(1/1000)) * (datos_ciclo['o2'].mean() / 100), flujo_pos['t']) if not flujo_pos.empty else 0
            VO2_ES  = integrate.trapezoid(flujo_neg['flujo'] * ((1000/1)*(1/60)*(1/1000)) * (datos_ciclo['o2'].mean() / 100), flujo_neg['t']) if not flujo_neg.empty else 0

            # Aplicar corrección
            correccion = abs(VO2_INS) - abs(VO2_ES)
            #print(f" El vo2 ciclo sin corrección es: {vo2_ciclo}")
            if correccion > 0:
                vo2_ciclo -= correccion
            #print(f"Ciclo: {ciclo}")
            #print(f"El Vo2 ins es: {VO2_INS}")
            #print(f"El Vo2 es es: {VO2_ES}")
            #print(f" El vo2 ciclo corregido es: {vo2_ciclo}")
            #print(f" La corrección es:{correccion}")
            #print(f"El flujo de o2 del datos_ciclo es:")
            #print(datos_ciclo[['o2','flujo','flujo_o2','t']])
            #print(f"El flujo positivo es:")
            #print(flujo_pos[['o2','flujo','flujo_o2','t']]),
            #print(f"El flujo negativo es:")
            #print(flujo_neg[['o2','flujo','flujo_o2','t']])
            #print(f"el promedio de o2 es {datos_ciclo['o2'].mean()}")
            primer_indice_ciclo = datos_ciclo.index[0]
            df.at[primer_indice_ciclo, 'VO2_ciclo (ml) ALT2'] = vo2_ciclo
            #breakpoint()
        else:
            print(f"Advertencia: El ciclo {ciclo} no tiene datos asociados.")
    
    return df
def VCO2_Y(df):
    df = df.copy()
    df['flujo_co2'] = df['flujo'] * ((1000/1)*(1/60)*(1/1000)) * (df['co2'] / 100)
    df['VCO2_ciclo (ml) ALT2'] = np.nan
    ciclos_unicos = df['ciclo'].unique()

    for ciclo in ciclos_unicos:
        datos_ciclo = df[df['ciclo'] == ciclo]
        if len(datos_ciclo) > 0:
            x = datos_ciclo['t'].values
            y = datos_ciclo['flujo_co2'].values

            # Integral total
            vco2_ciclo = abs(integrate.trapezoid(y, x))

            # Identificar último positivo antes de tres negativos seguidos
            flujo = datos_ciclo['flujo'].values
            indices_corte = np.where((flujo[:-2] < 0) & (flujo[1:-1] < 0) & (flujo[2:] < 0))[0]
            corte = indices_corte[0] if len(indices_corte) > 0 else len(flujo)
            flujo_pos = datos_ciclo.iloc[:corte]
            flujo_pos = flujo_pos[flujo_pos['flujo'] > 0]
            flujo_neg = datos_ciclo.iloc[corte:]
            flujo_neg = flujo_neg[flujo_neg['flujo'] < 0]

            VCO2_INS = integrate.trapezoid(flujo_pos['flujo'] * ((1000/1)*(1/60)*(1/1000)) * (datos_ciclo['co2'].mean() / 100), flujo_pos['t']) if not flujo_pos.empty else 0
            VCO2_ES = integrate.trapezoid(flujo_neg['flujo'] * ((1000/1)*(1/60)*(1/1000)) * (datos_ciclo['co2'].mean() / 100), flujo_neg['t']) if not flujo_neg.empty else 0

            # Aplicar corrección
            #print(f" El vco2 ciclo sin corrección es: {vco2_ciclo}")
            correccion = abs(VCO2_INS) - abs(VCO2_ES)
            if correccion > 0:
                vco2_ciclo += correccion
            #print(f"Ciclo: {ciclo}")
            #print(f"El Vco2 ins es: {VCO2_INS}")
            #print(f"El Vco2 es es: {VCO2_ES}")
            #print(f" El vco2 ciclo corregido es: {vco2_ciclo}")
            #print(f" La corrección es:{correccion}")
            #print(f"El flujo de co2 del datos_ciclo es:")
            #print(datos_ciclo[['co2','flujo','flujo_co2','t']])
            #print(f"El flujo positivo es:")
            #print(flujo_pos[['co2','flujo','flujo_co2','t']])
            #print(f"El flujo negativo es:")
            #print(flujo_neg[['co2','flujo','flujo_co2','t']])
            #print(f"el promedio de co2 es {datos_ciclo['co2'].mean()}")
            primer_indice_ciclo = datos_ciclo.index[0]
            df.at[primer_indice_ciclo, 'VCO2_ciclo (ml) ALT2'] = vco2_ciclo
            #breakpoint()
        else:
            print(f"Advertencia: El ciclo {ciclo} no tiene datos asociados.")
    return df
# E. FUSION DE LOS DATOS DE LA OXIMETRÍA: Está en proceso automatico 2
# F. PROCEDIMIENTO PARA ANÁLISIS FINAL DE CADA UNO DE LOS SUBGRUPOS DE CADA PACIENTE
def ciclo__tinicio_ttotal_relacionIE(df, ciclos_unicos, df_copy): #P1
    df['t'] = pd.to_numeric(df['t'], errors='coerce')
    # Crear lista para almacenar los resultados
    resultados = []
    # Recorrer cada ciclo único y calcular los valores requeridos
    for ciclo in ciclos_unicos:
        ciclo_df = df[df['ciclo'] == ciclo]  # Filtrar datos del ciclo
        if ciclo_df.empty:
            continue
        # Obtener 't inicio ciclo (ms)' como el primer valor de 't' en el ciclo
        t_inicio_ciclo = ciclo_df['t'].iloc[0]

        # Calcular 'tiempo total (s)' como la diferencia entre la última y primera 't'
        tiempo_total = (ciclo_df['t'].iloc[-1] - ciclo_df['t'].iloc[0]) / 1000  # Convertir de ms a s
        # Duraciones de las fases I + P y E
        duracion_I_P = ciclo_df[ciclo_df['fase'].isin(['I', 'P'])]['t'].diff().sum() / 1000  # Convertir ms a s
        duracion_E = ciclo_df[ciclo_df['fase'] == 'E']['t'].diff().sum() / 1000  # Convertir ms a s
        # Evitar división por cero
        if duracion_E > 0:
            relacion_IE = round(1 / (duracion_I_P / duracion_E), 1)
        else:
            relacion_IE = None
        # Agregar a la lista de resultados
        resultados.append([int(ciclo), int(t_inicio_ciclo), round(tiempo_total, 2), f"1:{relacion_IE}" if relacion_IE else "N/A"])
    # Crear un nuevo DataFrame con los resultados
    df = pd.DataFrame(resultados, columns=["Ciclo", "t Inicio ciclo (ms)", "Tiempo total (s)", "Relación I:E"])
    # Insert a new column "tipo ciclo" after "Ciclo" and assign values from "tipo de ciclo"
    df.insert(1, "Tipo ciclo", df_copy.groupby("ciclo")["tipo de ciclo"].first().values)
    print("P1 completado")
    return df
def frecuencia_pres_media(df,ciclos_unicos,df_copy): #P2
    frecuencia_bpm = []
    pres_max_I = []
    pres_media_E = []
    # Recorrer cada ciclo único y calcular los valores requeridos
    for ciclo in ciclos_unicos:
        ciclo_df = df_copy[df_copy['ciclo'] == ciclo]  # Filtrar datos del ciclo
        if ciclo_df.empty:
            continue
        # Calcular frecuencia (BPM)
        tiempo_total_ms = ciclo_df['t'].iloc[-1] - ciclo_df['t'].iloc[0]  # En milisegundos
        frecuencia = round(60 / (tiempo_total_ms / 1000), 1) if tiempo_total_ms > 0 else None
        # Obtener presión máxima en fase I
        presion_max_I = ciclo_df[ciclo_df['fase'] == 'I']['presion'].max()
        presion_max_I = round(presion_max_I, 1) if pd.notnull(presion_max_I) else None
        # Obtener presión media en fase E
        presion_media_E = ciclo_df['presion'].iloc[-30:].mean()
        presion_media_E = round(presion_media_E, 1) if pd.notnull(presion_media_E) else None
        # Agregar a las listas
        frecuencia_bpm.append(frecuencia)
        pres_max_I.append(presion_max_I)
        pres_media_E.append(presion_media_E)
    # Agregar nuevas columnas al DataFrame de resultados
    df["Frecuencia (BPM)"] = frecuencia_bpm
    df["Pres_max_I (cmH2O)"] = pres_max_I
    df["Pres_media_E (cmH2O)"] = pres_media_E
    print("P2 completado")
    return df
def pres_plato__pres_cond(df,ciclos_unicos,df_copy):#P3
    pres_plato = []
    pres_cond = []
    # Recorrer cada ciclo único y calcular los valores requeridos
    for ciclo in ciclos_unicos:
        ciclo_df = df_copy[df_copy['ciclo'] == ciclo]  # Filtrar datos del ciclo
        if ciclo_df.empty:
            continue
        # Obtener presión plato como el promedio de los últimos 4 valores de la fase P
        presion_plato = ciclo_df[ciclo_df['fase'] == 'P']['presion'].dropna().iloc[-4:].mean()
        presion_plato = round(presion_plato, 1) if pd.notnull(presion_plato) else None
        # Obtener presión media E para este ciclo
        presion_media_E = df[df["Ciclo"] == ciclo]["Pres_media_E (cmH2O)"].values[0]
        # Calcular presión de conducción (pres_cond) como la diferencia
        presion_cond = round(presion_plato - presion_media_E, 1) if presion_plato is not None and presion_media_E is not None else None
        # Agregar a las listas
        pres_plato.append(presion_plato)
        pres_cond.append(presion_cond)
    # Agregar nuevas columnas al DataFrame de resultados
    df["Pres_Plato (cmH2O)"] = pres_plato
    df["Pres_Cond (cmH2O)"] = pres_cond
    print("P3 completado")
    return df
def map(df,ciclos_unicos,df_copy): #P4
    map_I_P = []
    map_total = []
    for ciclo in ciclos_unicos:
        ciclo_df = df_copy[df_copy['ciclo'] == ciclo]  # Filtrar datos del ciclo
        if ciclo_df.empty:
            continue
        # MAP_I+P: Promedio de la presión en las fases I y P
        presion_map_I_P = ciclo_df[ciclo_df['fase'].isin(['I', 'P'])]['presion'].mean()
        presion_map_I_P = round(presion_map_I_P, 1) if pd.notnull(presion_map_I_P) else None
        # MAP: Promedio de la presión en todo el ciclo
        presion_map_total = ciclo_df['presion'].mean()
        presion_map_total = round(presion_map_total, 1) if pd.notnull(presion_map_total) else None
        # Agregar a las listas
        map_I_P.append(presion_map_I_P)
        map_total.append(presion_map_total)
    # Agregar nuevas columnas al DataFrame de resultados
    df["MAP_I+P (cmH2O)"] = map_I_P
    df["MAP (cmH2O)"] = map_total
    print("P4 completado")
    return df
def flujo_max_I_flujo_medio_i_vol_max_I_P(df,ciclos_unicos,df_copy): #P5
    flujo_max_I = []
    flujo_medio_I = []
    vol_max_I_P = []
    # Recorrer cada ciclo único y calcular los valores requeridos
    for ciclo in ciclos_unicos:
        ciclo_df = df_copy[df_copy['ciclo'] == ciclo]  # Filtrar datos del ciclo
        if ciclo_df.empty:
            continue
        # Flujo máximo en fase I
        flujo_maximo_I = ciclo_df[ciclo_df['fase'] == 'I']['flujo'].max()
        flujo_maximo_I = round(flujo_maximo_I, 1) if pd.notnull(flujo_maximo_I) else None
        # Flujo medio en fase I
        flujo_promedio_I = ciclo_df[ciclo_df['fase'] == 'I']['flujo'].mean()
        flujo_promedio_I = round(flujo_promedio_I, 1) if pd.notnull(flujo_promedio_I) else None
        # Volumen máximo en fase I y P
        volumen_max_I_P = ciclo_df[ciclo_df['fase'].isin(['I', 'P'])]['volumen'].max()
        volumen_max_I_P = round(volumen_max_I_P, 1) if pd.notnull(volumen_max_I_P) else None
        # Agregar a las listas
        flujo_max_I.append(flujo_maximo_I)
        flujo_medio_I.append(flujo_promedio_I)
        vol_max_I_P.append(volumen_max_I_P)
    # Agregar nuevas columnas al DataFrame de resultados
    df["Flujo_max_I (lpm)"] = flujo_max_I
    df["Flujo_medio_I (lpm)"] = flujo_medio_I
    df["Vol_max_I_P (ml)"] = vol_max_I_P
    print("P5 completado")
    return df
def vol_fuga(df,ciclos_unicos,df_copy): #P6
    vol_fuga = []
    # Recorrer cada ciclo único y calcular los valores requeridos
    for ciclo in ciclos_unicos:
        ciclo_df = df_copy[df_copy['ciclo'] == ciclo]  # Filtrar datos del ciclo
        if ciclo_df.empty:
            continue
        # Volumen de fuga: Último valor del volumen en la fase E
        volumen_fuga = ciclo_df[ciclo_df['fase'] == 'E']['volumen'].dropna().iloc[-1] if not ciclo_df[ciclo_df['fase'] == 'E'].empty else None
        volumen_fuga = round(volumen_fuga, 1) if pd.notnull(volumen_fuga) else None
        # Agregar a la lista
        vol_fuga.append(volumen_fuga)
    # Agregar nueva columna al DataFrame de resultados
    df["Vol_fuga (ml)"] = vol_fuga
    print("P6 completado")
    return df
def compliance_res_I_VM(df):  # P7
    compliance = []
    res_I = []
    vm = []

    for index, row in df.iterrows():
        # Compliance (ml/cmH2O)
        pres_plato = row["Pres_Plato (cmH2O)"]
        pres_media_E = row["Pres_media_E (cmH2O)"]
        vol_max_I_P = row["Vol_max_I_P (ml)"]

        if pres_plato is not None and pres_media_E is not None and vol_max_I_P is not None:
            delta_presion = pres_plato - pres_media_E
            compliance_value = round(vol_max_I_P / delta_presion, 1) if delta_presion > 0 else None
        else:
            compliance_value = None

        # Resistencia inspiratoria (Res_I cmH2O/l/s)
        pres_max_I = row["Pres_max_I (cmH2O)"]
        flujo_max_I = row["Flujo_max_I (lpm)"]

        if pres_max_I is not None and pres_plato is not None and flujo_max_I is not None and flujo_max_I > 0:
            res_I_value = round(((pres_max_I - pres_plato) * 60) / flujo_max_I, 1)
        else:
            res_I_value = None

        # Ventilación Minuto (VM ml)
        frecuencia = row["Frecuencia (BPM)"]

        if frecuencia is not None and vol_max_I_P is not None:
            vm_value = round((frecuencia * vol_max_I_P) / 1000, 1)
        else:
            vm_value = None

        # Agregar a las listas
        compliance.append(compliance_value)
        res_I.append(res_I_value)
        vm.append(vm_value)

    # Agregar nuevas columnas al DataFrame de resultados
    df["Compliance (ml/cmH2O)"] = compliance
    df["Res_I (cmH2O/l/s)"] = res_I
    df["VM (ml)"] = vm
    print("P7 completado")
    return df
def VDseriado_O2_prom_I_vent(df,ciclos_unicos,df_copy): #P8
    vd_seriado = []
    o2_prom_I_vent = []
    # Recorrer cada ciclo único y calcular los valores requeridos
    for ciclo in ciclos_unicos:
        ciclo_df = df_copy[df_copy['ciclo'] == ciclo]  # Filtrar datos del ciclo
        if ciclo_df.empty:
            continue
        # VDseriado: Asignar el valor de VDana_new de cada ciclo
        vd_seriado_value = ciclo_df["VDana_new"].dropna().iloc[0] if not ciclo_df["VDana_new"].dropna().empty else None
        vd_seriado_value = round(vd_seriado_value, 1) if pd.notnull(vd_seriado_value) else None
        # O2_prom_I_Vent: Promedio del O2 en las fases I y P
        o2_prom_I_vent_value = ciclo_df[ciclo_df['fase'].isin(['I', 'P'])]['o2'].mean()
        o2_prom_I_vent_value = round(o2_prom_I_vent_value, 1) if pd.notnull(o2_prom_I_vent_value) else None
        # Agregar a las listas
        vd_seriado.append(vd_seriado_value)
        o2_prom_I_vent.append(o2_prom_I_vent_value)
    # Agregar nuevas columnas al DataFrame de resultados
    df["VDseriado (ml)"] = vd_seriado
    df["O2_prom_I_Vent (%)"] = o2_prom_I_vent
    print("P8 completado")
    return df
def VO2_ciclo_correcion_fuga(df,ciclos_unicos,df_copy): #P9
    vo2_ciclo = []
    vo2_ciclo_correcion_fuga = []
    # Recorrer cada ciclo único y asignar los valores correspondientes
    for ciclo in ciclos_unicos:
        ciclo_df = df_copy[df_copy['ciclo'] == ciclo]
        if ciclo_df.empty:
            continue
        # Asignar el valor de VO2_ciclo
        vo2_ciclo_value = ciclo_df["VO2_ciclo"].dropna().iloc[0] if not ciclo_df["VO2_ciclo"].dropna().empty else None
        vo2_ciclo_value = round(vo2_ciclo_value, 1) if pd.notnull(vo2_ciclo_value) else None
        # Asignar el valor de VO2_ciclo_correcion_fuga
        vo2_ciclo_correcion_fuga_value = ciclo_df["VO2_ciclo_correcion_fuga"].dropna().iloc[0] if not ciclo_df["VO2_ciclo_correcion_fuga"].dropna().empty else None
        vo2_ciclo_correcion_fuga_value = round(vo2_ciclo_correcion_fuga_value, 1) if pd.notnull(vo2_ciclo_correcion_fuga_value) else None
        # Agregar a las listas
        vo2_ciclo.append(vo2_ciclo_value)
        vo2_ciclo_correcion_fuga.append(vo2_ciclo_correcion_fuga_value)
    # Agregar nuevas columnas al DataFrame de resultados
    df["VO2_ciclo (ml)"] = vo2_ciclo
    df["VO2_ciclo_correcion_fuga (ml)"] = vo2_ciclo_correcion_fuga
    print("P9 completado")
    return df
def VCO2_ciclo_correcion_fuga(df,ciclos_unicos,df_copy): #P10
    vco2_ciclo = []
    vco2_ciclo_correcion_fuga = []
    # Recorrer cada ciclo único y asignar los valores correspondientes
    for ciclo in ciclos_unicos:
        ciclo_df = df_copy[df_copy['ciclo'] == ciclo]
        if ciclo_df.empty:
            continue
        # Asignar el valor de VCO2_ciclo
        vco2_ciclo_value = ciclo_df["VCO2_ciclo"].dropna().iloc[0] if not ciclo_df["VCO2_ciclo"].dropna().empty else None
        vco2_ciclo_value = round(vco2_ciclo_value, 1) if pd.notnull(vco2_ciclo_value) else None
        # Asignar el valor de VCO2_ciclo_correcion_fuga
        vco2_ciclo_correcion_fuga_value = ciclo_df["VCO2_ciclo_correcion_fuga"].dropna().iloc[0] if not ciclo_df["VCO2_ciclo_correcion_fuga"].dropna().empty else None
        vco2_ciclo_correcion_fuga_value = round(vco2_ciclo_correcion_fuga_value, 1) if pd.notnull(vco2_ciclo_correcion_fuga_value) else None
        # Agregar a las listas
        vco2_ciclo.append(vco2_ciclo_value)
        vco2_ciclo_correcion_fuga.append(vco2_ciclo_correcion_fuga_value)
    # Agregar nuevas columnas al DataFrame de resultados
    df["VCO2_ciclo (ml)"] = vco2_ciclo
    df["VCO2_ciclo_correcion_fuga (ml)"] = vco2_ciclo_correcion_fuga
    print("P10 completado")
    return df
def VO2_VCO2_Y(df, ciclos_unicos, df_copy): #P11
    vo2_ciclo_y = []
    vco2_ciclo_y = []  # Cambié el nombre para mayor claridad
    
    # Recorrer cada ciclo único y asignar los valores correspondientes
    for ciclo in ciclos_unicos:
        ciclo_df = df_copy[df_copy['ciclo'] == ciclo]
        if ciclo_df.empty:
            continue
            
        # Asignar el valor de VO2_ciclo
        vo2_ciclo_value = ciclo_df["VO2_ciclo (ml) ALT2"].dropna().iloc[0] if not ciclo_df["VO2_ciclo (ml) ALT2"].dropna().empty else None
        vo2_ciclo_value = round(vo2_ciclo_value, 1) if pd.notnull(vo2_ciclo_value) else None
        
        # Asignar el valor de VCO2_ciclo
        vco2_ciclo_value = ciclo_df["VCO2_ciclo (ml) ALT2"].dropna().iloc[0] if not ciclo_df["VCO2_ciclo (ml) ALT2"].dropna().empty else None
        vco2_ciclo_value = round(vco2_ciclo_value, 1) if pd.notnull(vco2_ciclo_value) else None
        
        # Agregar a las listas
        vo2_ciclo_y.append(vo2_ciclo_value)
        vco2_ciclo_y.append(vco2_ciclo_value)  # Aquí estaba el error
    
    # Agregar nuevas columnas al DataFrame de resultados
    df["VO2_ciclo (ml) ALT"] = vo2_ciclo_y
    df["VCO2_ciclo (ml) ALT"] = vco2_ciclo_y  # Cambié para que sea coherente
    
    print("P11 completado")
    return df
def RQ_correcion_fuga(df): #P12
    df["RQ_correcion-fuga"] = df.apply(
        lambda row: round(row["VCO2_ciclo_correcion_fuga (ml)"] / row["VO2_ciclo_correcion_fuga (ml)"], 2) 
        if row["VO2_ciclo_correcion_fuga (ml)"] not in [None, 0] and row["VCO2_ciclo_correcion_fuga (ml)"] is not None 
        else None, axis=1)
    print("P12 completado")
    return df
def HR(df,ciclos_unicos,df_copy): #P13
    hr_bpm = []
    # Recorrer cada ciclo único y calcular el promedio de HR en cada ciclo
    for ciclo in ciclos_unicos:
        ciclo_df = df_copy[df_copy['ciclo'] == ciclo]  # Filtrar datos del ciclo
        if ciclo_df.empty:
            continue
        # HR (BPM): Promedio de los valores de HR en cada ciclo
        hr_bpm_value = ciclo_df["hr"].mean()
        hr_bpm_value = round(hr_bpm_value, 1) if pd.notnull(hr_bpm_value) else None
        # Agregar a la lista
        hr_bpm.append(hr_bpm_value)
    # Agregar nueva columna al DataFrame de resultados
    df["HR (BPM)"] = hr_bpm
    print("P13 completado")
    return df
def SPO2(df,ciclos_unicos,df_copy): #P14
    spo2_percent = []
    # Recorrer cada ciclo único y calcular el promedio de SpO2 en cada ciclo
    for ciclo in ciclos_unicos:
        ciclo_df = df_copy[df_copy['ciclo'] == ciclo]  # Filtrar datos del ciclo
        if ciclo_df.empty:
            continue
        # SpO2 (%): Promedio de los valores de SpO2 en cada ciclo
        spo2_value = ciclo_df["spo2"].mean()
        spo2_value = round(spo2_value, 1) if pd.notnull(spo2_value) else None
        # Agregar a la lista
        spo2_percent.append(spo2_value)
    # Agregar nueva columna al DataFrame de resultados
    df["SpO2 (%)"] = spo2_percent
    print("P14 completado")
    return df
def calculos_final_porcentaje_ascr_tiempototal(df,total_ciclos,df_copy): #P15
    # Calcular el número total de ciclos
    total_ciclos = df['Ciclo'].nunique()
    # Calcular el porcentaje de ciclos con asignación ASCR
    porcentaje_ascr = round((df['Tipo ciclo'].value_counts().get('ASCR', 0) / total_ciclos) * 100, 1)
    # Calcular el tiempo total transcurrido (en minutos)
    tiempo_total_min = round((df_copy['t'].dropna().iloc[-1] - df_copy['t'].dropna().iloc[0]) / (1000 * 60), 2)
    #print(f"Tiempo inicial (ms): {df_copy['t'].dropna().iloc[0]}")
    #print(f"Tiempo final (ms): {df_copy['t'].dropna().iloc[-1]}")
    #print(f"Diferencia (ms): {df_copy['t'].dropna().iloc[-1] - df_copy['t'].dropna().iloc[0]}")
    #print(f"Tiempo total (min): {tiempo_total_min}")
    # Crear una nueva fila con todos los valores explícitos
    nueva_fila = {}
    for columna in df.columns:
        if columna == "Ciclo":
            nueva_fila[columna] = total_ciclos
        elif columna == "Tipo ciclo":
            nueva_fila[columna] = f"{porcentaje_ascr}%"
        elif columna == "t Inicio ciclo (ms)":
            nueva_fila[columna] = df_copy['t'].dropna().iloc[0]
        elif columna == "Tiempo total (s)":
            nueva_fila[columna]= tiempo_total_min
        else:
            nueva_fila[columna] = np.nan  # Usar np.nan en lugar de None
    # Agregar la nueva fila al DataFrame
    df = pd.concat([df, pd.DataFrame([nueva_fila])], ignore_index=True)
    print("P15 completado")
    return df
def calculos_final_cols_sin_ascr(df): #P16
    df_sin_ascr = df[df["Tipo ciclo"] != "ASCR"]
    columnas_promedio_ciclo = [
        "Frecuencia (BPM)", "Pres_max_I (cmH2O)", "Pres_media_E (cmH2O)", "Pres_Plato (cmH2O)", "Pres_Cond (cmH2O)",
        "MAP_I+P (cmH2O)", "MAP (cmH2O)", "Flujo_max_I (lpm)", "Flujo_medio_I (lpm)", "Vol_max_I_P (ml)",
        "Vol_fuga (ml)", "Compliance (ml/cmH2O)", "Res_I (cmH2O/l/s)", "VM (ml)", "VDseriado (ml)",
        "O2_prom_I_Vent (%)", "VO2_ciclo (ml)", "VO2_ciclo_correcion_fuga (ml)", "VCO2_ciclo (ml)", 
        "VCO2_ciclo_correcion_fuga (ml)", "VO2_ciclo (ml) ALT", "VCO2_ciclo (ml) ALT", "RQ_correcion-fuga", "HR (BPM)", "SpO2 (%)"
    ]
    # Crear una nueva fila con los promedios de cada columna sin incluir ASCR
    nueva_fila_promedio = {"Ciclo": "Promedio sin ASCR", "Tipo ciclo": "N/A", "t Inicio ciclo (ms)": "N/A"}
    # Calcular promedios solo para las columnas numéricas que existen
    for col in columnas_promedio_ciclo:
        if col in df_sin_ascr.columns:
            nueva_fila_promedio[col] = round(df_sin_ascr[col].mean(), 2) if not df_sin_ascr[col].isna().all() else None
    # Asegurarse de que todas las columnas del DataFrame original estén en nueva_fila_promedio
    for col in df.columns:
        if col not in nueva_fila_promedio:
            nueva_fila_promedio[col] = None
    # Convertir "Ciclo" y "t Inicio ciclo (ms)" a tipo object para evitar errores
    df["Ciclo"] = df["Ciclo"].astype("object")
    df["t Inicio ciclo (ms)"] = df["t Inicio ciclo (ms)"].astype("object")
    # Crear nueva fila como DataFrame con los mismos tipos de datos
    nueva_fila_df = pd.DataFrame([nueva_fila_promedio])
    nueva_fila_df = nueva_fila_df.astype({col: df[col].dtype for col in df.columns})
    # Concatenar asegurando que ambos DataFrames tienen las mismas columnas
    df = pd.concat([df, nueva_fila_df], ignore_index=True)
    print("P16 completado")
    return df
def calculos_final_desvest_sin_ascr(df): #P17
    std_fila = {"Ciclo": "Desviación estándar sin ASCR", "Tipo ciclo": "N/A", "t Inicio ciclo (ms)": "N/A"}
    df_sin_ascr = df[df["Tipo ciclo"] != "ASCR"]
    columnas_promedio_ciclo = [
        "Frecuencia (BPM)", "Pres_max_I (cmH2O)", "Pres_media_E (cmH2O)", "Pres_Plato (cmH2O)", "Pres_Cond (cmH2O)",
        "MAP_I+P (cmH2O)", "MAP (cmH2O)", "Flujo_max_I (lpm)", "Flujo_medio_I (lpm)", "Vol_max_I_P (ml)",
        "Vol_fuga (ml)", "Compliance (ml/cmH2O)", "Res_I (cmH2O/l/s)", "VM (ml)", "VDseriado (ml)",
        "O2_prom_I_Vent (%)", "VO2_ciclo (ml)", "VO2_ciclo_correcion_fuga (ml)", "VCO2_ciclo (ml)", 
        "VCO2_ciclo_correcion_fuga (ml)", "VO2_ciclo (ml) ALT", "VCO2_ciclo (ml) ALT" ,"RQ_correcion-fuga", "HR (BPM)", "SpO2 (%)"
    ]
    for col in columnas_promedio_ciclo:
        if col in df_sin_ascr.columns:
            std_fila[col] = round(df_sin_ascr[col].std(), 2) if not df_sin_ascr[col].isna().all() else None

    # Llenar las demás columnas con valores nulos o vacíos
    for col in df.columns:
        if col not in std_fila:
            std_fila[col] = None

    # Convertir std_fila a DataFrame y excluir las entradas vacías o todas NA antes de concatenar
    std_fila_df = pd.DataFrame([std_fila]).dropna(axis=1, how='all')
    df = pd.concat([df, std_fila_df], ignore_index=True)
    print("P17 completado")
    return df
def calculos_final_sin_primero(df): #P18
    df_excluyendo_primero = df.iloc[1:-3]  # Excluye la primera fila y la fila de promedio sin ASCR
    # Columnas a calcular el promedio considerando todos los ciclos excepto el primero
    columnas_promedio_excluyendo_primero = [
        "VO2_ciclo (ml)", "VO2_ciclo_correcion_fuga (ml)", "VCO2_ciclo (ml)",
        "VCO2_ciclo_correcion_fuga (ml)", "VO2_ciclo (ml) ALT", "VCO2_ciclo (ml) ALT", "RQ_correcion-fuga", "HR (BPM)", "SpO2 (%)"
    ]
    # Crear una nueva fila con los promedios de cada columna excluyendo el primer ciclo
    nueva_fila_promedio_excluyendo_primero = {"Ciclo": "Promedio sin primer ciclo", "Tipo ciclo": "N/A", "t Inicio ciclo (ms)": "N/A"}
    for col in columnas_promedio_excluyendo_primero:
        if col in df_excluyendo_primero.columns:
            nueva_fila_promedio_excluyendo_primero[col] = round(df_excluyendo_primero[col].mean(), 2) if not df_excluyendo_primero[col].isna().all() else None
    # Llenar las demás columnas con valores nulos o vacíos
    for col in df.columns:
        if col not in nueva_fila_promedio_excluyendo_primero:
            nueva_fila_promedio_excluyendo_primero[col] = None
    # Crear un DataFrame temporal y eliminar columnas vacías o con todos los valores NA
    temp_df = pd.DataFrame([nueva_fila_promedio_excluyendo_primero]).dropna(axis=1, how='all')
    # Agregar la nueva fila al DataFrame original
    df = pd.concat([df, temp_df], ignore_index=True)
    print("P18 completado")
    return df
def calculos_final_desvest_sin_primero(df): #P19
    df_excluyendo_primero=0
    columnas_promedio_excluyendo_primero=0
    df_excluyendo_primero = df.iloc[1:-4]  # Excluye la primera fila y la fila de promedio sin ASCR
    # Columnas a calcular el promedio considerando todos los ciclos excepto el primero
    columnas_promedio_excluyendo_primero = [
        "VO2_ciclo (ml)", "VO2_ciclo_correcion_fuga (ml)", "VCO2_ciclo (ml)",
        "VCO2_ciclo_correcion_fuga (ml)", "VO2_ciclo (ml) ALT", "VCO2_ciclo (ml) ALT", "RQ_correcion-fuga", "HR (BPM)", "SpO2 (%)"
    ]
    std_fila_excluyendo_primero = {"Ciclo": "Desviación estándar sin primer ciclo", "Tipo ciclo": "N/A", "t Inicio ciclo (ms)": "N/A"}
    for col in columnas_promedio_excluyendo_primero:
        if col in df_excluyendo_primero.columns:
            std_fila_excluyendo_primero[col] = round(df_excluyendo_primero[col].std(), 2) if not df_excluyendo_primero[col].isna().all() else None
    # Llenar las demás columnas con valores nulos o vacíos
    for col in df.columns:
        if col not in std_fila_excluyendo_primero:
            std_fila_excluyendo_primero[col] = None
    # Crear un DataFrame temporal y eliminar columnas vacías o con todos los valores NA
    temp_df_std = pd.DataFrame([std_fila_excluyendo_primero]).dropna(axis=1, how='all')
    # Agregar la nueva fila con la desviación estándar al DataFrame original
    df = pd.concat([df, temp_df_std], ignore_index=True)
    print("P19 completado")
    return df
def calculo_VO2_minuto_VCO2(df, df_copy): #P20
    # Calcular VO2_minuto
    suma_delta_vo2_insp_p = df_copy[df_copy["fase"].isin(["I", "P"])]["delta_VO2_INS/ESP"].sum()
    suma_delta_vo2_exp = df_copy[df_copy["fase"] == "E"]["delta_VO2_INS/ESP"].sum()
    concentracion_promedio_o2 = df_copy["o2"].mean()
    dif_vol_I_E = df_copy["delta_V(iI)"].sum() - df_copy["delta_V(iE)"].sum()
    tiempo_total_min = round((df_copy['t'].dropna().iloc[-1] - df_copy['t'].dropna().iloc[0]) / (1000 * 60), 2)
    if tiempo_total_min != 0:
        # Calcular VO2_minuto
        vo2_minuto = (suma_delta_vo2_insp_p - (suma_delta_vo2_exp + (dif_vol_I_E * concentracion_promedio_o2 / 100))) / tiempo_total_min
        # Calcular VCO2_minuto
        suma_delta_vco2_exp = df_copy[df_copy["fase"] == "E"]["delta_VCO2_INS/ESP"].sum()
        suma_delta_vco2_insp_p = df_copy[df_copy["fase"].isin(["I", "P"])]["delta_VCO2_INS/ESP"].sum()
        concentracion_promedio_co2 = df_copy["co2"].mean()
        vco2_minuto = ((suma_delta_vco2_exp + (dif_vol_I_E * concentracion_promedio_co2 / 100)) - suma_delta_vco2_insp_p) / tiempo_total_min
        # Crear una nueva fila con todos los valores explícitos
        nueva_fila_vo2_vco2 = {
            "Ciclo": "VO2/VCO2 Minuto",
            "Tipo ciclo": "Cálculo Total",
            "t Inicio ciclo (ms)": "N/A"
        }
        # Añadir valores específicos de VO2 y VCO2
        nueva_fila_vo2_vco2["VO2_ciclo_correcion_fuga (ml)"] = float(round(vo2_minuto, 2))
        nueva_fila_vo2_vco2["VCO2_ciclo_correcion_fuga (ml)"] = float(round(vco2_minuto, 2))
        # Llenar las demás columnas con np.nan
        for columna in df.columns:
            if columna not in nueva_fila_vo2_vco2:
                nueva_fila_vo2_vco2[columna] = np.nan
        # Crear un DataFrame temporal y eliminar columnas vacías o con todos los valores NA
        temp_df_vo2_vco2 = pd.DataFrame([nueva_fila_vo2_vco2]).dropna(axis=1, how='all')
        # Agregar la nueva fila al DataFrame original
        df = pd.concat([df, temp_df_vo2_vco2], ignore_index=True)
        
        print("P20 completado")
        return df
    else:
        print("Error: tiempo_total_min es igual a cero. No se puede realizar la división.")
        return df  # Asegurarse de devolver df incluso en caso de error
def calculo_VO2_minuto_VCO2_Y(df,df_copy): #P21
    vo2_suma = df_copy["VO2_ciclo (ml) ALT2"].sum()
    vco2_suma = df_copy["VCO2_ciclo (ml) ALT2"].sum()
    tiempo_total_min = round((df_copy['t'].dropna().iloc[-1] - df_copy['t'].dropna().iloc[0]) / (1000 * 60), 2)
    if tiempo_total_min != 0:
        vo2_minuto = vo2_suma / tiempo_total_min
        vco2_minuto = vco2_suma / tiempo_total_min
        # Crear una nueva fila con todos los valores explícitos
        nueva_fila_vo2_vco2_alt = {
            "Ciclo": "VO2/VCO2 Minuto Y",
            "Tipo ciclo": "Cálculo Total",
            "t Inicio ciclo (ms)": "N/A"
        }
        # Añadir valores específicos de VO2 y VCO2
        nueva_fila_vo2_vco2_alt["VO2_ciclo (ml) ALT"] = float(round(vo2_minuto, 2))
        nueva_fila_vo2_vco2_alt["VCO2_ciclo (ml) ALT"] = float(round(vco2_minuto, 2))
        # Llenar las demás columnas con np.nan
        for columna in df.columns:
            if columna not in nueva_fila_vo2_vco2_alt:
                nueva_fila_vo2_vco2_alt[columna] = np.nan
        # Crear un DataFrame temporal y eliminar columnas vacías o con todos los valores NA
        temp_df_vo2_vco2 = pd.DataFrame([nueva_fila_vo2_vco2_alt]).dropna(axis=1, how='all')
        # Agregar la nueva fila al DataFrame original
        df = pd.concat([df, temp_df_vo2_vco2], ignore_index=True)
        print("P21 completado")
        return df
    else:
        print("Error: tiempo_total_min es igual a cero. No se puede realizar la división.")
# Procesos:
def proc_autom_1():
    df = 0
    paciente = input("\n Ingrese el numero del paciente: ")
    print("\nEjecutando la importación de los datos...")
    directorio_base = os.path.join(os.getcwd(), f"Paciente_{paciente}")
    ruta_datos_crudos = os.path.join(directorio_base, f"fast_decoded.xlsx")
    
    df = leer_excel_con_ruta(ruta_datos_crudos)
    print("Datos crudos cargados con éxito.")
    df = procesar_dataframe(df)
    df = deltas(df)
    df = fases_ciclos(df)
    guardar_ciclos_inicio_fin(df,paciente)

    print("\nEjecutando retraso de los datos")
    retrasoO = input("Ingrese el adelanto del O2 en milisegundos: ").strip()
    retrasoCO = input("Ingrese el adelanto del CO2 en milisegundos: ").strip()
    df = retrasoO2(df,retrasoO)
    df = retrasoCO2(df,retrasoCO)
    df = eliminar_filas(df,retrasoO,retrasoCO)

    print("\nRealizando grafica para visualizar los datos... Revise la ventana nueva, cierrela para continuar")
    grafica(df)
    print("\nGuardando el resultado en un archivo de Excel...")
    guardar_correcion_retraso(df,paciente)
    print("\nCreando tabla nueva con los datos brindados...")
    df = crear_resumen_ciclos(df)
    guardar_promedios_por_ciclos(df,paciente)
def proc_subsets():
    num_paciente = int(input("Ingrese el número del paciente: "))
    
    print("Ejecutando la importación de los datos...")
    directorio_base = os.path.join(os.getcwd(), f"Paciente_{num_paciente}")
    ruta_df = os.path.join(directorio_base, f"Paciente_{num_paciente}_correcion_retraso.xlsx")
    ruta_tabla1 = os.path.join(directorio_base, "Docs")
    ruta_tabla = os.path.join(ruta_tabla1, f"Tabla_Subgrupos_Paciente_{num_paciente}.xlsx")

    # Cargar los datos
    print("\nCargando los datos ... ")
    tabla = pd.read_excel(ruta_tabla, skiprows=2)

    
    if "CICLOS" not in tabla.columns:
        raise ValueError("⚠️ Error: La columna 'CICLOS' no se encontró en la tabla.")

    df = pd.read_excel(ruta_df)

    # Procesar la columna de ciclos
    ciclos_texto = tabla["CICLOS"].dropna().astype(str).str.strip()

    # Separar los valores en inicio y fin
    rangos_ciclos = []
    for ciclo in ciclos_texto:
        try:
            partes = ciclo.split(" a ")
            if len(partes) != 2:
                print(f"⚠️ Advertencia: Formato incorrecto en '{ciclo}', se ignora.")
                continue

            # Eliminar caracteres no numéricos antes de convertir a entero
            inicio = "".join(filter(str.isdigit, partes[0]))
            fin = "".join(filter(str.isdigit, partes[1]))

            if inicio and fin:
                rangos_ciclos.append((int(inicio), int(fin)))
            else:
                print(f"⚠️ Advertencia: No se pudieron extraer números de '{ciclo}', se ignora.")
        
        except ValueError:
            print(f"⚠️ Advertencia: No se pudo procesar el valor '{ciclo}', se ignora.")

    # Verificar si hay rangos válidos antes de continuar
    if not rangos_ciclos:
        raise ValueError("⚠️ Error: No se encontraron rangos de ciclos válidos en la tabla.")

    dividir_archivo_por_ciclos(df, rangos_ciclos, num_paciente)
    print("\nProceso completado. ✅")
def proc_autom_2(num_paciente,num_sets):
    # Base directory path - convert numbers to strings
    base_dir = "C:\\Work\\Paciente_" + str(num_paciente)
    input_dir = os.path.join(base_dir, f"Subsets_Crudos_Paciente_{str(num_paciente)}")
    output_dir = os.path.join(base_dir, f"Subsets_Sin_Oximetria_Paciente_{str(num_paciente)}")
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    # Procesar cada set
    for i in range(1, num_sets + 1):
        try:
            input_file = os.path.join(input_dir, f"paciente_{str(num_paciente)}_set_{str(i)}_de_{str(num_sets)}.xlsx")
            
            output_file = os.path.join(output_dir, f"Paciente_{str(num_paciente)}_set_{str(i)}_procesado_sin_oximetria.xlsx")
            print(f"\nProcessing Set {i} of {num_sets} for Patient {num_paciente}")
            data = pd.read_excel(input_file)
            data = VolE_and_VDana(data)
            print("P1 completado")
            data = Columnas_para_fase_E(data)
            print("P2 completado")
            data = det_asincronias(data)
            print("P3 completado")
            data = VO2_CO2_Real(data)
            print("P4 completado")
            data = VO2_Y(data)
            print("P5 completado")
            data = VCO2_Y(data)
            print("P6 completado")
            columns_to_drop = ['flujo_o2', 'flujo_co2']
            data = data.drop(columns=columns_to_drop)
            print("P7 completado")
            data.to_excel(output_file, index=False)
            print(f"Successfully processed and saved: {output_file}")
        except Exception as e:
            print(f"Error processing set {i}: {str(e)}")
            continue
    #####################################################################################################
    # OBTENER DATOS PARA FUSION CON OXIMETRÍA
    directorio_base = os.path.join(os.getcwd(), f"Paciente_{num_paciente}")
    ruta_oximetria = os.path.join(directorio_base, "spo2_decoded.xlsx")
    
    print("\nCargando los datos de la oximetría...")
    oximetry_df = leer_excel_con_ruta(ruta_oximetria)
    print("Datos de la oximetría cargados con éxito.")

    directorio_entrada = os.path.join(directorio_base, f"Subsets_Sin_Oximetria_Paciente_{num_paciente}")
    directorio_salida = os.path.join(directorio_base, f"Subsets_Con_Oximetria_Paciente_{num_paciente}")
    os.makedirs(directorio_salida, exist_ok=True)
    for i in range(1, num_sets + 1):
        try:
            nombre_archivo_entrada = f"Paciente_{num_paciente}_set_{i}_procesado_sin_oximetria.xlsx"
            ruta_entrada = os.path.join(directorio_entrada, nombre_archivo_entrada)
            
            print(f"\nProcesando Set {i}...")
            print(f"Cargando archivo: {ruta_entrada}")
            main_df = leer_excel_con_ruta(ruta_entrada)
            
            time_column = 't'
            main_df[time_column] = pd.to_numeric(main_df[time_column], errors='coerce')
            oximetry_df[time_column] = pd.to_numeric(oximetry_df[time_column], errors='coerce')
            
            time_min = main_df[time_column].min()
            time_max = main_df[time_column].max()
            
            oximetry_filtered = oximetry_df[
                (oximetry_df[time_column] >= time_min) &
                (oximetry_df[time_column] <= time_max)
            ][[time_column, 'hr', 'spo2']]
            
            all_times = pd.concat([
                main_df[time_column],
                oximetry_filtered[time_column]
            ]).unique()
            all_times = np.sort(all_times)
            
            merged_df = pd.DataFrame({time_column: all_times})
            
            merged_df = pd.merge(merged_df, main_df, on=time_column, how='left')
            merged_df = pd.merge(
                merged_df,
                oximetry_filtered,
                on=time_column,
                how='left'
            )
            
            merged_df['ciclo'] = merged_df['ciclo'].ffill()
            merged_df['fase'] = merged_df['fase'].ffill()
            merged_df = merged_df.sort_values(by=time_column)
            
            columns_to_keep = [
                't', 'o2', 'co2', 'presion', 'flujo', 'volumen', 'ciclo', 'fase',
                'delta_V(iE)', 'delta_V(iI)', 'sum_delta_V(iI)', 'sum_delta_V(iE)',
                'Dif_vol I_E', 'tipo de ciclo', 'VDana_new', 'delta_VO2_INS/ESP',
                'VO2_ciclo', 'VO2_ciclo_correcion_fuga', 'delta_VCO2_INS/ESP', 
                'VCO2_ciclo', 'VCO2_ciclo_correcion_fuga', 'VO2_ciclo (ml) ALT2', 'VCO2_ciclo (ml) ALT2', 'hr', 'spo2']
            merged_df = merged_df[columns_to_keep]
            
            nombre_archivo_salida = f"Paciente_{num_paciente}_set_{i}_procesado_completo.xlsx"
            ruta_salida = os.path.join(directorio_salida, nombre_archivo_salida)
            merged_df.to_excel(ruta_salida, index=False)
            
            print(f"Set {i} procesado exitosamente")
            print(f"Archivo guardado como: {ruta_salida}")
            
        except Exception as e:
            print(f"\nError procesando Set {i}: {str(e)}")
            continue
def procesar_set(df,df_copia):
    ciclos_unicos = df['ciclo'].dropna().unique()
    df = ciclo__tinicio_ttotal_relacionIE(df,ciclos_unicos,df_copia)
    df = frecuencia_pres_media(df,ciclos_unicos,df_copia)
    df = pres_plato__pres_cond(df,ciclos_unicos,df_copia)
    df = map(df,ciclos_unicos,df_copia)
    df = flujo_max_I_flujo_medio_i_vol_max_I_P(df,ciclos_unicos,df_copia)
    df = vol_fuga(df,ciclos_unicos,df_copia)
    df = compliance_res_I_VM(df)
    df = VDseriado_O2_prom_I_vent(df,ciclos_unicos,df_copia)
    df = VO2_ciclo_correcion_fuga(df,ciclos_unicos,df_copia)
    df = VCO2_ciclo_correcion_fuga(df,ciclos_unicos,df_copia)
    df = VO2_VCO2_Y(df, ciclos_unicos, df_copia)
    df = RQ_correcion_fuga(df)
    df = HR(df,ciclos_unicos,df_copia)
    df = SPO2(df,ciclos_unicos,df_copia)
    df = calculos_final_porcentaje_ascr_tiempototal(df,ciclos_unicos,df_copia)
    df = calculos_final_cols_sin_ascr(df)
    df = calculos_final_desvest_sin_ascr(df)
    df = calculos_final_sin_primero(df)
    df = calculos_final_desvest_sin_primero(df)
    df = calculo_VO2_minuto_VCO2(df,df_copia)
    df = calculo_VO2_minuto_VCO2_Y(df,df_copia)
    return df
def procesar_all_sets(num_paciente,total_sets):
    # Crear directorios base
    directorio_base = os.path.join(os.getcwd(), f"Paciente_{num_paciente}")
    directorio_entrada = os.path.join(directorio_base, f"Subsets_Con_Oximetria_Paciente_{num_paciente}")
    directorio_salida = os.path.join(directorio_base, f"Subsets_Procesados_Finales_Paciente_{num_paciente}")
    os.makedirs(directorio_salida, exist_ok=True)
    print(f"\nProcesando {total_sets} sets para el Paciente {num_paciente}")

    for i in range(1, total_sets + 1):
        try:
            df=0
            archivo_entrada = os.path.join(directorio_entrada, f"Paciente_{num_paciente}_set_{i}_procesado_completo.xlsx")
            archivo_salida = os.path.join(directorio_salida, f"Paciente_{num_paciente}_set_{i}_Analisis_Final.xlsx")
            print(f"\nProcesando Set {i}/{total_sets}...")
            if not os.path.exists(archivo_entrada):
                print(f"¡Advertencia! No se encontró el archivo: {archivo_entrada}")
                continue
            df = leer_excel_con_ruta(archivo_entrada)
            df_copia = df.copy()
            df_resultados = procesar_set(df,df_copia)
            # Lista de columnas a eliminar
            columnas_a_eliminar = [
                't', 'o2', 'co2', 'presion', 'flujo', 'volumen', 'ciclo', 'fase', 
                'delta_V(iE)', 'delta_V(iI)', 'sum_delta_V(iI)', 'sum_delta_V(iE)', 
                'Dif_vol', 'I_E', 'tipo de ciclo', 'VDana_new', 'delta_VO2_INS/ESP', 
                'VO2_ciclo', 'VO2_ciclo_correcion_fuga', 'delta_VCO2_INS/ESP', 
                'VCO2_ciclo', 'VCO2_ciclo_correcion_fuga', 'hr', 'spo2', 
                'VO2_ciclo (ml) ALT2', 'VCO2_ciclo (ml) ALT2'
            ]
            # Eliminar las columnas del DataFrame
            df_resultados = df_resultados.drop(columns=columnas_a_eliminar, errors='ignore')
            df_resultados.to_excel(archivo_salida, index=False)
            print(f"Set {i} completado - Guardado en: {archivo_salida}")
            
        except Exception as e:
            print(f"Error procesando Set {i}: {str(e)}")
            continue
    print(f"\nProcesamiento completado para todos los sets del Paciente {num_paciente}")
# Ejecución
def ejecutar_proceso():
    while True:
        menu()
        opcion = input("Ingrese un número para elegir el proceso: ").strip()
        if opcion == "1":
            try: 
                print("\n✅ Ejecutando Proceso 1, Graficando...")
                paciente = input("\n Ingrese el numero del paciente: ")
                print("\nEjecutando la importación de los datos...")
                directorio_base = os.path.join(os.getcwd(), f"Paciente_{paciente}")
                ruta_datos_crudos = os.path.join(directorio_base, f"Paciente_{paciente}_correcion_retraso.xlsx")
                df = leer_excel_con_ruta(ruta_datos_crudos)
                while continuar_proceso():
                    grafica(df)
                print("Proceso detenido. ✅")
            except Exception as e:
                print(f"Ocurrió un error: {e}")
                print("Proceso detenido. ✅")
        elif opcion == "2":
            try:
                print("\n✅ Ejecutando Proceso automatico 2.")
                proc_autom_1()
            except Exception as e:
                print(f"Ocurrió un error: {e}")
                print("Proceso detenido. ✅")
                break
        elif opcion == "3":
            try: 
                print("\n✅ Dividiendo los datos en subsets")
                proc_subsets()
            except Exception as e:
                print(f"Ocurrió un error: {e}")
                print("Proceso detenido. ✅")
                break
        elif opcion == "4":
            try: 
                print("✅ Realizando el analisis final")
                paciente = int(input("Ingrese el numero del paciente: "))
                sets =int(input("\nIngrese el numero total de sets: "))
                proc_autom_2(paciente,sets)
                procesar_all_sets(paciente, sets)
                print("\nProceso completado. ✅")
            except Exception as e:
                print(f"Ocurrió un error: {e}")
                print("Proceso detenido. ✅")
                break
        elif opcion == "5":
            try:
                print("\n✅ Ejecutando Proceso 5, Graficando...")
                paciente = input("\n Ingrese el numero del paciente: ")
                print("\nEjecutando la importación de los datos...")
                directorio_base = os.path.join(os.getcwd(), f"Paciente_{paciente}")
                ruta_datos_crudos = os.path.join(directorio_base, f"Paciente_{paciente}_correcion_retraso.xlsx")
                df = leer_excel_con_ruta(ruta_datos_crudos)
                while continuar_proceso():
                    grafica_comp(df)
                print("Proceso detenido. ✅")
            except Exception as e:
                print(f"Ocurrió un error: {e}")
                print("Proceso detenido. ✅")
        elif opcion == "0":
            print("\n👋 Saliendo del programa...")
            print("\n👋 Hasta la próxima")
            break  
# Main
ejecutar_proceso()
