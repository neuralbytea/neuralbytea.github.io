(function () {
  var d = document, de = d.documentElement;
  de.classList.add('js');

  // mobile menu
  var burger = d.querySelector('.burger');
  if (burger) burger.addEventListener('click', function () { d.body.classList.toggle('menu-open'); });

  // scroll reveal
  var els = [].slice.call(d.querySelectorAll('.reveal'));
  if ('IntersectionObserver' in window) {
    var io = new IntersectionObserver(function (es) {
      es.forEach(function (x) { if (x.isIntersecting) { x.target.classList.add('in'); io.unobserve(x.target); } });
    }, { threshold: 0.1 });
    els.forEach(function (n, i) { n.style.setProperty('--d', (i % 6) * 60 + 'ms'); io.observe(n); });
  } else els.forEach(function (n) { n.classList.add('in'); });

  // apps filter + search (progressive enhancement; the full list is already in the HTML)
  var grid = d.getElementById('app-grid');
  if (grid) {
    var cards = [].slice.call(grid.children), q = d.getElementById('q'), none = d.getElementById('none');
    var chips = [].slice.call(d.querySelectorAll('.fchip:not(.vchip)')), vchips = [].slice.call(d.querySelectorAll('.vchip'));
    var line = 'all', ver = 'all';
    var apply = function () {
      var t = q.value.trim().toLowerCase(), n = 0;
      cards.forEach(function (c) {
        var ok = (line === 'all' || c.dataset.line === line) &&
                 (ver === 'all' || (' ' + c.dataset.ver + ' ').indexOf(' ' + ver + ' ') > -1) &&
                 (!t || c.dataset.q.indexOf(t) > -1);
        c.hidden = !ok; if (ok) { n++; c.classList.add('in'); }
      });
      none.hidden = n > 0;
    };
    var setLine = function (l) { line = l; chips.forEach(function (c) { c.classList.toggle('on', c.dataset.line === l); }); apply(); };
    var setVer = function (v) { ver = v; vchips.forEach(function (c) { c.classList.toggle('on', c.dataset.ver === v); }); apply(); };
    chips.forEach(function (c) { c.addEventListener('click', function () { setLine(c.dataset.line); }); });
    vchips.forEach(function (c) { c.addEventListener('click', function () { setVer(c.dataset.ver); }); });
    q.addEventListener('input', apply);
    var P = new URLSearchParams(location.search);
    if (P.get('line')) setLine(P.get('line'));
    if (P.get('v')) setVer(P.get('v'));
  }

  // contact form: prefill subject, send via fetch
  var f = d.querySelector('form.form');
  if (f) {
    var s = new URLSearchParams(location.search).get('subject');
    if (s) d.getElementById('subject').value = 'Question about ' + s;
    f.addEventListener('submit', function (ev) {
      ev.preventDefault();
      var st = d.getElementById('status'), b = f.querySelector('button'); b.disabled = true; st.textContent = 'Sending…';
      fetch(f.action, { method: 'POST', body: new FormData(f), headers: { Accept: 'application/json' } })
        .then(function (r) { if (!r.ok) throw 0; f.reset(); st.textContent = 'Thanks, we will reply by email soon.'; st.className = 'status ok'; })
        .catch(function () { st.textContent = 'Could not send. Please email us directly.'; st.className = 'status err'; })
        .then(function () { b.disabled = false; });
    });
  }
})();
