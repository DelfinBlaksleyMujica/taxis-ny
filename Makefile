# Usamos shell para obtener la lista de archivos una sola vez
PYTHON_FILES := $(shell find . -iname "*.py" -not -path "./tests/*")

default: pylint pytest

pylint:
	# El prefijo '-' permite que continue si hay errores de estilo
	-pylint --output-format=colorized $(PYTHON_FILES)

pytest:
	# Pytest ya detecta colores si la terminal lo soporta
	PYTHONDONTWRITEBYTECODE=1 pytest -v
