#!/usr/bin/env python3
"""Build the Oldham Street Lofts investment report V3 from the original report (src/index.html).

Same approach as Charter House and The Print House: light theme, one continuous scroll, the shared
V2 skin (skin.css, skin.js), seven reasons as banners down the page, reviews, FAQs, the architect's
awards, then the V3 brief up front (Part one) with the full report as the deep dive (Part two).

  python3 v3/_build/build.py            -> writes the live page: index.html at the repo root
  OUT=/some/dir python3 v3/_build/build.py   -> writes a preview copy there instead
"""
import os, re, sys, json, html
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

MISSES = []
def rep(s, old, new, count=1, label=""):
    n = s.count(old)
    if n < 1:
        if os.environ.get("SOFT"):
            MISSES.append(label or old[:80]); return s
        sys.exit(f"PATCH NOT FOUND: {label or old[:80]}")
    return s.replace(old, new) if count == 0 else s.replace(old, new, count)

def js(t):
    return t.replace("\\", "\\\\").replace("`", "\\`").replace("${", "\\${")

def take_div(s, start):
    depth = 0
    for m in re.finditer(r'<div\b|</div>', s[start:]):
        depth += 1 if m.group(0) == '<div' else -1
        if depth == 0:
            return start, start + m.end()
    raise ValueError("unbalanced div")

PAYSTACK = ('<div class="paystack">${STOPS.map((st,i)=>`<div class="paycard ${i===ps?"on":""}" data-pc="${i}" aria-hidden="${i!==ps}">'
  '<div class="pcl"><div class="cap">${st.when}, ${st.sub.toLowerCase()}</div><h3 class="pct">${st.title}</h3><div class="pca">${gbp(st.amt)}</div><p class="pcn">${st.note}</p></div>'
  '<div class="pcr"><div class="rows big">${st.rows.map(([a,b])=>`<div><span>${a}</span><span>${gbp(b)}</span></div>`).join("")}</div>'
  '<div class="run"><span>Total paid by this stage</span><b>${gbp(run[i])}</b></div>'
  '<div class="pnav"><button class="b line sm" data-pstep="${Math.max(0,i-1)}" ${i===0?"disabled":""}>Back</button>${i<2?`<button class="b solid sm pnext" data-pstep="${i+1}">Next: ${STOPS[i+1].when}</button>`:""}</div></div>'
  '</div>`).join("")}</div>')


def build(src, dst, prefix):
    site = json.load(open(f"{HERE}/site.json", encoding="utf-8"))
    rv = json.load(open(f"{HERE}/reviews.json", encoding="utf-8"))
    e = lambda x: html.escape(x, quote=True)
    s = open(src, encoding="utf-8").read()
    P = prefix + "assets/img/"
    F = prefix + "assets/fonts/"

    # 1. leftover template images: the original carried 61 small embedded images it never shows; drop them
    s, n = re.subn(r'--([a-zA-Z0-9_]+):url\((?:"|\')?data:image/[a-z+\-]+;base64,[A-Za-z0-9+/=]+(?:"|\')?\)', r'--\1:none', s)
    assert n >= 50, n
    # 2. light theme always, dark mode removed
    s = rep(s, '<html lang="en">', '<html lang="en" data-theme="light">', label="html tag")
    j0 = s.find("<script"); head, tail = s[:j0], s[j0:]
    n1 = head.count("(prefers-color-scheme:dark)"); n2 = head.count('[data-theme="dark"]')
    head = head.replace("(prefers-color-scheme:dark)", "(prefers-color-scheme:dark) and (max-width:0px)").replace('[data-theme="dark"]', '[data-theme="dark-off"]')
    assert n1 >= 7 and n2 >= 5, (n1, n2)
    head = head.replace('<meta charset="utf-8">', '<meta charset="utf-8">\n<meta name="color-scheme" content="light only">', 1)
    s = head + tail
    # 3. fonts
    s = re.sub(r'<link href="https://fonts.googleapis.com/css2\?[^"]+" rel="stylesheet">',
               '<link href="https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@125,500;125,600&family=Besley:ital,wght@0,500;0,600;0,700;0,800;1,500&display=swap" rel="stylesheet">'
               f'\n<link rel="preload" href="{F}figtree-400.woff2" as="font" type="font/woff2" crossorigin>', s)
    # 4. one continuous scroll
    i = s.find('function renderMain(){if(!TABS[S.tab])')
    k = s.find('markNav(S.tab)}', i) + len('markNav(S.tab)}')
    assert i > 0 and k > i
    s = s[:i] + ('function renderMain(){if(!TABS[S.tab])S.tab="brief";S.group=groupOf(S.tab)[0];\n'
                 '  $("#view").innerHTML=GROUPS.map(g=>`<div class="ggroup" data-g="${g[0]}">`+g[2].map(id=>`<div class="gsec" id="t-${id}" data-sec="${id}">${T[id]()}</div>`).join("")+`</div>`).join("")'
                 '+`<div class="gsec galend" id="t-gallery" data-sec="heritage">${galleryTab()}</div>`;\n'
                 '  $("#chg").style.display="";markNav(S.tab);if(window.__v2skin)window.__v2skin()}\n'
                 'function rerender(id){const el=$("#t-"+id);if(!el){renderMain();return}el.innerHTML=T[id]();if(window.__v2skin)window.__v2skin()}') + s[k:]
    s = rep(s, 'function goTab(id){const g=groupOf(id),same=g[0]===S.group&&$("#t-"+id);S.tab=id;if(!same)renderMain();else markNav(id);\n  const el=g[2][0]===id?$("#view"):$("#t-"+id);const y=el.getBoundingClientRect().top+scrollY-navOff()-6;\n  spyLock=Date.now()+(same&&!RM?4000:300);scrollTo({top:Math.max(0,y),behavior:same&&!RM?"smooth":"auto"});',
            'function goTab(id){const g=groupOf(id);S.tab=id;S.group=g[0];markNav(id);\n  const el=$("#t-"+id)||$("#view");const y=el.getBoundingClientRect().top+scrollY-navOff()-6;\n  spyLock=Date.now()+(!RM?4000:300);scrollTo({top:Math.max(0,y),behavior:!RM?"smooth":"auto"});', label="goTab")
    s = rep(s, 'if(cur!==S.tab){S.tab=cur;markNav(cur);', 'if(cur!==S.tab){S.tab=cur;S.group=groupOf(cur)[0];markNav(cur);', label="spy")
    s = rep(s, 'if(d.mapmode){S.mapOld=d.mapmode==="old";renderMain();return}', 'if(d.mapmode){S.mapOld=d.mapmode==="old";rerender("location");return}', label="mapmode")
    s = rep(s, 'if(d.yr){S.yr=+d.yr;renderMain();return}', 'if(d.yr){S.yr=+d.yr;rerender("returns");return}', label="yr")
    s = rep(s, 'if(d.beds){S.beds=+d.beds;renderMain();return}', 'if(d.beds){S.beds=+d.beds;rerender("returns");return}', label="beds")
    s = rep(s, 'if(d.pstep!==undefined){S.payStep=+d.pstep;renderMain();return}', 'if(d.pstep!==undefined){S.payStep=+d.pstep;rerender("next");return}', label="pstep")
    # 4b. James's BRIK-down as one continuous quote
    s, k = re.subn(r'<blockquote>“([^<]*?)”</blockquote>\n  <div class="body" style="margin-top:14px"><p>“([^<]*?)”</p></div>',
                   lambda m: f'<blockquote class="v2q"><p>“{m.group(1)}</p><p>{m.group(2)}”</p></blockquote>', s, count=1)
    if k != 1: MISSES.append("james quote")
    # 4d. payment timeline: all three stages, pinned while you scroll
    s = rep(s, '<div class="ptl">', '<div class="ptlrun"><div class="ptl">', label="ptl open")
    s = rep(s, 'Click each stage to see what you pay and when', 'Scroll to move through each stage, or tap one', label="ptl hint")
    i0 = s.find('<div class="paycard" aria-live="polite">'); i1 = s.find('\n    <p class="fine">Total cash needed for ${u.name}')
    assert 0 < i0 < i1, (i0, i1)
    s = s[:i0] + PAYSTACK + '\n   </div></div>' + s[i1:]
    s = rep(s, 'Please take your own tax and legal advice.</p>\n   </div></section>', 'Please take your own tax and legal advice.</p>\n   </section>', label="ptl close")
    # 4e. essentials panel mark
    s, k = re.subn(r'<div class="esspanel"><svg class="solid"[^>]*>.*?</svg>', '<div class="esspanel"><span class="mask plogo lg7 essmark" aria-hidden="true"></span>', s, count=1, flags=re.S)
    if k != 1: MISSES.append("essentials mark")
    # 4f. gallery at the very end (renderMain above adds it)
    s = rep(s, r'building:()=>CH.building().replace(/<\/section>$/,"")+galleryTab()+"</section>"', 'building:CH.building', label="gallery out of building")
    s = s.replace('<h3 class="sh" style="font-size:clamp(28px,3.2vw,38px)!important;margin:6px 0 14px">', '<h3 class="sh" style="margin:6px 0 14px">')

    # 4h. chapter order: the brief, then Overview, Building, Why Hyde, Location, Data, Returns, Units, Next steps, Heritage
    s = rep(s, 'const GROUPS=[["opportunity","The opportunity",["overview","building","heritage"]],["intel","Location and intel",["location","hyde","data"]],["invest","Your investment",["units","returns","next"]]];',
            'const GROUPS=[["brief","The brief",["brief"]],["opportunity","The opportunity",["overview","building"]],["intel","Location and intel",["hyde","location","data"]],["invest","Your investment",["returns","units","next"]],["more","More",["heritage"]]];', label="groups")
    for old_n, new_n, title in [("05","03","Why Hyde"),("04","04","Location"),("06","05","The data"),("08","06","Returns"),("07","07","Recommended units"),("09","08","Next steps"),("03","09","Hyde's heritage")]:
        s = rep(s, f'chh("{old_n}","{title}"', f'chh("{new_n}","{title}"', label="renumber " + title)
    tab = lambda t, n, lab, sel="false": f'<button role="tab" data-tab="{t}" aria-selected="{sel}"><span class="tn0">{n}</span>{lab}</button>'
    grp = lambda g, lab, tabs, on="": f'<div class="tg{on}" data-g="{g}"><button class="tgl" data-group="{g}">{lab}</button><div class="tgb">{tabs}</div></div>'
    nav = ('<nav class="tabs gtabs" role="tablist" aria-label="Report sections">'
           + grp("brief", "The brief", tab("brief", "★", "The brief", "true"), " on")
           + grp("opportunity", "The opportunity", tab("overview", "01", "Overview") + tab("building", "02", "The building"))
           + grp("intel", "Location and intel", tab("hyde", "03", "Why Hyde") + tab("location", "04", "Location") + tab("data", "05", "The data"))
           + grp("invest", "Your investment", tab("returns", "06", "Returns") + tab("units", "07", "Recommended units") + tab("next", "08", "Next steps"))
           + grp("more", "More", tab("heritage", "09", "Heritage")) + '</nav>')
    s, k = re.subn(r'<nav class="tabs gtabs".*?</nav>', lambda m: nav, s, count=1, flags=re.S)
    assert k == 1
    s = rep(s, 'const NEXT={overview:["returns","Look at the numbers"],building:["heritage","Next: Hyde\'s heritage"],heritage:["location","Next: the location"],location:["hyde","Next: why Hyde"],hyde:["data","Next: the data"],',
            'const NEXT={overview:["returns","Look at the numbers"],building:["hyde","Next: why Hyde"],hyde:["location","Next: the location"],location:["data","Next: the data"],', label="next map")
    s = rep(s, 'intel:["invest","Your investment","See the recommended apartments"]}', 'intel:["invest","Your investment","Next: the returns"]}', label="gnext")
    s = rep(s, 'const S={tab:"overview",', 'const S={tab:"brief",', label="start tab")
    # 4j. developer and architect: one hero image each
    t0 = s.find('<div class="team2">')
    for key in ("dev_hero", "arch_hero"):
        g0 = s.find('<div class="pics3">', t0); g1 = s.find('</div>', g0) + len('</div>')
        assert t0 > 0 and g0 > t0, key
        img, alt, cap = site[key]
        s = s[:g0] + f'<div class="teamhero">${{IMG("{img}","{alt}","thero")}}<p class="thcap">{cap}</p></div>' + s[g1:]

    # ---------- the seven reasons, as banners at the start of each chapter
    s = rep(s, "const CH={};", open(f"{HERE}/case.js", encoding="utf-8").read() + "const CH={};", label="case defs")
    for i, (num, title) in enumerate([("02", "The building"), ("03", "Why Hyde"), ("04", "Location"), ("05", "The data")]):
        s, k = re.subn(r'(\$\{chh\("' + num + '","' + re.escape(title) + r'","[^"]*"\)\})', lambda m: m.group(1) + '${caseBand(' + str(i) + ')}', s, count=1)
        assert k == 1, ("case band", title)
    s = rep(s, '+returnsTab(),', '+caseBand(4)+returnsTab(),', label="returns band")
    s = rep(s, '+EARLY+AVAIL+unitsTab()+WHY37(),', '+caseBand(5)+EARLY+AVAIL+unitsTab()+WHY37(),', label="units band")
    # reason 7 and 'Book your video call' become one band, with the walkway picture
    a = s.find('<section class="hero-next">'); z = s.find('</section>', a) + len('</section>')
    assert a > 0 and z > a, "hero-next"
    hero = s[a:z]
    lead = re.search(r'<p class="lead">(.*?)</p>', hero, re.S).group(1)
    row = re.search(r'<div class="row">.*?</div>', hero, re.S).group(0)
    fig = re.search(r'<figure class="keyfig">.*?</figure>', hero, re.S).group(0)
    s = s[:a] + s[z:]
    resv = '<div class="c7res"><div class="cap">How it works</div><p>' + lead + '</p>' + row + '</div>'
    s = rep(s, "const CASE=[", 'const RESV=()=>`' + resv + '`,RESFIG=()=>`' + fig + '`;\nconst CASE=[', label="resv defs")
    # contact after the heritage chapter, so Next steps ends on the reviews and FAQs
    s = rep(s, '+nextTab()+howBlocks()+CONTACT};', '+caseBand(6)+nextTab()+howBlocks()+FAQ};', label="next chapter")
    s = rep(s, 'heritage:CH.heritage,', 'heritage:()=>CH.heritage()+CONTACT,', label="contact after heritage")

    # ---------- the architect's awards open the developer and architect section
    pen = '<svg class="penline" viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true"><polygon points="5,1.6 95,1.6 95,97 50,88 5,97" vector-effect="non-scaling-stroke"/></svg>'
    aw = ('<div class="awards pennants" style="--pbg:var(--' + site["awards_bg"] + ')"><div class="pnhead"><div class="cap">' + e(site["awards_cap"]) + '</div>'
          '<h3 class="pnh">' + e(site["awards_h"]) + '</h3></div><div class="pnrow">'
          + "".join(f'<div class="pennant" style="--i:{k}">{pen}<span class="pnbody">{e(b)}</span><span class="pnstat">{e(st)}</span>'
                    + (f'<span class="pncat">{e(c)}</span>' if c else '') + f'<span class="pnproj">{e(pr)}</span></div>'
                    for k, (b, st, c, pr, y) in enumerate(site["awards"])) + '</div></div>')
    t0 = s.find('<div class="team2">')
    s = s[:t0] + aw + s[t0:]
    # James's background
    s = rep(s, '<div class="jsig"><b>James Dempsey</b><span>CEO, BRIK Studios</span></div>',
            '<div class="jsig"><b>James Dempsey</b><span>CEO, BRIK Studios. Previously group sales director in Hong Kong for 12 years</span></div>', label="james sig")
    # the process: a carousel with arrows
    a = s.find('<ol class="proc">'); z = s.find('</ol></section>', a)
    assert 0 < a < z
    s = (s[:a] + '<div class="pcar" data-cur="${cur}"><div class="pcview"><ol class="proc">' + s[a + len('<ol class="proc">'):z]
         + '</ol></div><div class="pcnav"><button class="pcarb" data-pcar="-1" aria-label="Previous step"><svg viewBox="0 0 24 24"><path d="M15 5l-7 7 7 7"/></svg></button>'
           '<span class="pccount" aria-live="polite"><b>1</b> of ${STEPS.length}</span>'
           '<button class="pcarb" data-pcar="1" aria-label="Next step"><svg viewBox="0 0 24 24"><path d="M9 5l7 7-7 7"/></svg></button></div></div></section>'
         + s[z + len('</ol></section>'):])
    # specification CGIs: a left-to-right slider
    a = s.find('<div class="rooms-big" style="margin-top:56px">'); assert a > 0, "rooms-big"
    z = s.find('.join("")}</div>', a); assert 0 < z - a < 3000, "rooms-big end"
    z += len('.join("")}</div>')
    arr = ('<div class="tpnav rbnav"><button class="tparr prev" aria-label="Previous image"><svg viewBox="0 0 24 24"><path d="M15 5l-7 7 7 7"/></svg></button>'
           '<button class="tparr next" aria-label="Next image"><svg viewBox="0 0 24 24"><path d="M9 5l7 7-7 7"/></svg></button></div>')
    blk = s[a:z].replace('<div class="rooms-big" style="margin-top:56px">', '<div class="rooms-big rbtrack" tabindex="0" aria-label="Specification images, scroll sideways">', 1)
    s = s[:a] + '<div class="rbslider">' + blk + arr + '</div>' + s[z:]

    # ---------- reviews, FAQs, how to read
    star = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 2.6l2.9 6.3 6.9.7-5.2 4.6 1.5 6.8L12 17.5 5.9 21l1.5-6.8L2.2 9.6l6.9-.7z"/></svg>'
    stars = '<span class="tpstars" aria-label="5 out of 5 stars">' + star * 5 + '</span>'
    cards = "".join(f'<article class="tpcard"><div class="tpcard-top">{stars}</div>' + (f'<h4>{e(t)}</h4>' if t else '') + f'<p>{e(b)}</p>'
                    f'<div class="tpby"><b>{e(n)}</b><a href="{e(u)}" target="_blank" rel="noopener">Read on Trustpilot</a></div></article>' for t, b, n, u in rv["reviews"])
    TP = (f'<section class="sec tpsec"><div class="tphead"><div><div class="cap">What our clients say</div>'
          f'<h3 class="big-h">Rated {e(rv["label"])} on Trustpilot.</h3><p class="tpscore">TrustScore <b>{e(rv["score"])}</b> out of 5 from {e(rv["count"])} reviews</p></div>'
          f'<a class="tpbadge" href="{e(rv["link"])}" target="_blank" rel="noopener" aria-label="BRIK Studios on Trustpilot"><b>{e(rv["label"])}</b>{stars}<i class="tplogo" role="img" aria-label="Trustpilot"></i></a></div>'
          f'<div class="tpwrap"><div class="tptrack" tabindex="0" aria-label="Client reviews, scroll sideways">{cards}</div>'
          f'<div class="tpnav"><button class="tparr prev" aria-label="Previous reviews"><svg viewBox="0 0 24 24"><path d="M15 5l-7 7 7 7"/></svg></button>'
          f'<button class="tparr next" aria-label="More reviews"><svg viewBox="0 0 24 24"><path d="M9 5l7 7-7 7"/></svg></button></div></div></section>')
    FAQ = ('<section class="sec faqsec"><div class="faqgrid"><div class="faqlead"><div class="cap">Before you reserve</div>'
           '<h3 class="big-h">Frequently asked questions.</h3><p>The questions investors ask us most. Can\'t see yours? Message us and we\'ll come straight back to you.</p>'
           '</div><div class="faqlist">' + "".join(f'<details class="faq"><summary>{e(q)}<i aria-hidden="true"></i></summary><p>{e(a)}</p></details>' for q, a in site["faq"])
           + '</div></div></section>')
    hr = site["howread"]
    HOWREAD = (f'<section class="howread"><i class="hrscroll" aria-hidden="true"><b></b></i><div><div class="cap">{e(hr["cap"])}</div><h3 class="hrh">{e(hr["h"])}</h3>'
               + "".join(f"<p>{e(x)}</p>" for x in hr["p"]) + '</div></section>')

    # ---------- Part one, the brief
    a = s.find('<div class="kpis">', s.find('CH.overview=()=>`'))
    a, b = take_div(s, a)
    kpis = s[a:b]
    s = s[:a] + s[b:]
    u, t = site["urgency"], site["tour"]
    stats = "".join(f'<div><b>{e(v)}</b><span>{e(l)}</span></div>' for v, l in u["stats"])
    wa = 'encodeURIComponent("Hi Charlie, I\'ve been looking at Oldham Street Lofts. Could we book a video call?")'
    brief = (
        '<section class="brief">'
        '<div class="partlab"><span class="pno">Part one</span><span class="pnm">The brief</span><span class="ptime">2-minute read</span></div>'
        f'<div class="urgent"><div class="cap">{e(u["cap"])}</div><h2 class="urh">{e(u["h"])}</h2><div class="urstats">{stats}</div>'
        f'<p>{e(u["p"])}</p><div class="row"><button class="b solid" data-call>{e(t["btn"])}</button>'
        '<a class="b line" href="${WA_}${' + wa + '}" target="_blank" rel="noopener">WhatsApp me</a></div></div>'
        + js(HOWREAD) +
        '<div class="bknums"><div class="bkh"><div class="cap">The numbers</div><h3 class="bkt">On Plots 18 and 24.</h3></div>' + kpis + '</div>'
        '${CASEMAP}' + js(TP) +
        f'<div class="bktour"><button class="bkimg" style="background-image:var(--{t["img"]})" data-img="{t["img"]}" data-cap="{e(t["cap"])}" aria-label="View the CGI full screen"></button>'
        f'<div><h3 class="bkt">{e(t["h"])}</h3><p>{e(t["p"])}</p>'
        f'<div class="row"><button class="b solid" data-call>{e(t["btn"])}</button><a class="b line" href="${{FILM}}" target="_blank" rel="noopener">Watch the film</a></div></div></div>'
        '<div class="partlab deep" id="deepdive"><span class="pno">Part two</span><span class="pnm">The deep dive</span><span class="ptime">The full report, chapter by chapter</span></div>'
        '<div class="ddlist">${GROUPS.filter(g=>g[0]!=="brief").flatMap(g=>g[2]).map((id,k)=>`<button data-goto="${id}"><span>${String(k+1).padStart(2,"0")}</span>${TABS[id]}</button>`).join("")}</div>'
        '</section>')
    defs = "const FAQ=`" + js(FAQ) + "`;\nconst BRIEF=()=>`" + brief + "`;\n"
    s = rep(s, "const CH={};", defs + "const CH={};", label="brief defs")
    s = rep(s, 'const T={overview:CH.overview,', 'const T={brief:BRIEF,overview:CH.overview,', label="T brief")
    s = rep(s, 'const TABS={overview:"Investment overview",', 'const TABS={brief:"The brief",overview:"Investment overview",', label="TABS brief")

    # 8. link previews
    url = site["url"]; img = site["url"] + "assets/img/og.jpg"
    esc = lambda x: x.replace("&", "&amp;").replace('"', "&quot;")
    tt, dd = esc(site["title"]), esc(site["description"])
    s, k = re.subn(r'<title>[^<]*</title>', f'<title>{tt}</title>', s, count=1); assert k == 1
    s, k = re.subn(r'<meta name="description" content="[^"]*">',
                   f'<meta name="description" content="{dd}">\n<meta property="og:type" content="website">\n<meta property="og:site_name" content="BRIK Studios">'
                   f'\n<meta property="og:title" content="{tt}">\n<meta property="og:description" content="{dd}">\n<meta property="og:url" content="{url}">'
                   f'\n<meta property="og:image" content="{img}">\n<meta property="og:image:width" content="1200">\n<meta property="og:image:height" content="630">'
                   f'\n<meta name="twitter:card" content="summary_large_image">\n<meta name="twitter:title" content="{tt}">\n<meta name="twitter:description" content="{dd}">\n<meta name="twitter:image" content="{img}">', s, count=1)
    assert k == 1
    og = f"{REPO}/assets/img/og.jpg"
    if not os.path.exists(og):
        from PIL import Image
        im = Image.open(f"{REPO}/{site['og_source']}").convert("RGB")
        w, h = im.size; tw = min(w, round(h * 1200 / 630)); th = round(tw * 630 / 1200)
        im = im.crop(((w - tw) // 2, (h - th) // 2, (w - tw) // 2 + tw, (h - th) // 2 + th)).resize((1200, 630), Image.LANCZOS)
        os.makedirs(os.path.dirname(og), exist_ok=True)
        im.save(og, "JPEG", quality=84, optimize=True, progressive=True)

    # 6. skin
    # Charter House styles its short 'Choose your apartment' chapter as a navy band; here the units chapter
    # holds the full unit cards, so it keeps the normal light page instead
    def drop_units(m):
        sels = [x for x in m.group(1).split(",") if "#t-units" not in x or ":not(#t-units)" in x]
        return (",".join(sels) + "{" + m.group(2) + "}") if sels else ""
    skin = re.sub(r'([^{}]+)\{([^{}]*)\}', drop_units, open(f"{HERE}/skin.css", encoding="utf-8").read()).replace(".gsec:not(#t-units)", ".gsec")
    assert "#t-units" not in skin
    css = (skin + "\n:root{--tplogo:url(\"{{P}}trustpilot.png\")}\n"
           + open(f"{HERE}/skin_v3.css", encoding="utf-8").read()
           + "\n/* Oldham Street Lofts: private preview note in the units chapter */\n"
             "#view .earlynote{background:#A44C28!important;border:1.5px dashed rgba(255,214,190,.55)!important}"
             "#view .earlynote b,#view .earlynote p,#view .earlynote span,#view .earlynote .cap{color:#FFF4EC!important}\n"
             "#t-data .esspanel .cap,#t-data .esspanel .fine{color:#221C19!important}\n"
           ).replace("{{F}}", F).replace("{{P}}", P)
    jsx = open(f"{HERE}/skin.js", encoding="utf-8").read()
    k = s.rfind("</style>"); s = s[:k] + "\n/* ================= V2 SKIN ================= */\n" + css + "\n" + s[k:]
    k = s.rfind("</body>"); s = s[:k] + "<script>" + jsx + "</script>\n" + s[k:]
    assert "charit" not in s.lower()
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    open(dst, "w", encoding="utf-8").write(s)
    print(dst, round(os.path.getsize(dst) / 1024), "KB")


OUT = os.environ.get("OUT", REPO)
PFX = os.environ.get("PFX", "")
build(f"{HERE}/src/index.html", f"{OUT}/index.html", PFX)
if MISSES:
    print("MISSES:\n  " + "\n  ".join(dict.fromkeys(MISSES)))
