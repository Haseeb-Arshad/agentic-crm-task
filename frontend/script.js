const urlParams = new URLSearchParams(window.location.search);
const apiBase =
  urlParams.get("api") ||
  window.API_BASE_URL ||
  "http://localhost:8000";

const transcript = document.getElementById("transcript");
const form = document.getElementById("promptForm");
const input = document.getElementById("promptInput");
const sendButton = document.getElementById("sendButton");
const statusText = document.getElementById("statusText");
const presets = document.getElementById("presets");

const autoResize = () => {
  input.style.height = "auto";
  const next = Math.min(input.scrollHeight, 260);
  input.style.height = `${next}px`;
};

const scrollTranscript = () => {
  transcript.scrollTop = transcript.scrollHeight;
};

const renderBubble = (text, role) => {
  const wrapper = document.createElement("div");
  wrapper.className = `bubble bubble-${role}`;

  const paragraphs = text.split("\n").filter(Boolean);
  paragraphs.forEach((para) => {
    const p = document.createElement("p");
    p.textContent = para;
    wrapper.appendChild(p);
  });

  transcript.appendChild(wrapper);
  scrollTranscript();
};

const setStatus = (message, tone = "muted") => {
  statusText.textContent = message;
  statusText.dataset.tone = tone;
};

const runPrompt = async (prompt) => {
  const payload = { prompt };

  try {
    const response = await fetch(`${apiBase}/run`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      let detail = "Request failed.";
      try {
        const data = await response.json();
        detail = data.detail || data.error || detail;
      } catch (_) {
        // ignore JSON parse errors
      }
      const message = `HTTP ${response.status}: ${detail}`;
      throw new Error(message);
    }

    const json = await response.json();
    return json.output ?? "Done.";
  } catch (error) {
    const message =
      error instanceof Error ? error.message : "Unable to reach the backend.";
    if (message.startsWith("TypeError") || message.includes("Failed to fetch")) {
      throw new Error(`Unable to reach the backend at ${apiBase}. Is it running?`);
    }
    throw new Error(message);
  }
};

const processPrompt = async (prompt) => {
  if (!prompt) {
    return;
  }

  renderBubble(prompt, "user");
  input.value = "";
  sendButton.disabled = true;
  setStatus("Working...", "info");
  autoResize();

  try {
    const output = await runPrompt(prompt);
    renderBubble(output, "assistant");
    setStatus("Done", "success");
  } catch (error) {
    console.error(error);
    renderBubble(error.message, "assistant");
    setStatus("Error", "error");
  } finally {
    sendButton.disabled = false;
    input.focus();
  }
};

form.addEventListener("submit", (event) => {
  event.preventDefault();
  void processPrompt(input.value.trim());
});

input.addEventListener("input", () => {
  sendButton.disabled = input.value.trim().length === 0;
  setStatus("");
  autoResize();
});

presets.addEventListener("click", (event) => {
  const button = event.target.closest("button[data-prompt]");
  if (!button) {
    return;
  }
  const prompt = button.getAttribute("data-prompt");
  input.value = prompt;
  sendButton.disabled = false;
  autoResize();
  void processPrompt(prompt.trim());
});

// enable immediate focus
window.addEventListener("load", () => {
  sendButton.disabled = true;
  autoResize();
  input.focus();
});
