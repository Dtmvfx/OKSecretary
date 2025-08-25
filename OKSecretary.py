import os
import sys
from datetime import datetime
from random import randint
from time import sleep
from PySide6.QtCore import Qt, Signal, QObject, QThread
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QCheckBox, QPushButton, QTextEdit, QSplitter, QGroupBox, QSizePolicy, QLineEdit
from patchright.sync_api import sync_playwright
#-----------------------------------------------------------------------------------------------------------------------
id_account = ''; worker_thread = None
with open('stop_words.txt', 'r', encoding='utf-8') as f: stop_words: list[str] = f.read().split(',')

#-----------------------------------------------------------------------------------------------------------------------
def page_goto(page, url, signals, wait_until='load'):
    try: page.goto(url, timeout=180000)
    except Exception:
        for i in range(2):
            try: page.reload()
            except Exception:
                if i == 1: signals.log_signal.emit(f'!ЗАВИСАНИЕ СТРАНИЦЫ! Адрес: [{url}] недоступен длительное время. Перезапусти при необходимости неотработанные функции позже.')
                continue
            break

#-----------------------------------------------------------------------------------------------------------------------
def update_log(message):
    current_time = datetime.now().strftime('%H:%M:%S')
    log_message = f"[{current_time}:] {message}"  # Формируем строку с временем перед сообщением
    log_output.append(log_message)  # Добавляем сообщение в QTextEdit
    with open(f".log\\log{datetime.now().strftime("%d-%m-%Y")}.txt", "a", encoding="utf-8") as log_file:
        log_file.write(log_message + "\n")  # Запись лога в файл

#============================================OK==f=u=n=c=t=i=o=n=s======================================================
def start_ok(page, signals):
    try:
        global id_account
        page_goto(page, 'https://ok.ru/', signals)
        signals.log_signal.emit(f'ПАУЗА ДЛЯ ВХОДА В АККАУНТ. ПОСЛЕ АВТОРИЗАЦИИ ЗАКРОЙТЕ ОКНО ИНСПЕКТОРА И СКРИПТ ПРОДОЛЖИТ РАБОТУ'); page.pause()
        page.wait_for_selector('//a[@data-l="t,userPage"]')
        id_account = page.locator('//a[@data-l="t,userPage"]').get_attribute('href')
        signals.log_signal.emit(f'\n\n\n<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< СТАРТ ОСНОВНОГО АККАУНТА OK // {id_account} >>>>>>>>>>>>>>>>>>>>>>>>>>>>>\n')
    except Exception as e: signals.log_signal.emit(f'!КРИТИЧЕСКАЯ ОШИБКА!: НЕ УДАЛСЯ СТАРТ ОК // {e}\n\n')

#-----------------------------------------------------------------------------------------------------------------------
def liking_ok(page, signals):
    stories = 0; posts = 0
    try:
        signals.log_signal.emit('\n~~~~~~~~~~~~~~~~~~~~~~ ЛАЙКИНГ [OK] ~~~~~~~~~~~~~~~~~~~~~~\n')
        name_my_community = line_edit.text()
        if name_my_community: group_for_like_list = [f'https://ok.ru{id_account}', name_my_community]
        else: group_for_like_list = [f'https://ok.ru{id_account}']
        for group in group_for_like_list:
            repost = 0
            page_goto(page, group, signals)
            if page.locator('//span[contains(@class,"content") and text()="Скрыть"]').is_visible():
                page.click('//span[contains(@class,"content") and text()="Скрыть"]')
            page.evaluate("window.scrollBy(0, 3000)"); sleep(2)
            for post_number in range(5):
                el = page.locator('//div[@class="feed-w"]').nth(post_number)
                el_html = el.inner_html()
                if ((group != f'https://ok.ru{id_account}')
                        and 'class="widget  __no-count __redesign2023"' in el_html and repost == 0):
                    page.hover('//*[@class="widget_tx" and text()="Класс"][1]')
                    page.locator('//span[@title="Класс! (Приватная эмоция)"]').click(force=True)
                    page.locator(f'(//button[@aria-label="Поделиться"])[{post_number+1}]').click(delay=2000)
                    page.click('//*[text()="Поделиться сейчас"]')
                    repost = 1
                elif 'class="widget  __no-count __redesign2023"' in el_html:
                    page.hover('//*[@class="widget_tx" and text()="Класс"][1]')
                    page.locator('//span[@title="Класс! (Приватная эмоция)"]').click(force=True)
                    page.locator(f'(//button[@aria-label="Поделиться"])[{post_number+1}]').click(delay=2000)
                    if page.locator('//*[text()="Добавить в моменты"]').is_visible(timeout=2000):
                        page.click('//*[text()="Добавить в моменты"]'); sleep(3)
        signals.log_signal.emit('Мой профиль/группа ОК: полайкано, отрепощено, отправлено в моменты из профиля')
        try:
            page_goto(page, 'https://ok.ru', signals)
            page.click('(//div[@data-tsid="avatar-test-id"])[3]')
            for stories in range(31):
                sleep(1)
                page.locator('#dailyphoto-layer .dp_00599:first-of-type').hover(force=True)
                page.locator('#dailyphoto-layer .dp_00599:first-of-type').click()
                page.keyboard.press('ArrowRight')
            page.keyboard.press('Escape')
        except Exception: pass
        for posts in range (151):
            page.mouse.wheel(0, 1400); page.hover('(//*[@class="widget_tx" and text()="Класс"])[1]', force=True)
            page.keyboard.press('ArrowUp'); page.keyboard.press('ArrowUp'); page.hover('(//*[@class="widget_tx" and text()="Класс"])[1]', force=True)
            page.locator('//span[@title="Класс! (Приватная эмоция)"]').click()                          # click private like
        signals.log_signal.emit(f'Контент: Отлайкано {stories} историй и {posts} постов\n')
    except Exception: signals.log_signal.emit(f'Контент: Отлайкано {stories} историй и {posts} постов\n')

#-----------------------------------------------------------------------------------------------------------------------
def outgoing_requests_ok(page, signals):
    try:
        out_requests = 0
        signals.log_signal.emit(f'\n~~~~~~~~~~~~~~~~~~~~~~ ПОСЫЛАЕМ ИСХОДЯЩИЕ ЗАЯВКИ В ДРУЗЬЯ [рекомендации ОК] ~~~~~~~~~~~~~~~~~~~~~~\n')
        page_goto(page, 'https://ok.ru/dk?st.cmd=searchResult&st.mode=Users&st.grmode=Groups', signals)
        for i in range(50): page.mouse.wheel(0, 99999); sleep(3)
        cnt = page.locator('//div[@data-logger="SimpleLogger"][.//span[contains(@class,"user-online")] and .//*[text()="Добавить в друзья"]]').count()
        signals.log_signal.emit(f'Pекомендаций для заявок в друзья: [{cnt}]\n')

        for i in range (cnt):
            while out_requests < 50:
                num_cur_user_card = randint(3, cnt-70)
                combo_str_lower = page.locator('//div[@data-logger="SimpleLogger"][.//span[contains(@class,"user-online")] and .//*[text()="Добавить в друзья"]]').nth(num_cur_user_card).inner_text().lower()
                matching_stop_word = next((word for word in stop_words if word in combo_str_lower), None)
                if matching_stop_word is not None: continue
                try: page.locator('//div[@data-logger="SimpleLogger"][.//span[contains(@class,"user-online")]]//*[text()="Добавить в друзья"]').nth(num_cur_user_card).click(); sleep(0.5)
                except Exception: continue
                if page.get_by_text("Подружиться не удалось").is_visible():
                    signals.log_signal.emit('--------> Много заявок / выходим'); return
                else:
                    out_requests += 1
                    signals.log_signal.emit(f'Отправлена заявка [{out_requests}] в друзья // Юзер: {combo_str_lower}')
    except Exception as e: signals.log_signal.emit(f'\n!!!!!ЧТО-ТО СЛОМАЛОСЬ ПРИ ОТПРАВКЕ ИСХОДЯШЕК [ОК]!!!!! //  ошибка: {e}\n')

#-----------------------------------------------------------------------------------------------------------------------
def incoming_requests_ok(page, signals):
    try:
        signals.log_signal.emit(f'\n~~~~~~~~~~~~~~~~~~~~~~ ПРОВЕРКА ВХОДЯЩИХ ЗАЯВОК В ДРУЗЬЯ [ОК] ~~~~~~~~~~~~~~~~~~~~~~\n')
        page_goto(page, f'https://ok.ru{id_account}/friendRequests', signals)

        while page.get_by_text('Входящие заявки в друзья').is_visible(timeout=2000):
            page.locator('(//a[@data-l="t,e2" and @class="o"])[1]').click()
            name = page.locator('//h1').inner_text()
            descr = page.locator('//div[@id="hook_Block_AboutUserRB"]').inner_text()
            combo_str_lower = ' '.join([name, descr]).lower()
            matching_stop_word = next((word for word in stop_words if word in combo_str_lower), None)
            page.get_by_text('Ответить на заявку').click()
            if matching_stop_word:
                page.get_by_text('Игнорировать').click()
                signals.log_signal.emit(f'Юзер {name} ОТКЛОНЁН // Инфо: {combo_str_lower}\n------------------------------')
            else:
                page.get_by_text('Принять заявку').click()
                signals.log_signal.emit(f'Юзер {name} ПРИНЯТ в друзья // Инфо: {combo_str_lower}\n------------------------------')
            page_goto(page, f'https://ok.ru{id_account}/friendRequests', signals)
        signals.log_signal.emit('Заявок нет\n')
    except Exception as e: signals.log_signal.emit(f'\n!!!!!ЧТО-ТО СЛОМАЛОСЬ ПРИ ПРОВЕРКЕ ВХОДЯЩИХ ЗАЯВОК [ОК]!!!!! //  ошибка: {e}\n')

#-----------------------------------------------------------------------------------------------------------------------
def dell_out_requests_ok(page, signals):
    out_requests = 0
    try:
        signals.log_signal.emit(f'\n~~~~~~~~~~~~~~~~~~~~~~ УДАЛЯЕМ И БЛОКИРУЕМ СВОИ ЗАВИСШИЕ ПОДПИСКИ [ОК] ~~~~~~~~~~~~~~~~~~~~~~\n')
        page_goto(page, f'https://ok.ru/{id_account}/subscriptions', signals)

        while page.locator('(//a[@class="n-t bold"])[1]').is_visible(timeout=2000):
            page.hover('(//a[@class="n-t bold"])[1]')
            page.click('//div[@id="hook_Block_ShortcutMenu"]//text()[.="Заблокировать"]/..', delay=1500)
            page.click('//*[@id="hook_FormButton_button_add_confirm"]')
            out_requests += 1
        signals.log_signal.emit(f'Удалено {out_requests} подписок\n')
    except Exception as e: signals.log_signal.emit(f'\n!!!!!ЧТО-ТО СЛОМАЛОСЬ В УДАЛЯШКЕ ПОДПИСОК [ОК]!!!!! Удалено: {out_requests} подписок // ошибка: {e}\n')
#-----------------------------------------------------------------------------------------------------------------------
def send_invite_in_my_groups_ok(page, signals):
    try:
        title_my_group = line_edit.text()
        signals.log_signal.emit(f'\n~~~~~~~~~~~~~~~~~~~~~~ ИДЁТ ОТПРАВКА ДРУЗЬЯМ ИНВАЙТА В ГРУППУ [{title_my_group}] ~~~~~~~~~~~~~~~~~~~~~~\n')
        page_goto(page, title_my_group, signals)
        page.click('//button[@aria-label="Ещё"]')
        page.click('//*[text()="Пригласить друзей"]')
        page.click('//span[@class="irc_l" and contains(text(),"Выбрать")]')
        page.click('//input[@id="hook_FormButton_button_invite"]')

        if page.locator('//div[contains(text(),"слишком часто")]').is_visible(timeout=2000):
            page.click('//input[@id="buttonId_button_close"]')
            signals.log_signal.emit(f'Приглашение друзьям в: {title_my_group} НЕ ОТПРАВЛЕНО ("слишком часто")\n'); return
        signals.log_signal.emit(f'Приглашение друзьям в: {title_my_group} отправлено\n')
    except Exception: signals.log_signal.emit(f'Приглашение НЕ ОТПРАВЛЕНО! Проверьте url адрес группы!\n')
#====================================================M=I=N=E============================================================
class WorkerSignals(QObject):
    log_signal = Signal(str)

class WorkerThread(QThread):
    def __init__(self, signals):
        super().__init__()
        self.signals = signals

    def run(self):
        run_playwright(self.signals)
def start_playwright_thread():
    global worker_thread
    signals = WorkerSignals()
    signals.log_signal.connect(update_log)
    worker_thread = WorkerThread(signals)
    worker_thread.start()
def run_def_ok(page, signals):
    if cbox_function_ok[0].isChecked(): liking_ok(page, signals)
    if cbox_function_ok[1].isChecked(): incoming_requests_ok(page, signals)
    if cbox_function_ok[2].isChecked(): dell_out_requests_ok(page, signals)
    if cbox_function_ok[3].isChecked(): outgoing_requests_ok(page, signals)
    if cbox_function_ok[4].isChecked(): send_invite_in_my_groups_ok(page, signals)
def run_playwright(signals):
    if  not cbox_profiles_ok[0].isChecked():
        signals.log_signal.emit('\n~~~~~~~~~~~~~~~~~~~~~~ [ ВЫБЕРИ АККАУНТЫ ДЛЯ РАБОТЫ ] ~~~~~~~~~~~~~~~~~~~~~~\n'); return
    btn.setEnabled(False)
    line_edit.setEnabled(False)
    for cbox in cbox_function_ok + cbox_profiles_ok:
        cbox.setEnabled(False)                                                                   # Блокируем кнопку и все чекбоксы
    active_cbox_ok = [cbox.text() for cbox in cbox_function_ok if cbox.isChecked()]
    if not active_cbox_ok: active_cbox_ok.append('Нет активных функций')
    signals.log_signal.emit(f'{datetime.now().strftime("%d-%m-%Y")}: [[[[[[[[[[[[[[[ С Т А Р Т     O K S e c r e t a r y ]]]]]]]]]]]]]]]'                            f'\n\nАКТИВНЫЕ ФУНКЦИИ ДЛЯ ОК:\n\n{'\n '.join(item for item in active_cbox_ok)}\n')
    os.environ['PLAYWRIGHT_BROWSERS_PATH'] = '0'
    p = sync_playwright().start()
    browser = p.chromium.launch(executable_path="C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
                                args=["--disable-blink-features=AutomationControlled", '--enable-gpu',
                                      '--use-gl=desktop'],
                                headless=False, slow_mo=1000)
    context = browser.new_context(locale='en-US')
    context.set_default_timeout(60000)  # 60 seconds global timeout
    page = context.new_page()
    page.goto("https://intoli.com/blog/not-possible-to-block-chrome-headless/chrome-headless-test.html")
    if page.locator('text="missing (passed)"').is_visible(): signals.log_signal.emit('WebDriver не обнаружен')
    else: signals.log_signal.emit('\n!ВНИМАНИЕ! WebDriver ОБНАРУЖЕН')
    page.goto("https://www.browserscan.net/"); sleep(15)
    if page.locator('//a[@href="/bot-detection"]/preceding-sibling::span[1]').text_content() == 'Yes': signals.log_signal.emit('!ВНИМАНИЕ! Bot Detection НЕ ПРОЙДЕН')
    else: signals.log_signal.emit('Bot Detection пройден')
    if cbox_profiles_ok[0].isChecked():
        start_ok(page, signals)
        run_def_ok(page, signals)
    signals.log_signal.emit('\n\n~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ [ работа завершена ] ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n\n')
    os.system('powershell -c (New-Object Media.SoundPlayer "end.wav").PlaySync();')
    btn.setEnabled(True)
    for cbox in cbox_function_ok + cbox_profiles_ok:
        cbox.setEnabled(True)
#=======================================================================================================================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    dark_style = (
        "QWidget { background-color: #2E2E2E; color: #FFFFFF; } "
        "QCheckBox { background-color: #2E2E2E; color: #FFFFFF; font-size: 13px; } "
        "QTextEdit { background-color: #000000; color: #FFFFFF; font-size: 14px; } "
        "QPushButton { background-color: #4A4A4A; color: #FFFFFF; border: 1px solid #5A5A5A; font-size: 15px; } "
        "QPushButton:hover { background-color: #5A5A5A; }"
    )
    app.setStyleSheet(dark_style)
    w = QWidget()
    w.setWindowTitle('[OK_Secretary]')
    w.resize(1400, 350)
    layout = QVBoxLayout()
    splitter = QSplitter(Qt.Orientation.Horizontal)
    checkbox_widget = QWidget()
    checkbox_layout = QVBoxLayout()
    group1 = QGroupBox("Профили ОК")
    cbox_profiles_ok = [QCheckBox('[PROFILE OK : 1]')]
    layout1 = QVBoxLayout()
    group1.setLayout(layout1)
    for cb in cbox_profiles_ok:
        cb.setChecked(True)
        layout1.addWidget(cb)
    group1.setFixedSize(400, 80)
    group2 = QGroupBox("Выполняемые функции ОК")
    cbox_function_ok = [
        QCheckBox('[ЛАЙКИ/РЕПОСТЫ (группы, акки, посты и истории)]'),
        QCheckBox('[ПРОВЕРКА ВХОДЯЩИХ ЗАЯВОК В ДРУЗЬЯ]'),
        QCheckBox('[УДАЛЕНИЕ ИСХОДЯЩИХ ПОДПИСОК]'),
        QCheckBox('[ОТПРАВИТЬ ЗАЯВКИ В ДРУЗЬЯ]'),
        QCheckBox('[ОТПРАВИТЬ ПРИГЛАШЕНИЯ В ГРУППУ]')
    ]
    layout2 = QVBoxLayout()
    group2.setLayout(layout2)
    for cb in cbox_function_ok:
        cb.setChecked(True)
        layout2.addWidget(cb)
    line_edit = QLineEdit()
    line_edit.setPlaceholderText("адрес группы для инвайта: https://...")
    layout2.addWidget(line_edit)
    group2.setFixedSize(400, 200)
    def check_groups():
        if not (cbox_profiles_ok[0].isChecked()):
            for cb in cbox_function_ok:
                cb.setChecked(False)
    def key_press_event(event):
        if event.key() == 16777220:
            start_playwright_thread()
    for cb in cbox_profiles_ok + cbox_function_ok:
        cb.stateChanged.connect(check_groups)
    checkbox_layout.addWidget(group1)
    checkbox_layout.addWidget(group2)
    checkbox_widget.setLayout(checkbox_layout)
    log_output = QTextEdit()
    log_output.resize(1100, 300)
    log_output.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
    log_output.setReadOnly(True)
    splitter.addWidget(checkbox_widget)
    splitter.addWidget(log_output)
    btn = QPushButton('ВЫПОЛНИТЬ ПРОГРАММУ С ВЫБРАННЫМИ ОПЦИЯМИ')
    btn.clicked.connect(start_playwright_thread)
    layout.addWidget(splitter)
    layout.addWidget(btn)
    w.setLayout(layout)
    w.show()
    w.keyPressEvent = key_press_event
    sys.exit(app.exec())
#-----------------------------------------------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------------------------------------------
