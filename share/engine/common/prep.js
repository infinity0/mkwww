let mkw_keyShifted = false;
function mkw_keyShift(e) {
  mkw_keyShifted = e.shiftKey;
  return true;
}

function mkw_main(el) {
  let main = el.parentNode;
  while (main !== null && main !== document) {
    if (Array.from(main.classList).some(x => x.startsWith("main-"))) {
      break;
    }
    main = main.parentNode;
  }
  return (main === document)? null: main;
}

document.addEventListener('keyup', mkw_keyShift);
document.addEventListener('keydown', mkw_keyShift);
