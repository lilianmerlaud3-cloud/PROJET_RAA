(() => {
  const PANEL_ID = 'raa-sidebar-root';
  const STYLE_ID = 'raa-sidebar-style';
  const STORAGE_KEY = 'raaSidebarStrictSettings';
  const ROOT_PATH = '/Publications/Recueil-des-actes-administratifs';
  const DEFAULT_ROOT = `https://www.loir-et-cher.gouv.fr${ROOT_PATH}`;
  const RAA_PATH_HINTS = [/recueil-des-actes-administratifs/i, /\braa\b/i, /documents-publications/i, /documents\+et\+publications/i];
  const MONTHS = [
    ['01', 'Janvier'], ['02', 'Février'], ['03', 'Mars'], ['04', 'Avril'], ['05', 'Mai'], ['06', 'Juin'],
    ['07', 'Juillet'], ['08', 'Août'], ['09', 'Septembre'], ['10', 'Octobre'], ['11', 'Novembre'], ['12', 'Décembre']
  ];
  const MONTH_INDEX = {
    janvier: '01', fevrier: '02', février: '02', mars: '03', avril: '04', mai: '05', juin: '06',
    juillet: '07', aout: '08', août: '08', septembre: '09', octobre: '10', novembre: '11', decembre: '12', décembre: '12'
  };

  const state = {
    open: false,
    running: false,
    stopRequested: false,
    mode: 'idle',
    requestCount: 0,
    downloadedCount: 0,
    logs: [],
    rootUrl: '',
    years: [],
    selectedYear: '',
    months: [],
    selectedMonthKeys: new Set(),
  };

  browser.runtime.onMessage.addListener((message) => {
    if (message?.type === 'RAA_TOGGLE_PANEL') togglePanel();
  });

  function togglePanel() {
    const existing = document.getElementById(PANEL_ID);
    if (existing) {
      existing.remove();
      document.documentElement.classList.remove('raa-sidebar-open');
      state.open = false;
      return;
    }
    injectStyles();
    mountPanel();
    state.open = true;
    document.documentElement.classList.add('raa-sidebar-open');
  }

  function injectStyles() {
    if (document.getElementById(STYLE_ID)) return;
    const style = document.createElement('style');
    style.id = STYLE_ID;
    style.textContent = `
      #${PANEL_ID}{position:fixed;top:0;right:0;width:470px;max-width:96vw;height:100vh;background:#07111f;color:#e5eefc;z-index:2147483647;box-shadow:-12px 0 30px rgba(0,0,0,.28);font-family:Inter,system-ui,sans-serif;display:flex;flex-direction:column;border-left:1px solid #27415f}
      #${PANEL_ID} *{box-sizing:border-box}
      #${PANEL_ID} .raa-head{padding:14px 16px;border-bottom:1px solid #223856;background:linear-gradient(180deg,#0b1a2d,#0a1424)}
      #${PANEL_ID} .raa-title{display:flex;align-items:center;justify-content:space-between;gap:8px}
      #${PANEL_ID} h1{font-size:17px;margin:0}
      #${PANEL_ID} .raa-sub{font-size:12px;color:#98aac0;margin-top:6px;line-height:1.4}
      #${PANEL_ID} .raa-close{background:transparent;border:1px solid #355170;color:#d7e4f7;border-radius:10px;padding:6px 10px;cursor:pointer}
      #${PANEL_ID} .raa-body{padding:14px;overflow:auto;display:grid;gap:12px}
      #${PANEL_ID} .raa-card{background:#0d1a2b;border:1px solid #223856;border-radius:16px;padding:12px}
      #${PANEL_ID} label{display:block;font-size:12px;font-weight:700;margin-bottom:6px;color:#cfe0f5}
      #${PANEL_ID} input,#${PANEL_ID} select,#${PANEL_ID} button,#${PANEL_ID} textarea{font:inherit}
      #${PANEL_ID} input[type=text],#${PANEL_ID} input[type=number],#${PANEL_ID} select,#${PANEL_ID} textarea{width:100%;background:#07111f;color:#e5eefc;border:1px solid #355170;border-radius:10px;padding:10px}
      #${PANEL_ID} textarea{min-height:170px;resize:vertical;font:12px ui-monospace,monospace;line-height:1.45}
      #${PANEL_ID} .raa-row{display:grid;grid-template-columns:1fr 1fr;gap:10px}
      #${PANEL_ID} .raa-row-3{display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px}
      #${PANEL_ID} .raa-btns{display:flex;flex-wrap:wrap;gap:8px}
      #${PANEL_ID} button{background:#142842;color:#edf4ff;border:1px solid #355170;border-radius:10px;padding:9px 12px;cursor:pointer}
      #${PANEL_ID} button.raa-primary{background:#1c5fd3;border-color:#1c5fd3}
      #${PANEL_ID} button:disabled{opacity:.55;cursor:not-allowed}
      #${PANEL_ID} .raa-stats{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:8px}
      #${PANEL_ID} .raa-stat{background:#07111f;border:1px solid #223856;border-radius:12px;padding:10px}
      #${PANEL_ID} .raa-stat b{display:block;font-size:20px;margin-top:4px}
      #${PANEL_ID} .raa-check{display:flex;align-items:center;gap:8px;font-size:13px;margin:8px 0;color:#cfdef1}
      #${PANEL_ID} .raa-check input{width:16px;height:16px;flex:0 0 auto}
      #${PANEL_ID} .raa-doc{border:1px solid #223856;border-radius:10px;padding:9px;background:#07111f;margin-top:8px}
      #${PANEL_ID} .raa-doc a{color:#8fc0ff;text-decoration:none;word-break:break-word}
      #${PANEL_ID} .raa-meta{font-size:12px;color:#98aac0;margin-top:4px}
      #${PANEL_ID} .raa-log{max-height:220px;overflow:auto;background:#04101d;border:1px solid #223856;border-radius:12px;padding:10px;font:12px ui-monospace,monospace;white-space:pre-wrap;line-height:1.45}
      #${PANEL_ID} .ok{color:#8ce3a0} #${PANEL_ID} .warn{color:#ffd36c} #${PANEL_ID} .err{color:#ff9696} #${PANEL_ID} .info{color:#9bc4ff}
      #${PANEL_ID} .raa-muted{color:#98aac0;font-size:12px;line-height:1.45}
      #${PANEL_ID} .raa-section-title{font-weight:700;font-size:13px;margin-bottom:8px;color:#d8e6fa}
      #${PANEL_ID} .raa-badge{display:inline-block;padding:2px 7px;border:1px solid #355170;border-radius:999px;font-size:11px;color:#b9d0eb}
      #${PANEL_ID} .raa-list{display:grid;gap:8px}
    `;
    document.documentElement.appendChild(style);
  }

  async function mountPanel() {
    const root = document.createElement('aside');
    root.id = PANEL_ID;
    root.innerHTML = `
      <div class="raa-head">
        <div class="raa-title">
          <h1>RAA strict</h1>
          <button class="raa-close" id="raa-close">Fermer</button>
        </div>
        <div class="raa-sub">Flux : page courante → année → mois → PDF. L’addon essaie d’utiliser l’URL de la page où tu ouvres le panneau, puis reste dans la branche RAA/RAA équivalente.</div>
      </div>
      <div class="raa-body">
        <section class="raa-card">
          <div class="raa-section-title">Étape 1 — page de départ</div>
          <label for="raa-root-url">Page racine RAA</label>
          <input id="raa-root-url" type="text" />
          <div class="raa-muted" style="margin-top:8px">Par défaut, l’addon reprend l’URL de la page ouverte si elle ressemble à une page RAA. Exemple classique : ${escapeHtml(DEFAULT_ROOT)}</div>
          <div class="raa-btns" style="margin-top:10px"><button id="raa-save">Enregistrer</button><button class="raa-primary" id="raa-list-years">Lister les années</button><button id="raa-stop" disabled>Stop</button></div>
        </section>

        <section class="raa-card">
          <div class="raa-section-title">Étape 2 — année</div>
          <label for="raa-year-select">Choisir une année</label>
          <select id="raa-year-select"><option value="">—</option></select>
          <div class="raa-btns" style="margin-top:10px"><button class="raa-primary" id="raa-list-months" disabled>Lister les mois</button></div>
          <div class="raa-muted" style="margin-top:8px">Une seule année à la fois pour éviter les erreurs de structure.</div>
        </section>

        <section class="raa-card">
          <div class="raa-section-title">Étape 3 — mois</div>
          <div class="raa-row">
            <div><label for="raa-from-month">Du mois</label><select id="raa-from-month"></select></div>
            <div><label for="raa-to-month">Au mois</label><select id="raa-to-month"></select></div>
          </div>
          <div class="raa-btns" style="margin-top:10px"><button id="raa-apply-range">Appliquer la plage</button><button id="raa-all">Tout cocher</button><button id="raa-none">Tout décocher</button><button class="raa-primary" id="raa-load-docs" disabled>Charger les PDF</button></div>
          <div class="raa-muted" style="margin-top:8px">Les mois affichés viennent uniquement de la page année sélectionnée.</div>
        </section>

        <section class="raa-card">
          <div class="raa-section-title">Réglages</div>
          <div class="raa-row-3">
            <div><label for="raa-min-delay">Délai mini (ms)</label><input id="raa-min-delay" type="number" min="0" step="100"></div>
            <div><label for="raa-max-delay">Délai maxi (ms)</label><input id="raa-max-delay" type="number" min="0" step="100"></div>
            <div><label for="raa-timeout">Timeout (ms)</label><input id="raa-timeout" type="number" min="1000" step="1000"></div>
          </div>
          <label class="raa-check"><input id="raa-dedupe" type="checkbox" checked>Éviter les doublons d’URL PDF</label>
        </section>

        <section class="raa-stats">
          <div class="raa-stat">Années<b id="raa-years">0</b></div>
          <div class="raa-stat">Mois<b id="raa-months">0</b></div>
          <div class="raa-stat">PDF<b id="raa-docs">0</b></div>
          <div class="raa-stat">Requêtes<b id="raa-requests">0</b></div>
          <div class="raa-stat">Mois sel.<b id="raa-sel-months">0</b></div>
          <div class="raa-stat">PDF sel.<b id="raa-sel-docs">0</b></div>
          <div class="raa-stat">Téléchargés<b id="raa-downloaded">0</b></div>
          <div class="raa-stat">État<b id="raa-mode">idle</b></div>
        </section>

        <section class="raa-card">
          <div class="raa-section-title">Étape 4 — résultats</div>
          <div id="raa-results"></div>
          <div class="raa-btns" style="margin-top:10px"><button class="raa-primary" id="raa-download" disabled>Télécharger la sélection</button></div>
        </section>

        <section class="raa-card">
          <div class="raa-section-title">Journal</div>
          <div class="raa-btns" style="margin-bottom:10px"><button id="raa-copy-logs">Copier les logs</button><button id="raa-export-logs">Exporter les logs JSON</button><button id="raa-clear-logs">Vider</button></div>
          <div class="raa-log" id="raa-log"></div>
        </section>

        <section class="raa-card">
          <div class="raa-section-title">Rapport détaillé</div>
          <textarea id="raa-debug-report" readonly></textarea>
        </section>
      </div>
    `;
    document.body.appendChild(root);

    const els = collectEls(root);
    fillMonthSelects(els);

    const stored = await browser.storage.local.get({ [STORAGE_KEY]: null });
    const settings = normalizeStoredSettings(stored[STORAGE_KEY] || {});
    els.rootUrl.value = inferRootUrl(location.href) || settings.rootUrl || DEFAULT_ROOT;
    els.minDelay.value = String(settings.minDelay);
    els.maxDelay.value = String(settings.maxDelay);
    els.timeout.value = String(settings.timeoutMs);
    els.dedupe.checked = settings.dedupe;

    bindEvents(els);
    log(els, 'Panneau prêt. L’addon utilise d’abord l’URL de la page ouverte, puis lance “Lister les années”.', 'ok');
    updateAll(els);
  }

  function collectEls(root) {
    return {
      close: root.querySelector('#raa-close'),
      rootUrl: root.querySelector('#raa-root-url'),
      save: root.querySelector('#raa-save'),
      listYears: root.querySelector('#raa-list-years'),
      stop: root.querySelector('#raa-stop'),
      yearSelect: root.querySelector('#raa-year-select'),
      listMonths: root.querySelector('#raa-list-months'),
      fromMonth: root.querySelector('#raa-from-month'),
      toMonth: root.querySelector('#raa-to-month'),
      applyRange: root.querySelector('#raa-apply-range'),
      selectAll: root.querySelector('#raa-all'),
      selectNone: root.querySelector('#raa-none'),
      loadDocs: root.querySelector('#raa-load-docs'),
      minDelay: root.querySelector('#raa-min-delay'),
      maxDelay: root.querySelector('#raa-max-delay'),
      timeout: root.querySelector('#raa-timeout'),
      dedupe: root.querySelector('#raa-dedupe'),
      years: root.querySelector('#raa-years'),
      months: root.querySelector('#raa-months'),
      docs: root.querySelector('#raa-docs'),
      requests: root.querySelector('#raa-requests'),
      selectedMonths: root.querySelector('#raa-sel-months'),
      selectedDocs: root.querySelector('#raa-sel-docs'),
      downloaded: root.querySelector('#raa-downloaded'),
      mode: root.querySelector('#raa-mode'),
      results: root.querySelector('#raa-results'),
      download: root.querySelector('#raa-download'),
      log: root.querySelector('#raa-log'),
      copyLogs: root.querySelector('#raa-copy-logs'),
      exportLogs: root.querySelector('#raa-export-logs'),
      clearLogs: root.querySelector('#raa-clear-logs'),
      debugReport: root.querySelector('#raa-debug-report'),
    };
  }

  function bindEvents(els) {
    els.close.addEventListener('click', togglePanel);
    els.save.addEventListener('click', async () => {
      await browser.storage.local.set({ [STORAGE_KEY]: getSettings(els) });
      log(els, 'Réglages enregistrés.', 'ok');
    });
    els.listYears.addEventListener('click', () => listYears(els));
    els.yearSelect.addEventListener('change', () => {
      state.selectedYear = els.yearSelect.value || '';
      state.months = [];
      state.selectedMonthKeys = new Set();
      renderResults(els);
      updateAll(els);
      els.listMonths.disabled = !state.selectedYear || state.running;
      log(els, state.selectedYear ? `Année choisie: ${state.selectedYear}` : 'Année désélectionnée.', state.selectedYear ? 'info' : 'warn');
    });
    els.listMonths.addEventListener('click', () => listMonths(els));
    els.applyRange.addEventListener('click', () => {
      applyMonthRange(els);
      updateAll(els);
      renderResults(els);
    });
    els.selectAll.addEventListener('click', () => {
      state.selectedMonthKeys = new Set(state.months.map(m => m.monthKey));
      renderResults(els); updateAll(els);
    });
    els.selectNone.addEventListener('click', () => {
      state.selectedMonthKeys = new Set();
      renderResults(els); updateAll(els);
    });
    els.loadDocs.addEventListener('click', () => loadDocuments(els));
    els.download.addEventListener('click', () => downloadSelected(els));
    els.stop.addEventListener('click', () => {
      state.stopRequested = true;
      log(els, 'Arrêt demandé.', 'warn');
    });
    els.copyLogs.addEventListener('click', async () => {
      await navigator.clipboard.writeText(els.debugReport.value || state.logs.map(formatLogLine).join('\n'));
      log(els, 'Logs copiés.', 'ok');
    });
    els.exportLogs.addEventListener('click', () => exportLogs(els));
    els.clearLogs.addEventListener('click', () => {
      state.logs = [];
      els.log.innerHTML = '';
      updateAll(els);
    });
  }

  function normalizeStoredSettings(settings) {
    const minDelay = Math.max(0, Number(settings.minDelay ?? 1200));
    const maxDelay = Math.max(minDelay, Number(settings.maxDelay ?? 2600));
    return {
      rootUrl: settings.rootUrl || inferRootUrl(location.href) || DEFAULT_ROOT,
      minDelay,
      maxDelay,
      timeoutMs: Math.max(1000, Number(settings.timeoutMs ?? 15000)),
      dedupe: settings.dedupe !== false,
    };
  }

  function getSettings(els) {
    const minDelay = Math.max(0, Number(els.minDelay.value || 0));
    const maxDelay = Math.max(minDelay, Number(els.maxDelay.value || minDelay));
    return {
      rootUrl: normalizeUrl(els.rootUrl.value || DEFAULT_ROOT),
      minDelay,
      maxDelay,
      timeoutMs: Math.max(1000, Number(els.timeout.value || 15000)),
      dedupe: els.dedupe.checked,
    };
  }

  async function listYears(els) {
    await runTask(els, 'discovering-years', async (settings) => {
      resetStateForNewRoot(settings.rootUrl);
      const rootPage = await fetchPage(settings.rootUrl, settings, els, 'root');
      state.years = extractYearLinks(rootPage.document, rootPage.url);
      state.selectedYear = '';
      state.months = [];
      state.selectedMonthKeys = new Set();
      populateYearSelect(els);
      if (!state.years.length) throw new Error('Aucune année RAA détectée sur la page racine.');
      log(els, `${state.years.length} année(s) valide(s) trouvée(s).`, 'ok');
    });
  }

  async function listMonths(els) {
    if (!state.selectedYear) {
      log(els, 'Choisis une année avant de lister les mois.', 'warn');
      return;
    }
    await runTask(els, 'discovering-months', async (settings) => {
      const yearEntry = state.years.find(y => String(y.year) === String(state.selectedYear));
      if (!yearEntry) throw new Error(`Année introuvable: ${state.selectedYear}`);
      const yearPage = await fetchPage(yearEntry.url, settings, els, 'year');
      state.months = extractMonthLinks(yearPage.document, yearPage.url, yearEntry.year, els);
      state.selectedMonthKeys = new Set(state.months.map(m => m.monthKey));
      if (!state.months.length) throw new Error(`Aucun mois valide trouvé pour ${yearEntry.year}.`);
      log(els, `${state.months.length} mois valide(s) trouvé(s) pour ${yearEntry.year}.`, 'ok');
    });
  }

  async function loadDocuments(els) {
    const selectedMonths = state.months.filter(m => state.selectedMonthKeys.has(m.monthKey));
    if (!selectedMonths.length) {
      log(els, 'Aucun mois sélectionné.', 'warn');
      return;
    }
    await runTask(els, 'extracting-docs', async (settings) => {
      const seen = new Set();
      for (const month of selectedMonths) {
        ensureNotStopped();
        log(els, `Mois retenu: ${month.monthKey} ${month.label}`, 'info');
        const monthPage = await fetchPage(month.url, settings, els, 'month');
        const docs = extractPdfLinks(monthPage.document, monthPage.url, settings, seen);
        month.documents = docs;
        month.loaded = true;
        log(els, `PDF détectés sur ${month.label}: ${docs.length}`, docs.length ? 'ok' : 'warn');
        await randomDelay(settings);
        renderResults(els);
        updateAll(els);
      }
      log(els, 'Chargement des PDF terminé.', 'ok');
    });
  }

  async function downloadSelected(els) {
    const docs = getSelectedDocuments();
    if (!docs.length) {
      log(els, 'Aucun PDF à télécharger.', 'warn');
      return;
    }
    await runTask(els, 'downloading', async (settings) => {
      for (const doc of docs) {
        ensureNotStopped();
        const filename = buildDownloadPath(doc);
        log(els, `DOWNLOAD ${doc.url}`, 'info');
        const result = await browser.runtime.sendMessage({
          type: 'RAA_DOWNLOAD_FILE',
          url: doc.url,
          filename,
        });
        if (!result?.ok) {
          throw new Error(result?.error || `Échec téléchargement: ${filename}`);
        }
        state.downloadedCount += 1;
        updateAll(els);
        log(els, `Téléchargé ${state.downloadedCount}/${docs.length} : ${filename}`, 'ok');
        await randomDelay(settings);
      }
      log(els, 'Téléchargement terminé.', 'ok');
    });
  }

  async function runTask(els, mode, task) {
    const settings = getSettings(els);
    state.running = true;
    state.stopRequested = false;
    state.mode = mode;
    state.rootUrl = settings.rootUrl;
    setBusy(els, true);
    updateAll(els);
    try {
      await browser.storage.local.set({ [STORAGE_KEY]: settings });
      await task(settings);
    } catch (error) {
      log(els, error.message || String(error), 'err');
    } finally {
      state.running = false;
      state.stopRequested = false;
      state.mode = 'idle';
      setBusy(els, false);
      renderResults(els);
      updateAll(els);
    }
  }

  function resetStateForNewRoot(rootUrl) {
    state.rootUrl = rootUrl;
    state.requestCount = 0;
    state.downloadedCount = 0;
    state.years = [];
    state.selectedYear = '';
    state.months = [];
    state.selectedMonthKeys = new Set();
    renderResults({ results: document.querySelector(`#${PANEL_ID} #raa-results`) });
  }

  async function fetchPage(url, settings, els, kind) {
    ensureNotStopped();
    state.requestCount += 1;
    updateAll(els);
    log(els, `GET [${kind}] ${url}`, 'info');
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), settings.timeoutMs);
    try {
      const response = await fetch(url, {
        method: 'GET',
        credentials: 'omit',
        redirect: 'follow',
        signal: controller.signal,
        headers: { Accept: 'text/html,application/xhtml+xml', 'Cache-Control': 'no-cache', Pragma: 'no-cache' }
      });
      if (!response.ok) throw new Error(`HTTP ${response.status} sur ${url}`);
      const html = await response.text();
      const document = new DOMParser().parseFromString(html, 'text/html');
      log(els, `OK [${kind}] ${response.url || url} (${html.length} caractères)`, 'ok');
      return { document, url: response.url || url };
    } catch (error) {
      if (error.name === 'AbortError') throw new Error(`Timeout après ${settings.timeoutMs} ms sur ${url}`);
      throw error;
    } finally {
      clearTimeout(timer);
      updateAll(els);
    }
  }

  function extractYearLinks(doc, baseUrl) {
    const base = new URL(baseUrl);
    const items = Array.from(doc.querySelectorAll('a[href]')).map(a => {
      const url = absoluteUrl(a.getAttribute('href'), baseUrl);
      const label = normalizeSpace(a.textContent);
      if (!url) return null;
      let parsed;
      try { parsed = new URL(url); } catch { return null; }
      if (parsed.origin !== base.origin) return null;
      if (!looksLikeRaaPath(parsed.pathname)) return null;
      const year = extractYearFromText(label) || extractYearFromUrl(url);
      if (!year) return null;
      return { year, label: label || `Année ${year}`, url: normalizeUrl(url) };
    }).filter(Boolean);

    const uniq = uniqueByUrl(items).sort((a, b) => b.year - a.year);
    if (uniq.length) return uniq;

    const fallbackYear = extractYearFromUrl(baseUrl) || extractYearFromText(doc.querySelector('h1')?.textContent || '');
    if (fallbackYear && looksLikeRaaPath(base.pathname)) {
      return [{ year: fallbackYear, label: `Année ${fallbackYear}`, url: normalizeUrl(baseUrl) }];
    }
    return [];
  }

  function extractMonthLinks(doc, baseUrl, expectedYear, els) {
    const anchors = Array.from(doc.querySelectorAll('a[href]'));
    const items = [];
    const seen = new Set();
    const base = new URL(baseUrl);
    const baseDir = base.pathname.replace(/[^/]+\/?$/, '');

    log(els, `Liens <a> trouvés sur la page année: ${anchors.length}`, 'info');
    log(els, `Base année analysée: ${base.pathname}`, 'info');

    for (const a of anchors) {
      const rawUrl = absoluteUrl(a.getAttribute('href'), baseUrl);
      if (!rawUrl) continue;

      const url = normalizeUrl(rawUrl);
      let parsed;
      try {
        parsed = new URL(url);
      } catch {
        continue;
      }

      if (parsed.origin !== base.origin) continue;
      if (/\.pdf$/i.test(parsed.pathname) || parsed.pathname.includes('/contenu/telechargement/')) continue;

      const decodedPath = decodeURIComponent(parsed.pathname);
      const label = normalizeSpace(a.textContent) || decodedPath.split('/').pop().replace(/-/g, ' ');
      const monthNumber = monthToNumber(label) || monthToNumber(decodedPath);
      if (!monthNumber) continue;

      const yearInUrl = extractYearFromUrl(url);
      if (yearInUrl && Number(yearInUrl) !== Number(expectedYear)) continue;

      const pathLooksRelated = parsed.pathname.startsWith(baseDir) || looksLikeRaaPath(parsed.pathname);
      if (!pathLooksRelated) continue;

      if (seen.has(url)) continue;
      seen.add(url);

      const monthKey = `${expectedYear}-${monthNumber}`;
      items.push({
        year: Number(expectedYear),
        monthNumber,
        monthKey,
        label: monthDisplayLabel(label, expectedYear),
        url,
        documents: [],
        loaded: false,
      });
    }

    const sorted = items.sort((a, b) => a.monthNumber.localeCompare(b.monthNumber));
    log(els, `Mois reconnus pour ${expectedYear}: ${sorted.length}`, sorted.length ? 'ok' : 'warn');
    sorted.forEach((month) => log(els, `  Mois reconnu: ${month.label} -> ${month.url}`, 'ok'));
    return sorted;
  }

  function extractPdfLinks(doc, baseUrl, settings, seen) {
    const docs = [];
    for (const a of Array.from(doc.querySelectorAll('a[href]'))) {
      const url = absoluteUrl(a.getAttribute('href'), baseUrl);
      if (!url) continue;
      if (!looksLikePdfUrl(url)) continue;
      if (settings.dedupe && seen.has(url)) continue;
      const title = normalizeSpace(a.textContent) || inferFilenameFromUrl(url);
      const around = normalizeSpace(a.closest('li,p,div,article,section')?.textContent || '');
      const sizeMatch = around.match(/\b(\d+[\.,]?\d*)\s*(Ko|Mo|Go)\b/i);
      const item = {
        title,
        url,
        size: sizeMatch ? `${sizeMatch[1]} ${sizeMatch[2]}` : null,
        filename: sanitizeFilename(inferFilenameFromUrl(url, title)),
      };
      docs.push(item);
      seen.add(url);
    }
    return docs;
  }

  function applyMonthRange(els) {
    const from = els.fromMonth.value;
    const to = els.toMonth.value;
    if (!from || !to) return;
    const [start, end] = from <= to ? [from, to] : [to, from];
    const selected = state.months.filter(m => m.monthNumber >= start && m.monthNumber <= end).map(m => m.monthKey);
    state.selectedMonthKeys = new Set(selected);
    log(els, `Plage de mois appliquée: ${start} → ${end}`, 'ok');
  }

  function renderResults(els) {
    if (!els?.results) return;
    if (!state.selectedYear && !state.years.length) {
      els.results.innerHTML = '<div class="raa-muted">Aucune analyse encore. Commence par “Lister les années”.</div>';
      return;
    }
    if (state.selectedYear && !state.months.length) {
      els.results.innerHTML = `<div class="raa-muted">Année ${escapeHtml(state.selectedYear)} choisie. Lance “Lister les mois”.</div>`;
      return;
    }
    if (!state.months.length) {
      const years = state.years.map(y => `<div class="raa-check"><span class="raa-badge">${escapeHtml(String(y.year))}</span><span>${escapeHtml(y.url)}</span></div>`).join('');
      els.results.innerHTML = years ? `<div class="raa-list">${years}</div>` : '<div class="raa-muted">Aucune année détectée.</div>';
      return;
    }
    const html = state.months.map(month => {
      const checked = state.selectedMonthKeys.has(month.monthKey) ? 'checked' : '';
      const docs = month.loaded
        ? (month.documents.length
            ? month.documents.map(doc => `<div class="raa-doc"><a href="${escapeAttr(doc.url)}" target="_blank" rel="noopener">${escapeHtml(doc.title)}</a><div class="raa-meta">${escapeHtml(doc.filename)}${doc.size ? ' · ' + escapeHtml(doc.size) : ''}</div></div>`).join('')
            : '<div class="raa-muted" style="margin-top:8px">Aucun PDF détecté.</div>')
        : '<div class="raa-muted" style="margin-top:8px">PDF non chargés.</div>';
      return `
        <div class="raa-card" style="padding:10px;margin-bottom:8px">
          <label class="raa-check" style="margin:0"><input type="checkbox" data-role="month" data-key="${escapeAttr(month.monthKey)}" ${checked}><span>${escapeHtml(month.label)} <span class="raa-badge">${escapeHtml(month.monthKey)}</span></span></label>
          <div class="raa-meta">${escapeHtml(month.url)}</div>
          ${docs}
        </div>`;
    }).join('');
    els.results.innerHTML = html;
    els.results.querySelectorAll('input[data-role="month"]').forEach(input => {
      input.addEventListener('change', e => {
        const key = e.target.dataset.key;
        if (e.target.checked) state.selectedMonthKeys.add(key); else state.selectedMonthKeys.delete(key);
        updateAll(els);
      });
    });
  }

  function populateYearSelect(els) {
    const options = ['<option value="">—</option>'].concat(
      state.years.map(y => `<option value="${escapeAttr(String(y.year))}">${escapeHtml(String(y.year))}</option>`)
    );
    els.yearSelect.innerHTML = options.join('');
    els.listMonths.disabled = true;
  }

  function fillMonthSelects(els) {
    const options = MONTHS.map(([value, label]) => `<option value="${value}">${escapeHtml(label)}</option>`).join('');
    els.fromMonth.innerHTML = options;
    els.toMonth.innerHTML = options;
    els.fromMonth.value = '01';
    els.toMonth.value = '12';
  }

  function getSelectedDocuments() {
    const selectedKeys = state.selectedMonthKeys;
    return state.months
      .filter(month => selectedKeys.has(month.monthKey))
      .flatMap(month => month.documents.map(doc => ({
        ...doc,
        year: String(month.year),
        month: month.label,
        monthKey: month.monthKey,
      })));
  }

  function updateAll(els) {
    const yearsCount = state.years.length;
    const monthsCount = state.months.length;
    const docsCount = state.months.reduce((n, m) => n + m.documents.length, 0);
    const selectedDocsCount = getSelectedDocuments().length;
    if (els.years) els.years.textContent = String(yearsCount);
    if (els.months) els.months.textContent = String(monthsCount);
    if (els.docs) els.docs.textContent = String(docsCount);
    if (els.requests) els.requests.textContent = String(state.requestCount);
    if (els.selectedMonths) els.selectedMonths.textContent = String(state.selectedMonthKeys.size);
    if (els.selectedDocs) els.selectedDocs.textContent = String(selectedDocsCount);
    if (els.downloaded) els.downloaded.textContent = String(state.downloadedCount);
    if (els.mode) els.mode.textContent = state.mode;
    if (els.listMonths) els.listMonths.disabled = state.running || !state.selectedYear;
    if (els.loadDocs) els.loadDocs.disabled = state.running || state.selectedMonthKeys.size === 0;
    if (els.download) els.download.disabled = state.running || selectedDocsCount === 0;
    if (els.stop) els.stop.disabled = !state.running;
    if (els.listYears) els.listYears.disabled = state.running;
    updateDebugReport(els);
  }

  function setBusy(els, busy) {
    if (els.stop) els.stop.disabled = !busy;
    if (els.listYears) els.listYears.disabled = busy;
    if (els.listMonths) els.listMonths.disabled = busy || !state.selectedYear;
    if (els.loadDocs) els.loadDocs.disabled = busy || state.selectedMonthKeys.size === 0;
    if (els.download) els.download.disabled = busy || getSelectedDocuments().length === 0;
  }

  function updateDebugReport(els) {
    if (!els?.debugReport) return;
    const payload = {
      now: new Date().toISOString(),
      page: location.href,
      state: {
        running: state.running,
        stopRequested: state.stopRequested,
        mode: state.mode,
        requestCount: state.requestCount,
        downloadedCount: state.downloadedCount,
        rootUrl: state.rootUrl,
        selectedYear: state.selectedYear,
        selectedMonthKeys: Array.from(state.selectedMonthKeys),
      },
      years: state.years,
      months: state.months,
      logs: state.logs,
    };
    els.debugReport.value = JSON.stringify(payload, null, 2);
  }

  function ensureNotStopped() {
    if (state.stopRequested) throw new Error('Traitement interrompu par l’utilisateur.');
  }

  function randomDelay(settings) {
    const min = Math.max(0, Number(settings.minDelay || 0));
    const max = Math.max(min, Number(settings.maxDelay || min));
    const ms = Math.floor(Math.random() * (max - min + 1)) + min;
    return new Promise(resolve => setTimeout(resolve, ms));
  }


  function looksLikeRaaPath(pathname) {
    const path = decodeURIComponent(String(pathname || '')).toLowerCase();
    return RAA_PATH_HINTS.some((re) => re.test(path));
  }

  function extractYearFromUrl(url) {
    try {
      const decoded = decodeURIComponent(new URL(url).pathname);
      const matches = decoded.match(/(?:annee-|)(20\d{2})(?!\d)/gi) || [];
      if (matches.length) {
        const last = matches[matches.length - 1].match(/(20\d{2})/);
        return last ? Number(last[1]) : null;
      }
      return null;
    } catch {
      return null;
    }
  }

  function extractYearFromText(text) {
    const match = String(text || '').match(/(20\d{2})/);
    return match ? Number(match[1]) : null;
  }
  function inferRootUrl(url) {
    try {
      const parsed = new URL(url);
      if (looksLikeRaaPath(parsed.pathname)) return normalizeUrl(parsed.toString());
      return DEFAULT_ROOT;
    } catch {
      return DEFAULT_ROOT;
    }
  }

  function matchYearUrl(url) {
    if (!url) return null;
    try {
      const parsed = new URL(url);
      const re = new RegExp(`^${escapeRegex(ROOT_PATH)}/Annee-(\\d{4})/?$`);
      return parsed.pathname.match(re);
    } catch {
      return null;
    }
  }

  function monthDisplayLabel(label, year) {
    const clean = normalizeSpace(label);
    return /\b20\d{2}\b/.test(clean) ? clean : `${clean} ${year}`;
  }

  function monthToNumber(value) {
    const key = normalizeSpace(String(value || '')).toLowerCase();
    for (const [name, num] of Object.entries(MONTH_INDEX)) {
      if (key.includes(name)) return num;
    }
    return '';
  }

  function looksLikePdfUrl(url) {
    return /\.pdf(?:$|[?#])/i.test(url) || /\/contenu\/telechargement\//i.test(url) || /\/file\//i.test(url);
  }

  function normalizeUrl(url) { return String(url || '').trim().replace(/\/$/, ''); }
  function absoluteUrl(href, baseUrl) { try { return new URL(href, baseUrl).toString(); } catch { return null; } }
  function normalizeSpace(s) { return String(s || '').replace(/\s+/g, ' ').trim(); }
  function uniqueByUrl(items) { const seen = new Set(); return items.filter(item => item?.url && !seen.has(item.url) && seen.add(item.url)); }
  function sanitizeFilename(name) { return String(name || 'document.pdf').replace(/[\\/:*?"<>|]+/g, '_'); }
  function inferFilenameFromUrl(url, fallback = 'document.pdf') {
    try {
      const pathname = new URL(url).pathname;
      const candidate = decodeURIComponent(pathname.split('/').pop() || fallback).replace(/\+/g, ' ');
      return /\.pdf$/i.test(candidate) ? candidate : `${candidate}.pdf`;
    } catch { return fallback; }
  }
  function buildDownloadPath(doc) { return `RAA/${sanitizeFilename(doc.year)}/${sanitizeFilename(doc.month)}/${sanitizeFilename(doc.filename)}`; }
  function escapeRegex(s) { return String(s).replace(/[.*+?^${}()|[\]\\]/g, '\\$&'); }
  function escapeHtml(s){return String(s).replace(/[&<>"']/g,m=>({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"}[m]))}
  function escapeAttr(s){return escapeHtml(s)}

  function log(els, message, cls = 'ok') {
    const entry = { ts: new Date().toISOString(), cls, message };
    state.logs.unshift(entry);
    if (els?.log) {
      const line = document.createElement('div');
      line.className = cls;
      line.textContent = formatLogLine(entry);
      els.log.prepend(line);
    }
    updateAll(els);
  }

  function formatLogLine(entry) {
    const time = new Date(entry.ts).toLocaleTimeString('fr-FR');
    return `[${time}] ${entry.message}`;
  }

  function exportLogs(els) {
    const payload = {
      exportedAt: new Date().toISOString(),
      page: location.href,
      state: {
        rootUrl: state.rootUrl,
        selectedYear: state.selectedYear,
        selectedMonthKeys: Array.from(state.selectedMonthKeys),
        requestCount: state.requestCount,
        downloadedCount: state.downloadedCount,
      },
      years: state.years,
      months: state.months,
      logs: state.logs,
    };
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `raa-strict-debug-${Date.now()}.json`;
    a.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
    log(els, 'Export JSON généré.', 'ok');
  }
})();
