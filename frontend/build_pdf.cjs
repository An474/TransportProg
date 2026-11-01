const puppeteer = require('puppeteer-core');
const fs = require('fs');
const path = require('path');

const EDGE_PATH = "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe";
const ASSETS_DIR = path.join(__dirname, 'manual_assets');
const OUTPUT_PDF = path.join(__dirname, '..', 'РУКОВОДСТВО_ПОЛЬЗОВАТЕЛЯ.pdf');

function getBase64Image(filename) {
  const filePath = path.join(ASSETS_DIR, filename);
  if (!fs.existsSync(filePath)) return '';
  const data = fs.readFileSync(filePath);
  return `data:image/png;base64,${data.toString('base64')}`;
}

const images = {
  login: getBase64Image('01_login.png'),
  dashboard: getBase64Image('02_dashboard.png'),
  vehicles: getBase64Image('03_vehicles.png'),
  assignments: getBase64Image('04_assignments.png'),
  waybills: getBase64Image('05_waybills.png'),
  fines: getBase64Image('06_fines.png'),
  maintenance: getBase64Image('07_maintenance.png'),
  fuel: getBase64Image('08_fuel.png'),
  backups: getBase64Image('09_backups.png')
};

const htmlContent = `
<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<title>Руководство пользователя: Информационная система транспортного отдела</title>
<style>
  @page {
    size: A4 portrait;
    margin: 12mm 14mm 14mm 14mm;
    @bottom-right {
      content: counter(page);
    }
  }

  body {
    font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, Helvetica, Arial, sans-serif;
    color: #1f2937;
    line-height: 1.45;
    margin: 0;
    padding: 0;
    background: #ffffff;
    font-size: 11pt;
  }

  .page {
    page-break-after: always;
    position: relative;
    padding-bottom: 10px;
  }

  .page:last-child {
    page-break-after: avoid;
  }

  /* Cover Page */
  .cover {
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    min-height: 250mm;
    text-align: center;
    background: linear-gradient(145deg, #0f274a 0%, #1a4275 100%);
    color: #ffffff;
    border-radius: 12px;
    padding: 40px 30px;
    box-sizing: border-box;
  }

  .cover-icon {
    font-size: 64pt;
    margin-bottom: 20px;
  }

  .cover-title {
    font-size: 26pt;
    font-weight: 700;
    margin: 0 0 12px 0;
    color: #ffffff;
    letter-spacing: -0.5px;
    line-height: 1.2;
  }

  .cover-subtitle {
    font-size: 15pt;
    color: #93c5fd;
    margin: 0 0 35px 0;
    font-weight: 500;
  }

  .cover-badge {
    display: inline-block;
    background: rgba(255, 255, 255, 0.15);
    border: 1px solid rgba(255, 255, 255, 0.3);
    padding: 8px 24px;
    border-radius: 30px;
    font-size: 12pt;
    color: #ffffff;
    margin-bottom: 40px;
  }

  .cover-greeting {
    background: rgba(255, 255, 255, 0.95);
    color: #1f2937;
    border-radius: 10px;
    padding: 24px 30px;
    max-width: 580px;
    text-align: left;
    font-size: 11pt;
    line-height: 1.6;
    box-shadow: 0 10px 25px rgba(0,0,0,0.25);
  }

  .cover-greeting h4 {
    margin: 0 0 8px 0;
    color: #1e40af;
    font-size: 13pt;
  }

  /* Page Headers */
  .header {
    border-bottom: 2px solid #2563eb;
    padding-bottom: 8px;
    margin-bottom: 14px;
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
  }

  .header h2 {
    font-size: 16pt;
    color: #1e3a8a;
    margin: 0;
    font-weight: 700;
  }

  .header .section-tag {
    font-size: 9pt;
    color: #6b7280;
    text-transform: uppercase;
    font-weight: 600;
    letter-spacing: 0.5px;
  }

  .intro-text {
    font-size: 10pt;
    color: #4b5563;
    margin: 0 0 12px 0;
    line-height: 1.4;
  }

  /* Screenshot Container with Pins */
  .shot-wrap {
    position: relative;
    border: 1px solid #d1d5db;
    border-radius: 8px;
    overflow: hidden;
    box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    margin-bottom: 12px;
    background: #f9fafb;
  }

  .shot-img {
    width: 100%;
    display: block;
  }

  /* Callout Badges */
  .pin {
    position: absolute;
    width: 26px;
    height: 26px;
    background: #ef4444;
    color: #ffffff;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 800;
    font-size: 11pt;
    box-shadow: 0 0 0 3px #ffffff, 0 3px 8px rgba(0,0,0,0.4);
    z-index: 10;
    animation: pulse 2s infinite;
  }

  .pin-blue {
    background: #2563eb;
  }

  .pin-green {
    background: #10b981;
  }

  .pin-purple {
    background: #8b5cf6;
  }

  /* Explanation Cards */
  .notes-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px;
    margin-top: 10px;
  }

  .note-card {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-left: 4px solid #2563eb;
    border-radius: 6px;
    padding: 8px 12px;
    font-size: 9.5pt;
  }

  .note-card .title {
    font-weight: 700;
    color: #1e3a8a;
    margin-bottom: 3px;
    display: flex;
    align-items: center;
    gap: 6px;
  }

  .badge-num {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 18px;
    height: 18px;
    background: #ef4444;
    color: #ffffff;
    border-radius: 50%;
    font-size: 9pt;
    font-weight: 800;
  }

  .scenario-box {
    background: #eff6ff;
    border: 1px dashed #3b82f6;
    border-radius: 6px;
    padding: 8px 12px;
    margin-top: 8px;
    font-size: 9pt;
    color: #1e40af;
  }

  .scenario-box strong {
    color: #1e3a8a;
  }

  .footer-tip {
    font-size: 8.5pt;
    color: #64748b;
    border-top: 1px solid #e2e8f0;
    padding-top: 6px;
    margin-top: 8px;
    text-align: right;
  }

  .table-clean {
    width: 100%;
    border-collapse: collapse;
    margin: 10px 0;
    font-size: 9.5pt;
  }

  .table-clean th {
    background: #1e3a8a;
    color: white;
    padding: 6px 10px;
    text-align: left;
  }

  .table-clean td {
    padding: 6px 10px;
    border-bottom: 1px solid #e2e8f0;
  }
</style>
</head>
<body>

<!-- ============================================================== -->
<!-- 1. COVER PAGE -->
<!-- ============================================================== -->
<div class="page">
  <div class="cover">
    <div class="cover-icon">🚗 📋 ✨</div>
    <h1 class="cover-title">Информационная система<br>транспортного отдела</h1>
    <div class="cover-subtitle">Наглядное иллюстрированное руководство пользователя</div>
    <div class="cover-badge">Версия 1.0 • С наглядными скриншотами и пометками</div>

    <div class="cover-greeting">
      <h4>Дорогая мама!</h4>
      <p style="margin: 0 0 8px 0;">
        Эта памятка сделана специально для вас, чтобы работать с машинами и документами было легко и спокойно. Больше не нужно путаться в старых Excel-таблицах и вручную вспоминать, кто на какой машине ездил.
      </p>
      <p style="margin: 0;">
        На каждой странице вы увидите <b>реальную картинку экрана</b> с красными кружочками-номерами (①, ②, ③). Под картинкой сразу написано простое объяснение каждого шага.
      </p>
    </div>
  </div>
</div>

<!-- ============================================================== -->
<!-- 2. LOGIN PAGE -->
<!-- ============================================================== -->
<div class="page">
  <div class="header">
    <h2>1. Запуск программы и вход в систему</h2>
    <span class="section-tag">Начало работы</span>
  </div>
  <p class="intro-text">
    Утром дважды нажмите мышкой на файл <b>Запустить_Транспорт.bat</b>. Черное окно запуска сверните. Через пару секунд откроется окно входа.
  </p>

  <div class="shot-wrap">
    <img src="${images.login}" class="shot-img" alt="Экран входа">
    <!-- Pins on Login Screen -->
    <div class="pin" style="top: 48%; left: 44%;">①</div>
    <div class="pin" style="top: 57%; left: 44%;">②</div>
    <div class="pin" style="top: 67%; left: 50%;">③</div>
  </div>

  <div class="notes-grid">
    <div class="note-card">
      <div class="title"><span class="badge-num">①</span> Поле «Имя пользователя (Логин)»</div>
      Введите ваш логин: <b>dispatcher</b> (на английском языке).
    </div>
    <div class="note-card">
      <div class="title"><span class="badge-num">②</span> Поле «Пароль»</div>
      Введите пароль: <b>disp123</b> (символы будут скрыты точками).
    </div>
    <div class="note-card" style="grid-column: span 2;">
      <div class="title"><span class="badge-num">③</span> Синяя кнопка «Войти в систему»</div>
      Нажмите её мышкой (или нажмите клавишу Enter на клавиатуре). Вы сразу попадете на главный экран.
    </div>
  </div>

  <div class="scenario-box">
    💡 <b>Подсказка по учетным записям:</b> Для работы диспетчера входите под <code>dispatcher / disp123</code>. Если нужно показать директору отчеты без права случайного изменения — используйте вход <code>viewer / view123</code>.
  </div>
  <div class="footer-tip">Страница 1 • Начало работы</div>
</div>

<!-- ============================================================== -->
<!-- 3. DASHBOARD PAGE -->
<!-- ============================================================== -->
<div class="page">
  <div class="header">
    <h2>2. Дашборд (Главный экран)</h2>
    <span class="section-tag">Сводка и внимание</span>
  </div>
  <p class="intro-text">
    Здесь каждое утро программа сама собирает всю главную сводку: сколько машин на линии, где заканчивается страховка и какие штрафы не оплачены.
  </p>

  <div class="shot-wrap">
    <img src="${images.dashboard}" class="shot-img" alt="Дашборд">
    <div class="pin" style="top: 14%; left: 32%;">①</div>
    <div class="pin" style="top: 36%; left: 40%;">②</div>
    <div class="pin" style="top: 72%; left: 40%;">③</div>
    <div class="pin" style="top: 40%; left: 4%;">④</div>
  </div>

  <div class="notes-grid">
    <div class="note-card">
      <div class="title"><span class="badge-num">①</span> Карточки ключевых показателей</div>
      Сразу видно: сколько всего машин в компании (217+), сколько сейчас работают на линии, сколько стоят на СТО в ремонте и сколько в резерве.
    </div>
    <div class="note-card">
      <div class="title"><span class="badge-num">②</span> Блок внимания: Срочный техосмотр и страховка</div>
      <b>Самое полезное место!</b> Программа сама находит машины, у которых осталось меньше 30 дней страховки или техосмотра, чтобы вы успели заранее записаться.
    </div>
    <div class="note-card">
      <div class="title"><span class="badge-num">③</span> Реестр свежих неоплаченных штрафов</div>
      Показывает последние поступившие штрафы, по которым водители еще не предоставили квитанции об оплате.
    </div>
    <div class="note-card">
      <div class="title"><span class="badge-num">④</span> Главное меню навигации</div>
      Все разделы системы всегда под рукой слева: Автопарк, Водители, Пересадки, Путевые, Штрафы, ТО, ГСМ и Отчеты.
    </div>
  </div>

  <div class="footer-tip">Страница 2 • Главный экран</div>
</div>

<!-- ============================================================== -->
<!-- 4. VEHICLES PAGE -->
<!-- ============================================================== -->
<div class="page">
  <div class="header">
    <h2>3. Автопарк и цветной «Светофор» сроков</h2>
    <span class="section-tag">Реестр автомобилей</span>
  </div>
  <p class="intro-text">
    Полный список всех 217+ автомобилей компании. Программа подсказывает цветом статус документов каждой машины.
  </p>

  <div class="shot-wrap">
    <img src="${images.vehicles}" class="shot-img" alt="Автопарк">
    <div class="pin" style="top: 13%; left: 24%;">①</div>
    <div class="pin" style="top: 13%; left: 88%;">②</div>
    <div class="pin" style="top: 13%; left: 74%;">③</div>
    <div class="pin" style="top: 45%; left: 63%;">④</div>
    <div class="pin" style="top: 45%; left: 16%;">⑤</div>
  </div>

  <div class="notes-grid">
    <div class="note-card">
      <div class="title"><span class="badge-num">①</span> Быстрый поиск машины</div>
      Введите любые цифры или буквы номера (например, <code>014</code> или <code>Cobalt</code>) — список отфильтруется мгновенно!
    </div>
    <div class="note-card">
      <div class="title"><span class="badge-num">②</span> Кнопка «+ Добавить автомобиль»</div>
      Если компания приобрела новую машину, нажмите сюда и введите госномер, марку и дату страховки.
    </div>
    <div class="note-card">
      <div class="title"><span class="badge-num">③</span> Кнопка «Выгрузить в Excel»</div>
      В 1 клик скачивает на компьютер красивую готовую таблицу со всеми машинами, водителями и цветными статусами.
    </div>
    <div class="note-card">
      <div class="title"><span class="badge-num">④</span> Цветной светофор сроков</div>
      🟢 <b>Зеленый:</b> срок в порядке (>30 дней)<br>
      🟡 <b>Желтый:</b> осталось меньше месяца (пора продлевать)<br>
      🔴 <b>Красный:</b> просрочено! Выезд запрещен.
    </div>
  </div>

  <div class="scenario-box">
    🔍 <b>Как открыть карточку машины:</b> Нажмите прямо на синий госномер <span class="badge-num">⑤</span> — откроется полное досье авто: кто сейчас за рулем, все прошлые штрафы, ремонты и путевые листы.
  </div>
  <div class="footer-tip">Страница 3 • Автопарк</div>
</div>

<!-- ============================================================== -->
<!-- 5. ASSIGNMENTS PAGE -->
<!-- ============================================================== -->
<div class="page">
  <div class="header">
    <h2>4. Пересадки и замены (Решение путаницы)</h2>
    <span class="section-tag">Журнал передачи авто</span>
  </div>
  <p class="intro-text">
    <b>Главное спасение от путаницы!</b> Когда постоянный водитель болеет или уходит в отпуск, и машину передают другому — зафиксируйте это здесь за 10 секунд.
  </p>

  <div class="shot-wrap">
    <img src="${images.assignments}" class="shot-img" alt="Пересадки">
    <div class="pin" style="top: 13%; left: 88%;">①</div>
    <div class="pin" style="top: 40%; left: 32%;">②</div>
    <div class="pin" style="top: 40%; left: 70%;">③</div>
  </div>

  <div class="notes-grid">
    <div class="note-card" style="grid-column: span 2;">
      <div class="title"><span class="badge-num">①</span> Синяя кнопка «+ Новая пересадка / замена»</div>
      Нажмите её, выберите автомобиль из списка, укажите, кому временно передается машина, и выберите причину (<i>«Отпуск»</i>, <i>«Ремонт авто»</i>, <i>«Подмена»</i>).
    </div>
    <div class="note-card">
      <div class="title"><span class="badge-num">②</span> Закрепленный водитель и телефон</div>
      В таблице всегда видно, кто именно сейчас сидит за рулем этой машины и по какому номеру ему звонить.
    </div>
    <div class="note-card">
      <div class="title"><span class="badge-num">③</span> Причина и период передачи</div>
      Система точно фиксирует дату начала и окончания подмены.
    </div>
  </div>

  <div class="scenario-box">
    ⚡ <b>Почему это очень важно:</b> Когда с камер придет штраф, вам не нужно вспоминать, кто ездил на этой машине две недели назад. Программа сама сопоставит дату штрафа с этим журналом и найдет истинного нарушителя!
  </div>
  <div class="footer-tip">Страница 4 • Пересадки и замены</div>
</div>

<!-- ============================================================== -->
<!-- 6. WAYBILLS PAGE -->
<!-- ============================================================== -->
<div class="page">
  <div class="header">
    <h2>5. Путевые листы и еженедельный контроль</h2>
    <span class="section-tag">Учет пробега и возврата</span>
  </div>
  <p class="intro-text">
    Электронный учет всех маршрутных листов. Спидометры, расчет пробега и контроль возврата корешков по неделям.
  </p>

  <div class="shot-wrap">
    <img src="${images.waybills}" class="shot-img" alt="Путевые листы">
    <div class="pin" style="top: 13%; left: 88%;">①</div>
    <div class="pin" style="top: 40%; left: 52%;">②</div>
    <div class="pin" style="top: 40%; left: 72%;">③</div>
    <div class="pin" style="top: 40%; left: 86%;">④</div>
  </div>

  <div class="notes-grid">
    <div class="note-card">
      <div class="title"><span class="badge-num">①</span> Кнопка «+ Выдать путевой лист»</div>
      Выберите авто — имя водителя подставится само! Введите спидометр выезда и месяца.
    </div>
    <div class="note-card">
      <div class="title"><span class="badge-num">②</span> Авторасчет километража</div>
      Когда водитель сдает лист со спидометром возврата, программа сама вычитает начальный пробег и показывает точный километраж.
    </div>
    <div class="note-card">
      <div class="title"><span class="badge-num">③</span> Еженедельный контроль возврата (1, 2, 3, 4 недели)</div>
      Когда водитель приносит корешок за неделю, просто ставьте галочку в строке. Сразу видно, кто сдал документы вовремя, а кто задерживает.
    </div>
    <div class="note-card">
      <div class="title"><span class="badge-num">④</span> Статус листа («Сдан» / «Утерян»)</div>
      Если водитель потерял путевой лист — отметьте статус «Утерян». Программа зафиксирует это и позволит выдать дубликат.
    </div>
  </div>

  <div class="footer-tip">Страница 5 • Путевые листы</div>
</div>

<!-- ============================================================== -->
<!-- 7. FINES PAGE -->
<!-- ============================================================== -->
<div class="page">
  <div class="header">
    <h2>6. Штрафы ПДД и Служебные записки в СБ</h2>
    <span class="section-tag">Штрафы и автоопределение</span>
  </div>
  <p class="intro-text">
    Учет всех штрафов из бухгалтерии. Автоматическое определение водителя и генерация служебок для Службы безопасности.
  </p>

  <div class="shot-wrap">
    <img src="${images.fines}" class="shot-img" alt="Штрафы">
    <div class="pin" style="top: 13%; left: 88%;">①</div>
    <div class="pin" style="top: 13%; left: 66%;">②</div>
    <div class="pin" style="top: 40%; left: 34%;">③</div>
    <div class="pin" style="top: 40%; left: 80%;">④</div>
  </div>

  <div class="notes-grid">
    <div class="note-card">
      <div class="title"><span class="badge-num">①</span> Кнопка «+ Внести штраф»</div>
      Введите номер авто, дату нарушения и сумму штрафа. <b>Поле «Водитель» можно не заполнять!</b> Программа сама вычислит водителя по дате.
    </div>
    <div class="note-card">
      <div class="title"><span class="badge-num">②</span> Кнопка «Служебная записка в СБ (.xlsx)»</div>
      <b>Одной кнопкой</b> скачивает готовый файл Excel со списком водителей, отказавшихся платить штрафы, для Службы безопасности.
    </div>
    <div class="note-card">
      <div class="title"><span class="badge-num">③</span> Ответственный водитель</div>
      Программа автоматически показывает ФИО сотрудника, который был за рулем в момент фиксации камерой.
    </div>
    <div class="note-card">
      <div class="title"><span class="badge-num">④</span> Статус оплаты штрафа</div>
      Когда водитель оплатит через Kaspi, измените статус на «Оплачен» и укажите дату — штраф снимется с контроля.
    </div>
  </div>

  <div class="scenario-box">
    👮 <b>Что делать с должниками:</b> Если водитель спорит или не платит добровольно, нажмите значок карандаша и включите галочку <i>«В служебную записку»</i>. Он автоматически попадет в официальный документ в СБ <span class="badge-num">②</span>.
  </div>
  <div class="footer-tip">Страница 6 • Штрафы ПДД</div>
</div>

<!-- ============================================================== -->
<!-- 8. MAINTENANCE PAGE -->
<!-- ============================================================== -->
<div class="page">
  <div class="header">
    <h2>7. ТО, Ремонты и Эвакуация</h2>
    <span class="section-tag">Техническое обслуживание</span>
  </div>
  <p class="intro-text">
    История всех ремонтов, замен масла, геометрии и эвакуаций на базу Емцова 11.
  </p>

  <div class="shot-wrap">
    <img src="${images.maintenance}" class="shot-img" alt="ТО и Ремонты">
    <div class="pin" style="top: 13%; left: 88%;">①</div>
    <div class="pin" style="top: 40%; left: 24%;">②</div>
    <div class="pin" style="top: 40%; left: 68%;">③</div>
  </div>

  <div class="notes-grid">
    <div class="note-card" style="grid-column: span 2;">
      <div class="title"><span class="badge-num">①</span> Кнопка «+ Заявка на ТО / Ремонт»</div>
      Нажмите сюда, чтобы зафиксировать направление машины на сервис (замена масла, фильтров, колодок, лобового стекла или геометрия колес).
    </div>
    <div class="note-card">
      <div class="title"><span class="badge-num">②</span> Вид работ и описание поломки</div>
      Четко фиксируется, что именно сломалось и на каком пробеге производился ремонт.
    </div>
    <div class="note-card">
      <div class="title"><span class="badge-num">③</span> Подрядчик и номер документа (СТО / Эвакуатор)</div>
      Учет эвакуаторов ИП Мухраев, номеров ЕРП и подрядчиков (СТО Хабаров и др.).
    </div>
  </div>

  <div class="scenario-box">
    🔧 <b>Автоматический статус машины:</b> Пока машина находится в ремонте, ее статус на дашборде горит желтым <i>«В ремонте»</i>, что исключает ошибочную выписку путевого листа на неисправное авто.
  </div>
  <div class="footer-tip">Страница 7 • ТО и Ремонты</div>
</div>

<!-- ============================================================== -->
<!-- 9. FUEL PAGE -->
<!-- ============================================================== -->
<div class="page">
  <div class="header">
    <h2>8. Учет ГСМ и Топливных карт</h2>
    <span class="section-tag">Расход бензина и дизеля</span>
  </div>
  <p class="intro-text">
    Контроль фактических заправок по топливным картам и автоматическое выявление перерасхода топлива.
  </p>

  <div class="shot-wrap">
    <img src="${images.fuel}" class="shot-img" alt="Учет ГСМ">
    <div class="pin" style="top: 13%; left: 88%;">①</div>
    <div class="pin" style="top: 40%; left: 52%;">②</div>
    <div class="pin" style="top: 40%; left: 66%;">③</div>
  </div>

  <div class="notes-grid">
    <div class="note-card" style="grid-column: span 2;">
      <div class="title"><span class="badge-num">①</span> Кнопка «+ Внести заправку ГСМ»</div>
      Выберите авто, введите номер топливной карты, фактически заправленные литры по чеку и пройденный километраж.
    </div>
    <div class="note-card">
      <div class="title"><span class="badge-num">②</span> Нормативный расчет по километражу</div>
      Программа сама берет норму расхода для этой модели (например, 10 л / 100 км) и считает, сколько литров должно было уйти по норме.
    </div>
    <div class="note-card">
      <div class="title"><span class="badge-num">③</span> Отклонение: Экономия или Перерасход</div>
      🟢 <b>Зеленый цвет</b> — норма соблюдена или экономия.<br>
      🔴 <b>Красный цвет</b> — перерасход бензина (сигнал для проверки водителя).
    </div>
  </div>

  <div class="footer-tip">Страница 8 • Учет ГСМ</div>
</div>

<!-- ============================================================== -->
<!-- 10. BACKUPS & UPDATE PAGE -->
<!-- ============================================================== -->
<div class="page">
  <div class="header">
    <h2>9. Резервные копии и Обновление в 1 клик</h2>
    <span class="section-tag">Безопасность и обновления</span>
  </div>
  <p class="intro-text">
    Полная гарантия сохранности данных: копии сохраняются на компьютере, отправляются сыну на Google Диск, а программа обновляется нажатием одной кнопки.
  </p>

  <div class="shot-wrap">
    <img src="${images.backups}" class="shot-img" alt="Резервные копии и обновления">
    <div class="pin" style="top: 13%; left: 88%;">①</div>
    <div class="pin" style="top: 24%; left: 80%;">②</div>
    <div class="pin" style="top: 48%; left: 50%;">③</div>
    <div class="pin" style="top: 78%; left: 35%;">④</div>
  </div>

  <div class="notes-grid">
    <div class="note-card">
      <div class="title"><span class="badge-num">①</span> Кнопка «Создать резервную копию сейчас»</div>
      Программа сама делает бэкапы каждую ночь в 00:00, но вы в любой момент можете нажать эту кнопку перед важными изменениями.
    </div>
    <div class="note-card">
      <div class="title"><span class="badge-num">②</span> Зеленая кнопка «Обновить всю программу»</div>
      <b>Когда сын выпустит обновление</b>, здесь загорится зеленая кнопка. Нажмите её — программа обновится сама за 3 секунды, не трогая базу данных!
    </div>
    <div class="note-card">
      <div class="title"><span class="badge-num">③</span> Автоматическая выгрузка на Google Диск</div>
      Каждый созданный бэкап улетает в облако на Google Диск сына. Даже если компьютер сломается — все данные в безопасности.
    </div>
    <div class="note-card">
      <div class="title"><span class="badge-num">④</span> Список локальных копий на компьютере</div>
      Таблица архивов со временем создания и размером, готовых к быстрому восстановлению.
    </div>
  </div>

  <div class="footer-tip">Страница 9 • Резервные копии и Обновление</div>
</div>

<!-- ============================================================== -->
<!-- 11. CHEATSHEET -->
<!-- ============================================================== -->
<div class="page">
  <div class="header">
    <h2>10. Краткая памятка на каждый день</h2>
    <span class="section-tag">Шпаргалка</span>
  </div>

  <table class="table-clean">
    <thead>
      <tr>
        <th style="width: 30%;">Ситуация</th>
        <th style="width: 70%;">Что нужно сделать в программе</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td><b>Утром пришла на работу</b></td>
        <td>Дважды нажмите на <code>Запустить_Транспорт.bat</code>. Откроется браузер. Введите <code>dispatcher / disp123</code>. Проверьте карточки на Дашборде.</td>
      </tr>
      <tr>
        <td><b>Водитель ушел в отпуск / заболел</b></td>
        <td>Откройте раздел <b>«Пересадки и замены»</b> → нажмите «+ Новая пересадка» → выберите авто и того, кто будет временно подменять.</td>
      </tr>
      <tr>
        <td><b>Пришел штраф с камеры Сергек</b></td>
        <td>Откройте <b>«Штрафы»</b> → «+ Внести штраф» → введите номер авто, дату и сумму. Поле водителя оставьте пустым — программа найдет его сама!</td>
      </tr>
      <tr>
        <td><b>Водитель отказывается платить штраф</b></td>
        <td>Поставьте в штрафе галочку «В служебную записку» и нажмите сверху синюю кнопку <b>«Служебная записка в СБ (.xlsx)»</b>. Файл готов!</td>
      </tr>
      <tr>
        <td><b>Нужно узнать, когда техосмотр / страховка</b></td>
        <td>Откройте <b>«Автопарк»</b>: посмотрите на кружочки. Желтый = пора звонить, Красный = машина не должна выезжать.</td>
      </tr>
      <tr>
        <td><b>Водитель потерял путевой лист</b></td>
        <td>Откройте <b>«Путевые листы»</b> → откройте лист → поставьте статус «Утерян» → выпишите дубликат с тем же номером.</td>
      </tr>
      <tr>
        <td><b>Сын сказал: «Я выпустил обновление»</b></td>
        <td>Откройте раздел <b>«Резервные копии»</b> → нажмите зеленую кнопку <b>«Обновить всю программу»</b>. Готово!</td>
      </tr>
      <tr>
        <td><b>Случайно закрыла вкладку в браузере</b></td>
        <td>Откройте браузер и напишите адрес: <code>http://localhost:8000</code>. Всё откроется ровно там, где вы остановились.</td>
      </tr>
      <tr>
        <td><b>Вечером ухожу домой</b></td>
        <td>Просто закройте вкладку в браузере и закройте черное окно. Все данные сохранены автоматически!</td>
      </tr>
    </tbody>
  </table>

  <div style="background: #f0fdf4; border: 1px solid #86efac; border-radius: 8px; padding: 14px 20px; margin-top: 20px; text-align: center;">
    <h3 style="color: #166534; margin: 0 0 6px 0;">❤️ Приятной и легкой работы!</h3>
    <p style="color: #15803d; margin: 0; font-size: 10.5pt;">
      Программа сделана так, чтобы беречь ваше время и нервы. Если возникнет любой вопрос — сын всегда поможет и подскажет!
    </p>
  </div>
  <div class="footer-tip">Страница 10 • Шпаргалка на каждый день</div>
</div>

</body>
</html>
`;

async function generatePdf() {
  console.log("Compiling visual illustrated PDF manual...");
  const browser = await puppeteer.launch({
    executablePath: EDGE_PATH,
    headless: "new",
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  const page = await browser.newPage();
  await page.setContent(htmlContent, { waitUntil: 'networkidle0' });

  console.log(`Printing to ${OUTPUT_PDF}...`);
  await page.pdf({
    path: OUTPUT_PDF,
    format: 'A4',
    printBackground: true,
    margin: {
      top: '10mm',
      bottom: '10mm',
      left: '12mm',
      right: '12mm'
    }
  });

  await browser.close();
  console.log("PDF GENERATION COMPLETED SUCCESSFULLY!");
}

generatePdf().catch(err => {
  console.error("PDF generation failed:", err);
  process.exit(1);
});
