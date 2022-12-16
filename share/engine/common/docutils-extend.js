function mkw_dtlistTooltip(el, tl) {
  if (el.open) {
    tl.setAttribute("title", "shift-click to close all subchildren too");
  } else {
    tl.setAttribute("title", "shift-click to open all subchildren too");
  }
}

window.addEventListener("DOMContentLoaded", (_) => {
  for (let el of document.querySelectorAll(".dtlist details")) {
    let tl = el.querySelector(".dtlist-tooltip");
    el.addEventListener("toggle", (e) => {
      if (mkw_keyShifted) {
        for (let elch of el.querySelectorAll(".dtlist details")) {
          elch.open = el.open;
        }
      }
      mkw_dtlistTooltip(el, tl);
      return true;
    });
    mkw_dtlistTooltip(el, tl);
  }
});
