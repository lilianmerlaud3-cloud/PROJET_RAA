browser.action.onClicked.addListener(async (tab) => {
  if (!tab.id) return;
  try {
    await browser.tabs.sendMessage(tab.id, { type: 'RAA_TOGGLE_PANEL' });
  } catch (error) {
    console.error("Impossible d'ouvrir le panneau", error);
  }
});

browser.runtime.onMessage.addListener((message) => {
  if (message?.type !== 'RAA_DOWNLOAD_FILE') return undefined;

  return browser.downloads.download({
    url: message.url,
    filename: message.filename,
    conflictAction: 'uniquify',
    saveAs: false,
  }).then((downloadId) => ({
    ok: true,
    downloadId,
  })).catch((error) => ({
    ok: false,
    error: error?.message || String(error),
  }));
});
