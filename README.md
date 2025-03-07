# 📊 Análisis de Ciclos Respiratorios

Este repositorio contiene un conjunto de scripts en Python para procesar y analizar datos de ciclos respiratorios a partir de archivos Excel. El sistema automatiza la importación, el procesamiento, el análisis y la exportación de datos, permitiendo la extracción de métricas clave para el estudio de patrones respiratorios.

---

## 🚀 Características Principales
✅ Procesamiento de datos crudos para identificación de ciclos y fases respiratorias.
✅ Sincronización y ajuste de datos con retrasos en sensores.
✅ Generación de gráficos para visualización de datos.
✅ Cálculo de variables relevantes como volumen, presión, flujo y otros.
✅ Almacenamiento de resultados en archivos Excel.

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

## Requisitos
Este proyecto requiere Python 3 y las siguientes librerías:
- `pandas`
- `numpy`
- `matplotlib`
- `scipy`
- `tkinter`
- `openpyxl`

Puedes instalarlas con:
```bash
pip install pandas numpy matplotlib scipy openpyxl
```

## Uso
1. Coloca los archivos de datos en la misma carpeta que el script.
2. Ejecuta el script:
```bash
python Final_Code.py
```
3. Sigue las instrucciones en la terminal para seleccionar el proceso deseado.

## Estructura del Código
- **Procesamiento inicial**: Limpieza y estructuración de los datos.
- **Sincronización y ajuste**: Aplicación de retrasos y correcciones.
- **Cálculo de variables**: Determinación de métricas respiratorias.
- **Generación de reportes**: Almacenamiento de los resultados en Excel.

## 📝 Notas y Mejoras Futuras
🔹 Agregar más validaciones para evitar errores con archivos faltantes.  
🔹 Optimizar el tiempo de procesamiento al reducir llamadas innecesarias a funciones.  
🔹 Implementar una interfaz gráfica para facilitar la selección de archivos y visualización de datos.  

---

## 🤝 Contribuciones
Si deseas contribuir, siéntete libre de hacer un fork y enviar un pull request con mejoras o correcciones.

---

## 📜 Licencia
Este proyecto está bajo la licencia MIT. ¡Úsalo libremente! 🚀

