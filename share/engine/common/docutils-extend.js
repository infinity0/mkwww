function mkw_dtlistStorageId(el) {
  return "mkw_dtlist_" + mkw_main(el).id + "_" + el.id;
}

function mkw_dtlistWrite(el, open) {
  if (open !== undefined) {
    el.open = open;
  }
  sessionStorage.setItem(mkw_dtlistStorageId(el), el.open ? "1": "0");
}

function mkw_dtlistRead(el) {
  switch (sessionStorage.getItem(mkw_dtlistStorageId(el))) {
    case null: break;
    case "1": el.open = true; break;
    case "0": el.open = false; break;
  }
}

function mkw_dtlistOpen(id) {
  if (id === undefined || id.constructor.name == "HashChangeEvent") {
    id = document.location.hash.substring(1);
    if (!id) return;
  }
  let el = document.getElementById(id);
  let anc = el;
  while (anc !== null && anc !== document) {
    if (anc.tagName == "DETAILS" && anc.parentNode.classList.contains("dtlist")) {
      mkw_dtlistWrite(anc, true);
    }
    anc = anc.parentNode;
  }
  el.scrollIntoView();
}

function mkw_dtlistTooltip(el, tl) {
  if (el.open) {
    tl.setAttribute("title", "shift-click to close all subchildren too");
  } else {
    tl.setAttribute("title", "shift-click to open all subchildren too");
  }
}

window.addEventListener("hashchange", mkw_dtlistOpen);
window.addEventListener("DOMContentLoaded", (_) => {
  for (let el of document.querySelectorAll(".dtlist details")) {
    // sync "open" states with sessionStorage
    mkw_dtlistRead(el);
    el.addEventListener("toggle", (e) => {
      mkw_dtlistWrite(el);
      return true;
    });

    // shift-click behaviour and its tooltip
    let tl = el.querySelector(".dtlist-tooltip");
    mkw_dtlistTooltip(el, tl);
    el.addEventListener("toggle", (e) => {
      if (mkw_keyShifted) {
        for (let elch of el.querySelectorAll(".dtlist details")) {
          mkw_dtlistWrite(elch, el.open);
        }
      }
      mkw_dtlistTooltip(el, tl);
      return true;
    });
  }

  mkw_dtlistOpen(); // this must run after sync code, otherwise scroll gets lost
});
