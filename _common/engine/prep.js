let mkw_keyShifted = false;
function mkw_keyShift(e) {
  mkw_keyShifted = e.shiftKey;
  return true;
}

document.addEventListener('keyup', mkw_keyShift);
document.addEventListener('keydown', mkw_keyShift);
