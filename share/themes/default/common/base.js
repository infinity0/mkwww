/// Automatically show/hide the navbar based on the viewport width, and
/// persist it across different page visits.

// Our navbar has manual show/hide in CSS-only, auto-show/hide requires JS.
// Another option is the converse; however in that case small screens would
// require JS to show the navbar, so we felt this approach is better.

function mkwT_writeNavBar(v) {
  sessionStorage.setItem("mkwT_navBar", v);
  sessionStorage.setItem("mkwT_navBarRW", document.body.clientWidth);
}

let mkwT_navBarWidth = null;
window.addEventListener("DOMContentLoaded", (_) => {
  let styles = window.getComputedStyle(document.querySelector("#sitenav nav"));
  mkwT_navBarWidth = parseInt(styles.width.replace(/px$/, ""));
});
function mkwT_autoNavBar(e) {
  let savedWidth = sessionStorage.getItem("mkwT_navBarRW");
  if (Math.abs(parseInt(savedWidth) - document.body.clientWidth) < 16) {
    // mobile browsers fire spurious resize events sometimes
    return true;
  }
  let navBar = document.querySelector("#sitenav .navbar");
  if (document.body.clientWidth < 3 * mkwT_navBarWidth) {
    navBar.removeAttribute("open");
    mkwT_writeNavBar("0");
  } else {
    navBar.setAttribute("open", "");
    mkwT_writeNavBar("1");
  }
}

function mkwT_readNavBar() {
  let navBar = document.querySelector("#sitenav .navbar");
  switch (sessionStorage.getItem("mkwT_navBar")) {
    case null: mkwT_autoNavBar(); break;
    case "1": navBar.setAttribute("open", ""); break;
    case "0": navBar.removeAttribute("open"); break;
  }
  navBar.addEventListener("toggle", (e) => {
    mkwT_writeNavBar(navBar.open? "1": "0");
  });
}

let mkwT_autoNavBarTimer = null;
function mkwT_autoNavBarTimeout(e) {
  if (mkwT_autoNavBarTimer) {
    window.clearTimeout(mkwT_autoNavBarTimer);
    mkwT_autoNavBarTimer = null;
  }
  mkwT_autoNavBarTimer = window.setTimeout(() => mkwT_autoNavBar(e), 16);
}

window.addEventListener("DOMContentLoaded", mkwT_readNavBar);
window.addEventListener("resize", mkwT_autoNavBarTimeout);
