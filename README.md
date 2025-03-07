# 📊 Análisis de Ciclos Respiratorios

Este repositorio contiene un conjunto de scripts en Python para procesar y analizar datos de ciclos respiratorios a partir de archivos Excel. El sistema automatiza la importación, el procesamiento, el análisis y la exportación de datos, permitiendo la extracción de métricas clave para el estudio de patrones respiratorios.

---

## 🚀 Características Principales
✅ **Carga y procesamiento de datos** desde archivos Excel.  
✅ **Cálculo de métricas respiratorias** como frecuencia, presión, volumen y sincronización de fases.  
✅ **Corrección de fugas y análisis de tendencias.**  
✅ **Generación de gráficos** para visualización de datos.  
✅ **Exportación de resultados** en archivos Excel con la información procesada.  

---

## 📂 Estructura del Proyecto
```
📁 Paciente_{num_paciente}/
 ├── 📁 Subsets_Con_Oximetria_Paciente_{num_paciente}/   # Datos procesados por set
 ├── 📁 Subsets_Procesados_Finales_Paciente_{num_paciente}/  # Resultados finales
 ├── 📄 Paciente_{num_paciente}_correcion_retraso.xlsx  # Datos crudos corregidos
 ├── 📜 scripts/  # Código fuente
```

---

## 🛠️ Instalación y Uso
### 🔹 Requisitos Previos
Antes de ejecutar el código, asegúrate de tener instalado:
- Python 3.8+
- Pandas
- NumPy
- Matplotlib
- OpenPyXL

Instala las dependencias con:
```bash
pip install -r requirements.txt
```

### 🔹 Ejecución del Programa
Para ejecutar el análisis, usa:
```bash
python main.py
```
El sistema pedirá el número del paciente y el número total de conjuntos de datos (sets) a procesar.

---

## 📊 Flujo de Trabajo
1️⃣ **Importación de Datos:** Se cargan archivos Excel con registros de ciclos respiratorios.  
2️⃣ **Procesamiento:** Se ejecutan cálculos de métricas como presiones, volúmenes y tiempos.  
3️⃣ **Corrección de Fugas:** Se aplican correcciones a las mediciones de O₂ y CO₂.  
4️⃣ **Análisis Final:** Se generan estadísticas y gráficos para su interpretación.  
5️⃣ **Exportación:** Los resultados finales se guardan en archivos Excel en la carpeta `Subsets_Procesados_Finales_Paciente_{num_paciente}`.

---

## 📝 Notas y Mejoras Futuras
🔹 Agregar más validaciones para evitar errores con archivos faltantes.  
🔹 Optimizar el tiempo de procesamiento al reducir llamadas innecesarias a funciones.  
🔹 Implementar una interfaz gráfica para facilitar la selección de archivos y visualización de datos.  

---

## 🤝 Contribuciones
Si deseas contribuir, abre un issue o envía un pull request con mejoras.

---

## 📜 Licencia
Este proyecto está bajo la licencia MIT. ¡Úsalo libremente! 🚀

