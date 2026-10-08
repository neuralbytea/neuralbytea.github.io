(function () {
  var d = document, de = d.documentElement;
  de.classList.add('js');
  var reduce = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;

  // mobile menu
  var burger = d.querySelector('.burger');
  if (burger) burger.addEventListener('click', function () { d.body.classList.toggle('menu-open'); });

  // scroll reveal
  var els = [].slice.call(d.querySelectorAll('.reveal'));
  if ('IntersectionObserver' in window) {
    var io = new IntersectionObserver(function (es) {
      es.forEach(function (x) { if (x.isIntersecting) { x.target.classList.add('in'); io.unobserve(x.target); } });
    }, { threshold: 0.08 });
    els.forEach(function (n, i) { n.style.setProperty('--d', (i % 6) * 60 + 'ms'); io.observe(n); });
  } else els.forEach(function (n) { n.classList.add('in'); });

  // carousel: arrows, dots, autoplay (pauses on hover/focus, off with reduced motion)
  [].forEach.call(d.querySelectorAll('[data-carousel]'), function (root) {
    var track = root.querySelector('.car-track'), items = [].slice.call(track.children);
    var dots = root.querySelector('.car-dots'), prev = root.querySelector('.prev'), next = root.querySelector('.next');
    var perView = function () { var w = items[0].getBoundingClientRect().width; return Math.max(1, Math.round(track.clientWidth / (w + 20))); };
    var pages = function () { return Math.max(1, Math.ceil(items.length / perView())); };
    var step = function () { return items[0].getBoundingClientRect().width + 20; };
    var current = function () { return Math.round(track.scrollLeft / (step() * perView())); };
    var go = function (p) { track.scrollTo({ left: Math.max(0, Math.min(p, pages() - 1)) * step() * perView(), behavior: reduce ? 'auto' : 'smooth' }); };
    var drawDots = function () {
      dots.innerHTML = '';
      for (var i = 0; i < pages(); i++) (function (i) {
        var b = d.createElement('button'); b.setAttribute('aria-label', 'Go to slide ' + (i + 1));
        b.addEventListener('click', function () { go(i); }); dots.appendChild(b);
      })(i);
      mark();
    };
    var mark = function () { var c = Math.min(current(), pages() - 1); [].forEach.call(dots.children, function (b, i) { b.classList.toggle('on', i === c); }); };
    prev.addEventListener('click', function () { go(current() - 1); });
    next.addEventListener('click', function () { go(current() + 1 >= pages() ? 0 : current() + 1); });
    track.addEventListener('scroll', function () { window.requestAnimationFrame(mark); }, { passive: true });
    window.addEventListener('resize', drawDots);
    drawDots();
    var timer = null, paused = false;
    var play = function () { if (reduce || timer) return; timer = setInterval(function () { if (!paused) go(current() + 1 >= pages() ? 0 : current() + 1); }, 5000); };
    root.addEventListener('mouseenter', function () { paused = true; });
    root.addEventListener('mouseleave', function () { paused = false; });
    root.addEventListener('focusin', function () { paused = true; });
    root.addEventListener('focusout', function () { paused = false; });
    play();
  });

  // apps page: search + filters + sort + pagination (the full list is already in the HTML)
  var grid = d.getElementById('app-grid');
  if (grid) {
    var PER = 6;
    var cards = [].slice.call(grid.children);
    var $ = function (id) { return d.getElementById(id); };
    var ctl = { q: $('q'), ver: $('f-ver'), line: $('f-line'), price: $('f-price'), upd: $('f-upd'), sort: $('f-sort') };
    var pager = $('pager'), none = $('none'), count = $('count'), sortnote = $('sortnote');
    var page = 1, today = new Date();
    var inPrice = function (p, k) {
      return k === 'all' || (k === 'free' && p === 0) || (k === 'lt25' && p > 0 && p < 25) || (k === '25-50' && p >= 25 && p <= 50) ||
             (k === '50-100' && p > 50 && p <= 100) || (k === 'gt100' && p > 100);
    };
    var cmp = {
      top: function (a, b) { return a.rank - b.rank; },
      latest: function (a, b) { return b.upd - a.upd || a.rank - b.rank; },
      'price-asc': function (a, b) { return a.price - b.price || a.rank - b.rank; },
      'price-desc': function (a, b) { return b.price - a.price || a.rank - b.rank; },
      name: function (a, b) { return a.name < b.name ? -1 : a.name > b.name ? 1 : 0; }
    };
    var notes = { top: 'Top picks come first', latest: 'Most recently updated first', 'price-asc': 'Cheapest first', 'price-desc': 'Most expensive first', name: 'Alphabetical' };
    var rows = cards.map(function (c) {
      return { el: c, rank: +c.dataset.rank, price: +c.dataset.price, upd: new Date(c.dataset.updated).getTime(), name: c.dataset.name };
    });
    var draw = function () {
      var t = ctl.q.value.trim().toLowerCase(), v = ctl.ver.value, l = ctl.line.value, pk = ctl.price.value, u = ctl.upd.value;
      var list = rows.filter(function (r) {
        var c = r.el;
        return (v === 'all' || (' ' + c.dataset.ver + ' ').indexOf(' ' + v + ' ') > -1) && (l === 'all' || c.dataset.line === l) &&
               inPrice(r.price, pk) && (u === 'all' || (today - r.upd) / 864e5 <= +u) && (!t || c.dataset.q.indexOf(t) > -1);
      }).sort(cmp[ctl.sort.value]);
      var pages = Math.max(1, Math.ceil(list.length / PER));
      page = Math.min(page, pages);
      rows.forEach(function (r) { r.el.hidden = true; });
      list.slice((page - 1) * PER, page * PER).forEach(function (r) { r.el.hidden = false; grid.appendChild(r.el); });
      none.hidden = list.length > 0;
      var from = list.length ? (page - 1) * PER + 1 : 0, to = Math.min(page * PER, list.length);
      count.textContent = list.length ? 'Showing ' + from + '-' + to + ' of ' + list.length + ' apps' : '0 apps';
      sortnote.textContent = notes[ctl.sort.value];
      pager.innerHTML = '';
      if (pages < 2) return;
      var btn = function (label, p, cls, dis) {
        var b = d.createElement('button'); b.type = 'button'; b.textContent = label; if (cls) b.className = cls; b.disabled = !!dis;
        b.addEventListener('click', function () { page = p; draw(); window.scrollTo({ top: grid.getBoundingClientRect().top + scrollY - 200, behavior: reduce ? 'auto' : 'smooth' }); });
        pager.appendChild(b);
      };
      btn('‹ Prev', page - 1, '', page === 1);
      for (var i = 1; i <= pages; i++) btn(String(i), i, i === page ? 'on' : '', false);
      btn('Next ›', page + 1, '', page === pages);
    };
    var reset = function () { ctl.q.value = ''; ['ver', 'line', 'price', 'upd'].forEach(function (k) { ctl[k].value = 'all'; }); ctl.sort.value = 'top'; page = 1; draw(); };
    Object.keys(ctl).forEach(function (k) { ctl[k].addEventListener(k === 'q' ? 'input' : 'change', function () { page = 1; draw(); }); });
    $('f-reset').addEventListener('click', reset);
    $('clear').addEventListener('click', function (e) { e.preventDefault(); reset(); });
    var P = new URLSearchParams(location.search);
    if (P.get('line')) ctl.line.value = P.get('line');
    if (P.get('v')) ctl.ver.value = P.get('v');
    draw();
  }

  // FAQ search
  var fq = d.getElementById('faq-q');
  if (fq) {
    var fd = [].slice.call(d.querySelectorAll('#faq-list details')), fn = d.getElementById('faq-none');
    fq.addEventListener('input', function () {
      var t = fq.value.trim().toLowerCase(), n = 0;
      fd.forEach(function (x) { var ok = !t || x.textContent.toLowerCase().indexOf(t) > -1; x.hidden = !ok; if (ok) n++; if (t && ok) x.open = true; });
      fn.hidden = n > 0;
    });
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
