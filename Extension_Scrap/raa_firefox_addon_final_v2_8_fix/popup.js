async function openDashboard() {
  const tabs = await browser.tabs.query({ active: true, currentWindow: true });
  const activeUrl = tabs?.[0]?.url || "";
  const dashboardUrl = new URL(browser.runtime.getURL("dashboard.html"));
  if (activeUrl.startsWith("http://") || activeUrl.startsWith("https://")) {
    dashboardUrl.searchParams.set("url", activeUrl);
  }
  await browser.tabs.create({ url: dashboardUrl.toString() });
  window.close();
}

document.getElementById("open-dashboard").addEventListener("click", () => {
  openDashboard().catch((error) => {
    console.error(error);
    alert(`Impossible d'ouvrir le tableau de bord : ${error.message}`);
  });
});
