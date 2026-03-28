TARGET = sobol
RESOURCES = src/resources.py

srcdir = src

compile: $(RESOURCES)

onefile: compile src/*.py src/*.ui
	pyinstaller --onefile --windowed --add-data="src/*.ui:." --name $(TARGET) src/sobol4.py

# $@ - имя цели ($(RESOURCES))
# $< - имя первого переквизита (prerequisite, зависимость) (src/resources.qrc)
# $^ - список всех пререквизитов (разделенных пробелами)
$(RESOURCES): src/resources.qrc src/*.ui img/*.png
	pyrcc5 src/resources.qrc -o $@

clean:
	rm -rf $(TARGET).spec build dist
	rm -rf src/__pycache__
	rm src/resources.py
