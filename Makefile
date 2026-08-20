TARGET = sobol4emu
RESOURCES = src/resources.py
TARGET_PATH = /opt/vlab/sobol4

all: deb

compile: $(RESOURCES)

deb: clean
	@echo "Чтение шаблона deb-пакета..."
	$(eval PKG_NAME := $(shell awk '/^Package:/ {print $$2}' control))
	$(eval BASE_VER  := $(shell awk '/^Version:/ {print $$2}' control))
	$(eval PKG_ARCH := $(shell awk '/^Architecture:/ {print $$2}' control))

	$(eval GIT_REV  := $(shell git rev-list --count HEAD 2>/dev/null || echo 0))
	$(eval PKG_VER  := $(BASE_VER).$(GIT_REV))

	$(eval BUILD_PATH := $(shell mktemp -d /tmp/deb-build.XXXXXX))

	@echo "Подготовка структуры deb-пакета..."
	@mkdir -p $(BUILD_PATH)/DEBIAN
	@cp control $(BUILD_PATH)/DEBIAN/control

	@# cp postinst $(BUILD_PATH)/DEBIAN/postinst
	@# cp prerm $(BUILD_PATH)/DEBIAN/prerm
	@# chmod 755 $(BUILD_PATH)/DEBIAN/postinst
	@# chmod 755 $(BUILD_PATH)/DEBIAN/prerm

	@mkdir -p $(BUILD_PATH)$(TARGET_PATH) $(BUILD_PATH)/etc/xdg/autostart
	@cp -r src img ui $(BUILD_PATH)$(TARGET_PATH)
	@cp ibutton2dbus.desktop $(BUILD_PATH)/etc/xdg/autostart

	@echo "Сборка deb-пакета..."
	@dpkg-deb --build --root-owner-group $(BUILD_PATH) $(PKG_NAME)_$(PKG_VER)_$(PKG_ARCH).deb
	@rm -rf $(BUILD_PATH)
	@echo "Пакет успешно собран: $(PKG_NAME)_$(PKG_VER)_$(PKG_ARCH).deb"


# $@ - имя цели ($(RESOURCES))
# $< - имя первого переквизита (prerequisite, зависимость) (src/resources.qrc)
# $^ - список всех пререквизитов (разделенных пробелами)
$(RESOURCES): src/resources.qrc ui/*.ui img/*.png
	pyrcc5 src/resources.qrc -o $@

clean:
	rm -rf $(BUILD_PATH)
	rm -rf src/__pycache__
	rm -f $(RESOURCES) $(PKG_NAME)
