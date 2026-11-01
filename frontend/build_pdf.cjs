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
    font-size: 10.5pt;
  }

  .page {
    page-break-after: always;
    position: relative;
    padding-bottom: 8px;
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
    min-height: 255mm;
    text-align: center;
    background: linear-gradient(145deg, #0f274a 0%, #1a4275 100%);
    color: #ffffff;
    border-radius: 8px;
    padding: 40px 30px;
    box-sizing: border-box;
  }

  .cover-icon {
    font-size: 52pt;
    margin-bottom: 16px;
  }

  .cover-title {
    font-size: 26pt;
    font-weight: 700;
    margin: 0 0 10px 0;
    color: #ffffff;
    letter-spacing: -0.5px;
    line-height: 1.2;
    text-transform: uppercase;
  }

  .cover-subtitle {
    font-size: 14pt;
    color: #93c5fd;
    margin: 0 0 30px 0;
    font-weight: 500;
  }

  .cover-badge {
    display: inline-block;
    background: rgba(255, 255, 255, 0.12);
    border: 1px solid rgba(255, 255, 255, 0.25);
    padding: 6px 20px;
    border-radius: 20px;
    font-size: 10.5pt;
    color: #ffffff;
    margin-bottom: 35px;
  }

  .cover-desc {
    background: rgba(255, 255, 255, 0.96);
    color: #1f2937;
    border-radius: 8px;
    padding: 22px 28px;
    max-width: 580px;
    text-align: left;
    font-size: 10pt;
    line-height: 1.6;
    box-shadow: 0 8px 20px rgba(0,0,0,0.25);
  }

  .cover-desc h4 {
    margin: 0 0 8px 0;
    color: #1e40af;
    font-size: 12pt;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  /* Page Headers */
  .header {
    border-bottom: 2px solid #2563eb;
    padding-bottom: 6px;
    margin-bottom: 12px;
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
  }

  .header h2 {
    font-size: 14pt;
    color: #1e3a8a;
    margin: 0;
    font-weight: 700;
  }

  .header .section-tag {
    font-size: 8.5pt;
    color: #6b7280;
    text-transform: uppercase;
    font-weight: 600;
    letter-spacing: 0.5px;
  }

  .intro-text {
    font-size: 9.5pt;
    color: #4b5563;
    margin: 0 0 10px 0;
    line-height: 1.4;
  }

  /* Screenshot Container with Pins */
  .shot-wrap {
    position: relative;
    border: 1px solid #d1d5db;
    border-radius: 6px;
    overflow: hidden;
    box-shadow: 0 3px 10px rgba(0,0,0,0.06);
    margin-bottom: 10px;
    background: #f9fafb;
  }

  .shot-img {
    width: 100%;
    display: block;
  }

  /* Callout Badges */
  .pin {
    position: absolute;
    width: 24px;
    height: 24px;
    background: #ef4444;
    color: #ffffff;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 800;
    font-size: 10pt;
    box-shadow: 0 0 0 2.5px #ffffff, 0 2px 6px rgba(0,0,0,0.4);
    z-index: 10;
  }

  /* Explanation Cards */
  .notes-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px;
    margin-top: 8px;
  }

  .note-card {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-left: 3.5px solid #2563eb;
    border-radius: 5px;
    padding: 7px 10px;
    font-size: 9pt;
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
    width: 17px;
    height: 17px;
    background: #ef4444;
    color: #ffffff;
    border-radius: 50%;
    font-size: 8.5pt;
    font-weight: 800;
  }

  .spec-box {
    background: #f0fdf4;
    border: 1px solid #86efac;
    border-radius: 5px;
    padding: 7px 11px;
    margin-top: 8px;
    font-size: 8.8pt;
    color: #166534;
  }

  .spec-box strong {
    color: #14532d;
  }

  .footer-tip {
    font-size: 8pt;
    color: #94a3b8;
    border-top: 1px solid #f1f5f9;
    padding-top: 4px;
    margin-top: 8px;
    text-align: right;
  }

  .table-clean {
    width: 100%;
    border-collapse: collapse;
    margin: 8px 0;
    font-size: 9pt;
  }

  .table-clean th {
    background: #1e3a8a;
    color: white;
    padding: 6px 9px;
    text-align: left;
    font-weight: 600;
  }

  .table-clean td {
    padding: 6px 9px;
    border-bottom: 1px solid #e2e8f0;
  }

  .table-clean tr:nth-child(even) {
    background: #f8fafc;
  }
</style>
</head>
<body>

<!-- ============================================================== -->
<!-- 1. COVER PAGE -->
<!-- ============================================================== -->
<div class="page">
  <div class="cover">
    <div class="cover-icon">🚚 📋 ⚙️</div>
    <h1 class="cover-title">Информационная система<br>транспортного отдела</h1>
    <div class="cover-subtitle">Регламент и практическое руководство пользователя</div>
    <div class="cover-badge">Версия системы 1.0 • Иллюстрированное издание</div>

    <div class="cover-desc">
      <h4>Назначение документа</h4>
      <p style="margin: 0 0 8px 0;">
        Настоящее руководство определяет порядок работы с единой информационной системой транспортного отдела, заменяющей учет в разрозненных таблицах Excel.
      </p>
      <p style="margin: 0 0 8px 0;">
        В документе описаны функциональные модули: оперативный учет автопарка, реестр водителей, оформление временных пересадок, выписка путевых листов, автоматическое определение нарушителей при обработке штрафов, фиксация ТО и ремонтов, контроль ГСМ, а также регламент создания резервных копий и установки обновлений.
      </p>
      <p style="margin: 0;">
        Все ключевые элементы интерфейса снабжены скриншотами с номерными указателями (①, ②, ③) и детальными инструкциями.
      </p>
    </div>
  </div>
</div>

<!-- ============================================================== -->
<!-- 2. LOGIN PAGE -->
<!-- ============================================================== -->
<div class="page">
  <div class="header">
    <h2>1. Запуск системы и авторизация</h2>
    <span class="section-tag">Авторизация</span>
  </div>
  <p class="intro-text">
    Запуск программного комплекса выполняется запуском исполняемого файла <b>Запустить_Транспорт.bat</b> (или <code>START.bat</code>). После старта локального веб-сервера браузер открывает окно авторизации.
  </p>

  <div class="shot-wrap">
    <img src="${images.login}" class="shot-img" alt="Экран авторизации">
    <div class="pin" style="top: 48%; left: 44%;">①</div>
    <div class="pin" style="top: 57%; left: 44%;">②</div>
    <div class="pin" style="top: 67%; left: 50%;">③</div>
  </div>

  <div class="notes-grid">
    <div class="note-card">
      <div class="title"><span class="badge-num">①</span> Поле «Имя пользователя (Логин)»</div>
      Ввод идентификатора учетной записи (например, <code>dispatcher</code>).
    </div>
    <div class="note-card">
      <div class="title"><span class="badge-num">②</span> Поле «Пароль»</div>
      Ввод пароля доступа (символы скрыты маской).
    </div>
    <div class="note-card" style="grid-column: span 2;">
      <div class="title"><span class="badge-num">③</span> Кнопка «Войти в систему»</div>
      Инициация проверки учетных данных и переход к главному интерфейсу.
    </div>
  </div>

  <table class="table-clean" style="margin-top: 10px;">
    <thead>
      <tr>
        <th>Роль</th>
        <th>Логин</th>
        <th>Пароль</th>
        <th>Предоставляемые права</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td><b>Диспетчер</b></td>
        <td><code>dispatcher</code></td>
        <td><code>disp123</code></td>
        <td>Полный операционный доступ: редактирование ТС, водителей, путевых, штрафов, ТО, ГСМ.</td>
      </tr>
      <tr>
        <td><b>Руководитель</b></td>
        <td><code>viewer</code></td>
        <td><code>view123</code></td>
        <td>Аналитический доступ: просмотр дашборда, фильтрация данных, экспорт отчетов в Excel.</td>
      </tr>
      <tr>
        <td><b>Администратор</b></td>
        <td><code>admin</code></td>
        <td><code>admin123</code></td>
        <td>Системный доступ: создание/удаление учетных записей, журнал аудита, бэкапы.</td>
      </tr>
    </tbody>
  </table>
  <div class="footer-tip">Страница 1 • Авторизация и разграничение прав</div>
</div>

<!-- ============================================================== -->
<!-- 3. DASHBOARD PAGE -->
<!-- ============================================================== -->
<div class="page">
  <div class="header">
    <h2>2. Сводный дашборд оперативных показателей</h2>
    <span class="section-tag">Мониторинг</span>
  </div>
  <p class="intro-text">
    Экран предназначен для непрерывного контроля ключевых параметров автопарка, сроков действия разрешительных документов и статуса штрафов.
  </p>

  <div class="shot-wrap">
    <img src="${images.dashboard}" class="shot-img" alt="Дашборд показателей">
    <div class="pin" style="top: 14%; left: 32%;">①</div>
    <div class="pin" style="top: 36%; left: 40%;">②</div>
    <div class="pin" style="top: 72%; left: 40%;">③</div>
    <div class="pin" style="top: 40%; left: 4%;">④</div>
  </div>

  <div class="notes-grid">
    <div class="note-card">
      <div class="title"><span class="badge-num">①</span> Индикаторы баланса парка</div>
      Отображение суммарного количества ТС (217+), единиц в эксплуатации, находящихся на СТО и в резерве.
    </div>
    <div class="note-card">
      <div class="title"><span class="badge-num">②</span> Виджет упреждающего контроля ТО и страховок</div>
      Автоматическая фильтрация транспортных средств, до окончания срока техосмотра или страхования которых осталось менее 30 дней.
    </div>
    <div class="note-card">
      <div class="title"><span class="badge-num">③</span> Реестр неоплаченной задолженности</div>
      Список активных штрафов с указанием сумм, подразделений и ответственных лиц.
    </div>
    <div class="note-card">
      <div class="title"><span class="badge-num">④</span> Модульное меню разделов</div>
      Быстрый переход между функциональными блоками системы.
    </div>
  </div>

  <div class="spec-box">
    <b>Порядок утреннего контроля:</b> Проверить виджет ②. По автомобилям в желтой и красной зонах заблаговременно запланировать прохождение осмотра или переоформление полиса страхования.
  </div>
  <div class="footer-tip">Страница 2 • Мониторинг ключевых показателей</div>
</div>

<!-- ============================================================== -->
<!-- 4. VEHICLES PAGE -->
<!-- ============================================================== -->
<div class="page">
  <div class="header">
    <h2>3. Учет автопарка и контроль сроков действия документов</h2>
    <span class="section-tag">Автопарк</span>
  </div>
  <p class="intro-text">
    Реестр содержит полные сведения обо всех 217+ автомобилях компаний («Meganet», «Elite ProBuilding», «NLS», «СвязьСервисКомплект»).
  </p>

  <div class="shot-wrap">
    <img src="${images.vehicles}" class="shot-img" alt="Реестр автопарка">
    <div class="pin" style="top: 13%; left: 24%;">①</div>
    <div class="pin" style="top: 13%; left: 88%;">②</div>
    <div class="pin" style="top: 13%; left: 74%;">③</div>
    <div class="pin" style="top: 45%; left: 63%;">④</div>
    <div class="pin" style="top: 45%; left: 16%;">⑤</div>
  </div>

  <div class="notes-grid">
    <div class="note-card">
      <div class="title"><span class="badge-num">①</span> Строка поиска и фильтрации</div>
      Быстрый поиск по государственному номеру (включая слитное и раздельное написание), марке, модели или подразделению.
    </div>
    <div class="note-card">
      <div class="title"><span class="badge-num">②</span> Кнопка добавления ТС</div>
      Ввод нового транспортного средства с фиксацией VIN, данных техпаспорта и сроков осмотра.
    </div>
    <div class="note-card">
      <div class="title"><span class="badge-num">③</span> Экспорт данных в Excel</div>
      Генерация реестра парка в формате <code>.xlsx</code> с сохранением цветовой индикации сроков.
    </div>
    <div class="note-card">
      <div class="title"><span class="badge-num">④</span> Цветовая индикация состояния (Светофор)</div>
      🟢 <b>Зеленый:</b> срок действия >30 дней.<br>
      🟡 <b>Желтый:</b> предупреждение (<30 дней).<br>
      🔴 <b>Красный:</b> срок истек. Выпуск на линию запрещен.
    </div>
  </div>

  <div class="spec-box">
    <b>Карточка транспортного средства:</b> Клик по госномеру <span class="badge-num">⑤</span> открывает карточку ТС с отображением текущего водителя, истории пересадок, путевых листов, штрафов и ремонтов.
  </div>
  <div class="footer-tip">Страница 3 • Учет автопарка и карточка ТС</div>
</div>

<!-- ============================================================== -->
<!-- 5. ASSIGNMENTS PAGE -->
<!-- ============================================================== -->
<div class="page">
  <div class="header">
    <h2>4. Журнал пересадок и временных закреплений</h2>
    <span class="section-tag">Пересадки</span>
  </div>
  <p class="intro-text">
    Модуль обеспечивает хронологический учет передачи автомобилей между сотрудниками при отпусках, ремонтах и ротации персонала.
  </p>

  <div class="shot-wrap">
    <img src="${images.assignments}" class="shot-img" alt="Журнал пересадок">
    <div class="pin" style="top: 13%; left: 88%;">①</div>
    <div class="pin" style="top: 40%; left: 32%;">②</div>
    <div class="pin" style="top: 40%; left: 70%;">③</div>
  </div>

  <div class="notes-grid">
    <div class="note-card" style="grid-column: span 2;">
      <div class="title"><span class="badge-num">①</span> Кнопка «+ Новая пересадка / замена»</div>
      Регистрация передачи ТС: выбор автомобиля, выбор принимающего водителя, фиксация даты и причины передачи (<i>«Отпуск»</i>, <i>«Ремонт авто»</i>, <i>«Служебная необходимость»</i>).
    </div>
    <div class="note-card">
      <div class="title"><span class="badge-num">②</span> Текущий водитель и контактные данные</div>
      Отображение фактического пользователя автомобиля на текущий момент времени с рабочим телефоном.
    </div>
    <div class="note-card">
      <div class="title"><span class="badge-num">③</span> Основание передачи</div>
      Фиксация причины временного или постоянного закрепления с автоматическим архивированием предыдущей привязки.
    </div>
  </div>

  <div class="spec-box">
    <b>Принцип сквозной привязки:</b> При регистрации нарушения ПДД система автоматически сопоставляет дату правонарушения с периодом действия записи в журнале пересадок, безошибочно определяя фактического нарушителя.
  </div>
  <div class="footer-tip">Страница 4 • Учет движения ТС и закреплений</div>
</div>

<!-- ============================================================== -->
<!-- 6. WAYBILLS PAGE -->
<!-- ============================================================== -->
<div class="page">
  <div class="header">
    <h2>5. Путевые листы и еженедельный контроль возврата</h2>
    <span class="section-tag">Путевые листы</span>
  </div>
  <p class="intro-text">
    Модуль автоматизирует выписку путевых листов, расчет пробега по показаниям одометра и мониторинг еженедельной сдачи корешков.
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
      Формирование нового листа с автоподстановкой закрепленного водителя и начальных показаний одометра.
    </div>
    <div class="note-card">
      <div class="title"><span class="badge-num">②</span> Расчет суммарного пробега</div>
      Автоматическое вычисление фактически пройденной дистанции: <code>Пробег = Одометр_возврат - Одометр_выезд</code>.
    </div>
    <div class="note-card">
      <div class="title"><span class="badge-num">③</span> Чеклист еженедельной сдачи (1–4 недели)</div>
      Фиксация возврата отрывных талонов и маршрутных листов по неделям месяца.
    </div>
    <div class="note-card">
      <div class="title"><span class="badge-num">④</span> Статусный учет и обработка утерь</div>
      Перевод в статус «Сдан» либо маркировка флагом «Утерян» с возможностью выдачи дубликата.
    </div>
  </div>

  <div class="footer-tip">Страница 5 • Учет путевой документации и пробега</div>
</div>

<!-- ============================================================== -->
<!-- 7. FINES PAGE -->
<!-- ============================================================== -->
<div class="page">
  <div class="header">
    <h2>6. Штрафы ПДД и формирование служебных записок в СБ</h2>
    <span class="section-tag">Штрафы ПДД</span>
  </div>
  <p class="intro-text">
    Обработка постановлений об административных правонарушениях, автоматическое определение водителя и выгрузка ведомостей задолженности.
  </p>

  <div class="shot-wrap">
    <img src="${images.fines}" class="shot-img" alt="Штрафы ПДД">
    <div class="pin" style="top: 13%; left: 88%;">①</div>
    <div class="pin" style="top: 13%; left: 66%;">②</div>
    <div class="pin" style="top: 40%; left: 34%;">③</div>
    <div class="pin" style="top: 40%; left: 80%;">④</div>
  </div>

  <div class="notes-grid">
    <div class="note-card">
      <div class="title"><span class="badge-num">①</span> Кнопка «+ Внести штраф»</div>
      Ввод реквизитов постановления (номер, дата нарушения, сумма). Поле водителя может оставаться пустым для автоопределения.
    </div>
    <div class="note-card">
      <div class="title"><span class="badge-num">②</span> Экспорт служебной записки в СБ</div>
      Генерация официального документа <code>.xlsx</code> со списком сотрудников, имеющих непогашенную задолженность, для Службы безопасности.
    </div>
    <div class="note-card">
      <div class="title"><span class="badge-num">③</span> Автоматически определенный водитель</div>
      Идентификация ответственного лица на основе журнала пересадок на момент фиксации нарушения.
    </div>
    <div class="note-card">
      <div class="title"><span class="badge-num">④</span> Статусы жизненного цикла штрафа</div>
      «Новый» → «Оповещен» → «Оплачен через Kaspi» (с фиксацией даты оплаты) / «Отказ от оплаты».
    </div>
  </div>

  <div class="spec-box">
    <b>Порядок передачи задолженности в СБ:</b> По штрафам с отказом от добровольной оплаты активировать опцию <i>«В служебную записку»</i>. Документ формируется нажатием кнопки <span class="badge-num">②</span>.
  </div>
  <div class="footer-tip">Страница 6 • Учет штрафов и претензионная работа</div>
</div>

<!-- ============================================================== -->
<!-- 8. MAINTENANCE PAGE -->
<!-- ============================================================== -->
<div class="page">
  <div class="header">
    <h2>7. Техническое обслуживание, ремонты и эвакуация</h2>
    <span class="section-tag">ТО и Ремонты</span>
  </div>
  <p class="intro-text">
    Регистрация планового сервисного обслуживания, кузовных и агрегатных ремонтов, а также случаев транспортировки эвакуатором.
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
      Создание сервисной карточки: фиксация пробега, типа обслуживания (плановое ТО, замена масла, лобовое стекло, геометрия, эвакуация).
    </div>
    <div class="note-card">
      <div class="title"><span class="badge-num">②</span> Описание неисправности и регламентные работы</div>
      Детализация дефектов, причин направления на сервис и перечня замененных запчастей.
    </div>
    <div class="note-card">
      <div class="title"><span class="badge-num">③</span> Подрядная организация и номер акта</div>
      Учет сервисных центров (СТО Хабаров и др.), номеров ЕРП и услуг эвакуатора (ИП Мухраев, доставка на базу Емцова 11).
    </div>
  </div>

  <div class="spec-box">
    <b>Синхронизация статуса:</b> Перевод заявки в статус «В ремонте» автоматически изменяет статус автомобиля в главном реестре, исключая его ошибочное назначение на маршрут.
  </div>
  <div class="footer-tip">Страница 7 • Технический надзор и обслуживание</div>
</div>

<!-- ============================================================== -->
<!-- 9. FUEL PAGE -->
<!-- ============================================================== -->
<div class="page">
  <div class="header">
    <h2>8. Контроль расхода ГСМ и баланса топливных карт</h2>
    <span class="section-tag">Учет ГСМ</span>
  </div>
  <p class="intro-text">
    Учет фактической выборки топлива по безналичным картам и автоматическое сопоставление с нормативным расходом.
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
      Ввод данных транзакции: привязка к номеру топливной карты, фактически заправленный объем (л), пройденный километраж.
    </div>
    <div class="note-card">
      <div class="title"><span class="badge-num">②</span> Расчет расхода по норме</div>
      Вычисление нормативного объема списания топлива на основании утвержденной нормы для модели ТС: <code>(Пробег * Норма) / 100</code>.
    </div>
    <div class="note-card">
      <div class="title"><span class="badge-num">③</span> Выявление отклонений (Экономия / Перерасход)</div>
      🟢 <b>Зеленый:</b> фактический расход не превышает нормативный (экономия).<br>
      🔴 <b>Красный:</b> перерасход топлива относительно нормы (требует служебной проверки).
    </div>
  </div>

  <div class="footer-tip">Страница 8 • Учет горюче-смазочных материалов</div>
</div>

<!-- ============================================================== -->
<!-- 10. BACKUPS & UPDATE PAGE -->
<!-- ============================================================== -->
<div class="page">
  <div class="header">
    <h2>9. Резервное копирование базы данных и обновления</h2>
    <span class="section-tag">Безопасность</span>
  </div>
  <p class="intro-text">
    Регламент резервного сохранения данных автопарка, облачной синхронизации и установки программных обновлений.
  </p>

  <div class="shot-wrap">
    <img src="${images.backups}" class="shot-img" alt="Резервное копирование и обновления">
    <div class="pin" style="top: 13%; left: 88%;">①</div>
    <div class="pin" style="top: 24%; left: 80%;">②</div>
    <div class="pin" style="top: 48%; left: 50%;">③</div>
    <div class="pin" style="top: 78%; left: 35%;">④</div>
  </div>

  <div class="notes-grid">
    <div class="note-card">
      <div class="title"><span class="badge-num">①</span> Внеплановое создание резервной копии</div>
      Ручное сохранение архива базы данных в директорию <code>backend/data/backups/</code>.
    </div>
    <div class="note-card">
      <div class="title"><span class="badge-num">②</span> Автоматическое обновление системы</div>
      Проверка наличия новых релизов в репозитории GitHub и установка обновления в 1 клик с предварительным автобэкапом.
    </div>
    <div class="note-card">
      <div class="title"><span class="badge-num">③</span> Облачная выгрузка на Google Диск</div>
      Автоматическая передача каждого созданного архива в облачное хранилище через защищенный веб-хук.
    </div>
    <div class="note-card">
      <div class="title"><span class="badge-num">④</span> Журнал резервных копий</div>
      Таблица доступных точек восстановления с фиксацией даты, времени и размера архива.
    </div>
  </div>

  <div class="spec-box">
    <b>Автоматическое расписание:</b> Резервный снимок базы данных создается встроенным планировщиком ежедневно в <b>00:00</b> без участия оператора.
  </div>
  <div class="footer-tip">Страница 9 • Обеспечение отказоустойчивости</div>
</div>

<!-- ============================================================== -->
<!-- 11. REGULATION TABLE -->
<!-- ============================================================== -->
<div class="page">
  <div class="header">
    <h2>10. Сводный регламент типовых операций</h2>
    <span class="section-tag">Регламент</span>
  </div>

  <table class="table-clean">
    <thead>
      <tr>
        <th style="width: 25%;">Событие</th>
        <th style="width: 75%;">Порядок действий оператора</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td><b>Начало рабочего дня</b></td>
        <td>Запустить <code>Запустить_Транспорт.bat</code>. Выполнить вход под учетной записью <code>dispatcher</code>. Проверить на Дашборде блок предупреждений по срокам ТО и страховок.</td>
      </tr>
      <tr>
        <td><b>Замена водителя / Отпуск</b></td>
        <td>Открыть раздел <b>«Пересадки и замены»</b> → «+ Новая пересадка» → указать авто, временного водителя и основание.</td>
      </tr>
      <tr>
        <td><b>Поступление постановления о штрафе</b></td>
        <td>Раздел <b>«Штрафы»</b> → «+ Внести штраф» → указать номер авто, дату и сумму. Водитель определяется автоматически на основе пересадок.</td>
      </tr>
      <tr>
        <td><b>Отказ водителя от оплаты штрафа</b></td>
        <td>В свойствах штрафа активировать признак «В служебную записку». Нажать <b>«Служебная записка в СБ (.xlsx)»</b> для выгрузки реестра в Службу безопасности.</td>
      </tr>
      <tr>
        <td><b>Выпуск ТС на маршрут</b></td>
        <td>Раздел <b>«Путевые листы»</b> → «+ Выдать путевой лист» → зафиксировать начальный одометр. По возвращении внести конечный одометр.</td>
      </tr>
      <tr>
        <td><b>Сдача еженедельной отчетности</b></td>
        <td>В разделе «Путевые листы» проставить отметки в чеклисте возврата (Недели 1–4).</td>
      </tr>
      <tr>
        <td><b>Направление ТС на ремонт / СТО</b></td>
        <td>Раздел <b>«ТО, Ремонты, Эвакуация»</b> → оформить заявку с указанием СТО или эвакуатора ИП Мухраев.</td>
      </tr>
      <tr>
        <td><b>Формирование отчета руководству</b></td>
        <td>Раздел «Автопарк» → нажать <b>«Выгрузить в Excel»</b>. Сформированный файл содержит полный актуальный статус парка.</td>
      </tr>
      <tr>
        <td><b>Установка обновления ПО</b></td>
        <td>Раздел «Резервные копии» → нажать кнопку <b>«Обновить всю программу»</b>. Система автоматически выполнит бэкап и перезапустится.</td>
      </tr>
      <tr>
        <td><b>Завершение работы</b></td>
        <td>Закрыть вкладку браузера и окно консоли запуска. Все транзакции фиксируются в базе данных моментально.</td>
      </tr>
    </tbody>
  </table>

  <div style="background: #f8fafc; border: 1px solid #cbd5e1; border-radius: 6px; padding: 12px 16px; margin-top: 14px; text-align: center;">
    <span style="font-size: 10pt; font-weight: 700; color: #1e3a8a;">Информационная система транспортного отдела • Эксплуатационная документация</span>
  </div>
  <div class="footer-tip">Страница 10 • Сводный регламент типовых операций</div>
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
