# Inducción PMA (versión juego, v2)

## A. Probarla en tu laptop (Windows)
1. Instala Python 3.10+ (marca "Add Python to PATH").
2. Extrae esta carpeta en un lugar PROPIO (por ejemplo D:\Induccion), nunca dentro de la carpeta del dashboard de Asistencia.
3. Doble clic en `iniciar_induccion.bat` (abre en http://localhost:8502, así no choca con el dashboard de Asistencia en el 8501).

## B. Ponerla en línea (celulares)
Código en GitHub (repositorio privado) y publicación en Streamlit Community Cloud. Para actualizar: extrae el zip en una
carpeta limpia, en GitHub usa Add file > Upload files, arrastra TODO el contenido y Commit changes.

## C. Guardar los resultados en una hoja de cálculo
Elige UNA de las dos vías y pega el dato en Streamlit > tu app > Settings > Secrets.

### Vía 1 (recomendada): Google Forms
1. Crea un formulario de Google con 8 preguntas de «Respuesta corta», en este orden y con estos nombres:
   nombre, puesto, area, sede, puntos, porcentaje, examen_puesto, errores. Sin validaciones ni preguntas obligatorias.
2. Configuración > Respuestas: desactiva «Recopilar direcciones de correo» y «Limitar a 1 respuesta».
3. Menú ⋮ > «Obtener enlace prellenado». Escribe una «x» en las 8 preguntas, «Obtener enlace», «Copiar enlace».
4. Pestaña Respuestas > «Vincular a Hojas de cálculo»: ahí llegan los resultados.
5. En Secrets agrega:   FORM_ENLACE = "el_enlace_prellenado"

### Vía 2: Apps Script (guarda además cada respuesta en otra pestaña)
Pega `apps_script_hoja_google.gs` en Extensiones > Apps Script de tu hoja, impleméntalo como aplicación web
(Ejecutar como: Yo; Acceso: Cualquier persona) y en Secrets agrega:
   HOJA_URL = "la_url_que_termina_en_/exec"
   HOJA_TOKEN = "la_misma_clave_del_script"

### Para cualquiera de las dos
   CLAVE_ADMIN = "una_clave"
Luego abre la app, despliega la barra lateral > «Panel Capital Humano», escribe la clave y presiona
«Probar conexión con la hoja». Te dice si funcionó y, si no, qué revisar.

## Qué editar
- `app.py`: al inicio están `SEDES`, `SEDES_HORARIO_2026` y `SEDES_COMITE` (para qué sedes hay horarios y comité propios).
- `contenido_base.py`: textos y preguntas del PPT.
- `bloques.py`: orden de los 7 bloques, tarjetas, preguntas nuevas y comité.
- `puestos.json`: los 39 puestos del MOF.
- `horarios.json`: horarios 2026 de Chimbote y qué puesto usa cuál.
- `examen_puesto.py`: cómo se arma el examen de cada puesto.
- `envio.py`: envío de resultados a Google.
- `assets/`: imágenes (diapositivas, organigrama, fotos del comité, dibujos de puestos).

## Notas
- Si no configuras ninguna hoja, los resultados quedan solo en `data/` (en la nube esa carpeta no es permanente).
- Si la app se queda muchas horas sin visitas, la nube la duerme: la primera persona verá un botón para despertarla.
