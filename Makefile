TARGET = sobol4emu
PKGNAME = sobol4emu-2.2.deb
RESOURCES = src/resources.py
BUILDPATH = /tmp/sobol4emu
TARGETPATH = /opt/sodol4emu

all: dpkg

compile: $(RESOURCES)

dpkg:
	rm -rf src/__pycache
	mkdir -p $(BUILDPATH)$(TARGETPATH) $(BUILDPATH)/etc/xdg/autostart $(BUILDPATH)/DEBIAN
	cp control $(BUILDPATH)/DEBIAN
	cp -r src img ui $(BUILDPATH)$(TARGETPATH)
	cp ibutton2dbus.desktop $(BUILDPATH)/etc/xdg/autostart
	fakeroot sh -c "chown -R root:root $(BUILDPATH) && dpkg-deb --build $(BUILDPATH) $(PKGNAME)"
@echo "Пакет успешно собран: $(PKGNAME)"

# $@ - имя цели ($(RESOURCES))
# $< - имя первого переквизита (prerequisite, зависимость) (src/resources.qrc)
# $^ - список всех пререквизитов (разделенных пробелами)
$(RESOURCES): src/resources.qrc ui/*.ui img/*.png
	pyrcc5 src/resources.qrc -o $@

clean:
	rm -rf $(BUILDPATH)
	rm -rf src/__pycache__
	rm -f $(RESOURCES) $(PKGNAME)
