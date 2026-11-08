export function $(selector, root = document) {
  return root.querySelector(selector);
}

export function $$(selector, root = document) {
  return [...root.querySelectorAll(selector)];
}

export function cloneTemplate(id) {
  return document.getElementById(id).content.firstElementChild.cloneNode(true);
}

export function fillText(root, values) {
  for (const [selector, text] of Object.entries(values)) {
    root.querySelector(selector).textContent = text;
  }
}

export function render(container, elements) {
  container.replaceChildren(...elements);
}

export function setStatusText(element, text) {
  element.textContent = text;
  element.hidden = !text;
}

export function setActive(elements, isActive, className = "active") {
  for (const element of elements) {
    element.classList.toggle(className, isActive(element));
  }
}

export function onClick(container, selector, handler) {
  container.addEventListener("click", (event) => {
    const target = event.target.closest(selector);
    if (target && container.contains(target)) {
      handler(target, event);
    }
  });
}

export function onAction(container, handler) {
  onClick(container, "button[data-action]", (button, event) => handler(button.dataset.action, button, event));
}

export async function whileDisabled(buttons, task) {
  for (const button of buttons) {
    button.disabled = true;
  }
  try {
    return await task();
  } finally {
    for (const button of buttons) {
      button.disabled = false;
    }
  }
}
