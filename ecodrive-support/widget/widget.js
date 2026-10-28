/* ECODRIVE — чат-виджет онлайн-консультанта. Подключается одной строкой:
   <script src="https://chat.<домен>/widget.js" async></script> */
(function () {
  "use strict";
  if (window.EcodriveChat) return;

  var BASE = "__BASE_URL__";
  if (BASE.indexOf("__") === 0) {
    var script = document.currentScript;
    BASE = script && script.src ? new URL(script.src).origin : "";
  }
  var BOT_NAME = "__BOT_NAME__";
  if (BOT_NAME.indexOf("__") === 0) BOT_NAME = "Консультант";

  var isRu =
    (document.documentElement.lang || "").toLowerCase().indexOf("ru") === 0 ||
    location.pathname.indexOf("/ru/") === 0;
  var LANG = isRu ? "ru" : "uk";
  var T = {
    uk: {
      title: BOT_NAME + " · ECODRIVE",
      status: "онлайн",
      greeting:
        "Вітаю! Я " + BOT_NAME + ", консультант ECODRIVE. Допоможу знайти посилку, підкажу по авто, " +
        "запчастинах чи аксесуарах. Чим можу допомогти?",
      placeholder: "Напишіть повідомлення…",
      send: "Надіслати",
      open: "Написати нам",
      close: "Згорнути",
      manager: "Діалог передано менеджеру. Відповідь зʼявиться тут.",
      error: "Не вдалося надіслати. Спробуйте ще раз."
    },
    ru: {
      title: BOT_NAME + " · ECODRIVE",
      status: "онлайн",
      greeting:
        "Здравствуйте! Я " + BOT_NAME + ", консультант ECODRIVE. Помогу найти посылку, подскажу по авто, " +
        "запчастям или аксессуарам. Чем могу помочь?",
      placeholder: "Напишите сообщение…",
      send: "Отправить",
      open: "Написать нам",
      close: "Свернуть",
      manager: "Диалог передан менеджеру. Ответ появится здесь.",
      error: "Не удалось отправить. Попробуйте ещё раз."
    }
  }[LANG];

  var STORAGE_KEY = "ecodrive_chat";
  var state = { session: null, lastId: 0, open: false, handedOff: false, history: [] };
  try {
    var saved = JSON.parse(localStorage.getItem(STORAGE_KEY) || "null");
    if (saved && typeof saved === "object") {
      state.session = saved.session || null;
      state.lastId = saved.lastId || 0;
      state.handedOff = !!saved.handedOff;
      state.history = Array.isArray(saved.history) ? saved.history.slice(-40) : [];
    }
  } catch (e) { /* localStorage недоступен — работаем без памяти */ }

  function persist() {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify({
        session: state.session, lastId: state.lastId, handedOff: state.handedOff,
        history: state.history.slice(-40)
      }));
    } catch (e) { /* ignore */ }
  }

  var css =
    ".ecd-launcher{position:fixed;right:24px;bottom:24px;z-index:2147483000;width:60px;height:60px;border-radius:30px;" +
    "border:0;background:#1F7A5A;color:#fff;box-shadow:0 8px 24px rgba(15,61,46,.35);cursor:pointer;display:flex;" +
    "align-items:center;justify-content:center;transition:transform .15s}" +
    ".ecd-launcher:hover{transform:scale(1.05)}.ecd-launcher svg{width:28px;height:28px}" +
    ".ecd-badge{position:absolute;top:-4px;right:-4px;min-width:20px;height:20px;border-radius:10px;background:#E5484D;" +
    "color:#fff;font:600 12px/20px system-ui,sans-serif;text-align:center;padding:0 5px;display:none}" +
    ".ecd-panel{position:fixed;right:24px;bottom:96px;z-index:2147483000;width:380px;max-width:calc(100vw - 32px);" +
    "height:600px;max-height:calc(100vh - 120px);background:#fff;border-radius:20px;box-shadow:0 24px 64px rgba(15,61,46,.25);" +
    "display:none;flex-direction:column;overflow:hidden;font-family:system-ui,-apple-system,'Segoe UI',Roboto,sans-serif}" +
    ".ecd-panel.ecd-open{display:flex}" +
    ".ecd-head{background:#0F3D2E;color:#F4F7F2;padding:16px 20px;display:flex;align-items:center;gap:12px}" +
    ".ecd-dot{width:10px;height:10px;border-radius:5px;background:#6FD39C;flex:none}" +
    ".ecd-head b{font-size:16px;font-weight:600}.ecd-head small{display:block;font-size:12px;color:#A9CBB9}" +
    ".ecd-x{margin-left:auto;background:none;border:0;color:#A9CBB9;font-size:22px;cursor:pointer;line-height:1}" +
    ".ecd-body{flex:1;overflow-y:auto;padding:16px;background:#F4F7F2;display:flex;flex-direction:column;gap:10px}" +
    ".ecd-msg{max-width:82%;padding:10px 14px;border-radius:16px;font-size:15px;line-height:1.4;white-space:pre-wrap;" +
    "word-wrap:break-word;color:#0F3D2E}" +
    ".ecd-msg a{color:#1F7A5A}" +
    ".ecd-user{align-self:flex-end;background:#CFE8D9;border-bottom-right-radius:6px}" +
    ".ecd-bot{align-self:flex-start;background:#fff;border-bottom-left-radius:6px;box-shadow:0 1px 2px rgba(0,0,0,.06)}" +
    ".ecd-mgr{align-self:flex-start;background:#FFF3C4;border-bottom-left-radius:6px}" +
    ".ecd-note{align-self:center;font-size:12px;color:#5F6F67;text-align:center}" +
    ".ecd-typing{align-self:flex-start;background:#fff;border-radius:16px;padding:12px 16px;display:flex;gap:4px;align-items:center}" +
    ".ecd-typing span{font-size:13px;color:#5F6F67;margin-left:8px}" +
    ".ecd-typing i{width:7px;height:7px;border-radius:4px;background:#9FC2B1;animation:ecd-b 1.2s infinite}" +
    ".ecd-typing i:nth-child(2){animation-delay:.2s}.ecd-typing i:nth-child(3){animation-delay:.4s}" +
    "@keyframes ecd-b{0%,60%,100%{transform:translateY(0);opacity:.5}30%{transform:translateY(-4px);opacity:1}}" +
    ".ecd-foot{display:flex;gap:8px;padding:12px;border-top:1px solid #E3EBE5;background:#fff}" +
    ".ecd-foot textarea{flex:1;resize:none;border:1px solid #D7E3D9;border-radius:12px;padding:10px 12px;font:15px/1.4 inherit;" +
    "max-height:96px;outline:none;color:#0F3D2E}.ecd-foot textarea:focus{border-color:#1F7A5A}" +
    ".ecd-send{width:44px;border:0;border-radius:12px;background:#1F7A5A;color:#fff;cursor:pointer;display:flex;" +
    "align-items:center;justify-content:center}.ecd-send:disabled{opacity:.5;cursor:default}.ecd-send svg{width:20px;height:20px}" +
    "@media (max-width:480px){.ecd-panel{right:0;bottom:0;width:100vw;max-width:100vw;height:100vh;max-height:100vh;border-radius:0}" +
    ".ecd-launcher{right:16px;bottom:16px}}";

  var style = document.createElement("style");
  style.textContent = css;
  document.head.appendChild(style);

  var ICON_CHAT = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12a8 8 0 0 1-8 8H8l-5 3 1.5-4.5A8 8 0 1 1 21 12z"/></svg>';
  var ICON_SEND = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 2 11 13"/><path d="m22 2-7 20-4-9-9-4z"/></svg>';

  var launcher = document.createElement("button");
  launcher.className = "ecd-launcher";
  launcher.type = "button";
  launcher.setAttribute("aria-label", T.open);
  launcher.innerHTML = ICON_CHAT + '<span class="ecd-badge"></span>';
  var badge = launcher.querySelector(".ecd-badge");

  var panel = document.createElement("div");
  panel.className = "ecd-panel";
  panel.setAttribute("role", "dialog");
  panel.innerHTML =
    '<div class="ecd-head"><span class="ecd-dot"></span><div><b></b><small></small></div>' +
    '<button class="ecd-x" type="button" aria-label="' + T.close + '">×</button></div>' +
    '<div class="ecd-body"></div>' +
    '<div class="ecd-foot"><textarea rows="1" placeholder="' + T.placeholder + '"></textarea>' +
    '<button class="ecd-send" type="button" aria-label="' + T.send + '">' + ICON_SEND + "</button></div>";
  panel.querySelector("b").textContent = T.title;
  panel.querySelector("small").textContent = T.status;

  var body = panel.querySelector(".ecd-body");
  var input = panel.querySelector("textarea");
  var sendBtn = panel.querySelector(".ecd-send");
  document.body.appendChild(launcher);
  document.body.appendChild(panel);

  function linkify(text) {
    var safe = text.replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
    return safe.replace(/https?:\/\/[^\s<]+[^\s<.,;:!?)]/g, function (url) {
      return '<a href="' + url + '" target="_blank" rel="noopener">' + url + "</a>";
    });
  }

  function render(role, text) {
    var el = document.createElement("div");
    if (role === "note") {
      el.className = "ecd-note";
      el.textContent = text;
    } else {
      el.className = "ecd-msg " + (role === "user" ? "ecd-user" : role === "manager" ? "ecd-mgr" : "ecd-bot");
      el.innerHTML = linkify(text);
    }
    body.appendChild(el);
    body.scrollTop = body.scrollHeight;
  }

  function addMessage(role, text) {
    render(role, text);
    state.history.push({ r: role, t: text });
    persist();
  }

  var typingEl = null;
  function showTyping(status) {
    if (!typingEl) {
      typingEl = document.createElement("div");
      typingEl.className = "ecd-typing";
      body.appendChild(typingEl);
    }
    typingEl.innerHTML = "<i></i><i></i><i></i>";
    if (status) {
      var s = document.createElement("span");
      s.textContent = status;
      typingEl.appendChild(s);
    }
    body.scrollTop = body.scrollHeight;
  }
  function hideTyping() {
    if (typingEl && typingEl.parentNode) typingEl.parentNode.removeChild(typingEl);
    typingEl = null;
  }

  function restore() {
    body.innerHTML = "";
    if (!state.history.length) {
      addMessage("assistant", T.greeting);
      return;
    }
    state.history.forEach(function (m) { render(m.r, m.t); });
  }

  function setOpen(open) {
    state.open = open;
    panel.classList.toggle("ecd-open", open);
    if (open) {
      badge.style.display = "none";
      badge.textContent = "";
      if (!body.childNodes.length) restore();
      setTimeout(function () { input.focus(); }, 50);
      poll();
    }
  }

  // Сообщения, уже показанные через send(): опрос их пропустит, а курсор lastId
  // двигает только опрос — иначе можно перескочить ответ менеджера, пришедший между опросами.
  var seen = {};
  function applyResult(data) {
    state.session = data.session_id;
    state.handedOff = !!data.handed_off;
    if (data.reply) seen[data.last_id] = true;
    persist();
  }

  // Потоковый ответ: текст появляется по мере генерации, пока работают инструменты — статус.
  function sendStream(payload) {
    if (!window.ReadableStream || !window.TextDecoder) return Promise.reject(new Error("no stream"));
    var bubble = null, acc = "", buffer = "", received = false;
    function handle(ev) {
      received = true;
      if (ev.type === "session") {
        state.session = ev.session_id;
        persist();
      } else if (ev.type === "status") {
        showTyping(ev.text);
      } else if (ev.type === "delta") {
        if (!bubble) {
          hideTyping();
          bubble = document.createElement("div");
          bubble.className = "ecd-msg ecd-bot";
          body.appendChild(bubble);
        }
        acc += ev.text;
        bubble.innerHTML = linkify(acc);
        body.scrollTop = body.scrollHeight;
      } else if (ev.type === "done") {
        hideTyping();
        applyResult(ev);
        if (ev.reply) {
          if (bubble) {
            bubble.innerHTML = linkify(ev.reply);
            state.history.push({ r: "assistant", t: ev.reply });
            persist();
          } else {
            addMessage("assistant", ev.reply);
          }
        }
        if (ev.handed_off) render("note", T.manager);
      }
    }
    return fetch(BASE + "/api/chat/stream", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: payload
    }).then(function (r) {
      if (!r.ok || !r.body) throw new Error("HTTP " + r.status);
      var reader = r.body.getReader(), decoder = new TextDecoder();
      function pump() {
        return reader.read().then(function (chunk) {
          buffer += decoder.decode(chunk.value || new Uint8Array(), { stream: !chunk.done });
          var parts = buffer.split("\n\n");
          buffer = parts.pop();
          parts.forEach(function (part) {
            var data = part.split("\n").filter(function (l) { return l.indexOf("data: ") === 0; })
              .map(function (l) { return l.slice(6); }).join("");
            if (data) handle(JSON.parse(data));
          });
          if (!chunk.done) return pump();
        });
      }
      return pump();
    }).catch(function (err) {
      err.partial = received; // уже что-то показали — повторять запрос нельзя
      throw err;
    });
  }

  function sendPlain(payload) {
    return fetch(BASE + "/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: payload
    }).then(function (r) {
      if (!r.ok) throw new Error("HTTP " + r.status);
      return r.json();
    }).then(function (data) {
      hideTyping();
      applyResult(data);
      if (data.reply) addMessage("assistant", data.reply);
      if (data.handed_off) render("note", T.manager);
    });
  }

  var sending = false;
  function send() {
    var text = input.value.trim();
    if (!text || sending) return;
    sending = true;
    sendBtn.disabled = true;
    input.value = "";
    input.style.height = "";
    addMessage("user", text);
    showTyping();
    var payload = JSON.stringify({ session_id: state.session, message: text, page_url: location.href, lang: LANG });
    sendStream(payload)
      .catch(function (err) {
        if (err && err.partial) throw err;
        return sendPlain(payload); // старый браузер или потоковый ответ не прошёл
      })
      .catch(function () {
        hideTyping();
        render("note", T.error);
      })
      .then(function () {
        sending = false;
        sendBtn.disabled = false;
        input.focus();
      });
  }

  var polling = false;
  function poll() {
    if (!state.session || polling || sending) return; // во время отправки ответ придёт потоком
    polling = true;
    fetch(BASE + "/api/chat/" + state.session + "/messages?after=" + state.lastId)
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (data) {
        if (!data) return;
        state.handedOff = !!data.handed_off;
        data.messages.forEach(function (m) {
          if (m.id <= state.lastId) return;
          state.lastId = m.id;
          if (seen[m.id]) return;
          if (!body.childNodes.length) restore();
          addMessage(m.role, m.text); // панель скрыта или нет — DOM есть всегда
          if (!state.open) {
            badge.textContent = String((parseInt(badge.textContent || "0", 10) || 0) + 1);
            badge.style.display = "block";
          }
        });
        persist();
      })
      .catch(function () { /* сеть — попробуем в следующий раз */ })
      .then(function () { polling = false; });
  }
  setInterval(function () {
    if (state.session && (state.open || state.handedOff)) poll();
  }, state.open ? 4000 : 4000);

  launcher.addEventListener("click", function () { setOpen(!state.open); });
  panel.querySelector(".ecd-x").addEventListener("click", function () { setOpen(false); });
  sendBtn.addEventListener("click", send);
  input.addEventListener("keydown", function (e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  });
  input.addEventListener("input", function () {
    input.style.height = "";
    input.style.height = Math.min(input.scrollHeight, 96) + "px";
  });

  window.EcodriveChat = { open: function () { setOpen(true); }, close: function () { setOpen(false); } };
})();
