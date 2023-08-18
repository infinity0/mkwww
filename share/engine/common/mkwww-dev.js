let mkwD_autoRefreshTimer = null;

function mkwD_autoRefresh(_) {
  // read intended behaviour from storage
  let refresh = false;
  if (sessionStorage.getItem("mkwD_autoRefresh") == "1") {
    refresh = true;
  }

  // set actual refresh based on intended behaviour
  if (mkwD_autoRefreshTimer) {
    clearTimeout(mkwD_autoRefreshTimer);
    mkwD_autoRefreshTimer = null;
  }
  if (refresh) {
    // javascript reload preserves document.location.hash, meta http-equiv doesn't
    mkwD_autoRefreshTimer = setTimeout(() => document.location.reload(), 4000);
  }

  // set UI to match
  let autoRef = document.getElementById("dev-auto-refresh");
  autoRef.firstChild.nodeValue = refresh? "ON": "OFF";
  let toggle = refresh? "0": "1";
  autoRef.href = `javascript:sessionStorage.setItem("mkwD_autoRefresh","${toggle}");window.mkwD_autoRefresh();`;
}

window.addEventListener("DOMContentLoaded", (_) => {
  mkwD_autoRefresh();
  document.getElementById("dev-settings-clear").href = `javascript:sessionStorage.clear();document.location.reload();`;
});
