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
  if (!el) return;
  let anc = el;
  while (anc !== null && anc !== document) {
    if (anc.tagName == "DETAILS" && anc.parentNode.classList.contains("dtlist")) {
      mkw_dtlistWrite(anc, true);
    }
    anc = anc.parentNode;
  }
  el.scrollIntoView();
}

function mkw_dtlistControl(el, tl) {
  let stats = tl.firstChild.nodeValue.split("|");
  // this terminology is more precise than "show" vs "hide":
  // e.g. both "close" actions visually hide all layers below, but
  // non-shift-close can leave some grandchildren "open" yet hidden.
  // e.g. non-shift-open can visually show more than just the next layer, if
  // some grandchildren were previously left "open" yet hidden.
  let cmd = (el.open)? "close": "open";
  let title = `click to ${cmd} the next layer, ~${stats[0]} words`;
  if (stats.length > 1) {
    title += `\nshift-click to ${cmd} all layers below, ~${stats[1]} words`;
  }
  tl.setAttribute("title", title);
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
    let tl = el.querySelector(".dtlist-ctl");
    if (tl === null) continue; // empty details don't have a ctl
    mkw_dtlistControl(el, tl);
    el.addEventListener("toggle", (e) => {
      if (mkw_keyShifted) {
        for (let elch of el.querySelectorAll(".dtlist details")) {
          mkw_dtlistWrite(elch, el.open);
        }
      }
      mkw_dtlistControl(el, tl);
      return true;
    });
  }

  mkw_dtlistOpen(); // this must run after sync code, otherwise scroll gets lost
});
