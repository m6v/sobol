# virDomainEventType
VIR_DOMAIN_EVENT_MAPPING = {
    0: "VIR_DOMAIN_EVENT_DEFINED",
    1: "VIR_DOMAIN_EVENT_UNDEFINED",
    2: "VIR_DOMAIN_EVENT_STARTED",
    3: "VIR_DOMAIN_EVENT_SUSPENDED",
    4: "VIR_DOMAIN_EVENT_RESUMED",
    5: "VIR_DOMAIN_EVENT_STOPPED",
    6: "VIR_DOMAIN_EVENT_SHUTDOWN",
    7: "VIR_DOMAIN_EVENT_PMSUSPENDED",
}

# virDomainState
VIR_DOMAIN_STATE_MAPPING = {
    0: "VIR_DOMAIN_NOSTATE",
    1: "VIR_DOMAIN_RUNNING",
    2: "VIR_DOMAIN_BLOCKED",
    3: "VIR_DOMAIN_PAUSED",
    4: "VIR_DOMAIN_SHUTDOWN",
    5: "VIR_DOMAIN_SHUTOFF",
    6: "VIR_DOMAIN_CRASHED",
    7: "VIR_DOMAIN_PMSUSPENDED",
}

KB_to_MB_FACTOR = 0.0009765625

# Нумерация панелей на странице инициализации платы
SYS_LOAD_PANEL = 0
COMMON_PARMS_PANEL = 1
JOURNAL_PARMS_PANEL = 2
PASSWD_PARMS_PANEL = 3
ADMIN_REGISTRATION_PANEL = 4
INTEGRITY_CONTROL_PANEL = 5

# Типы событий, регистрируемых в журнале
EVENTS_TYPE = {
    0: "Автоматический расчет КС",
    1: "Администратор сменил пароль пользователя",
    2: "Администратор сменил свой пароль",
    3: "Время/дата установки пароля опережает системное",
    4: "Вход администратора",
    5: "Вход пользователя",
    6: "Добавлен новый пользователь",
    7: "Запрос: Добавление пользователя",
    8: "Запрос: Удаление пользователя",
    9: "Идентификатор не зарегистрирован",
    10: "Изменение шаблонов КЦ",
    11: "Изменены параметры загрузочного диска",
    12: "Изменены системное время и дата",
    13: "Импорт ресурсов",
    14: "Не рассчитаны контрольные суммы",
    15: "Неправильный пароль",
    16: "Несоответствие идентификатора запроса",
    17: "Обнаружен перевод системного времени назад",
    18: "Обновление ключа КЦ",
    19: "Обработаны внешние запросы",
    20: "Ошибка КС в памяти идентификатора",
    21: "Ошибка внешнего запроса",
    22: "Ошибка обновления ключа КЦ",
    23: "Ошибка при контроле целостности",
    24: "Ошибка при экспорте журнала событий",
    25: "Перерасчет контрольных сумм",
    26: "Переход в автономный режим",
}
