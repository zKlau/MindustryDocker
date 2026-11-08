let active = false;

export function setPollingActive(value) {
  active = value;
}

export function every(milliseconds, callback) {
  setInterval(() => {
    if (active && !document.hidden) {
      callback();
    }
  }, milliseconds);
}
