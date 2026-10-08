/* NeuralBytea chat widget. Talks to the chat proxy (worker/); the AI key is never in this file.
   It only appears when the site was built with a chat endpoint (window.NB_CHAT). */
(function () {
  var cfg = window.NB_CHAT;
  if (!cfg || !(cfg.endpoint || (cfg.mode === 'direct' && cfg.k))) return;
  var d = document, KEY = 'nb_chat_v1', MAX_KEEP = 12;
  var reduce = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;
  var site = (cfg.site || location.origin).replace(/\/$/, '');
  var rootPath = (function () { var s = d.querySelector('script[src*="assets/chat.js"]'); return s ? s.getAttribute('src').replace('assets/chat.js', '') : ''; })();

  var GREETING = 'Hi! I can answer questions about our Odoo apps, versions and prices, or help you scope a custom module. What do you need?';
  var CHIPS = ['What apps do you have?', 'Is there a free app?', 'Which apps work on Odoo 17?', 'I need a custom module'];
  var history = [];
  try { history = JSON.parse(sessionStorage.getItem(KEY) || '[]').filter(function (m) { return m && typeof m.content === 'string' && (m.role === 'user' || m.role === 'assistant'); }); } catch (e) {}
  var busy = false;

  var esc = function (s) { return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;'); };
  var safeUrl = function (u) {
    u = u.trim();
    if (u.indexOf(site) === 0 || u.indexOf('https://apps.odoo.com/') === 0 || /^\/(?!\/)/.test(u)) return u;
    return null;
  };
  var inline = function (t) {
    t = esc(t);
    t = t.replace(/\[([^\]]+)\]\(([^)\s]+)\)/g, function (m, label, url) {
      var u = safeUrl(url.replace(/&amp;/g, '&'));
      return u ? '<a href="' + esc(u) + '"' + (u.indexOf(site) === 0 || u.charAt(0) === '/' ? '' : ' target="_blank" rel="noopener"') + '>' + label + '</a>' : label;
    });
    t = t.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
    return t;
  };
  // Small, safe markdown subset: paragraphs, bullet/numbered lists, tables, bold, allowed links.
  var render = function (src) {
    var lines = String(src).replace(/\r/g, '').split('\n'), out = '', list = null, tbl = [];
    var closeList = function () { if (list) { out += '</' + list + '>'; list = null; } };
    var flushTbl = function () {
      if (!tbl.length) return;
      var rows = tbl.filter(function (r) { return !/^\s*\|?[\s:|-]+\|?\s*$/.test(r); }).map(function (r) { return r.replace(/^\s*\||\|\s*$/g, '').split('|'); });
      out += '<div class="nbc-tw"><table>' + rows.map(function (r, i) { var tag = i === 0 ? 'th' : 'td'; return '<tr>' + r.map(function (c) { return '<' + tag + '>' + inline(c.trim()) + '</' + tag + '>'; }).join('') + '</tr>'; }).join('') + '</table></div>';
      tbl = [];
    };
    lines.forEach(function (ln) {
      if (/^\s*\|/.test(ln)) { closeList(); tbl.push(ln); return; }
      flushTbl();
      var b = ln.match(/^\s*[-*•]\s+(.*)/), n = ln.match(/^\s*\d+[.)]\s+(.*)/);
      if (b || n) { var tag = b ? 'ul' : 'ol'; if (list !== tag) { closeList(); out += '<' + tag + '>'; list = tag; } out += '<li>' + inline((b || n)[1]) + '</li>'; return; }
      closeList();
      if (ln.trim()) out += '<p>' + inline(ln) + '</p>';
    });
    flushTbl(); closeList();
    return out;
  };

  // ---- DOM
  var root = d.createElement('div'); root.className = 'nbc';
  root.innerHTML =
    '<button class="nbc-fab" type="button" aria-label="Open chat assistant" aria-expanded="false"><svg viewBox="0 0 24 24" width="26" height="26" aria-hidden="true"><path fill="currentColor" d="M4 4h16a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2H9l-5 4v-4H4a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2z"/></svg><span>Ask us</span></button>' +
    '<section class="nbc-panel" role="dialog" aria-label="NeuralBytea assistant" hidden>' +
    '<header><img src="' + esc(rootPath) + 'images/mark-512.png" alt="" width="34" height="34"><div><b>NeuralBytea Assistant</b><small>Ask about our apps or custom work</small></div>' +
    '<button type="button" class="nbc-new" title="Start a new chat" aria-label="Start a new chat">↺</button><button type="button" class="nbc-x" aria-label="Close chat">×</button></header>' +
    '<div class="nbc-log" role="log" aria-live="polite"></div>' +
    '<div class="nbc-chips"></div>' +
    '<form class="nbc-form"><textarea rows="1" maxlength="500" placeholder="Type your question…" aria-label="Your question"></textarea><button type="submit" aria-label="Send"><svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true"><path fill="currentColor" d="M3 20.5v-6l9-2.5-9-2.5v-6L22 12z"/></svg></button></form>' +
    '<p class="nbc-note">AI answers can be wrong: check the app page or the Odoo store. Please do not share passwords or private data.</p></section>';
  d.body.appendChild(root);
  var $ = function (s) { return root.querySelector(s); };
  var fab = $('.nbc-fab'), panel = $('.nbc-panel'), log = $('.nbc-log'), chips = $('.nbc-chips'), form = $('.nbc-form'), ta = form.querySelector('textarea');

  var save = function () { try { sessionStorage.setItem(KEY, JSON.stringify(history.slice(-MAX_KEEP))); } catch (e) {} };
  var scroll = function () { log.scrollTop = log.scrollHeight; };
  var bubble = function (role, html) { var el = d.createElement('div'); el.className = 'nbc-m nbc-' + role; el.innerHTML = html; log.appendChild(el); scroll(); return el; };
  var drawAll = function () {
    log.innerHTML = '';
    bubble('bot', render(GREETING));
    history.forEach(function (m) { bubble(m.role === 'user' ? 'me' : 'bot', m.role === 'user' ? '<p>' + esc(m.content) + '</p>' : render(m.content)); });
    chips.hidden = history.length > 0;
  };
  chips.innerHTML = CHIPS.map(function (c) { return '<button type="button">' + esc(c) + '</button>'; }).join('');

  var open = function (on) {
    panel.hidden = !on; fab.setAttribute('aria-expanded', on ? 'true' : 'false'); root.classList.toggle('open', on);
    if (on) { drawAll(); setTimeout(function () { ta.focus(); }, reduce ? 0 : 150); } else fab.focus();
  };
  fab.addEventListener('click', function () { open(panel.hidden); });
  $('.nbc-x').addEventListener('click', function () { open(false); });
  d.addEventListener('keydown', function (e) { if (e.key === 'Escape' && !panel.hidden) open(false); });
  $('.nbc-new').addEventListener('click', function () { history = []; save(); drawAll(); });
  chips.addEventListener('click', function (e) { if (e.target.tagName === 'BUTTON') send(e.target.textContent); });

  var fail = function (html) { bubble('bot nbc-err', html); };
  // Two transports with the same result shape {status, j:{reply, retry_after}}:
  //  - proxy: our Cloudflare Worker holds the key (recommended)
  //  - direct: GitHub-Pages-only; the key was injected at build time from a CI secret (camouflaged, not secret)
  var brain = null, lastCall = 0;
  var groqKey = function () { try { return atob(cfg.k.join('')).split('').reverse().join(''); } catch (e) { return ''; } };
  var ask = function (msgs, signal) {
    if (!cfg.endpoint) {
      var wait = 3000 - (Date.now() - lastCall);
      if (wait > 0) return Promise.resolve({ status: 429, j: { retry_after: Math.ceil(wait / 1000) } });
      lastCall = Date.now();
      brain = brain || import('./chat/prompt.js');
      return brain.then(function (m) {
        var clean = msgs.map(function (x) { return { role: x.role, content: String(x.content).slice(0, 600) }; });
        return fetch('https://api.groq.com/openai/v1/chat/completions', { method: 'POST', signal: signal,
          headers: { authorization: 'Bearer ' + groqKey(), 'content-type': 'application/json' }, body: JSON.stringify(m.groqBody(clean, cfg.model)) })
          .then(function (r) {
            return r.json().catch(function () { return {}; }).then(function (j) {
              var text = j && j.choices && j.choices[0] && j.choices[0].message && j.choices[0].message.content;
              return { status: r.status === 200 && !text ? 502 : r.status, j: { reply: text ? String(text).replace(/gsk_[A-Za-z0-9]+/g, '[removed]').trim().slice(0, 2500) : '', retry_after: Math.min(60, Math.ceil(parseFloat(r.headers.get('retry-after')) || 20)) } };
            });
          });
      });
    }
    return fetch(cfg.endpoint, { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ messages: msgs }), signal: signal })
      .then(function (r) { return r.json().catch(function () { return {}; }).then(function (j) { return { status: r.status, j: j }; }); });
  };
  var contactLink = '<a href="' + esc(rootPath) + 'contact/">contact form</a>';
  var send = function (text) {
    text = String(text || '').trim().slice(0, 500);
    if (!text || busy) return;
    busy = true; form.classList.add('busy'); chips.hidden = true;
    history.push({ role: 'user', content: text }); save();
    bubble('me', '<p>' + esc(text) + '</p>');
    var typing = bubble('bot nbc-typing', '<span></span><span></span><span></span>');
    var ctl = new AbortController(), to = setTimeout(function () { ctl.abort(); }, 35000);
    ask(history.slice(-5), ctl.signal)
      .then(function (x) {
        typing.remove();
        if (x.status === 200 && x.j.reply) { history.push({ role: 'assistant', content: x.j.reply }); save(); bubble('bot', render(x.j.reply)); }
        else if (x.status === 429) { history.pop(); save(); fail('<p>I am getting a lot of questions right now. Please try again in a minute' + (x.j.retry_after ? ' (about ' + x.j.retry_after + 's)' : '') + ', or use the ' + contactLink + '.</p>'); }
        else { history.pop(); save(); fail('<p>Sorry, the assistant is not available right now. Please use the ' + contactLink + ' or email us.</p>'); }
      })
      .catch(function () { typing.remove(); history.pop(); save(); fail('<p>I could not reach the assistant. Please check your connection, or use the ' + contactLink + '.</p>'); })
      .then(function () { clearTimeout(to); busy = false; form.classList.remove('busy'); ta.focus(); });
  };
  // Public hooks so any button on the page can open the chat (optionally with a question)
  window.NBChat = { open: function (q) { if (panel.hidden) open(true); hideTeaser(true); if (q) setTimeout(function () { send(q); }, 350); } };
  d.addEventListener('click', function (e) {
    var el = e.target.closest && e.target.closest('[data-nbc-open],[data-nbc-ask]');
    if (!el) return;
    e.preventDefault(); d.body.classList.remove('menu-open');
    window.NBChat.open(el.getAttribute('data-nbc-ask') || '');
  });
  // Greeting pop-up next to the bubble (once per tab session, dismissible)
  var teaser = d.createElement('div'); teaser.className = 'nbc-teaser'; teaser.hidden = true;
  teaser.innerHTML = '<button type="button" class="nbc-tx" aria-label="Dismiss">×</button><p><b>Hi! 👋</b> Ask me about our Odoo apps, prices or custom work.</p>';
  root.insertBefore(teaser, fab);
  function hideTeaser(remember) { teaser.hidden = true; if (remember) try { sessionStorage.setItem('nb_chat_teaser', '1'); } catch (e) {} }
  teaser.querySelector('.nbc-tx').addEventListener('click', function (e) { e.stopPropagation(); hideTeaser(true); });
  teaser.querySelector('p').addEventListener('click', function () { window.NBChat.open(''); });
  var seen = false; try { seen = sessionStorage.getItem('nb_chat_teaser') === '1'; } catch (e) {}
  if (!seen && !history.length) setTimeout(function () { if (panel.hidden) teaser.hidden = false; }, reduce ? 800 : 3500);
  fab.addEventListener('click', function () { hideTeaser(true); });
  form.addEventListener('submit', function (e) { e.preventDefault(); var t = ta.value; ta.value = ''; ta.style.height = ''; send(t); });
  ta.addEventListener('keydown', function (e) { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); form.requestSubmit(); } });
  ta.addEventListener('input', function () { ta.style.height = 'auto'; ta.style.height = Math.min(ta.scrollHeight, 110) + 'px'; });
})();
