import configparser

# Конфиг определен в модуле, чтобы импортировать его единственный экземпляр,
# а не передавать каждый раз ссылку при создании объектов классов
config = configparser.ConfigParser(allow_no_value=True)
# Установить чувствительность ключей к регистру
config.optionxform = str
