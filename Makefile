TARGET = sobol4
PKGNAME = sobol4-1.1.deb
DISTPATH = sobol4/opt/sobol4/
RESOURCES = src/resources.py

srcdir = src

compile: $(RESOURCES)

dpkg: compile src/*.py src/*.ui
	cp -r src img panels $(DISTPATH)
	dpkg-deb --build sobol4 $(PKGNAME)


onefile: compile src/*.py src/*.ui
	pyinstaller --onefile --windowed --add-data="src/*.ui:." --name $(TARGET) src/sobol4.py

# $@ - имя цели ($(RESOURCES))
# $< - имя первого переквизита (prerequisite, зависимость) (src/resources.qrc)
# $^ - список всех пререквизитов (разделенных пробелами)
$(RESOURCES): src/resources.qrc src/*.ui img/*.png
	pyrcc5 src/resources.qrc -o $@

clean:
	rm -rf $(TARGET).spec build dist $(DISTPATH)*
	rm -rf src/__pycache__
	rm -f $(RESOURCES) $(PKGNAME)
