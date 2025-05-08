# 📊 Análisis de Ciclos Respiratorios

Este repositorio contiene un conjunto de scripts en Python para procesar y analizar datos de ciclos respiratorios a partir de archivos Excel. El sistema automatiza la importación, el procesamiento, el análisis y la exportación de datos, permitiendo la extracción de métricas clave para el estudio de patrones respiratorios.

---
## 🚀 Características
- 🔍 Procesamiento de datos crudos para identificación de ciclos y fases respiratorias.
- 🔄 Sincronización y ajuste de datos con retrasos en sensores.
- 📈 Generación de gráficos para visualización de datos.
- 📊 Cálculo de variables relevantes como volumen, presión, flujo y otros.
- 💾 Almacenamiento de resultados en archivos Excel.

## 🛠️ Requisitos
Este proyecto requiere Python 3 y las siguientes librerías:
- 🐍 `pandas`
- 🔢 `numpy`
- 🎨 `matplotlib`
- 🧪 `scipy`
- 🎛️ `tkinter`
- 📂 `openpyxl`

Puedes instalarlas con:
```bash
pip install pandas numpy matplotlib scipy openpyxl
```

## 🚀 Uso
1. 📂 Coloca los archivos de datos en la misma carpeta que el script.
2. ▶️ Ejecuta el script:
```bash
python Final_Code.py
```
3. 🖥️ Sigue las instrucciones en la terminal para seleccionar el proceso deseado.
De forma mas detallada:
1. Ejecuta el codigo con la carpeta llamada Paciente_i en la misma carpeta del script
2. Ejecuta el script
3. En consola, ejecutar la opción 2, teniendo en cuenta que se necesita el fast_decoded y el spo2
4. Revisar cual es el retraso de O2 y CO2 para el paciente
5. Realizar la tabla de subgrupos con el archivo final que se crea en el proceso 2.
6. Dividir el paciente en subsets con el proceso 3
7. Procesar el paciente finalmente, ejecutar el proceso 4
8. Generar hoja de resumen con los datos del paciente procesados finales.

A continuación se explica de manera detallada los archivos usados y generados por el codigo y de forma manual
- fast_decoded y spo2_decoded: Archivos fuentes que nos pasa Mateo.
- Paciente_1_proceso_ciclos y fases_ciclo inicio(1)_ciclo final(2358): Contiene el procesamiento inicial que separa los datos por ciclos.
- Paciente_1_correcion_retraso: Contiene los datos con el retraso de O2 y CO2 realizado según cada paciente.
- Paciente_1_Promedios_por_Ciclos_PEEP_Vt_F: Contiene el resumen de cada ciclo para identificar los cambios de variables y poder dividir el archivo en subsets.
- Subsets_Crudos_Paciente_1: Contiene los datos retrasados sin procesamiento adicional PERO dividido por subsets.
- Subsets_Sin_Oximetria_Paciente_1: Contiene los datos de cada subset donde se hacen los cálculos del Vol_E, VDana, Columnas para fase espiratoria, detección de asincronías, VO2 y CO2 real, VO2 y VCO2 calculado por la integral del flujo.
- Subsets_Con_Oximetria_Paciente_1: Se le agrega a los datos procesados anteriormente los datos de oximetría.
- Subsets_Procesados_Finales_Paciente_1: Contiene el archivo de cada subset con los cálculos finales y el resumen en las ultimas filas del archivo
- Docs: Contiene la presentación de Power Point, el resumen del paciente 1 y la tabla de subgrupos.

## 🏗️ Estructura del Código
- ⚙️ **Procesamiento inicial**: Limpieza y estructuración de los datos.
- 🕒 **Sincronización y ajuste**: Aplicación de retrasos y correcciones.
- 📊 **Cálculo de variables**: Determinación de métricas respiratorias.
- 📑 **Generación de reportes**: Almacenamiento de los resultados en Excel.

  ## 📂 Estructura del Proyecto
```
📦 Respiratory-Cycle-Analysis
├── 📜 README.md      # Documentación del proyecto
├── 📂 Paciente_i     # Carpeta para los archivos iniciales y donde se guardarán los analizados finales
└── 📜 Final_Code.py  # Script principal del análisis
```

  
## 📝 Notas y Mejoras Futuras
🔹 Agregar más validaciones para evitar errores con archivos faltantes.  
🔹 Optimizar el tiempo de procesamiento al reducir llamadas innecesarias a funciones.  
🔹 Implementar una interfaz gráfica para facilitar la selección de archivos y visualización de datos.  

---
## 🤝 Contribuciones
Si deseas contribuir, siéntete libre de hacer un fork y enviar un pull request con mejoras o correcciones. 🛠️✨

## 📜 Licencia
Este proyecto se distribuye bajo la licencia MIT. ✅
