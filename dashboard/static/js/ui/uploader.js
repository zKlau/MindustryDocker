import { whileDisabled } from "./dom.js";
import { run, toast } from "./toast.js";

export function setupUploader(fileInput, button, send, onDone) {
  button.addEventListener("click", async () => {
    const file = fileInput.files[0];
    if (!file) {
      toast("Choose a file first", true);

      return;
    }
    const ok = await whileDisabled([button], () => run(send(file), "Uploaded"));
    if (ok) {
      fileInput.value = "";
      onDone();
    }
  });
}
