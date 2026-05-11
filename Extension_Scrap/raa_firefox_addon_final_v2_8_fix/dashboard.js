const state = {
  running: false,
  stopRequested: false,
  siteMap: null,
  downloadedCount: 0,
  selectedMonthKeys: new Set(),
  downloadedHistory: {},
  currentStep: 1,
  pageKind: 'unknown',
  currentUrl: '',
};

const DEFAULT_URL = 'https://www.loir-et-cher.gouv.fr/Publications/Recueil-des-actes-administratifs';
const APP_VERSION = '2.8.1';

const els = {
  rootUrl: document.getElementById('root-url'),
  currentRootDisplay: document.getElementById('current-root-display'),
  minDelay: document.getElementById('min-delay'),
  maxDelay: document.getElementById('max-delay'),
  downloadPdfs: document.getElementById('download-pdfs'),
  dedupePdfs: document.getElementById('dedupe-pdfs'),
  onlyCurrentOrigin: document.getElementById('only-current-origin'),
  skipDownloaded: document.getElementById('skip-downloaded'),
  fromMonth: document.getElementById('from-month'),
  toMonth: document.getElementById('to-month'),
  yearSelect: document.getElementById('year-select'),
  applyRangeBtn: document.getElementById('apply-range-btn'),
  selectAllBtn: document.getElementById('select-all-btn'),
  clearSelectionBtn: document.getElementById('clear-selection-btn'),
  analyzeBtn: document.getElementById('analyze-btn'),
  downloadBtn: document.getElementById('download-btn'),
  stopBtn: document.getElementById('stop-btn'),
  exportBtn: document.getElementById('export-btn'),
  saveSettings: document.getElementById('save-settings'),
  resetHistoryBtn: document.getElementById('reset-history-btn'),
  yearsCount: document.getElementById('years-count'),
  monthsCount: document.getElementById('months-count'),
  docsCount: document.getElementById('docs-count'),
  selectedMonthsCount: document.getElementById('selected-months-count'),
  selectedDocsCount: document.getElementById('selected-docs-count'),
  downloadedCount: document.getElementById('downloaded-count'),
  tree: document.getElementById('tree'),
  log: document.getElementById('log'),
  historyList: document.getElementById('history-list'),
  historyCount: document.getElementById('history-count'),
  folderPattern: document.getElementById('folder-pattern'),
  pageKind: document.getElementById('page-kind'),
  modeChip: document.getElementById('mode-chip'),
  selectionSummary: document.getElementById('selection-summary'),
  previewChip: document.getElementById('preview-chip'),
  selectedDocsPreview: document.getElementById('selected-docs-preview'),
  stepTabs: [...document.querySelectorAll('.step-tab')],
  stepPages: [...document.querySelectorAll('.wizard-page')],
  nextBtns: [...document.querySelectorAll('.next-step')],
  prevBtns: [...document.querySelectorAll('.prev-step')],
};

init().catch(handleFatalError);

async function init() {
  const queryUrl = new URL(window.location.href).searchParams.get('url');
  const stored = await browser.storage.local.get({
    rootUrl: queryUrl || DEFAULT_URL,
    minDelay: 1200,
    maxDelay: 2600,
    downloadPdfs: false,
    dedupePdfs: true,
    onlyCurrentOrigin: true,
    skipDownloaded: true,
    downloadedHistory: {},
  });

  state.currentUrl = queryUrl || stored.rootUrl || DEFAULT_URL;
  state.downloadedHistory = stored.downloadedHistory || {};

  els.rootUrl.value = state.currentUrl;
  els.currentRootDisplay.textContent = state.currentUrl;
  els.minDelay.value = String(stored.minDelay);
  els.maxDelay.value = String(stored.maxDelay);
  els.downloadPdfs.checked = !!stored.downloadPdfs;
  els.dedupePdfs.checked = !!stored.dedupePdfs;
  els.onlyCurrentOrigin.checked = !!stored.onlyCurrentOrigin;
  els.skipDownloaded.checked = !!stored.skipDownloaded;

  bindEvents();
  renderHistory();
  updateFolderPatternPreview();
  updatePageKind('unknown', state.currentUrl);
  updateCounters({ years: 0, months: 0, docs: 0, selectedMonths: 0, selectedDocs: 0, downloaded: 0 });
  setRunning(false);
  setStep(1);
  log(`RAA Downloader v${APP_VERSION} prêt. L’addon utilise d’abord l’URL de la page ouverte, puis lance “Analyser cette page”.`, 'ok');
}

function bindEvents() {
  els.saveSettings.addEventListener('click', saveSettings);
  els.analyzeBtn.addEventListener('click', () => runAnalyze({ autoDownload: false }));
  els.downloadBtn.addEventListener('click', runDownloadSelected);
  els.stopBtn.addEventListener('click', requestStop);
  els.exportBtn.addEventListener('click', exportJson);
  els.applyRangeBtn.addEventListener('click', applyMonthRangeSelection);
  els.selectAllBtn.addEventListener('click', selectAllMonths);
  els.clearSelectionBtn.addEventListener('click', clearSelection);
  els.resetHistoryBtn.addEventListener('click', resetHistory);
  els.yearSelect.addEventListener('change', onYearSelectChange);

  els.stepTabs.forEach((tab) => tab.addEventListener('click', () => setStep(Number(tab.dataset.step || '1'))));
  els.nextBtns.forEach((btn) => btn.addEventListener('click', () => setStep(Number(btn.dataset.next || '1'))));
  els.prevBtns.forEach((btn) => btn.addEventListener('click', () => setStep(Number(btn.dataset.prev || '1'))));
}

function getSettings() {
  const minDelay = Number(els.minDelay.value || 0);
  const maxDelay = Number(els.maxDelay.value || 0);
  return {
    rootUrl: els.rootUrl.value.trim(),
    minDelay: Math.max(0, minDelay),
    maxDelay: Math.max(minDelay, maxDelay),
    downloadPdfs: els.downloadPdfs.checked,
    dedupePdfs: els.dedupePdfs.checked,
    onlyCurrentOrigin: els.onlyCurrentOrigin.checked,
    skipDownloaded: els.skipDownloaded.checked,
  };
}

async function saveSettings() {
  const settings = getSettings();
  await browser.storage.local.set(settings);
  els.currentRootDisplay.textContent = settings.rootUrl;
  updateFolderPatternPreview();
  updatePageKind(classifyPageUrl(settings.rootUrl), settings.rootUrl);
  log('Réglages enregistrés.', 'ok');
}

function setStep(step) {
  state.currentStep = step;
  els.stepTabs.forEach((tab) => tab.classList.toggle('is-active', Number(tab.dataset.step) === step));
  els.stepPages.forEach((page) => page.classList.toggle('is-active', Number(page.dataset.stepPage) === step));
}

function setRunning(flag) {
  state.running = flag;
  els.analyzeBtn.disabled = flag;
  els.stopBtn.disabled = !flag;
  els.downloadBtn.disabled = flag || getSelectedDocuments().length === 0;
  els.exportBtn.disabled = !state.siteMap;
}

function requestStop() {
  state.stopRequested = true;
  log('Arrêt demandé.', 'warn');
}

function ensureNotStopped() {
  if (state.stopRequested) throw new Error('Traitement interrompu par l’utilisateur.');
}

async function runAnalyze({ autoDownload = false }) {
  const settings = getSettings();
  if (!settings.rootUrl) throw new Error('Renseigne une URL.');

  state.stopRequested = false;
  state.downloadedCount = 0;
  state.siteMap = null;
  state.selectedMonthKeys = new Set();
  els.tree.innerHTML = '';
  els.selectedDocsPreview.innerHTML = '';
  setRunning(true);
  updateFolderPatternPreview();
  els.currentRootDisplay.textContent = settings.rootUrl;
  updatePageKind(classifyPageUrl(settings.rootUrl), settings.rootUrl);
  log(`Analyse démarrée sur ${settings.rootUrl}`, 'ok');

  try {
    const siteMap = await crawlSite(settings);
    state.siteMap = siteMap;
    fillYearSelect(siteMap);
    selectDefaultMonths(siteMap);
    initMonthRangeInputs(siteMap);
    renderTree(siteMap);
    renderSelectedDocumentsPreview();
    updateCountersFromState();
    log(`Analyse terminée : ${siteMap.summary.years} année(s), ${siteMap.summary.months} mois, ${siteMap.summary.docs} PDF.`, 'ok');
    setStep(2);
    if (autoDownload || settings.downloadPdfs) {
      setStep(4);
      await downloadSelected(siteMap, settings);
    }
  } catch (error) {
    log(error.message || String(error), 'error');
  } finally {
    setRunning(false);
  }
}

async function runDownloadSelected() {
  if (!state.siteMap) {
    alert('Analyse d’abord la page.');
    return;
  }
  setStep(4);
  state.stopRequested = false;
  setRunning(true);
  try {
    await downloadSelected(state.siteMap, getSettings());
  } catch (error) {
    log(error.message || String(error), 'error');
  } finally {
    setRunning(false);
  }
}

async function crawlSite(settings) {
  const rootUrl = normalizeUrl(settings.rootUrl);
  const rootPage = await fetchPage(rootUrl);
  const pageKind = classifyPage(rootPage.document, rootUrl);
  updatePageKind(pageKind, rootUrl);
  await delayRandom(settings);
  ensureNotStopped();

  const pdfSeen = new Set();
  let years = [];

  if (pageKind === 'month') {
    years = [await buildSingleMonthYear(rootPage.document, rootUrl, settings, pdfSeen)];
  } else if (pageKind === 'year') {
    years = [await processYearLikePage(rootPage.document, rootUrl, settings, pdfSeen)];
  } else {
    const yearLinks = extractYearLinks(rootPage.document, rootUrl, settings);
    if (yearLinks.length) {
      log(`${yearLinks.length} année(s) valide(s) trouvée(s).`, 'ok');
      for (const yearLink of yearLinks) {
        ensureNotStopped();
        const yearPage = await fetchPage(yearLink.url, 'year');
        await delayRandom(settings);
        years.push(await processYearLikePage(yearPage.document, yearLink.url, settings, pdfSeen, yearLink.label));
      }
    } else {
      const collectionMonths = extractCollectionMonthLinks(rootPage.document, rootUrl, settings);
      if (!collectionMonths.length) {
        throw new Error('Aucune année RAA détectée sur la page racine.');
      }
      log(`Mode collection mensuelle détecté : ${collectionMonths.length} mois.`, 'warn');
      years = await processCollectionMonths(collectionMonths, settings, pdfSeen);
    }
  }

  years = years.filter((year) => year.months.length || year.directDocuments?.length);
  years.sort((a, b) => (b.yearNumber || 0) - (a.yearNumber || 0));
  return buildSiteMap(rootUrl, years);
}

async function processCollectionMonths(monthLinks, settings, pdfSeen) {
  const grouped = new Map();
  for (const month of monthLinks) {
    const yearNumber = month.yearNumber || inferYear(month.url, month.label);
    if (!yearNumber) continue;
    if (!grouped.has(yearNumber)) {
      grouped.set(yearNumber, {
        label: `Année ${yearNumber}`,
        url: month.collectionUrl || month.url,
        yearNumber,
        months: [],
        directDocuments: [],
      });
    }
    ensureNotStopped();
    const page = await fetchPage(month.url, 'month');
    await delayRandom(settings);
    const docs = extractPdfLinks(page.document, month.url, settings, pdfSeen);
    grouped.get(yearNumber).months.push({
      label: month.label,
      url: stripHash(month.url),
      monthKey: `${yearNumber}-${String(month.monthNumber).padStart(2, '0')}`,
      monthNumber: String(month.monthNumber).padStart(2, '0'),
      documents: docs,
      loaded: true,
    });
  }
  return [...grouped.values()].map(sortYearMonths);
}

async function processYearLikePage(document, yearUrl, settings, pdfSeen, yearLabelOverride = '') {
  const yearNumber = inferYear(yearUrl, yearLabelOverride) || extractYearNumber(yearLabelOverride) || 0;
  const yearLabel = yearLabelOverride || inferYearLabel(yearUrl, yearNumber);
  const monthLinks = extractMonthLinks(document, yearUrl, settings, yearNumber);

  log(`Base année analysée: ${new URL(yearUrl).pathname}`, 'info');
  log(`Liens <a> trouvés sur la page année: ${document.querySelectorAll('a[href]').length}`, 'info');

  if (!monthLinks.length) {
    const directDocuments = extractPdfLinks(document, yearUrl, settings, pdfSeen);
    if (!directDocuments.length) {
      throw new Error(`Aucun mois valide trouvé pour ${yearNumber || yearLabel}.`);
    }
    log(`Aucun mois détecté : ${directDocuments.length} PDF directs trouvés.`, 'warn');
    return sortYearMonths({
      label: yearLabel,
      url: yearUrl,
      yearNumber,
      directDocuments,
      months: [decorateMonth({
        label: `PDF directs ${yearNumber}`,
        url: yearUrl,
        monthKey: `${yearNumber}-00`,
        monthNumber: '00',
        documents: directDocuments,
        loaded: true,
      }, yearNumber)],
    });
  }

  log(`${monthLinks.length} mois valide(s) trouvé(s) pour ${yearNumber}.`, 'ok');
  monthLinks.forEach((m) => log(`  Mois reconnu: ${m.label} -> ${m.url}`, 'ok'));

  const months = [];
  for (const month of monthLinks) {
    ensureNotStopped();
    log(`Mois retenu: ${month.monthKey} ${month.label}`, 'info');
    const page = await fetchPage(month.url, 'month');
    await delayRandom(settings);
    const documents = extractPdfLinks(page.document, month.url, settings, pdfSeen);
    log(`PDF détectés sur ${month.label}: ${documents.length}`, documents.length ? 'ok' : 'warn');
    months.push(decorateMonth({
      label: month.label,
      url: stripHash(month.url),
      monthKey: month.monthKey,
      monthNumber: String(month.monthNumber).padStart(2, '0'),
      documents,
      loaded: true,
    }, yearNumber));
  }

  return sortYearMonths({
    label: yearLabel,
    url: yearUrl,
    yearNumber,
    months,
    directDocuments: [],
  });
}

async function buildSingleMonthYear(document, monthUrl, settings, pdfSeen) {
  const yearNumber = inferYear(monthUrl) || 0;
  const monthNumber = monthIndexFromLabel(monthUrl);
  const label = buildMonthLabel(monthNumber, yearNumber);
  const documents = extractPdfLinks(document, monthUrl, settings, pdfSeen);
  return {
    label: `Année ${yearNumber}`,
    url: monthUrl,
    yearNumber,
    directDocuments: [],
    months: [decorateMonth({
      label,
      url: stripHash(monthUrl),
      monthKey: `${yearNumber}-${String(monthNumber).padStart(2, '0')}`,
      monthNumber: String(monthNumber).padStart(2, '0'),
      documents,
      loaded: true,
    }, yearNumber)],
  };
}

function sortYearMonths(year) {
  year.months.sort((a, b) => Number(a.monthNumber) - Number(b.monthNumber) || a.label.localeCompare(b.label, 'fr'));
  return year;
}

function decorateMonth(month, yearNumber) {
  const normalizedUrl = stripHash(month.url || '');
  const selectionKey = normalizedUrl || `${yearNumber || '0'}-${month.monthKey || month.label}`;
  return { ...month, selectionKey, yearNumber: yearNumber || month.yearNumber || extractYearNumber(month.label) || 0 };
}

function buildSiteMap(rootUrl, years) {
  const months = years.flatMap((year) => year.months || []);
  const docs = months.flatMap((month) => month.documents || []);
  return {
    rootUrl,
    generatedAt: new Date().toISOString(),
    years,
    summary: { years: years.length, months: months.length, docs: docs.length },
  };
}

async function fetchPage(url, kind = 'root') {
  log(`GET [${kind}] ${url}`, 'info');
  const response = await fetch(url, {
    method: 'GET',
    credentials: 'omit',
    redirect: 'follow',
    headers: { Accept: 'text/html,application/xhtml+xml', 'Cache-Control': 'no-cache', Pragma: 'no-cache' },
  });
  if (!response.ok) throw new Error(`Échec HTTP ${response.status} sur ${url}`);
  const html = await response.text();
  const parser = new DOMParser();
  const document = parser.parseFromString(html, 'text/html');
  log(`OK [${kind}] ${response.url || url} (${html.length} caractères)`, 'ok');
  return { document, url: response.url || url };
}

function classifyPage(document, url) {
  const kindByUrl = classifyPageUrl(url);
  if (kindByUrl !== 'unknown') return kindByUrl;
  const pdfCount = extractPdfLinks(document, url, { onlyCurrentOrigin: false, dedupePdfs: false }, new Set()).length;
  if (pdfCount) return 'month';
  return 'root';
}

function classifyPageUrl(url) {
  const path = decodeURIComponent(new URL(url).pathname);
  if (/\/(Annee-(?:19|20)\d{2}|Raa-[^/]+?-(?:19|20)\d{2})(?:\/)(?!$)/i.test(path)) return 'month';
  if (/\/(Annee-(?:19|20)\d{2}|Les-recueils-des-actes-administratifs-annee-(?:19|20)\d{2}|Raa-[^/]+?-(?:19|20)\d{2})\/?$/i.test(path)) return 'year';
  if (/\/(Janvier|Fevrier|Février|Mars|Avril|Mai|Juin|Juillet|Aout|Août|Septembre|Octobre|Novembre|Decembre|Décembre)(?:-(?:19|20)\d{2})?(?:\/)?$/i.test(path)) return 'month';
  if (/(?:^|\/)Annee-(?:19|20)\d{2}(?:\/|$)/i.test(path) || /Raa-[^/]+?-(?:19|20)\d{2}/i.test(path)) return 'year';
  return 'root';
}

function extractYearLinks(document, baseUrl, settings) {
  const links = mapLinks(document, baseUrl)
    .filter((item) => item.url)
    .filter((item) => looksLikeYearLink(item.url, item.label, baseUrl));
  return uniqueByUrl(filterByOrigin(links, settings, baseUrl))
    .map((item) => ({ ...item, yearNumber: inferYear(item.url, item.label) }))
    .filter((item) => item.yearNumber)
    .sort((a, b) => b.yearNumber - a.yearNumber);
}

function extractMonthLinks(document, baseUrl, settings, expectedYear) {
  const baseUrlClean = stripHash(baseUrl);
  const basePath = decodeURIComponent(new URL(baseUrlClean).pathname).replace(/\/+$/, '');
  const expectedContext = extractYearContext(baseUrlClean);
  const expectedBasePrefix = `${basePath}/`;

  const links = mapLinks(document, baseUrl)
    .filter((item) => item.url)
    .map((item) => ({ ...item, url: stripHash(item.url) }))
    .filter((item) => item.url !== baseUrlClean)
    .filter((item) => !looksLikeYearLink(item.url, item.label, baseUrl))
    .filter((item) => looksLikeMonthLink(item.url, item.label))
    .filter((item) => isMonthInsideExpectedBranch(item.url, item.label, expectedYear, expectedContext, expectedBasePrefix))
    .map((item) => {
      const yearNumber = inferYear(item.url, item.label) || expectedYear;
      const monthNumber = inferMonth(item.url, item.label);
      return {
        ...item,
        yearNumber,
        monthNumber,
        monthKey: `${yearNumber}-${String(monthNumber).padStart(2, '0')}`,
        label: buildMonthLabel(monthNumber, yearNumber, item.label),
      };
    })
    .filter((item) => item.monthNumber)
    .filter((item) => !expectedYear || item.yearNumber === expectedYear);

  return uniqueByKey(links, (item) => item.monthKey + '|' + item.url)
    .sort((a, b) => a.monthNumber - b.monthNumber || a.label.localeCompare(b.label, 'fr'));
}

function extractYearContext(url) {
  const path = decodeURIComponent(new URL(url).pathname);
  const exactSegment = path.match(/\/(Annee-(?:19|20)\d{2}|Les-recueils-des-actes-administratifs-annee-(?:19|20)\d{2}|Raa-[^/]+?-(?:19|20)\d{2})(?:\/|$)/i);
  return exactSegment ? exactSegment[1].toLowerCase() : '';
}

function isMonthInsideExpectedBranch(url, label, expectedYear, expectedContext, expectedBasePrefix) {
  const cleanUrl = stripHash(url);
  const path = decodeURIComponent(new URL(cleanUrl).pathname).replace(/\/+$/, '');
  if (expectedBasePrefix && `${path}/`.startsWith(expectedBasePrefix)) {
    return true;
  }
  const urlContext = extractYearContext(cleanUrl);
  if (expectedContext) {
    return urlContext === expectedContext;
  }
  const extractedYear = inferYear(cleanUrl, label);
  return !expectedYear || extractedYear === expectedYear;
}

function extractCollectionMonthLinks(document, baseUrl, settings) {
  const basePath = stripHash(baseUrl).replace(/\/+$/, '') + '/';
  const links = mapLinks(document, baseUrl)
    .filter((item) => item.url)
    .map((item) => ({ ...item, url: stripHash(item.url) }))
    .filter((item) => item.url.startsWith(basePath))
    .filter((item) => looksLikeMonthLink(item.url, item.label))
    .map((item) => {
      const yearNumber = inferYear(item.url, item.label);
      const monthNumber = inferMonth(item.url, item.label);
      return {
        ...item,
        collectionUrl: baseUrl,
        yearNumber,
        monthNumber,
        monthKey: yearNumber ? `${yearNumber}-${String(monthNumber).padStart(2, '0')}` : '',
        label: buildMonthLabel(monthNumber, yearNumber, item.label),
      };
    })
    .filter((item) => item.yearNumber && item.monthNumber);

  return uniqueByKey(filterByOrigin(links, settings, baseUrl), (item) => item.monthKey + '|' + item.url)
    .sort((a, b) => b.yearNumber - a.yearNumber || a.monthNumber - b.monthNumber);
}

function extractPdfLinks(document, baseUrl, settings, pdfSeen) {
  const links = Array.from(document.querySelectorAll('a[href]'));
  const docs = [];
  const localSeen = new Set();
  for (const a of links) {
    const url = absoluteUrl(a.getAttribute('href'), baseUrl);
    if (!url) continue;
    if (!looksLikePdfUrl(url)) continue;
    if (settings.onlyCurrentOrigin && new URL(url).origin !== new URL(baseUrl).origin) continue;
    if (settings.dedupePdfs && (pdfSeen.has(url) || localSeen.has(url))) continue;
    const title = normalizeSpace(a.textContent) || inferFilenameFromUrl(url);
    const containerText = normalizeSpace(a.closest('li, p, div, article, section, td, tr')?.textContent || '');
    const dateMatch = containerText.match(/\b(\d{2}\/\d{2}\/\d{4})\b/);
    const sizeMatch = containerText.match(/\b(\d+[\.,]?\d*)\s*(Ko|Mo|Go)\b/i);
    docs.push({
      title,
      url,
      date: dateMatch ? dateMatch[1] : null,
      size: sizeMatch ? `${sizeMatch[1]} ${sizeMatch[2]}` : null,
      filename: sanitizeFilename(inferFilenameFromUrl(url, title)),
    });
    pdfSeen.add(url);
    localSeen.add(url);
  }
  return docs;
}

async function downloadSelected(siteMap, settings) {
  const allDocs = getSelectedDocuments();
  const docs = allDocs.filter((doc) => !shouldSkipDownloaded(doc, settings));
  const skipped = allDocs.length - docs.length;
  log(`Historique chargé : ${Object.keys(state.downloadedHistory || {}).length} entrée(s).`, 'info');
  log(`PDF candidats : ${allDocs.length}. Ignorés car déjà téléchargés : ${skipped}. À télécharger : ${docs.length}.`, skipped ? 'warn' : 'ok');
  if (!docs.length) {
    log('Aucun PDF nouveau à télécharger.', 'warn');
    return;
  }

  state.downloadedCount = 0;
  for (const doc of docs) {
    ensureNotStopped();
    const path = buildDownloadPath(doc);
    try {
      const result = await browser.runtime.sendMessage({ type: 'RAA_DOWNLOAD_FILE', url: doc.url, filename: path });
      if (!result?.ok) throw new Error(result?.error || 'Téléchargement refusé');
      state.downloadedCount += 1;
      rememberDownloaded(doc, path);
      updateCountersFromState();
      renderHistory();
      renderTree(state.siteMap);
      renderSelectedDocumentsPreview();
      log(`Téléchargé ${state.downloadedCount}/${docs.length} : ${path}`, 'ok');
    } catch (error) {
      log(`Échec téléchargement ${doc.url} : ${error.message}`, 'error');
    }
    await delayRandom(settings);
  }
  log('Téléchargement terminé.', 'ok');
}

function fillYearSelect(siteMap) {
  els.yearSelect.innerHTML = '';
  const years = siteMap.years.map((year) => year.yearNumber || extractYearNumber(year.label)).filter(Boolean);
  const uniqueYears = [...new Set(years)].sort((a, b) => b - a);
  uniqueYears.forEach((yearNumber) => {
    const option = document.createElement('option');
    option.value = String(yearNumber);
    option.textContent = String(yearNumber);
    els.yearSelect.appendChild(option);
  });
  if (uniqueYears.length) els.yearSelect.value = String(uniqueYears[0]);
}

function onYearSelectChange() {
  if (!state.siteMap) return;
  const year = Number(els.yearSelect.value || '0');
  state.siteMap.years.forEach((item) => {
    item.months.forEach((month) => {
      const monthYear = Number(month.monthKey.split('-')[0] || '0');
      if (monthYear !== year) state.selectedMonthKeys.delete(month.selectionKey);
    });
  });
  const targetYear = state.siteMap.years.find((item) => (item.yearNumber || extractYearNumber(item.label)) === year);
  if (targetYear) {
    targetYear.months.forEach((month) => state.selectedMonthKeys.add(month.selectionKey));
  }
  initMonthRangeInputs(state.siteMap, year);
  renderTree(state.siteMap);
  renderSelectedDocumentsPreview();
  updateCountersFromState();
  log(`Année choisie: ${year}`, 'info');
}

function selectDefaultMonths(siteMap) {
  state.selectedMonthKeys = new Set();
  const firstYear = siteMap.years[0];
  if (!firstYear) return;
  const selectedYear = String(firstYear.yearNumber || extractYearNumber(firstYear.label));
  els.yearSelect.value = selectedYear;
  firstYear.months.forEach((month) => state.selectedMonthKeys.add(month.selectionKey));
}

function getSelectedDocuments() {
  if (!state.siteMap) return [];
  return state.siteMap.years.flatMap((year) =>
    year.months
      .filter((month) => state.selectedMonthKeys.has(month.selectionKey))
      .flatMap((month) => month.documents.map((document) => ({
        year: year.label,
        yearNumber: year.yearNumber || extractYearNumber(year.label),
        month: month.label,
        monthKey: month.monthKey,
        monthNumber: month.monthNumber,
        ...document,
      })))
  );
}

function buildDownloadPath(doc) {
  const siteFolder = sanitizeFolderName(extractSiteFolderName(getSettings().rootUrl));
  const year = sanitizeFolderName(String(doc.yearNumber || 'annee-inconnue'));
  const monthNumber = String(doc.monthNumber || '00').padStart(2, '0');
  const monthName = sanitizeFolderName(normalizeMonthFolderLabel(doc.month || 'Mois'));
  const file = sanitizeFilename(doc.filename || doc.title || inferFilenameFromUrl(doc.url));
  return `RAA/${siteFolder}/${year}/${monthNumber}-${monthName}/${file}`;
}

function shouldSkipDownloaded(doc, settings = getSettings()) {
  return settings.skipDownloaded && Boolean(state.downloadedHistory[doc.url]);
}

function rememberDownloaded(doc, path) {
  state.downloadedHistory[doc.url] = {
    title: doc.title,
    filename: doc.filename,
    path,
    monthKey: doc.monthKey,
    downloadedAt: new Date().toISOString(),
  };
  browser.storage.local.set({ downloadedHistory: state.downloadedHistory }).catch((error) => log(`Échec sauvegarde historique : ${error.message}`, 'error'));
}

function countDownloadedInMonth(month) {
  return (month.documents || []).filter((doc) => Boolean(state.downloadedHistory[doc.url])).length;
}

function renderHistory() {
  const entries = Object.entries(state.downloadedHistory || {}).sort((a, b) => String(b[1]?.downloadedAt || '').localeCompare(String(a[1]?.downloadedAt || '')));
  els.historyCount.textContent = `${entries.length} fichier${entries.length > 1 ? 's' : ''}`;
  els.historyList.innerHTML = entries.length ? entries.slice(0, 18).map(([url, meta]) => `
    <div class="history-item">
      <div class="history-item-title">${escapeHtml(meta.filename || meta.title || inferFilenameFromUrl(url))}</div>
      <div class="history-item-meta">${escapeHtml(meta.path || '')}</div>
      <div class="history-item-meta">${escapeHtml(formatIsoDate(meta.downloadedAt))}</div>
    </div>`).join('') : '<div class="history-empty">Aucun téléchargement mémorisé.</div>';
}

async function resetHistory() {
  state.downloadedHistory = {};
  await browser.storage.local.set({ downloadedHistory: {} });
  renderHistory();
  renderTree(state.siteMap);
  renderSelectedDocumentsPreview();
  log('Historique local réinitialisé.', 'warn');
}

function renderTree(siteMap) {
  if (!siteMap) {
    els.tree.innerHTML = '<div class="history-empty">Aucune donnée.</div>';
    return;
  }
  const selectedYear = Number(els.yearSelect.value || siteMap.years[0]?.yearNumber || 0);
  const years = siteMap.years.filter((year) => !selectedYear || (year.yearNumber || 0) === selectedYear);
  els.selectionSummary.textContent = `${state.selectedMonthKeys.size} mois choisis`;
  els.tree.innerHTML = years.map((year) => {
    const yearDocsCount = year.months.reduce((acc, month) => acc + month.documents.length, 0);
    return `
      <details class="year" open>
        <summary>
          <span class="tree-line"><span class="tree-main"><span class="tree-title">${escapeHtml(year.label)}</span><span class="tree-sub">${year.months.length} mois • ${yearDocsCount} PDF</span></span></span>
        </summary>
        <div class="months-wrap">
          ${year.months.map((month) => renderMonthCard(month)).join('')}
        </div>
      </details>`;
  }).join('') || '<div class="history-empty">Aucun mois pour cette année.</div>';
  bindTreeSelectionEvents();
}

function renderMonthCard(month) {
  const checked = state.selectedMonthKeys.has(month.selectionKey);
  const count = month.documents.length;
  const downloaded = countDownloadedInMonth(month);
  return `
    <details class="month" ${count ? '' : ''}>
      <summary>
        <label class="tree-check tree-check-month">
          <input type="checkbox" data-role="month-checkbox" data-month-key="${escapeAttribute(month.selectionKey)}" ${checked ? 'checked' : ''} />
          <span class="tree-line">
            <span class="tree-main">
              <span class="tree-title">${escapeHtml(month.label)}</span>
              <span class="tree-sub">${count} PDF${downloaded ? ` • ${downloaded} déjà téléchargé(s)` : ''}</span>
            </span>
            <span class="badge ${count ? 'success' : 'muted'}">${count} PDF</span>
          </span>
        </label>
      </summary>
      <div class="doc-list">
        ${month.documents.map((doc) => `
          <div class="doc-item">
            <div class="doc-top">
              <div><a href="${escapeAttribute(doc.url)}" target="_blank" rel="noopener noreferrer">${escapeHtml(doc.title)}</a></div>
              <span class="badge ${state.downloadedHistory[doc.url] ? 'muted' : 'success'}">${state.downloadedHistory[doc.url] ? 'déjà vu' : 'à télécharger'}</span>
            </div>
            <div class="doc-meta">${escapeHtml(compactMeta(doc))}</div>
          </div>`).join('') || '<div class="history-empty">Aucun PDF sur cette page.</div>'}
      </div>
    </details>`;
}

function bindTreeSelectionEvents() {
  els.tree.querySelectorAll('input[data-role="month-checkbox"]').forEach((input) => {
    input.addEventListener('click', (event) => event.stopPropagation());
    input.addEventListener('change', (event) => {
      const key = event.target.dataset.monthKey;
      if (!key) return;
      if (event.target.checked) state.selectedMonthKeys.add(key);
      else state.selectedMonthKeys.delete(key);
      renderTree(state.siteMap);
      renderSelectedDocumentsPreview();
      updateCountersFromState();
      setRunning(state.running);
    });
  });
}

function renderSelectedDocumentsPreview() {
  const docs = getSelectedDocuments();
  const visible = docs.slice(0, 60);
  els.previewChip.textContent = `${docs.length} PDF sélectionnés`;
  els.selectedDocsPreview.innerHTML = visible.length ? visible.map((doc) => `
    <div class="preview-item">
      <div class="preview-top"><strong>${escapeHtml(doc.month)}</strong><span class="badge ${state.downloadedHistory[doc.url] ? 'muted' : 'success'}">${state.downloadedHistory[doc.url] ? 'déjà vu' : 'nouveau'}</span></div>
      <div class="preview-title">${escapeHtml(doc.filename || doc.title)}</div>
      <div class="preview-meta">${escapeHtml(compactMeta(doc))}</div>
    </div>`).join('') : '<div class="history-empty">Aucun PDF dans la sélection.</div>';
}

function initMonthRangeInputs(siteMap, targetYear = Number(els.yearSelect.value || '0')) {
  const monthKeys = siteMap.years
    .filter((year) => !targetYear || (year.yearNumber || 0) === targetYear)
    .flatMap((year) => year.months.map((month) => month.monthKey))
    .sort();
  els.fromMonth.value = monthKeys[0] || '';
  els.toMonth.value = monthKeys[monthKeys.length - 1] || '';
}

function applyMonthRangeSelection() {
  if (!state.siteMap) return;
  const from = els.fromMonth.value;
  const to = els.toMonth.value;
  if (!from || !to) return;
  const [start, end] = from <= to ? [from, to] : [to, from];
  const selected = new Set();
  const targetYear = Number(els.yearSelect.value || '0');
  for (const year of state.siteMap.years) {
    if (targetYear && (year.yearNumber || 0) !== targetYear) continue;
    for (const month of year.months) {
      if (month.monthKey >= start && month.monthKey <= end) selected.add(month.selectionKey);
    }
  }
  state.selectedMonthKeys = selected;
  renderTree(state.siteMap);
  renderSelectedDocumentsPreview();
  updateCountersFromState();
  log(`Plage de mois appliquée: ${start.slice(5)} → ${end.slice(5)}`, 'ok');
}

function selectAllMonths() {
  if (!state.siteMap) return;
  const targetYear = Number(els.yearSelect.value || '0');
  state.selectedMonthKeys = new Set(
    state.siteMap.years
      .filter((year) => !targetYear || (year.yearNumber || 0) === targetYear)
      .flatMap((year) => year.months.map((month) => month.selectionKey))
  );
  renderTree(state.siteMap);
  renderSelectedDocumentsPreview();
  updateCountersFromState();
  log('Tous les mois disponibles sont sélectionnés.', 'ok');
}

function clearSelection() {
  state.selectedMonthKeys = new Set();
  renderTree(state.siteMap);
  renderSelectedDocumentsPreview();
  updateCountersFromState();
  log('Sélection vidée.', 'warn');
}

function updateCountersFromState() {
  const selectedMonths = state.selectedMonthKeys.size;
  const selectedDocs = getSelectedDocuments().filter((doc) => !shouldSkipDownloaded(doc)).length;
  const summary = state.siteMap?.summary || { years: 0, months: 0, docs: 0 };
  updateCounters({ years: summary.years, months: summary.months, docs: summary.docs, selectedMonths, selectedDocs, downloaded: state.downloadedCount });
}

function updateCounters({ years, months, docs, selectedMonths, selectedDocs, downloaded }) {
  els.yearsCount.textContent = String(years);
  els.monthsCount.textContent = String(months);
  els.docsCount.textContent = String(docs);
  els.selectedMonthsCount.textContent = String(selectedMonths);
  els.selectedDocsCount.textContent = String(selectedDocs);
  els.downloadedCount.textContent = String(downloaded);
}

function exportJson() {
  if (!state.siteMap) return;
  const payload = {
    now: new Date().toISOString(),
    page: state.currentUrl,
    state: {
      running: state.running,
      stopRequested: state.stopRequested,
      mode: state.pageKind,
      requestCount: els.log.children.length,
      downloadedCount: state.downloadedCount,
      rootUrl: getSettings().rootUrl,
      selectedYear: els.yearSelect.value,
      selectedMonthKeys: [...state.selectedMonthKeys].sort(),
    },
    years: state.siteMap.years,
    months: state.siteMap.years.flatMap((year) => year.months),
    logs: [...els.log.querySelectorAll('.log-line')].map((line) => ({ message: line.dataset.raw || line.textContent })),
  };
  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const filename = `raa-export-${new Date().toISOString().slice(0, 19).replace(/[:T]/g, '-')}.json`;
  browser.downloads.download({ url, filename, saveAs: false, conflictAction: 'uniquify' })
    .then(() => log(`Export JSON enregistré : ${filename}`, 'ok'))
    .catch((error) => log(`Échec export JSON : ${error.message}`, 'error'))
    .finally(() => setTimeout(() => URL.revokeObjectURL(url), 5000));
}

function updatePageKind(kind, url) {
  state.pageKind = kind;
  const labels = { root: 'Racine / index', year: 'Page année', month: 'Page mois', unknown: 'À classifier' };
  els.pageKind.textContent = labels[kind] || kind;
  els.modeChip.textContent = kind === 'root' ? 'Index' : kind === 'year' ? 'Année' : kind === 'month' ? 'Mois' : 'Inconnu';
  els.currentRootDisplay.textContent = url;
}

function filterByOrigin(items, settings, baseUrl) {
  if (!settings.onlyCurrentOrigin) return items;
  const origin = new URL(baseUrl).origin;
  return items.filter((item) => new URL(item.url).origin === origin);
}

function uniqueByUrl(items) { return uniqueByKey(items, (item) => item.url); }
function uniqueByKey(items, getKey) {
  const seen = new Set();
  return items.filter((item) => {
    const key = getKey(item);
    if (!key || seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

function mapLinks(document, baseUrl) {
  return Array.from(document.querySelectorAll('a[href]')).map((a) => ({
    label: normalizeSpace(a.textContent),
    url: absoluteUrl(a.getAttribute('href'), baseUrl),
  }));
}

function looksLikeYearLink(url, label = '', baseUrl = '') {
  const path = decodeURIComponent(new URL(url).pathname);
  const cleanBase = stripHash(baseUrl);
  if (cleanBase && stripHash(url) === cleanBase) return false;
  return /\/(Annee-(?:19|20)\d{2}|Les-recueils-des-actes-administratifs-annee-(?:19|20)\d{2}|Raa-[^/]+?-(?:19|20)\d{2})(?:\/)?$/i.test(path)
    || /ann[ée]e\s+(?:19|20)\d{2}/i.test(label);
}

function looksLikeMonthLink(url, label = '') {
  const clean = stripHash(url);
  const path = decodeURIComponent(new URL(clean).pathname);
  if (looksLikePdfUrl(clean)) return false;
  return /(Janvier|Fevrier|Février|Mars|Avril|Mai|Juin|Juillet|Aout|Août|Septembre|Octobre|Novembre|Decembre|Décembre)(?:-\d{4})?(?:\/)?$/i.test(path)
    || /\b(janvier|février|fevrier|mars|avril|mai|juin|juillet|août|aout|septembre|octobre|novembre|décembre|decembre)\b/i.test(label);
}

function looksLikePdfUrl(url) {
  return /\.pdf(?:$|[?#])/i.test(url) || /\/(?:i?re)?contenu\/telechargement\//i.test(url);
}

function inferYear(url, label = '') {
  const decodedUrl = decodeURIComponent(String(url || ''));
  const path = (() => { try { return decodeURIComponent(new URL(decodedUrl).pathname); } catch { return decodedUrl; } })();
  const segmentMatches = [...path.matchAll(/(?:^|\/)(?:Annee-|Les-recueils-des-actes-administratifs-annee-|Raa-[^/]+?-)((?:19|20)\d{2})(?=\/|$)/gi)].map((m) => Number(m[1]));
  if (segmentMatches.length) return segmentMatches[segmentMatches.length - 1];
  const labelMatches = [...String(label || '').matchAll(/(?:19|20)\d{2}/g)].map((m) => Number(m[0]));
  if (labelMatches.length) return labelMatches[labelMatches.length - 1];
  const genericMatches = [...(`${decodedUrl} ${label}`).matchAll(/(^|[^\d])((?:19|20)\d{2})(?!\d)/g)].map((m) => Number(m[2]));
  return genericMatches.length ? genericMatches[genericMatches.length - 1] : 0;
}

function inferMonth(url, label = '') {
  return monthIndexFromLabel(`${decodeURIComponent(url)} ${label}`);
}

function inferYearLabel(url, yearNumber) {
  if (/Raa-du-departement/i.test(url)) {
    const m = decodeURIComponent(url).match(/Raa-du-departement-de-([^/]+?)-\d{4}/i);
    if (m) return `Année ${yearNumber} · ${m[1].replace(/-/g, ' ')}`;
  }
  return `Année ${yearNumber}`;
}

function buildMonthLabel(monthNumber, yearNumber, fallback = '') {
  const monthNames = [null, 'Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin', 'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre'];
  if (monthNumber && yearNumber) return `${monthNames[monthNumber]} ${yearNumber}`;
  return normalizeSpace(fallback) || `Mois ${monthNumber}`;
}

function monthIndexFromLabel(label) {
  const normalized = stripDiacritics(String(label || '').toLowerCase());
  const names = {
    janvier: 1, fevrier: 2, mars: 3, avril: 4, mai: 5, juin: 6, juillet: 7, aout: 8, septembre: 9, octobre: 10, novembre: 11, decembre: 12,
  };
  for (const [name, index] of Object.entries(names)) {
    if (normalized.includes(name)) return index;
  }
  return 0;
}

function normalizeSpace(value) { return String(value || '').replace(/\s+/g, ' ').trim(); }
function absoluteUrl(href, baseUrl) { try { return href ? new URL(href, baseUrl).toString() : null; } catch { return null; } }
function normalizeUrl(value) { try { return new URL(value).toString(); } catch { throw new Error(`URL invalide : ${value}`); } }
function stripHash(url) { return String(url || '').replace(/[?#].*$/, ''); }
function extractYearNumber(value) { const m = String(value || '').match(/(19\d{2}|20\d{2})/); return m ? Number(m[1]) : 0; }
function inferFilenameFromUrl(url, fallback = 'document.pdf') { try { const last = decodeURIComponent(new URL(url).pathname.split('/').filter(Boolean).pop() || ''); return /\.pdf$/i.test(last) ? last : `${last || fallback}.pdf`; } catch { return fallback; } }
function sanitizeFolderName(value) { return String(value || 'document').trim().replace(/[\\/:*?"<>|]/g, '_').replace(/\s+/g, ' ').slice(0, 120); }
function sanitizeFilename(value) { let output = String(value || 'document.pdf').trim().replace(/[\\/:*?"<>|]/g, '_').replace(/\s+/g, ' '); if (!/\.pdf$/i.test(output)) output += '.pdf'; return output.slice(0, 180); }
function stripDiacritics(value) { return String(value || '').normalize('NFD').replace(/[\u0300-\u036f]/g, ''); }
function compactMeta(doc) { return [doc.date, doc.size, doc.filename].filter(Boolean).join(' • '); }
function formatIsoDate(value) { try { return value ? new Date(value).toLocaleString('fr-FR') : ''; } catch { return String(value || ''); } }
function extractSiteFolderName(rootUrl) {
  const value = String(rootUrl || 'raa');
  if (/loir-et-cher/i.test(value)) return 'Loir-et-Cher';
  if (/ile-de-france/i.test(value)) return 'Ile-de-France';
  if (/haute-garonne/i.test(value)) return 'Haute-Garonne';
  if (/val-de-marne/i.test(value)) return 'Val-de-Marne';
  try { const host = new URL(value).hostname.replace(/^www\./, ''); return host.split('.').slice(0, -1).join('-') || host; } catch { return 'RAA'; }
}
function normalizeMonthFolderLabel(label) { return stripDiacritics(String(label || '')).replace(/\s+\d{4}\b/g, '').trim() || 'Mois'; }
function updateFolderPatternPreview() { els.folderPattern.textContent = `RAA/${extractSiteFolderName(getSettings().rootUrl)}/2026/01-Janvier/...`; }
function delayRandom(settings) { const min = Math.max(0, Number(settings.minDelay || 0)); const max = Math.max(min, Number(settings.maxDelay || min)); const duration = Math.floor(Math.random() * (max - min + 1)) + min; return new Promise((resolve) => setTimeout(resolve, duration)); }

function log(message, level = 'ok') {
  const line = document.createElement('div');
  const timestamp = new Date().toISOString();
  line.className = `log-line ${level === 'error' ? 'status-error' : level === 'warn' ? 'status-warn' : 'status-ok'}`;
  line.dataset.raw = message;
  line.textContent = `[${new Date().toLocaleTimeString('fr-FR')}] ${message}`;
  els.log.prepend(line);
}

function escapeHtml(value) {
  return String(value || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}
function escapeAttribute(value) { return escapeHtml(value).replace(/`/g, '&#96;'); }
function handleFatalError(error) { console.error(error); alert(`Erreur fatale : ${error.message || error}`); }
