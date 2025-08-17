import os
import sys
from datetime import datetime
from random import randint
from time import sleep
from PySide6.QtCore import Qt, Signal, QObject, QThread
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QCheckBox, QPushButton, QTextEdit, QSplitter, QGroupBox, QSizePolicy, QLineEdit

from patchright.sync_api import sync_playwright

#-----------------------------------------------------------------------------------------------------------------------
id_account = ''; worker_thread = None                         # Глобальная переменная для хранения потока
with open('stop_words.txt', 'r', encoding='utf-8') as f: stop_words: list[str] = f.read().split(',')

#-----------------------------------------------------------------------------------------------------------------------
def browser_start(p):
    browser = p.chromium.launch(channel="chrome",
                                args=["--disable-blink-features=AutomationControlled", '--enable-gpu', '--use-gl=desktop'],
                                headless=False, slow_mo=1000)
    context = browser.new_context(locale='en-US', storage_state="C:/Users/NICK/PycharmProjects/.auth/state.json") # auto auth with cookie
    context.set_default_timeout(60000)                                                                            # 60 seconds global timeout
    page = context.new_page()                                                                                     # start browser
    return  page, context, browser

#-----------------------------------------------------------------------------------------------------------------------
def page_goto(page, url, signals, context, browser, p, wait_until="load"):
    try: page.goto(url, timeout=180000)
    except Exception:
        browser.close()
        os.system("taskkill /IM chrome.exe /F")
        page, context, browser = browser_start(p)
        signals.log_signal.emit(f'!ЗАВИСАНИЕ СТРАНИЦЫ! Адрес: [{url}] недоступен. Перезапуск браузера!')
        try: page.goto(url, timeout=180000)
        except Exception:
            signals.log_signal.emit(f'ВСЁ! ПЗДЦ! Этому урлу ничто не поможет. Перезвоните позже')
    return page, context, browser

#-----------------------------------------------------------------------------------------------------------------------
def update_log(message):
    current_time = datetime.now().strftime('%H:%M:%S')
    log_message = f"[{current_time}:] {message}"  # Формируем строку с временем перед сообщением
    log_output.append(log_message)  # Добавляем сообщение в QTextEdit
    with open(f".log\\log{datetime.now().strftime("%d-%m-%Y")}.txt", "a", encoding="utf-8") as log_file:
        log_file.write(log_message + "\n")  # Запись лога в файл

#============================================OK==f=u=n=c=t=i=o=n=s======================================================
def start_ok(page, signals, context, browser, p):
    try:
        global id_account
        page, context, browser = page_goto(page, 'https://ok.ru/', signals, context, browser, p)
        link_profile = page.locator('//a[@data-l="t,userPage"]').get_attribute('href')
        if link_profile == "/turistor1": id_account = 'turistor1'
        else: change_account_ok(page, signals, context, browser, p)
        signals.log_signal.emit(f'\n\n\n<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< СТАРТ ОСНОВНОГО АККАУНТА OK // {id_account} >>>>>>>>>>>>>>>>>>>>>>>>>>>>>\n')
    except Exception as e: signals.log_signal.emit(f'!КРИТИЧЕСКАЯ ОШИБКА!: НЕ УДАЛСЯ СТАРТ ОК // {e}\n\n')

#-----------------------------------------------------------------------------------------------------------------------
def change_account_ok(page, signals, context, browser, p):
    try:
        global id_account
        page, context, browser = page_goto(page, 'https://ok.ru/', signals, context, browser, p)
        link_profile_cur = page.locator('//a[@data-l="t,userPage"]').get_attribute('href')
        page.click('//span[@class="ucard-mini_cnt"]')                                                        # click profile icon
        page.click('(//div[@class="toolbar_accounts-user_name"])[2]')

        if page.locator('//*[text()="Скрыть"]').count() > 0: page.click('//*[text()="Скрыть"]')              # close banner
        if page.locator('//*[text()="Войти"]').count() > 0:
            page.locator('//*[text()="Войти"]').nth(1).click()
            page.click('id("hook_Block_AuthLoginAutoOpen")//*[text()="Nick Ivanov"]]')

        page, context, browser = page_goto(page, 'https://ok.ru/', signals, context, browser, p)
        link_profile = page.locator('//a[@data-l="t,userPage"]').get_attribute('href')
        if link_profile_cur != link_profile:
            if "turistor1" in link_profile: id_account = 'turistor1'
            if "turistor2" in link_profile: id_account = 'turistor2'
        else: raise Exception
        signals.log_signal.emit(f'\n\n\n<<<<<<<<<<<<<<<<<<<<<<<<<<<< АВТОРИЗАЦИЯ ОК: {id_account} >>>>>>>>>>>>>>>>>>>>>>>>>>\n')
    except Exception as e:
        signals.log_signal.emit(f'\n\n!КРИТИЧЕСКАЯ ОШИБКА!: НЕ УДАЛАСЬ СМЕНА АККА В ОК // {e}\n\n')
        os.system('powershell -c (New-Object Media.SoundPlayer "end.wav").PlaySync();')
        os.system('powershell -c (New-Object Media.SoundPlayer "pause_reauth_ok.wav").PlaySync();')
        page.pause()

#-----------------------------------------------------------------------------------------------------------------------
def liking_ok(page, signals, context, browser, p):
    stories = 0; posts = 0
    try:
        signals.log_signal.emit('\n~~~~~~~~~~~~~~~~~~~~~~ ЛАЙКИНГ [OK] ~~~~~~~~~~~~~~~~~~~~~~\n')
        # 40=foto20vek, 68=постой-я с тобой, 00=посоветуй,
        group_for_like_list = ['https://ok.ru/testomatica', 'https://ok.ru/clipomatica', 'https://ok.ru/nightfeel4u',
                               'https://ok.ru/group/70000033320968', 'https://ok.ru/group/70000033170440', 'https://ok.ru/group/70000033320200',
                               'https://ok.ru/foto19vek', 'https://ok.ru/normolive', 'https://ok.ru/turistor',
                               'https://ok.ru/turistor1', 'https://ok.ru/turistor2']
        # cycle by groups
        for group in group_for_like_list:
            repost = 0
            page, context, browser = page_goto(page, group, signals, context, browser, p)
            page.evaluate("window.scrollBy(0, 3000)"); sleep(2)                                            # scroll page for load html
            if page.locator('//span[text()="Скрыть"]').count() > 0: page.click('//span[text()="Скрыть"]')  # close banner
            # cycle by posts
            for post_number in range(5):
                el = page.locator('//div[@class="feed-w"]').nth(post_number)  # post in series
                el_html = el.inner_html()                                     # take html post

                if ((group != 'https://ok.ru/turistor1' and group != 'https://ok.ru/turistor2')
                        and 'class="widget  __no-count __redesign2023"' in el_html and repost == 0):     # if not like post and not repost
                    page.hover('//*[@class="widget_tx" and text()="Класс"][1]')
                    page.locator('//span[@title="Класс! (Приватная эмоция)"]').click(force=True)         # click private like
                    page.locator(f'(//button[@aria-label="Поделиться"])[{post_number+1}]').click(delay=2000) # podelitsa
                    page.click('//*[text()="Поделиться сейчас"]')
                    repost = 1
                elif 'class="widget  __no-count __redesign2023"' in el_html:                             # if not like post
                    page.hover('//*[@class="widget_tx" and text()="Класс"][1]')
                    page.locator('//span[@title="Класс! (Приватная эмоция)"]').click(force=True)                   # click like and send in my chat
                    page.locator(f'(//button[@aria-label="Поделиться"])[{post_number+1}]').click(delay=2000)# podelitsa
                    if page.locator('//*[text()="Добавить в моменты"]').is_visible(timeout=2000):
                        page.click('//*[text()="Добавить в моменты"]'); sleep(3)
        signals.log_signal.emit('Мои группы ОК: полайкано и отрепощено')
        # likes posts and stories
        try:
            page, context, browser = page_goto(page, 'https://ok.ru', signals, context, browser, p)
            page.click('(//div[@data-tsid="avatar-test-id"])[3]')                                           #click on story
            for stories in range(31):                                                                       #30 likes stories
                sleep(1)
                page.locator('#dailyphoto-layer .dp_00599:first-of-type').hover(force=True)
                page.locator('#dailyphoto-layer .dp_00599:first-of-type').click()                           #click like {shadow dom}
                page.keyboard.press('ArrowRight')                                                           #click next story
            page.keyboard.press('Escape')                                                                   #close story
        except Exception: pass

        if page.locator('//span[text()="Скрыть"]').count() > 0: page.click('//span[text()="Скрыть"]')   # close banner
#        for i in range(30): page.mouse.wheel(0, 99999); sleep(1)
        for posts in range (251):                                                                       #250 likes posts
            page.mouse.wheel(0, 1400); page.hover('(//*[@class="widget_tx" and text()="Класс"])[1]', force=True)
            page.keyboard.press('ArrowUp'); page.keyboard.press('ArrowUp'); page.hover('(//*[@class="widget_tx" and text()="Класс"])[1]', force=True)
            page.locator('//span[@title="Класс! (Приватная эмоция)"]').click()                          # click private like

        signals.log_signal.emit(f'Контент: Отлайкано {stories} историй и {posts} постов\n')
    except Exception as e: signals.log_signal.emit(f'\n!!!!!ЧТО-ТО СЛОМАЛОСЬ В ЛАЙКАХ / РЕПОСТАХ [ОК]!!!!! // Контент: Отлайкано {stories} историй и {posts} постов / ошибка: {e}\n')

#-----------------------------------------------------------------------------------------------------------------------
def outgoing_requests_ok(page, signals, context, browser, p):
    try:
        out_requests = 0
        signals.log_signal.emit(f'\n~~~~~~~~~~~~~~~~~~~~~~ ПОСЫЛАЕМ ИСХОДЯЩИЕ ЗАЯВКИ В ДРУЗЬЯ [ОК] ~~~~~~~~~~~~~~~~~~~~~~\n')
        page, context, browser = page_goto(page, 'https://ok.ru/dk?st.cmd=searchResult&st.mode=Users&st.grmode=Groups', signals, context, browser, p)
        for i in range(50): page.mouse.wheel(0, 99999); sleep(3)
        cnt = page.locator('//div[@data-logger="SimpleLogger"][.//span[contains(@class,"user-online")] and .//*[text()="Добавить в друзья"]]').count()
        signals.log_signal.emit(f'Pекомендаций для заявок в друзья: [{cnt}]\n')

        for i in range (cnt):
            while out_requests < 50:
                num_cur_user_card = randint(3, cnt-50)
                combo_str_lower = page.locator('//div[@data-logger="SimpleLogger"][.//span[contains(@class,"user-online")] and .//*[text()="Добавить в друзья"]]').nth(num_cur_user_card).inner_text().lower()
                matching_stop_word = next((word for word in stop_words if word in combo_str_lower), None)
                if matching_stop_word is not None: continue
                try: page.locator('//div[@data-logger="SimpleLogger"][.//span[contains(@class,"user-online")]]//*[text()="Добавить в друзья"]').nth(num_cur_user_card).click(); sleep(0.5)
                except Exception: continue
                if page.get_by_text("Подружиться не удалось").is_visible():
                    signals.log_signal.emit('--------> Много заявок / return'); return
                else:
                    out_requests += 1
                    signals.log_signal.emit(f'Отправлена заявка [{out_requests}] в друзья // Юзер: {combo_str_lower}')
    except Exception as e: signals.log_signal.emit(f'\n!!!!!ЧТО-ТО СЛОМАЛОСЬ ПРИ ОТПРАВКЕ ИСХОДЯШЕК [ОК]!!!!! //  ошибка: {e}\n')

#-----------------------------------------------------------------------------------------------------------------------
def incoming_requests_ok(page, signals, context, browser, p):
    try:
        signals.log_signal.emit(f'\n~~~~~~~~~~~~~~~~~~~~~~ ПРОВЕРКА ВХОДЯЩИХ ЗАЯВОК В ДРУЗЬЯ [ОК] ~~~~~~~~~~~~~~~~~~~~~~\n')
        if id_account == 'turistor1': page, context, browser = page_goto(page, 'https://ok.ru/turistor1/friendRequests', signals, context, browser, p)
        if id_account == 'turistor2': page, context, browser = page_goto(page, 'https://ok.ru/turistor2/friendRequests', signals, context, browser, p)

        while page.get_by_text('Входящие заявки в друзья').is_visible(timeout=2000):
            page.locator('(//a[@data-l="t,e2" and @class="o"])[1]').click()
            name = page.locator('//h1').inner_text()
            descr = page.locator('//div[@id="hook_Block_AboutUserRB"]').inner_text()
            combo_str_lower = ' '.join([name, descr]).lower()
            matching_stop_word = next((word for word in stop_words if word in combo_str_lower), None)
            page.get_by_text('Ответить на заявку').click()
            if matching_stop_word:
                page.get_by_text('Игнорировать').click()
                signals.log_signal.emit(f'Юзер ОТКЛОНЁН // Инфо: {combo_str_lower}\n------------------------------')
            else:
                page.get_by_text('Принять заявку').click()
                signals.log_signal.emit(f'Юзер ПРИНЯТ в друзья // Инфо: {combo_str_lower}\n------------------------------')
            if id_account == 'turistor1': page, context, browser = page_goto(page, 'https://ok.ru/turistor1/friendRequests', signals, context, browser, p)
            if id_account == 'turistor2': page, context, browser = page_goto(page, 'https://ok.ru/turistor2/friendRequests', signals, context, browser, p)
        signals.log_signal.emit('Заявок нет\n')
    except Exception as e: signals.log_signal.emit(f'\n!!!!!ЧТО-ТО СЛОМАЛОСЬ ПРИ ПРОВЕРКЕ ВХОДЯЩИХ ЗАЯВОК [ОК]!!!!! //  ошибка: {e}\n')

#-----------------------------------------------------------------------------------------------------------------------
def dell_out_requests_ok(page, signals, context, browser, p):
    out_requests = 0
    try:
        signals.log_signal.emit(f'\n~~~~~~~~~~~~~~~~~~~~~~ УДАЛЯЕМ 0ХYЕВШИХ [ОК] ~~~~~~~~~~~~~~~~~~~~~~\n')
        if id_account == 'turistor1': page, context, browser = page_goto(page, 'https://ok.ru/turistor1/subscriptions', signals, context, browser, p)
        if id_account == 'turistor2': page, context, browser = page_goto(page, 'https://ok.ru/turistor2/subscriptions', signals, context, browser, p)

        while page.locator('(//a[@class="n-t bold"])[1]').is_visible(timeout=2000):
            page.hover('(//a[@class="n-t bold"])[1]')
            page.click('//div[@id="hook_Block_ShortcutMenu"]//text()[.="Заблокировать"]/..', delay=1500)
            page.click('//*[@id="hook_FormButton_button_add_confirm"]')
            out_requests += 1
        signals.log_signal.emit(f'Удалено {out_requests} подписок\n')
    except Exception as e: signals.log_signal.emit(f'\n!!!!!ЧТО-ТО СЛОМАЛОСЬ В УДАЛЯШКЕ ПОДПИСОК [ОК]!!!!! Удалено: {out_requests} подписок // ошибка: {e}\n')
#-----------------------------------------------------------------------------------------------------------------------
def send_invite_in_my_groups_ok(page, signals, context, browser, p):
    try:
        title_my_group = ''
        signals.log_signal.emit(f'\n~~~~~~~~~~~~~~~~~~~~~~ ИДЁТ ОТПРАВКА ИНВАЙТА ДРУЗЬЯМ [ОК] // ПРИГЛАШАЕТ: {id_account} ~~~~~~~~~~~~~~~~~~~~~~\n')
        group_list = ['https://ok.ru/testomatica','https://ok.ru/clipomatica','https://ok.ru/nightfeel4u','https://ok.ru/group/70000033320968','https://ok.ru/group/70000033170440','https://ok.ru/group/70000033320200','https://ok.ru/foto19vek', 'https://ok.ru/normolive', 'https://ok.ru/turistor']
        day_of_year = datetime.now().timetuple().tm_yday
        my_group = group_list[(day_of_year - 1) % len(group_list)]              # -1, чтобы сделать индексацию с 0

        if my_group == 'https://ok.ru/testomatica': title_my_group = 'ТЕСТЫ И ГОЛОВОЛОМКИ'
        if my_group == 'https://ok.ru/clipomatica': title_my_group = 'КЛИПЫ И ТОЧКА'
        if my_group == 'https://ok.ru/nightfeel4u': title_my_group = 'ЧУВСТВО НОЧИ'
        if my_group == 'https://ok.ru/foto19vek': title_my_group = 'ФОТО 19 ВЕК'
        if my_group == 'https://ok.ru/group/70000033320200': title_my_group = 'ПОСОВЕТУЙ МНЕ'
        if my_group == 'https://ok.ru/turistor': title_my_group = 'ФОТОФАКТЫ'
        if my_group == 'https://ok.ru/normolive': title_my_group = 'СВОЛОЧЬ ЛИ Я?'
        if my_group == 'https://ok.ru/group/70000033170440': title_my_group = 'ФОТО 20 ВЕК'
        if my_group == 'https://ok.ru/group/70000033320968': title_my_group = 'ПОСТОЙ! МОЖНО Я С ТОБОЙ?'

        page, context, browser = page_goto(page, my_group, signals, context, browser, p)
        page.click('//button[@aria-label="Ещё"]')
        page.click('//*[text()="Пригласить друзей"]')
        page.click('//span[@class="irc_l" and contains(text(),"Выбрать")]')
        page.click('//input[@id="hook_FormButton_button_invite"]')

        if page.locator('//div[ contains(text(),"слишком часто")]').is_visible(timeout=2000):
            page.click('//input[@id="buttonId_button_close"]')
            signals.log_signal.emit(f'Приглашение друзьям в: {title_my_group} НЕ ОТПРАВЛЕНО ("слишком часто")\n'); return

        signals.log_signal.emit(f'Приглашение друзьям в: {title_my_group} отправлено\n')
    except Exception as e: signals.log_signal.emit(f'\n!!!!!ЧТО-ТО СЛОМАЛОСЬ В ОТПРАВКЕ ИНВАЙТА [ОК]!!!!! // ошибка: {e}\n')

#====================================================M=I=N=E============================================================
class WorkerSignals(QObject):
    log_signal = Signal(str)

class WorkerThread(QThread):
    def __init__(self, signals):
        super().__init__()
        self.signals = signals

    def run(self):
        run_playwright(self.signals)

# Функция для запуска потока
def start_playwright_thread():
    global worker_thread
    signals = WorkerSignals()
    signals.log_signal.connect(update_log)
    worker_thread = WorkerThread(signals)
    worker_thread.start()

def run_def_ok(page, signals, context, browser, p):
    if cbox_function_ok[4].isChecked(): send_invite_in_my_groups_ok(page, signals, context, browser, p)
    if cbox_function_ok[0].isChecked(): liking_ok(page, signals, context, browser, p)
    if cbox_function_ok[1].isChecked(): incoming_requests_ok(page, signals, context, browser, p)
    if cbox_function_ok[2].isChecked(): dell_out_requests_ok(page, signals, context, browser, p)
    if cbox_function_ok[3].isChecked(): outgoing_requests_ok(page, signals, context, browser, p)

#=======================================================================================================================
# start browser / main fun vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
#=======================================================================================================================
def run_playwright(signals):
    if  not cbox_profiles_ok[0].isChecked():
        signals.log_signal.emit('\n~~~~~~~~~~~~~~~~~~~~~~ [ ВЫБЕРИ АККАУНТЫ ДЛЯ РАБОТЫ ] ~~~~~~~~~~~~~~~~~~~~~~\n'); return

    btn.setEnabled(False)
    for cbox in cbox_function_ok + cbox_profiles_ok:
        cbox.setEnabled(False)                                                                   # Блокируем кнопку и все чекбоксы

    active_cbox_ok = [cbox.text() for cbox in cbox_function_ok if cbox.isChecked()]
    if not active_cbox_ok: active_cbox_ok.append('Нет активных функций')

    signals.log_signal.emit(f'{datetime.now().strftime("%d-%m-%Y")}: [[[[[[[[[[[[[[[ СТАРТ OKSECRETARY ]]]]]]]]]]]]]]]'
                            f'\n\nАКТИВНЫЕ ФУНКЦИИ ДЛЯ ОК:\n\n{'\n '.join(item for item in active_cbox_ok)}\n')
    os.environ['PLAYWRIGHT_BROWSERS_PATH'] = '0'
    p = sync_playwright().start()
    page, context, browser = browser_start(p)

#    page.goto("https://intoli.com/blog/not-possible-to-block-chrome-headless/chrome-headless-test.html")
#    if page.locator('text="missing (passed)"').is_visible(): signals.log_signal.emit('WebDriver не обнаружен')
#    else: signals.log_signal.emit('\n!ВНИМАНИЕ! WebDriver ОБНАРУЖЕН')
#    page.goto("https://www.browserscan.net/"); sleep(15)
#    if page.locator('//a[@href="/bot-detection"]/preceding-sibling::span[1]').text_content() == 'Yes': signals.log_signal.emit('!ВНИМАНИЕ! Bot Detection НЕ ПРОЙДЕН')
#    else: signals.log_signal.emit('Bot Detection пройден')

    if cbox_profiles_ok[0].isChecked() or cbox_profiles_ok[1].isChecked():
        browser.close()
        os.system("taskkill /IM chrome.exe /F")
        page, context, browser = browser_start(p)
        start_ok(page, signals, context, browser, p)
    if cbox_profiles_ok[0].isChecked() and not cbox_profiles_ok[1].isChecked(): run_def_ok(page, signals, context, browser, p)
    if not cbox_profiles_ok[0].isChecked() and cbox_profiles_ok[1].isChecked():
        browser.close()
        os.system("taskkill /IM chrome.exe /F")
        page, context, browser = browser_start(p)
        change_account_ok(page, signals, context, browser, p); run_def_ok(page, signals, context, browser, p)
    if cbox_profiles_ok[0].isChecked() and cbox_profiles_ok[1].isChecked():
       for i in range(2):
           if i == 1:
               browser.close()
               os.system("taskkill /IM chrome.exe /F")
               page, context, browser = browser_start(p)
               change_account_ok(page, signals, context, browser, p)
           run_def_ok(page, signals, context, browser, p)

    signals.log_signal.emit('\n\n~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ [ работа завершена ] ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n\n')
    os.system('powershell -c (New-Object Media.SoundPlayer "end.wav").PlaySync();')  # sound
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
    line_edit.setPlaceholderText("адрес группы для инвайта: http://...")
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
