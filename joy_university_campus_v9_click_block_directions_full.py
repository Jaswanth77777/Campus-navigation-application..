#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JOY UNIVERSITY - 3D SMART CAMPUS v9  (ONE complete file, no patching)
RUN:   pip install pypdf pillow
       put this file + your photos PDF (reddy.pdf) in the SAME folder
       python joy_university_campus_v2.py          -> opens http://127.0.0.1:8000
       python joy_university_campus_v2.py --lan    -> phones on same Wi-Fi
       python joy_university_campus_v2.py --export -> index.html (+photos/) for Netlify / GitHub Pages (online)
"""
import io, sys, socket, threading, webbrowser
from pathlib import Path
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

HERE = Path(__file__).resolve().parent
PHOTOS = HERE / "photos"


def _save(data, n):
    out = PHOTOS / f"photo_{n:02d}.jpg"
    try:
        from PIL import Image
        im = Image.open(io.BytesIO(data)).convert("RGB")
        im.thumbnail((1600, 1600))
        im.save(out, "JPEG", quality=85)
    except Exception:
        out.write_bytes(data)


def extract_photos():
    """
    Extract campus photos when a valid PDF is available.
    Empty/corrupt PDFs are skipped so the 3D campus still starts normally.
    """
    PHOTOS.mkdir(exist_ok=True)
    if len(list(PHOTOS.glob("photo_*.jpg"))) >= 20:
        return True

    pdfs = sorted(HERE.glob("*.pdf"))
    if not pdfs:
        print("[!] No PDF next to this script -> photos skipped (3D still works).")
        return False

    n = 0
    valid_pdf_found = False

    # Try each PDF instead of blindly opening the first one.
    # This avoids EmptyFileError when an empty PDF happens to sort first.
    for pdf in pdfs:
        try:
            size = pdf.stat().st_size
        except OSError:
            size = 0

        if size <= 0:
            print(f"[!] Skipping empty PDF: {pdf.name}")
            continue

        print(f"[+] Extracting photos from {pdf.name} ...")

        # First choice: pypdf
        try:
            from pypdf import PdfReader
            try:
                reader = PdfReader(str(pdf))
                valid_pdf_found = True
                for page in reader.pages:
                    for img in page.images:
                        try:
                            _save(img.data, n)
                            n += 1
                        except Exception as e:
                            print(f"[!] Skipping an embedded image: {e}")
                if n > 0:
                    break
            except Exception as e:
                print(f"[!] pypdf could not read {pdf.name}: {e}")
        except ImportError:
            pass

        # Fallback: PyMuPDF if pypdf cannot read the PDF.
        if n == 0:
            try:
                import fitz
                try:
                    doc = fitz.open(str(pdf))
                    valid_pdf_found = True
                    for page in doc:
                        for x in page.get_images(full=True):
                            try:
                                _save(doc.extract_image(x[0])["image"], n)
                                n += 1
                            except Exception as e:
                                print(f"[!] Skipping an embedded image: {e}")
                    doc.close()
                    if n > 0:
                        break
                except Exception as e:
                    print(f"[!] PyMuPDF could not read {pdf.name}: {e}")
            except ImportError:
                pass

    if n == 0:
        if not valid_pdf_found:
            print("[!] No readable PDF with embedded images was found.")
        else:
            print("[!] No embedded photos found in the available PDF(s).")
        print("[i] Continuing without PDF extraction. The 3D campus still works.")
        print("[i] To load your own photos, place a valid PDF beside this script.")
        return False

    print(f"[+] {n} photos saved")
    return True


HTML = r'''<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Joy University • 3D Smart Campus</title>
<style>
:root{--bg:#06121d;--panel:#0b1c2bd9;--line:#ffffff1c;--text:#f6fbff;--muted:#a8bbca;--a:#5eead4;--b:#60a5fa;--y:#fbbf24}
*{box-sizing:border-box}html,body{margin:0;height:100%;overflow:hidden;background:var(--bg);color:var(--text);font-family:system-ui,-apple-system,Segoe UI,Roboto,Arial,sans-serif}
#c{position:fixed;inset:0;width:100%;height:100%;display:block}
.glass{background:var(--panel);backdrop-filter:blur(16px);border:1px solid var(--line);border-radius:18px;box-shadow:0 20px 60px #0007}
button{font:inherit;cursor:pointer;color:var(--text);background:#ffffff10;border:1px solid var(--line);border-radius:12px;padding:8px 12px;font-weight:700}
button:hover{background:#ffffff22}button.on,.pri{background:linear-gradient(135deg,var(--a),var(--b));color:#03101a;border:0}
#top{position:fixed;top:12px;left:12px;right:12px;display:flex;justify-content:space-between;gap:10px;pointer-events:none;z-index:5}#top>*{pointer-events:auto}
.brand{display:flex;align-items:center;gap:10px;padding:8px 14px}.mark{width:38px;height:38px;border-radius:11px;background:linear-gradient(135deg,var(--a),var(--b));display:grid;place-items:center;color:#03101a;font-weight:900}
.brand b{display:block;font-size:15px}.brand small{color:var(--muted);font-size:11px}
#tools{display:flex;gap:6px;flex-wrap:wrap;justify-content:flex-end;padding:8px}
#side{position:fixed;left:12px;top:90px;bottom:150px;width:300px;display:flex;flex-direction:column;padding:12px;z-index:4;transition:.25s}#side.hide{transform:translateX(-330px)}
#q{width:100%;padding:10px 12px;border-radius:12px;border:1px solid var(--line);background:#071827;color:#fff;outline:none;margin-bottom:8px}
#chips{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:8px}#chips button{padding:4px 10px;font-size:12px}
#list{overflow:auto;flex:1;display:grid;gap:6px;align-content:start}
.it{display:flex;gap:10px;align-items:center;padding:8px 10px;border-radius:12px;background:#ffffff08;border:1px solid transparent;cursor:pointer}.it:hover,.it.sel{border-color:#5eead466;background:#5eead412}
.num{min-width:26px;height:26px;border-radius:50%;background:var(--y);color:#111;font-weight:900;font-size:12px;display:grid;place-items:center}.num.h{background:#c1121f;color:#fff}.it small{color:var(--muted);display:block;font-size:11px}
#card{position:fixed;right:12px;top:90px;width:330px;max-height:calc(100% - 260px);overflow:auto;padding:14px;z-index:14;display:none}
#card img{display:none!important}
#card h2{margin:0 0 4px;font-size:20px}#card p{color:var(--muted);line-height:1.5;font-size:13px;margin:6px 0}
.tag{display:inline-block;font-size:11px;padding:3px 9px;border-radius:99px;background:#60a5fa22;color:#93c5fd;margin-bottom:6px}
.row{display:flex;gap:8px;flex-wrap:wrap;margin-top:8px}.mini{display:flex;gap:6px;overflow:auto;margin-bottom:8px}.mini img{width:64px;height:48px;object-fit:cover;border-radius:8px;cursor:pointer}
.nav{border-top:1px solid var(--line);margin-top:8px;padding-top:6px}.nav b{color:#fde68a}
#x{float:right;padding:2px 9px}
#gal{position:fixed;left:12px;right:12px;bottom:12px;padding:10px 12px;z-index:4;transition:.25s}#gal.hide{transform:translateY(calc(100% + 20px))}
#profilePanel{position:fixed;right:18px;top:78px;width:min(360px,calc(100vw - 36px));padding:16px;z-index:12;display:none}#profilePanel.show{display:block}#profilePanel label{display:block;font-size:12px;color:var(--muted);margin:8px 0 4px}#profilePanel input,#profilePanel select{width:100%;box-sizing:border-box;padding:9px;border-radius:9px;border:1px solid #ffffff22;background:#0c1720;color:#fff}.profilePreview{margin-top:12px;padding:10px;border-radius:10px;background:#ffffff0d;color:#d9e4ec;font-size:13px}
#gal h3{margin:0 0 6px;font-size:13px;color:var(--muted);display:flex;justify-content:space-between;align-items:center}
#strip{display:flex;gap:9px;overflow-x:auto}.th{flex:0 0 140px;cursor:pointer;border-radius:12px;overflow:hidden;border:1px solid var(--line)}.th:hover{border-color:var(--a)}
.th img{width:100%;height:78px;object-fit:cover;display:block}.th span{display:block;font-size:11px;padding:5px 7px;color:#dbe8f2;height:34px;overflow:hidden}
#tip{position:fixed;pointer-events:none;padding:6px 10px;border-radius:9px;background:#000c;font-size:12px;font-weight:700;display:none;z-index:9;border:1px solid var(--line)}
#lb{position:fixed;inset:0;background:#000d;z-index:20;display:none;place-items:center;padding:20px}#lb.show{display:grid}#lb .box{max-width:min(1100px,96vw);text-align:center}
#lb img{max-width:100%;max-height:76vh;border-radius:14px}#lb p{margin:10px 0;font-weight:700}#lb .row{justify-content:center}
#load{position:fixed;inset:0;background:#000;z-index:50;display:grid;place-items:center;transition:opacity .8s;text-align:center}
#setupGate{position:fixed;inset:0;z-index:49;display:none;place-items:center;padding:18px;background:#020912d9;backdrop-filter:blur(12px)}
#setupGate.show{display:grid}
#setupGate .setupbox{width:min(420px,94vw);padding:24px;border:1px solid #ffffff24;border-radius:22px;background:#0b1c2bf2;box-shadow:0 25px 90px #000c}
#setupGate h2{margin:0 0 6px}
#setupGate p{color:var(--muted);font-size:13px;line-height:1.5}
#setupGate label{display:block;margin:12px 0 5px;color:var(--muted);font-size:12px}
#setupGate input{width:100%;padding:11px;border-radius:10px;border:1px solid #ffffff25;background:#071827;color:#fff}
#setupError{min-height:20px;color:#fca5a5;font-size:12px}
#comp{position:fixed;right:14px;bottom:150px;width:60px;height:60px;border-radius:50%;z-index:6;display:grid;place-items:center}
#needle{width:0;height:0;border-left:7px solid transparent;border-right:7px solid transparent;border-bottom:26px solid #f87171;position:relative}#needle b{position:absolute;top:-18px;left:-4px;font-size:11px}
#load .loadbox{width:min(420px,88vw);padding:28px 26px;text-align:center;border:1px solid #ffffff1c;border-radius:22px;background:#06121df2;box-shadow:0 25px 90px #000b;backdrop-filter:blur(18px)}
#load .loadlogo{width:62px;height:62px;margin:0 auto 12px;border-radius:17px;display:grid;place-items:center;background:linear-gradient(135deg,var(--a),var(--b));color:#03101a;font-size:25px;font-weight:1000}
#load h2{margin:0;color:#f6fbff;font-size:20px;font-weight:700}
#load p{margin:8px 0 12px;color:var(--muted);font-size:12px}
#load .loadbar{height:7px;background:#ffffff12;border-radius:99px;overflow:hidden;border:1px solid #ffffff10}
#load .loadbar span{display:block;width:0;height:100%;border-radius:99px;background:linear-gradient(90deg,var(--a),var(--b));transition:width .25s ease}
#load small{display:block;margin-top:8px;color:#93c5fd;font-weight:800}
#morePanel{position:fixed;right:12px;top:90px;width:min(360px,calc(100% - 24px));max-height:calc(100% - 110px);overflow:auto;padding:14px;z-index:12;display:none}
#morePanel.show{display:block}
#morePanel h2{margin:0 0 6px;font-size:18px}
#morePanel p,#morePanel li{color:var(--muted);font-size:12px;line-height:1.55}
#morePanel .stat{display:grid;grid-template-columns:1fr 1fr;gap:7px;margin:10px 0}
#morePanel .stat div{padding:9px;border:1px solid var(--line);border-radius:10px;background:#ffffff08}
#morePanel .stat b{display:block;color:var(--text);font-size:14px}
#toast{position:fixed;left:50%;bottom:30px;transform:translate(-50%,20px);opacity:0;pointer-events:none;z-index:80;padding:10px 15px;border-radius:12px;background:#06121df5;border:1px solid #ffffff22;box-shadow:0 12px 40px #0008;color:#fff;font-size:12px;font-weight:700;transition:.25s}
#toast.show{opacity:1;transform:translate(-50%,0)}
#routeHint{position:fixed;left:50%;top:78px;transform:translateX(-50%);z-index:7;padding:8px 14px;border-radius:99px;background:#06121df2;border:1px solid #5eead466;color:#dffefa;font-size:12px;font-weight:800;display:none;pointer-events:none;box-shadow:0 10px 30px #0008}#routeHint.show{display:block}
#directionsPanel{position:fixed;right:14px;top:90px;width:min(390px,calc(100% - 28px));max-height:calc(100% - 115px);overflow:auto;padding:15px;z-index:14;display:none;border:1px solid #5eead455;box-shadow:0 24px 70px #000b}
#directionsPanel.show{display:block}
#directionsPanel h2{margin:0 0 5px;font-size:19px}
#directionsPanel .dirHead{padding:10px;border-radius:12px;background:#5eead410;border:1px solid #5eead433;margin:9px 0}
#directionsPanel .dirMetric{display:grid;grid-template-columns:1fr 1fr 1fr;gap:6px;margin:8px 0}
#directionsPanel .dirMetric div{padding:8px;border-radius:10px;background:#ffffff08;border:1px solid var(--line);text-align:center}
#directionsPanel .dirMetric small{display:block;color:var(--muted);font-size:10px}
#directionsPanel .dirMetric b{font-size:13px}
#directionsPanel ol{padding-left:24px;margin:9px 0}
#directionsPanel li{padding:7px 4px;color:#e2e8f0;font-size:12px;border-bottom:1px solid #ffffff0d}
#directionsPanel li:last-child{border-bottom:0}
@media(max-width:820px){#directionsPanel{left:10px;right:10px;top:auto;bottom:12px;width:auto;max-height:48%;z-index:27}}
#livePanel{position:fixed;left:12px;top:90px;width:min(360px,calc(100% - 24px));max-height:calc(100% - 170px);overflow:auto;padding:14px;z-index:13;display:none}
#livePanel.show{display:block}
#livePanel h2{margin:0 0 5px;font-size:18px}
#livePanel p,#livePanel li{color:var(--muted);font-size:12px;line-height:1.5}
.liveStatus{display:flex;align-items:center;gap:8px;padding:9px;border:1px solid var(--line);border-radius:11px;background:#ffffff08;margin:8px 0}
.liveDot{width:9px;height:9px;border-radius:50%;background:#64748b;box-shadow:0 0 0 4px #64748b22}.liveDot.ok{background:#34d399;box-shadow:0 0 0 4px #34d39922}.liveDot.warn{background:#fbbf24;box-shadow:0 0 0 4px #fbbf2422}
.liveGrid{display:grid;grid-template-columns:1fr 1fr;gap:7px;margin:9px 0}.liveStat{padding:9px;border:1px solid var(--line);border-radius:10px;background:#ffffff08}.liveStat small{color:var(--muted);display:block}.liveStat b{font-size:14px}
#liveSteps{margin:8px 0;padding-left:20px}.liveStep{margin:7px 0;color:#dbeafe}.liveStep.current{color:#5eead4;font-weight:800}.liveStep.done{color:#94a3b8;text-decoration:line-through}
#gpsCoords{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:11px;color:#93c5fd}
#walkerLabel{position:fixed;z-index:15;display:none;pointer-events:none;padding:5px 8px;border-radius:8px;background:#06121df5;border:1px solid #5eead466;color:#fff;font-size:11px;font-weight:800;white-space:nowrap}
#livePanel .row button{flex:1}
@media(max-width:820px){#livePanel{top:auto;bottom:150px;max-height:42%}}
#favStar{float:right;padding:3px 9px}
#sideTools{display:flex;gap:6px;margin-bottom:8px}
#sideTools button{flex:1;font-size:11px;padding:6px 7px}
@media(max-width:820px){#side{width:240px}#card{left:12px;right:12px;width:auto;top:auto;bottom:12px;max-height:58%;z-index:25;box-shadow:0 24px 80px #000d}.brand small{display:none}}
</style></head><body>
<div id="load">
  <div class="loadbox">
    <div class="loadlogo">JU</div>
    <h2>Building 3D campus…</h2>
    <p id="loadText">Preparing campus engine</p><div id="loadUser" style="display:none;color:#5eead4;font-weight:800;font-size:12px;margin:6px 0 10px"></div>
    <div class="loadbar"><span id="loadBar"></span></div>
    <small id="loadPct">0%</small>
  </div>
</div>
<div id="setupGate" role="dialog" aria-modal="true" aria-labelledby="setupTitle">
  <div class="setupbox">
    <div class="loadlogo">JU</div>
    <h2 id="setupTitle">Create your campus profile</h2>
    <p>Set a name and local password to personalize this campus on this browser. No email is needed; your profile stays on this device.</p>
    <label for="setupName">Your name</label>
    <input id="setupName" type="text" maxlength="40" autocomplete="name" placeholder="Full name">
    <label for="setupPassword">Create password</label>
    <input id="setupPassword" type="password" maxlength="64" autocomplete="new-password" placeholder="At least 6 characters">
    <label for="setupPasswordConfirm">Confirm password</label>
    <input id="setupPasswordConfirm" type="password" maxlength="64" autocomplete="new-password" placeholder="Enter password again">
    <div id="setupError" role="alert"></div>
    <button id="setupCreate" class="pri" style="width:100%">Create profile &amp; open campus</button>
  </div>
</div>
<canvas id="c"></canvas>
<div id="top"><div class="glass brand"><div class="mark">JU</div><div><b>Joy University • 3D Smart Campus</b><small>Raja Nagar, Vadakangulam, Tirunelveli – 627116, Tamil Nadu</small></div></div>
<div class="glass" id="tools"><button id="bList">☰ Places</button><button id="bTour">🎬 Tour</button><button id="bOrbit">🔄 Orbit</button><button id="bTop">🛰 Top</button><button id="bReset">🏠 Reset</button><button id="bNight">🌙 Night</button><button id="bLab" class="on">🔢 Markers</button><button id="bWalk">🚶 Walk route</button><button id="bShare">🔗 Share</button><button id="bShot">📷 Snapshot</button><button id="bFull">⛶ Fullscreen</button><button id="bLive">📍 Live Walk</button><button id="bProfile">👤 Profile</button><button id="bMore">⚙ Settings</button></div></div>
<div id="side" class="glass">
<input id="q" name="campus-search" type="search" autocomplete="off" autocapitalize="none" spellcheck="false" placeholder="Search block, hostel, sports, parking…">
<div id="sideTools"><button id="bVoice">🎙 Voice</button><button id="bFav">⭐ Favorites</button><button id="bClear">✕ Clear</button></div>
<div id="chips"></div><div id="list"></div></div>
<div id="card" class="glass"></div>
<div id="directionsPanel" class="glass">
  <button id="directionsClose" style="float:right;padding:2px 9px">✕</button>
  <h2>🧭 Walking Directions</h2>
  <div class="dirHead"><b id="dirDestination">Select a block</b><div id="dirSummary" style="color:var(--muted);font-size:12px;margin-top:3px">Choose a block, then press Get Directions.</div></div>
  <div class="dirMetric">
    <div><small>Distance</small><b id="dirDistance">--</b></div>
    <div><small>Walk time</small><b id="dirTime">--</b></div>
    <div><small>Heading</small><b id="dirHeading">--</b></div>
  </div>
  <p style="margin:8px 0 3px"><b>Turn-by-turn</b></p>
  <ol id="dirSteps"><li>Click a block to generate directions.</li></ol>
  <div class="row"><button id="dirWalk" class="pri">🚶 Start Walking</button><button id="dirLive">📍 Live Walk</button></div>
</div>
<div id="livePanel" class="glass">
  <button id="liveClose" style="float:right;padding:2px 9px">✕</button>
  <h2>📍 Real-Life Campus Walk</h2>
  <p>Use your phone/browser GPS when available, or use the built-in walking simulation on the 3D campus.</p>
  <div class="liveStatus"><span id="liveDot" class="liveDot"></span><div><b id="liveStatusText">Ready</b><div id="gpsCoords">GPS not started</div></div></div>
  <div class="liveGrid">
    <div class="liveStat"><small>Destination</small><b id="liveDest">Select a place</b></div>
    <div class="liveStat"><small>Progress</small><b id="liveProgress">0%</b></div>
    <div class="liveStat"><small>Distance</small><b id="liveDistance">0 m</b></div>
    <div class="liveStat"><small>ETA</small><b id="liveEta">--</b></div>
  </div>
  <div class="row">
    <button id="bGPS" class="pri">📍 Use My GPS</button>
    <button id="bSim">▶ Walk Simulation</button>
  </div>
  <div class="row">
    <button id="bPause">⏸ Pause</button>
    <button id="bFollow">🎯 Follow Walker</button>
    <button id="bStopWalk">⏹ Stop</button>
  </div>
  <p style="margin-bottom:4px"><b>Walking directions</b></p>
  <ol id="liveSteps"><li class="liveStep">Select a block to generate directions.</li></ol>
  <p><b>GPS:</b> <span id="gpsAccuracy">--</span></p>
</div>
<div id="walkerLabel">🚶 You are here</div>
<div id="profilePanel" class="glass">
  <button id="profileClose" style="float:right;padding:2px 9px">✕</button>
  <h2>👤 Professional Campus Profile</h2>
  <div class="profileHead"><div id="profileAvatar">JU</div><div><div id="profileNameView">New Campus Member</div><div id="profileMeta">Complete your local campus profile</div></div></div>
  <div class="profileMeter"><span id="profileMeterBar"></span></div>
  <small id="profileCompletion" style="color:var(--muted)">0% profile complete</small>
  <div class="profileGrid"><div class="profileStat"><small>Role</small><b id="profileRoleView">Student</b></div><div class="profileStat"><small>Password</small><b id="profilePasswordView">Not set</b></div></div>
  <label>Full Name</label><input id="profileName" maxlength="40" placeholder="Your professional name">
  <label>Role</label><select id="profileRole"><option>Student</option><option>Faculty</option><option>Staff</option><option>Visitor</option></select>
  <label>Department / Course</label><input id="profileDept" maxlength="60" placeholder="Department or course">
  <label>Year / Semester</label><input id="profileYear" maxlength="20" placeholder="Year / Semester">
  <label>Campus Password</label><input id="profilePassword" type="password" maxlength="64" placeholder="Create a local password">
  <small style="display:block;color:var(--muted);margin-top:5px">Local browser password only. No email, account, or server login is used.</small>
  <div class="row"><button id="profileSave" class="pri">💾 Save Profile</button><button id="profileClear">🧹 Clear</button></div>
  <div id="profilePreview" class="profilePreview">Professional profile preview will appear here.</div>
</div>
<div id="morePanel" class="glass">
  <button id="moreClose" style="float:right;padding:2px 9px">✕</button>
  <h2>⚙ Campus Settings</h2>
  <p>Profile, walking route, display and campus controls. No email login is required.</p>
  <div class="stat">
    <div><small>Selected</small><b id="stSelected">None</b></div>
    <div><small>Start</small><b id="stStart">#29</b></div>
    <div><small>Route</small><b id="stRoute">0 m</b></div>
    <div><small>FPS</small><b id="stFPS">--</b></div>
  </div>
  <div class="row">
    <button id="bAutoDay">☀️ Auto Day/Night</button>
    <button id="bClearRoute">🧹 Clear Route</button>
    <button id="bHelp">⌨ Shortcuts</button>
  </div>
  <ul>
    <li><b>F</b> fullscreen, <b>H</b> home/reset, <b>T</b> top view.</li>
    <li><b>O</b> orbit, <b>N</b> night mode, <b>M</b> markers.</li>
    <li><b>G</b> photos, <b>L</b> live walk, <b>R</b> clear route, <b>Esc</b> close panels.</li>
    <li>Click any building/marker in the 3D view to open its full card.</li>
  </ul>
</div>
<div id="toast"></div><div id="routeHint">Selected place</div>
<div id="comp" class="glass"><div id="needle"><b>N</b></div></div>
<div id="tip"></div>
<div id="lb"><div class="box"><img id="lbi"><p id="lbt"></p><div class="row"><button id="lp">◀</button><button id="l3" class="pri">🧊 Show in 3D</button><button id="ln">▶</button><button id="lx">✕ Close</button></div></div></div>
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
<script>
"use strict";
const $=id=>document.getElementById(id);
const PH=n=>`photos/photo_${String(n).padStart(2,'0')}.jpg`;
const ADDR="Joy University, Raja Nagar, Vadakangulam, Tamil Nadu 627116";
const PHOTOS=[
 {i:25,t:"Aerial view of Joy University campus",b:null},{i:0,t:"Gino Block with the ‘Joy University’ entrance sign",b:2},
 {i:5,t:"Gino Block – front façade",b:2},{i:1,t:"JU Arena",b:24},{i:17,t:"Student Activity Centre (SAC) dome building",b:21},
 {i:14,t:"Student Activity Centre – entrance",b:21},{i:6,t:"Arul Block (red) & SAC skyline",b:14},{i:9,t:"Arul Block beside the basketball court",b:14},
 {i:10,t:"Joe Block – Intel Unnati • NEC AI/HPC Labs",b:13},{i:18,t:"Joe Block with Eiffel-style tower",b:13},{i:13,t:"Soosai-B Block – School of Nursing",b:4},
 {i:2,t:"Aircraft display in front of the academic block",b:null},{i:4,t:"Aeronautical display & AI/ML screen block",b:null},{i:3,t:"“We Trust in God” plaza",b:null},
 {i:15,t:"Joy University signage building",b:null},{i:16,t:"Joy University logo wall",b:null},{i:12,t:"“Ignites Passion” campus mural",b:null},
 {i:7,t:"Volleyball court with wind turbines",b:null},{i:8,t:"Basketball court",b:null}];
const D="Block on the official Joy University campus map.";
/* [id,name,type,mapX,mapY,w,d,h,photos[],description] */
const BLOCKS=[
 [1,"Administrative Block","g",620,355,14,5,8,[],"Main administrative block at the heart of the campus."],
 [2,"Gino Block","w",336,380,14,4.5,7,[5,0],"White block with a perforated façade; the ‘Joy University’ entrance sign stands in front."],
 [3,"Soosai-A Block","w",225,355,9,3.5,7,[],D],[4,"Soosai-B Block","w",260,330,9,3.5,7,[13],"School of Nursing is signed on this block."],
 [5,"Selvam Block","w",272,298,5,3,6,[],D],[6,"St. Lourdes Chapel","c",352,290,4,4,5,[],"Chapel beside the central lawn."],
 [7,"Adhikaram Block","w",372,262,10,3,6,[],D],[8,"S.A. Raja Memorial Block","w",398,238,4,3,6,[],D],
 [9,"Gnana Prakasam Block","w",378,214,4,3,6,[],D],[10,"Annam Block","w",440,208,6,3,6,[],D],
 [11,"Grace Block","w",528,240,4,3,6,[],D],[12,"Celin Block","w",516,268,3,3,6,[],D],
 [13,"Joe Block","o",500,292,4.6,4.6,7,[10,18],"Round glass block topped by an Eiffel-style tower. Intel Unnati • NEC AI/HPC Labs."],
 [14,"Arul Block","r",548,282,4.5,3,7,[9,6],"Red block beside the basketball court."],
 [15,"S.A. Raja Convention Hall","w",562,254,4,3,5,[],"Convention hall."],[16,"Pushpam Block","w",573,228,3,3,6,[],D],
 [17,"Muthuraj Block","w",587,203,5,3,6,[],D],[18,"Cricket Ground","gr",724,196,18,18,.2,[],"Cricket ground."],
 [19,"Francis Block","w",750,226,8,3.5,6,[],D],[20,"Store & Maintenance","s",712,252,5,3,3,[],"Stores and maintenance."],
 [21,"Student Activity Centre (SAC)","sac",745,275,9,5,9,[17,14,6],"Glass & dark-brown façade with twin domes. Food, recreation and student services."],
 [22,"Manickam Block","w",902,272,8,3.5,6,[],D],[23,"Football Turf","ft",982,296,15,10,.2,[],"Football turf."],
 [24,"JU Arena","a",1104,318,16,9,9,[1],"Large arena hall with a silver wave-pattern glass façade."],
 [25,"Joshua Block","w",940,385,10,4,7,[],D],[26,"Joveena Block","w",1000,405,8,4,7,[],D],[27,"Julliana Block","w",940,472,10,5,7,[],D],
 [28,"Security Office","s",818,512,3,2.5,3,[],"Security office."],[29,"Waiting Hall","s",742,514,4,3,3,[],"Waiting hall (default start point)."],
 [30,"Canteen","s",768,577,5,3,3,[],"Canteen."],[31,"Outside Parking","pk",285,605,16,8,.2,[],"Outside parking."],[32,"Inside Parking","pk",255,432,10,6,.2,[],"Inside parking."],
 ["A","Sophia Hostel","h",70,432,8,4,7,[],"Hostel."],["B","Green Field Residence","h",155,296,7,4,6,[],"Residence."],
 ["C","Green Field Studio","h",130,270,5,3.5,5,[],"Studio."],["D","Cicily Hostel","h",195,248,9,4,7,[],"Hostel."],
 ["E","Theresa Hostel","h",610,242,6,4,6,[],"Hostel."],["F","Devasahayam Hostel","h",1133,358,8,4,7,[],"Hostel."]];
const CAT=b=>typeof b[0]==="string"?"Hostels":[18,23,24].includes(b[0])?"Sports":[6,15,20,21,28,29,30,31,32].includes(b[0])?"Services":"Blocks";
const wx=px=>(px-600)/6, wz=py=>(py-390)/5.2;
const bOf=id=>BLOCKS.find(b=>String(b[0])===String(id));

/* ---------- scene ---------- */
const canvas=$("c");
const renderer=new THREE.WebGLRenderer({canvas,antialias:true});
renderer.setPixelRatio(Math.min(devicePixelRatio,2));renderer.setSize(innerWidth,innerHeight);
renderer.outputEncoding=THREE.sRGBEncoding;renderer.shadowMap.enabled=true;renderer.shadowMap.type=THREE.PCFSoftShadowMap;
renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=1.05;
const scene=new THREE.Scene();scene.fog=new THREE.FogExp2(0xbfe0ff,.0026);
const cam=new THREE.PerspectiveCamera(50,innerWidth/innerHeight,.5,1500);cam.position.set(0,85,135);
const controls=new THREE.OrbitControls(cam,canvas);controls.enableDamping=true;controls.dampingFactor=.07;
controls.maxPolarAngle=Math.PI*.485;controls.minDistance=8;controls.maxDistance=260;controls.autoRotateSpeed=.6;
const hemi=new THREE.HemisphereLight(0xdff1ff,0x4b6b3a,.85);scene.add(hemi);
const sun=new THREE.DirectionalLight(0xffffff,1.15);sun.position.set(70,100,50);sun.castShadow=true;
sun.shadow.mapSize.set(4096,4096);Object.assign(sun.shadow.camera,{left:-130,right:130,top:90,bottom:-90,near:10,far:400});sun.shadow.bias=-.0004;scene.add(sun);
const skyU={top:{value:new THREE.Color(0x2a8cff)},bot:{value:new THREE.Color(0xd5ecff)}};
scene.add(new THREE.Mesh(new THREE.SphereGeometry(900,32,16),new THREE.ShaderMaterial({side:THREE.BackSide,depthWrite:false,fog:false,uniforms:skyU,
 vertexShader:"varying vec3 v;void main(){v=normalize(position);gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.);}",
 fragmentShader:"uniform vec3 top;uniform vec3 bot;varying vec3 v;void main(){float h=clamp(v.y*1.5+.08,0.,1.);gl_FragColor=vec4(mix(bot,top,pow(h,.7)),1.);}"})));
const stars=(()=>{const g=new THREE.BufferGeometry(),p=[];for(let i=0;i<900;i++){const a=Math.random()*6.283,e=Math.random()*1.3+.1,r=800;p.push(Math.cos(a)*Math.cos(e)*r,Math.sin(e)*r,Math.sin(a)*Math.cos(e)*r)}
 g.setAttribute("position",new THREE.Float32BufferAttribute(p,3));const m=new THREE.Points(g,new THREE.PointsMaterial({color:0xffffff,size:2.2,sizeAttenuation:false,transparent:true,opacity:0,fog:false}));scene.add(m);return m})();
const std=(c,o={})=>new THREE.MeshStandardMaterial(Object.assign({color:c,roughness:.7},o));
function box(w,h,d,mat,x=0,y=0,z=0){const m=new THREE.Mesh(new THREE.BoxGeometry(w,h,d),mat);m.position.set(x,y,z);m.castShadow=m.receiveShadow=true;return m}
function flat(w,d,mat,x,y,z){const m=new THREE.Mesh(new THREE.PlaneGeometry(w,d),mat);m.rotation.x=-Math.PI/2;m.position.set(x,y,z);m.receiveShadow=true;scene.add(m);return m}
function grassTex(){const c=document.createElement("canvas");c.width=c.height=256;const g=c.getContext("2d");g.fillStyle="#5c9a3d";g.fillRect(0,0,256,256);
 for(let i=0;i<2600;i++){g.fillStyle=`hsl(${90+Math.random()*30},${45+Math.random()*20}%,${30+Math.random()*16}%)`;g.fillRect(Math.random()*256,Math.random()*256,2,3)}
 const t=new THREE.CanvasTexture(c);t.wrapS=t.wrapT=THREE.RepeatWrapping;t.repeat.set(60,40);t.encoding=THREE.sRGBEncoding;return t}
flat(320,220,std(0xffffff,{map:grassTex(),roughness:1}),0,0,0);flat(2000,2000,std(0x78a955,{roughness:1}),0,-.2,0);
const roads=[];
function road(x1,y1,x2,y2,wpx,color=0x4a4f57){const a=[wx(x1),wz(y1)],b=[wx(x2),wz(y2)],w=Math.abs(b[0]-a[0])+wpx/6,d=Math.abs(b[1]-a[1])+wpx/5.2,cx=(a[0]+b[0])/2,cz=(a[1]+b[1])/2;
 flat(w,d,std(color,{roughness:.9}),cx,.06,cz);roads.push([cx,cz,w,d])}
road(560,440,680,490,10,0xb9b3a4);
flat(22,11,std(0x62b043,{roughness:1}),wx(400),.05,wz(340));
function court(px,py,w,d){flat(w,d,std(0xc4262e,{roughness:.6}),wx(px),.09,wz(py));const l=flat(w*.94,d*.9,new THREE.MeshBasicMaterial({color:0xffffff,wireframe:true}),wx(px),.11,wz(py));l.receiveShadow=false}
court(640,330,6,5);court(680,330,6,5);court(870,330,5,4);

/* ---------- buildings ---------- */
const winMats=[],emis=[];let NIGHT=false;
function winCanvas(wall,glass,night){const c=document.createElement("canvas");c.width=c.height=256;const g=c.getContext("2d");g.fillStyle=night?"#000":wall;g.fillRect(0,0,256,256);
 for(let r=0;r<2;r++)for(let k=0;k<4;k++){const x=k*64+10,y=r*128+34;
  if(night){g.fillStyle=(Math.sin(k*7+r*3)+1)>.55?"#ffd98a":"#000";g.fillRect(x,y,44,52)}
  else{const gr=g.createLinearGradient(x,y,x+44,y+52);gr.addColorStop(0,glass);gr.addColorStop(1,"#0b1d3a");g.fillStyle=gr;g.fillRect(x,y,44,52);g.fillStyle="#ffffff30";g.fillRect(x,y,44,8)}}
 const t=new THREE.CanvasTexture(c);t.wrapS=t.wrapT=THREE.RepeatWrapping;t.encoding=THREE.sRGBEncoding;t.anisotropy=4;return t}
function sideMat(wall,glass,len,h){const m=new THREE.MeshStandardMaterial({map:winCanvas(wall,glass,false),emissiveMap:winCanvas(wall,glass,true),emissive:0xffffff,emissiveIntensity:NIGHT?1:0,roughness:.75});
 m.map.repeat.set(Math.max(1,len/6.4),Math.max(1,h/4.8));m.emissiveMap.repeat.copy(m.map.repeat);winMats.push(m);return m}
const pick=[],nodes={};
function tag(o,id){o.traverse(x=>{if(x.isMesh){x.userData.id=id;pick.push(x)}})}
function blockBox(w,d,h,wall,glass){const roof=std(0xdedede,{roughness:.9}),bot=std(0x999999,{roughness:.9});
 const b=new THREE.Mesh(new THREE.BoxGeometry(w,h,d),[sideMat(wall,glass,d,h),sideMat(wall,glass,d,h),roof,bot,sideMat(wall,glass,w,h),sideMat(wall,glass,w,h)]);
 b.position.y=h/2;b.castShadow=b.receiveShadow=true;return b}
function build(b){const [id,name,type,px,py,w,d,h]=b;const g=new THREE.Group();g.position.set(wx(px),0,wz(py));let top=h;
 if("wrch".includes(type)&&type.length===1){
  const wall=type==="r"?"#d9512c":type==="h"?"#dfe6ff":"#f1f3f6",glass=type==="r"?"#1d3f9a":"#5d7fb0";g.add(blockBox(w,d,h,wall,glass));
  const pc=type==="r"?0xd9512c:type==="h"?0x3651c9:0x4257c7;for(let x=-w/2+.4;x<=w/2;x+=Math.max(2.4,w/6))g.add(box(.4,h,.5,std(pc),x,h/2,d/2+.2));
  g.add(box(w+.3,.4,d+.3,std(0xcfd3da),0,h+.2,0));
  if(type==="c"){const r=new THREE.Mesh(new THREE.ConeGeometry(Math.max(w,d)*.75,3,4),std(0x9b3b2e));r.rotation.y=Math.PI/4;r.position.y=h+1.7;r.castShadow=true;g.add(r);
   g.add(box(.25,2,.25,std(0xf5c542),0,h+4.2,0));g.add(box(1.1,.25,.25,std(0xf5c542),0,h+4.6,0));top=h+5}
 }else if(type==="g"){const gm=std(0x1d3f7a,{metalness:.6,roughness:.15,emissive:0x0a1a3a,emissiveIntensity:0});emis.push(gm);
  g.add(box(w,h,d,gm,0,h/2,0));for(let y=0;y<=h;y+=2.7)g.add(box(w+.4,.3,d+.4,std(0xf2f4f8),0,y+.2,0));g.add(box(w*.3,3,d*.8,std(0xeeeeee),0,h+1.5,0));top=h+3;
 }else if(type==="sac"){g.add(box(w,h,d,std(0x5a4a45,{metalness:.3,roughness:.3}),0,h/2,0));
  const gl=std(0x274a7d,{metalness:.7,roughness:.1,emissive:0x1a2a4a,emissiveIntensity:0});emis.push(gl);g.add(box(w*.9,h*.7,d+.15,gl,0,h*.45,0));
  for(let y=0;y<=h;y+=3)g.add(box(w+.5,.5,d+.6,std(0xf4f4f4),0,y+.3,0));
  for(const s of[-1,1]){const dm=new THREE.Mesh(new THREE.SphereGeometry(d*.5,20,10,0,6.283,0,1.57),std(0xf4f4f4));dm.scale.set(1.4,.6,1);dm.position.set(s*w*.32,h,0);dm.castShadow=true;g.add(dm)}top=h+3;
 }else if(type==="o"){const r=w/2;const base=new THREE.Mesh(new THREE.CylinderGeometry(r,r,h*.42,32),std(0xd7dfea));base.position.y=h*.21;base.castShadow=true;g.add(base);
  const gm=std(0x1740c9,{metalness:.7,roughness:.12,emissive:0x0a1a5a,emissiveIntensity:0});emis.push(gm);
  const up=new THREE.Mesh(new THREE.CylinderGeometry(r+.2,r+.2,h*.5,32),gm);up.position.y=h*.67;up.castShadow=true;g.add(up);
  const rf=new THREE.Mesh(new THREE.CylinderGeometry(r+.35,r+.35,.35,32),std(0xe8e0a0));rf.position.y=h*.92+.2;g.add(rf);
  const tw=new THREE.Mesh(new THREE.ConeGeometry(1.3,9,4),std(0xd8433c,{transparent:true,opacity:.5}));tw.rotation.y=Math.PI/4;tw.position.y=h+4.6;g.add(tw);
  const tw2=new THREE.Mesh(new THREE.ConeGeometry(1.3,9,4,1,true),std(0xd8433c,{side:THREE.DoubleSide,wireframe:true}));tw2.rotation.y=Math.PI/4;tw2.position.y=h+4.6;g.add(tw2);top=h+9.5;
 }else if(type==="a"){g.add(box(w,h,d,std(0x1d2230),0,h/2,0));
  const fg=std(0x2a4f9a,{metalness:.8,roughness:.08,emissive:0x0a1a3a,emissiveIntensity:0});emis.push(fg);g.add(box(w*.42,h*1.2,.6,fg,w*.12,h*.6,d/2+.1));
  for(let i=0;i<14;i++)g.add(box(.18,h*1.25,.3,std(0xe8edf5,{metalness:.6}),w*.12-w*.2+i*(w*.4/14),h*.62,d/2+.5));
  const rf=new THREE.Mesh(new THREE.CylinderGeometry(d*.6,d*.6,w,24,1,false,0,Math.PI),std(0xcfd6e0,{side:THREE.DoubleSide}));rf.rotation.z=Math.PI/2;rf.rotation.y=Math.PI/2;rf.position.y=h;rf.castShadow=true;g.add(rf);top=h+5;
 }else if(type==="gr"){const m=new THREE.Mesh(new THREE.CircleGeometry(w/2,48),std(0x6dc04a,{roughness:1}));m.rotation.x=-Math.PI/2;m.position.y=.08;m.receiveShadow=true;g.add(m);
  const r=new THREE.Mesh(new THREE.RingGeometry(w/2-.4,w/2,48),new THREE.MeshBasicMaterial({color:0xffffff,side:THREE.DoubleSide}));r.rotation.x=-Math.PI/2;r.position.y=.1;g.add(r);top=1;
 }else if(type==="ft"){const m=new THREE.Mesh(new THREE.PlaneGeometry(w,d),std(0x3f9d3a,{roughness:1}));m.rotation.x=-Math.PI/2;m.position.y=.08;g.add(m);
  const l=new THREE.Mesh(new THREE.PlaneGeometry(w*.94,d*.9),new THREE.MeshBasicMaterial({color:0xffffff,wireframe:true}));l.rotation.x=-Math.PI/2;l.position.y=.1;g.add(l);
  for(const s of[-1,1]){g.add(box(.2,2.2,.2,std(0xffffff),s*w/2,1.1,-1.2));g.add(box(.2,2.2,.2,std(0xffffff),s*w/2,1.1,1.2));g.add(box(.2,.2,2.6,std(0xffffff),s*w/2,2.2,0))}top=2;
 }else if(type==="pk"){g.add(box(w,.15,d,std(0x62666e),0,.08,0));const cols=[0xdd3333,0x3399cc,0xeeeeee,0x222222,0xffcc33,0x33aa55];
  for(let i=0;i<Math.floor(w/1.8);i++)for(let j=0;j<Math.floor(d/2.6);j++)if(Math.random()<.65)g.add(box(1.1,.7,1.9,std(cols[(Math.random()*6)|0],{metalness:.5,roughness:.35}),-w/2+1+i*1.8,.5,-d/2+1.3+j*2.6));top=1;
 }else{g.add(box(w,h,d,std(0xe9dcc4),0,h/2,0));g.add(box(w+.4,.3,d+.4,std(0x8a3f2c),0,h+.15,0))}
 g.userData.top=top;scene.add(g);nodes[id]=g;
 g.add(box(w*1.02,Math.max(h,.6),d*1.02,new THREE.MeshBasicMaterial({visible:false}),0,Math.max(h,.6)/2,0));tag(g,id)}
BLOCKS.forEach(build);

/* ---------- ROAD NETWORK (drawn + used for routing) ---------- */
const ROADS=[
 [[100,225],[290,225]],[[100,225],[100,395],[100,522]],[[290,395],[100,395]],
 [[290,192],[290,225],[290,330],[290,395],[290,430],[290,522]],[[290,192],[470,192],[640,192]],
 [[470,192],[470,330]],[[640,192],[640,330]],[[290,330],[470,330],[560,330],[640,330],[830,330],[1040,330]],
 [[560,330],[560,430]],[[290,430],[560,430],[620,430],[830,430],[1040,430],[1133,430],[1133,380]],
 [[1040,330],[1040,430]],[[620,385],[620,430],[620,522],[620,600]],[[100,522],[290,522],[340,522],[620,522],[830,522]],
 [[340,522],[340,600]],[[340,600],[620,600],[830,600]],[[830,190],[830,330],[830,430],[830,522],[830,600]]];
const RW=2.6;
const roadTex=(()=>{const c=document.createElement("canvas");c.width=128;c.height=64;const g=c.getContext("2d");g.fillStyle="#454a52";g.fillRect(0,0,128,64);
 g.fillStyle="#f2f2f2";g.fillRect(0,4,128,3);g.fillRect(0,57,128,3);g.fillStyle="#f6c343";g.fillRect(0,29,64,6);
 const t=new THREE.CanvasTexture(c);t.wrapS=t.wrapT=THREE.RepeatWrapping;t.anisotropy=8;t.encoding=THREE.sRGBEncoding;return t})();
const walkMat=std(0xcfc7b4,{roughness:1});
const gNodes=[],gAdj=[],gKey=new Map();
function gNode(px,py){const k=Math.round(px)+","+Math.round(py);if(gKey.has(k))return gKey.get(k);const i=gNodes.length;gNodes.push(new THREE.Vector3(wx(px),0,wz(py)));gAdj.push([]);gKey.set(k,i);return i}
function gEdge(a,b){const w=gNodes[a].distanceTo(gNodes[b]);gAdj[a].push([b,w]);gAdj[b].push([a,w])}
ROADS.forEach(pl=>{for(let i=0;i<pl.length-1;i++){const [x1,y1]=pl[i],[x2,y2]=pl[i+1];
 const A=new THREE.Vector3(wx(x1),0,wz(y1)),B=new THREE.Vector3(wx(x2),0,wz(y2)),L=A.distanceTo(B),horiz=Math.abs(B.x-A.x)>=Math.abs(B.z-A.z);
 const g=new THREE.Group();g.position.set((A.x+B.x)/2,.072,(A.z+B.z)/2);g.rotation.y=horiz?0:Math.PI/2;
 const sw=new THREE.Mesh(new THREE.PlaneGeometry(L+RW+1.4,RW+1.4),walkMat);sw.rotation.x=-Math.PI/2;sw.receiveShadow=true;g.add(sw);
 const tx=roadTex.clone();tx.needsUpdate=true;tx.repeat.set((L+RW)/5,1);
 const rd=new THREE.Mesh(new THREE.PlaneGeometry(L+RW,RW),std(0xffffff,{map:tx,roughness:.9}));rd.rotation.x=-Math.PI/2;rd.position.y=.006;rd.receiveShadow=true;g.add(rd);scene.add(g);
 roads.push([g.position.x,g.position.z,horiz?L+RW:RW,horiz?RW:L+RW]);
 const n=Math.max(1,Math.ceil(L/7));let prev=gNode(x1,y1);
 for(let k=1;k<=n;k++){const cur=gNode(x1+(x2-x1)*k/n,y1+(y2-y1)*k/n);gEdge(prev,cur);prev=cur}}});
const bNode={};
BLOCKS.forEach(b=>{const id=b[0],p=nodes[id].position;let best=0,bd=1e9;
 gNodes.forEach((n,i)=>{const d=Math.hypot(n.x-p.x,n.z-p.z);if(d<bd){bd=d;best=i}});bNode[id]=best;
 const q=gNodes[best],dx=p.x-q.x,dz=p.z-q.z,L2=Math.hypot(dx,dz);if(L2<.5)return;
 const g=new THREE.Group();g.position.set((p.x+q.x)/2,.073,(p.z+q.z)/2);g.rotation.y=-Math.atan2(dz,dx);
 const m=new THREE.Mesh(new THREE.PlaneGeometry(L2,1.1),walkMat);m.rotation.x=-Math.PI/2;g.add(m);scene.add(g)});
function findPath(a,b){const s=bNode[a],t=bNode[b],N=gNodes.length,dist=new Array(N).fill(1e9),prev=new Array(N).fill(-1),done=new Array(N).fill(false);dist[s]=0;
 for(let it=0;it<N;it++){let u=-1;for(let i=0;i<N;i++)if(!done[i]&&(u<0||dist[i]<dist[u]))u=i;if(u<0||dist[u]>=1e9)break;done[u]=true;if(u===t)break;
  gAdj[u].forEach(([v,w])=>{if(dist[u]+w<dist[v]){dist[v]=dist[u]+w;prev[v]=u}})}
 if(dist[t]>=1e9)return null;const idx=[];for(let u=t;u>=0;u=prev[u])idx.unshift(u);
 const pa=nodes[a].position,pb=nodes[b].position,P=[pa.clone().setY(.7)];idx.forEach(i=>P.push(gNodes[i].clone().setY(.7)));P.push(pb.clone().setY(.7));
 return{P,len:dist[t]+pa.distanceTo(gNodes[s])+pb.distanceTo(gNodes[t])}}

/* markers */
const markers=new THREE.Group();scene.add(markers);
function markerTex(t,hostel){const c=document.createElement("canvas");c.width=c.height=128;const g=c.getContext("2d");
 g.beginPath();g.arc(64,64,58,0,7);g.fillStyle=hostel?"#c1121f":"#fbbf24";g.fill();g.lineWidth=6;g.strokeStyle="#fff";g.stroke();
 g.fillStyle=hostel?"#fff":"#111";g.font="bold 64px Arial";g.textAlign="center";g.textBaseline="middle";g.fillText(String(t),64,68);const tx=new THREE.CanvasTexture(c);tx.encoding=THREE.sRGBEncoding;return tx}
BLOCKS.forEach(b=>{const id=b[0],nd=nodes[id];const s=new THREE.Sprite(new THREE.SpriteMaterial({map:markerTex(id,typeof id==="string"),depthTest:false,transparent:true}));
 s.scale.set(3.4,3.4,1);s.position.set(nd.position.x,(nd.userData.top||2)+3,nd.position.z);s.renderOrder=10;s.userData.id=id;pick.push(s);markers.add(s)});

/* trees, turbines, mountains, clouds */
const rects=BLOCKS.map(b=>[wx(b[3]),wz(b[4]),b[5]+5,b[6]+5]);
const free=(x,z)=>{for(const r of rects)if(Math.abs(x-r[0])<r[2]/2&&Math.abs(z-r[1])<r[3]/2)return false;for(const r of roads)if(Math.abs(x-r[0])<r[2]/2+1.2&&Math.abs(z-r[1])<r[3]/2+1.2)return false;return true};
const pts=[];let tries=0;while(pts.length<260&&tries++<6000){const x=(Math.random()-.5)*230,z=(Math.random()-.5)*130;if(free(x,z))pts.push([x,z,Math.random()])}
const trunk=new THREE.InstancedMesh(new THREE.CylinderGeometry(.22,.32,1,6),std(0x8a6a48),pts.length),crown=new THREE.InstancedMesh(new THREE.SphereGeometry(1,10,8),std(0x2f8f3a,{roughness:.9}),pts.length);
const M4=new THREE.Matrix4(),Q=new THREE.Quaternion(),Sv=new THREE.Vector3(),Pv=new THREE.Vector3();
pts.forEach((p,i)=>{const th=2+p[2]*3;Sv.set(1,th,1);Pv.set(p[0],th/2,p[1]);M4.compose(Pv,Q,Sv);trunk.setMatrixAt(i,M4);const r=1.9+p[2];Sv.set(r,r*.9,r);Pv.set(p[0],th+r*.5,p[1]);M4.compose(Pv,Q,Sv);crown.setMatrixAt(i,M4)});
[trunk,crown].forEach(m=>{m.castShadow=true;scene.add(m)});
const rotors=[];
function turbine(x,z,s=1){const g=new THREE.Group();const tw=new THREE.Mesh(new THREE.CylinderGeometry(.35,.6,16,10),std(0xf2f2f2));tw.position.y=8;g.add(tw);g.add(box(1.2,1,2.2,std(0xe6e6e6),0,16.2,0));
 const rot=new THREE.Group();rot.position.set(0,16.2,1.3);for(let i=0;i<3;i++){const pv=new THREE.Group();pv.rotation.z=i*2.094;pv.add(box(.5,8,.14,std(0xffffff),0,4,0));rot.add(pv)}
 g.add(rot);rotors.push(rot);g.position.set(x,0,z);g.scale.setScalar(s);scene.add(g)}
for(let i=-6;i<=6;i++)turbine(i*22+Math.sin(i)*6,-88-Math.abs(i%3)*10,1.3);for(let i=0;i<5;i++)turbine(105+i*3,-60+i*28,1.1);turbine(-108,20);turbine(-112,-30);
for(let i=0;i<14;i++){const m=new THREE.Mesh(new THREE.ConeGeometry(30+Math.random()*40,45+Math.random()*50,5),std(0x5d7ea3,{roughness:1}));m.position.set(-450+i*70+Math.random()*30,15,-330-Math.random()*60);scene.add(m)}
const ct=(()=>{const c=document.createElement("canvas");c.width=c.height=128;const g=c.getContext("2d");const r=g.createRadialGradient(64,64,4,64,64,62);r.addColorStop(0,"#fff");r.addColorStop(1,"#fff0");g.fillStyle=r;g.fillRect(0,0,128,128);return new THREE.CanvasTexture(c)})();
const clouds=[];for(let i=0;i<22;i++){const s=new THREE.Sprite(new THREE.SpriteMaterial({map:ct,transparent:true,opacity:.75,depthWrite:false,fog:false}));const k=40+Math.random()*60;s.scale.set(k*1.8,k*.7,1);s.position.set((Math.random()-.5)*600,110+Math.random()*60,-200+Math.random()*300);scene.add(s);clouds.push(s)}

/* street lamps + cars */
const RZ=wz(522),lampM=new THREE.MeshStandardMaterial({color:0xfff2c8,emissive:0xffd58a,emissiveIntensity:0}),glows=[],cars=[];
for(let x=-70;x<=36;x+=9){const p=new THREE.Mesh(new THREE.CylinderGeometry(.12,.16,4.5,6),std(0x333a44));p.position.set(x,2.25,RZ-2.4);p.castShadow=true;scene.add(p);
 const bulb=new THREE.Mesh(new THREE.SphereGeometry(.35,10,8),lampM);bulb.position.set(x,4.6,RZ-2.4);scene.add(bulb);
 const gl=new THREE.Sprite(new THREE.SpriteMaterial({map:ct,color:0xffd58a,blending:THREE.AdditiveBlending,transparent:true,depthWrite:false,opacity:0}));gl.scale.set(6,6,1);gl.position.copy(bulb.position);scene.add(gl);glows.push(gl)}
for(let i=0;i<7;i++){const c=box(2,.7,1.1,std([0xdd3333,0x3399cc,0xeeeeee,0xffcc33][i%4],{metalness:.5,roughness:.35}),-70+i*15,.5,RZ+(i%2?.6:-.6));c.userData.v=(.05+Math.random()*.05)*(i%2?1:-1);scene.add(c);cars.push(c)}

/* ---------- camera fly ---------- */
const ring=new THREE.Mesh(new THREE.RingGeometry(1,1.25,48),new THREE.MeshBasicMaterial({color:0x5eead4,side:THREE.DoubleSide,transparent:true,opacity:.9,depthTest:false}));ring.rotation.x=-Math.PI/2;ring.position.y=.3;ring.visible=false;ring.renderOrder=9;scene.add(ring);
let selectedHelper=null;
function highlightBlock(id){
  if(selectedHelper){scene.remove(selectedHelper);selectedHelper=null;}
  const g=nodes[id]; if(!g) return;
  const box3=new THREE.Box3().setFromObject(g);
  selectedHelper=new THREE.Box3Helper(box3,0x5eead4); selectedHelper.renderOrder=20; scene.add(selectedHelper);
  const c=box3.getCenter(new THREE.Vector3()); ring.position.set(c.x,.35,c.z); ring.visible=true;
}
let fly=null,CUR=null;const clock=new THREE.Clock();
const flyTo=(p,t,d=1.6)=>{fly={p0:cam.position.clone(),t0:controls.target.clone(),p1:p,t1:t,s:clock.elapsedTime,d}};
const HOME=[new THREE.Vector3(0,85,135),new THREE.Vector3(0,0,0)];
function flyBlock(id){const nd=nodes[id],t=nd.position.clone();t.y=(nd.userData.top||4)*.4;const dir=cam.position.clone().sub(controls.target);dir.y=0;if(dir.lengthSq()<1)dir.set(0,0,1);dir.normalize();
 const dist=Math.max(22,bOf(id)[5]*1.4);flyTo(t.clone().add(dir.multiplyScalar(dist)).add(new THREE.Vector3(0,dist*.55,0)),t)}

/* ---------- NAVIGATION: distance + direction ---------- */
const SCALE_M=2.5,WALK_MS=1.3,CARD8=["N","NE","E","SE","S","SW","W","NW"],ARW=["↑","↗","→","↘","↓","↙","←","↖"];
let START=29,routeLen=0;const navG=new THREE.Group();scene.add(navG);let curve=null,flow=[];
let currentPathRes=null, currentDestination=null, walkU=0, walkRunning=false, walkPaused=false, followWalker=false, gpsWatchId=null, gpsLast=null, walkerMesh=null;
const routeStartRing=new THREE.Mesh(new THREE.RingGeometry(1.0,1.45,48),new THREE.MeshBasicMaterial({color:0x60a5fa,side:THREE.DoubleSide,transparent:true,opacity:.95,depthTest:false}));routeStartRing.rotation.x=-Math.PI/2;routeStartRing.position.y=.36;routeStartRing.visible=false;routeStartRing.renderOrder=11;scene.add(routeStartRing);
const routeEndRing=new THREE.Mesh(new THREE.RingGeometry(1.2,1.7,48),new THREE.MeshBasicMaterial({color:0xfbbf24,side:THREE.DoubleSide,transparent:true,opacity:.95,depthTest:false}));routeEndRing.rotation.x=-Math.PI/2;routeEndRing.position.y=.35;routeEndRing.visible=false;routeEndRing.renderOrder=11;scene.add(routeEndRing);
const fmt=m=>m>=1000?(m/1000).toFixed(2)+" km":Math.round(m)+" m";
function dirInfo(a,b){
  const dx=b.x-a.x,dz=b.z-a.z,deg=(Math.atan2(dx,-dz)*180/Math.PI+360)%360,k=Math.round(deg/45)%8;
  return{deg:Math.round(deg),card:CARD8[k],arrow:ARW[k]};
}

function clearRoute(){
  while(navG.children.length) navG.remove(navG.children[0]);
  flow=[]; curve=null; currentPathRes=null; currentDestination=null; routeLen=0; routeEndRing.visible=false; routeStartRing.visible=false;
  stopWalkSimulation(false);
  if(typeof updateStats==="function") updateStats();
  if(typeof renderLiveInfo==="function") renderLiveInfo();
}

function drawRoute(pathRes){
  clearRoute();
  if(!pathRes||!pathRes.P||pathRes.P.length<2) return;
  currentPathRes=pathRes;
  const pts=pathRes.P.map(p=>p.clone().setY(2.15));
  routeLen=pathRes.len*SCALE_M;
  curve=new THREE.CatmullRomCurve3(pts,false,"centripetal",0.15);
  const geo=new THREE.TubeGeometry(curve,Math.max(48,pts.length*10),0.78,12,false);
  const mat=new THREE.MeshBasicMaterial({color:0x5eead4,transparent:true,opacity:.96,depthTest:false});
  const routeMesh=new THREE.Mesh(geo,mat);routeMesh.renderOrder=12;navG.add(routeMesh);
  const glowGeo=new THREE.TubeGeometry(curve,Math.max(48,pts.length*10),1.35,10,false);
  const glowMat=new THREE.MeshBasicMaterial({color:0x60a5fa,transparent:true,opacity:.18,depthTest:false});
  const glowMesh=new THREE.Mesh(glowGeo,glowMat);glowMesh.renderOrder=11;navG.add(glowMesh);
  const dotGeo=new THREE.SphereGeometry(.7,10,10);
  const dotMat=new THREE.MeshBasicMaterial({color:0xfbbf24,depthTest:false});
  for(let i=0;i<12;i++){const m=new THREE.Mesh(dotGeo,dotMat);m.renderOrder=13;navG.add(m);flow.push(m);}
  const startP=pts[0],endP=pts[pts.length-1];
  routeStartRing.position.set(startP.x,.35,startP.z);
  routeStartRing.visible=true;
  routeEndRing.position.set(endP.x,.35,endP.z);
  routeEndRing.visible=true;
  currentDestination=CUR;
  walkU=0;
  ensureWalker();
  renderLiveInfo();
}

/* UI Controls & List Filtering */
const qInput = $("q"), listEl = $("list"), chipsEl = $("chips"), cardEl = $("card");
const morePanel=$("morePanel"), toastEl=$("toast");
let favorites=new Set(JSON.parse(localStorage.getItem("joyCampusFavoritesV2")||"[]"));
let showFavorites=false, autoDay=false, autoTimer=null, fpsFrames=0, fpsLast=performance.now();
const cats = ["All", "Blocks", "Hostels", "Sports", "Services"];
let activeCat = "All";

function renderChips(){
  chipsEl.innerHTML = cats.map(c => `<button class="${c===activeCat?'on':''}" onclick="setCat('${c}')">${c}</button>`).join("");
}

window.setCat = function(c){
  activeCat = c;
  renderChips();
  renderList();
};

function renderList(){
  // Some browsers may autofill an email address into the search box.
  // Never use an email address as a campus search query.
  if(qInput.value.includes('@')) qInput.value = '';
  const q = qInput.value.toLowerCase().trim();
  const filtered = BLOCKS.filter(b => {
    const catMatch = activeCat === "All" || CAT(b) === activeCat;
    const favMatch = !showFavorites || favorites.has(String(b[0]));
    const nameMatch = String(b[0]).toLowerCase().includes(q) || b[1].toLowerCase().includes(q) || b[9].toLowerCase().includes(q);
    return catMatch && favMatch && nameMatch;
  });
  
  listEl.innerHTML = filtered.map(b => {
    const isH = typeof b[0] === "string";
    return `    <div class="it ${CUR===b[0]?'sel':''}" title="Click to view block information" onclick="selectBlock('${b[0]}')">
      <div class="num ${isH?'h':''}">${b[0]}</div>
      <div><b>${b[1]}</b><small>${CAT(b)} • ${b[5]}x${b[6]}m</small></div>
    </div>`;
  }).join("");
}

qInput.addEventListener("input", renderList);

function renderDirections(id, pathRes){
  const panel=$("directionsPanel"); const b=bOf(id);
  if(!b || !pathRes) return;
  const m=pathRes.len*SCALE_M;
  const mins=Math.max(1,Math.ceil(m/(WALK_MS*60)));
  const info=dirInfo(nodes[START].position,nodes[id].position);
  $("dirDestination").textContent=`${b[0]}. ${b[1]}`;
  $("dirSummary").textContent=`From #${START} to ${b[0]} • Route highlighted in the 3D campus`;
  $("dirDistance").textContent=fmt(m);
  $("dirTime").textContent=`~${mins} min`;
  $("dirHeading").textContent=`${info.arrow} ${info.card}`;
  const P=pathRes.P||[]; const steps=[];
  for(let i=1;i<P.length;i++){
    const d=dirInfo(P[i-1],P[i]); const dm=P[i-1].distanceTo(P[i])*SCALE_M;
    if(dm>=2) steps.push(`${d.arrow} Walk ${d.card} for ${fmt(dm)}`);
  }
  if(!steps.length) steps.push(`🚶 Continue to ${b[1]}`);
  steps.push(`📍 Arrive at ${b[1]}`);
  $("dirSteps").innerHTML=steps.slice(0,12).map((x,i)=>`<li>${i===0?'🚩 ':''}${x}</li>`).join('');
  panel.classList.add('show');
  $("dirWalk").onclick=()=>startWalkingTo(id);
  $("dirLive").onclick=()=>openLiveWalk(id);
}

window.getDirections = function(id){
  const b = bOf(id);
  if(!b){
    showToast("Select a valid campus block first");
    return false;
  }
  id = b[0];
  if(!nodes[id]){
    showToast("Campus location data is unavailable for this block");
    return false;
  }
  if(START === null || START === undefined || !nodes[START]){
    showToast("Set a valid starting location first");
    return false;
  }

  CUR = id;
  currentDestination = id;
  updateStats();
  clearRoute();
  currentDestination = id;

  let pathRes = findPath(START, id);
  if(!pathRes){
    const a = nodes[START].position.clone().setY(1.05);
    const end = nodes[id].position.clone().setY(1.05);
    pathRes = {P:[a,end],len:a.distanceTo(end)};
    showToast("Road graph route unavailable; showing a direct campus route");
  }

  drawRoute(pathRes);
  currentDestination = id;
  renderDirections(id,pathRes);
  renderLiveInfo();
  return true;
};

window.selectBlock = function(id){
  const b = bOf(id);
  if(!b) return;
  id = b[0];

  CUR = id;
  clearRoute();
  $("directionsPanel").classList.remove("show");
  currentDestination = id;
  updateStats();
  flyBlock(id);
  highlightBlock(id);
  const routeHint=$("routeHint"); routeHint.textContent=`Selected: ${b[0]}. ${b[1]}`; routeHint.classList.add("show");
  clearTimeout(selectBlock.hintTimer); selectBlock.hintTimer=setTimeout(()=>routeHint.classList.remove("show"),2400);
  renderList();

  cardEl.style.display = "block";
  const favOn=favorites.has(String(id));
  cardEl.innerHTML = `<button id="x" onclick="closeCard()">✕</button>
    <button id="favStar" title="Save this place" onclick="toggleFavorite('${id}')">${favOn?'⭐ Saved':'☆ Save'}</button>
    <span class="tag">${CAT(b)}</span>
    <h2>${b[0]}. ${b[1]}</h2>
    <p>${b[9]}</p>
    <div class="row">
      <button onclick="setStart('${id}')">🚩 Set Start</button>
      <button class="pri" onclick="getDirections('${id}')">🧭 Get Directions</button>
      <button onclick="openLiveWalk('${id}')">📍 Live GPS</button>
    </div>`;
  renderLiveInfo();
};

function ensureWalker(){
  if(walkerMesh) return;
  const g=new THREE.Group();
  const bodyGeometry=typeof THREE.CapsuleGeometry==="function"?new THREE.CapsuleGeometry(.42,1.0,4,8):new THREE.CylinderGeometry(.42,.42,1.6,10);
  const body=new THREE.Mesh(bodyGeometry,new THREE.MeshBasicMaterial({color:0xfbbf24,depthTest:false}));
  body.position.y=1.0; g.add(body);
  const head=new THREE.Mesh(new THREE.SphereGeometry(.38,12,10),new THREE.MeshBasicMaterial({color:0xffe0bd,depthTest:false})); head.position.y=2.0; g.add(head);
  g.renderOrder=30; g.visible=false; scene.add(g); walkerMesh=g;
}
function routeStepList(){
  const el=$("liveSteps");
  if(!currentPathRes||!currentPathRes.P||currentPathRes.P.length<2){el.innerHTML='<li class="liveStep">Select a block to generate directions.</li>';return;}
  const P=currentPathRes.P; const steps=[];
  for(let i=1;i<P.length;i++){
    const d=dirInfo(P[i-1],P[i]);
    const dist=P[i-1].distanceTo(P[i])*SCALE_M;
    if(dist<3) continue;
    steps.push({text:`${d.arrow} Continue ${d.card} for ${fmt(dist)}`,dist});
  }
  if(steps.length===0) steps.push({text:'→ Continue to destination',dist:currentPathRes.len*SCALE_M});
  const max=10;
  el.innerHTML=steps.slice(0,max).map((x,i)=>`<li class="liveStep" data-step="${i}">${x.text}</li>`).join('');
}
function renderLiveInfo(){
  const b=currentDestination!=null?bOf(currentDestination):null;
  $("liveDest").textContent=b?`${b[0]}. ${b[1]}`:'Select a place';
  const m=routeLen||0; $("liveDistance").textContent=fmt(m);
  const remain=Math.max(0,m*(1-walkU)); $("liveProgress").textContent=currentPathRes?Math.round(walkU*100)+'%':'0%';
  $("liveEta").textContent=currentPathRes?(Math.max(1,Math.ceil(remain/(WALK_MS*60)))+' min'):'--';
  routeStepList();
}
function updateWalker(){
  if(!walkerMesh||!curve){if(walkerMesh) walkerMesh.visible=false;return;}
  walkerMesh.visible=true;
  const p=curve.getPoint(Math.min(1,Math.max(0,walkU))); walkerMesh.position.copy(p);
  const ahead=curve.getPoint(Math.min(1,walkU+.01)); walkerMesh.lookAt(ahead.x,p.y,ahead.z);
  const screen=p.clone().project(cam);
  const label=$("walkerLabel");
  if(screen.z<1){label.style.display='block';label.style.left=((screen.x*.5+.5)*innerWidth+12)+'px';label.style.top=((-screen.y*.5+.5)*innerHeight-12)+'px';}
  else label.style.display='none';
  if(followWalker){cam.position.lerp(p.clone().add(new THREE.Vector3(0,28,34)),.035);controls.target.lerp(p,.06);}
  const lis=document.querySelectorAll('#liveSteps .liveStep');
  const idx=Math.min(lis.length-1,Math.floor(walkU*Math.max(1,lis.length)));
  lis.forEach((x,i)=>{x.classList.toggle('current',i===idx&&walkU<1);x.classList.toggle('done',i<idx);});
  renderLiveInfo();
}
function startWalkSimulation(){
  if(!currentPathRes||!curve){showToast('Select a block first to create a route');return;}
  ensureWalker(); walkRunning=true; walkPaused=false; if(walkU>=1) walkU=0; showToast('Real-life walking simulation started'); $("liveStatusText").textContent='Walking simulation'; $("liveDot").className='liveDot ok';
}
function stopWalkSimulation(reset=true){walkRunning=false;walkPaused=false; if(reset) walkU=0; if(walkerMesh) walkerMesh.visible=false; $("walkerLabel").style.display='none';}
function openLiveWalk(id){
  if(!bOf(id)){showToast("Select a valid campus block first");return;}
  selectBlock(id);
  if(!window.getDirections(id)) return;
  $("livePanel").classList.add('show');
  startWalkSimulation();
}
window.openLiveWalk=openLiveWalk;
function useGPS(){
  if(!navigator.geolocation){showToast('GPS is not supported by this browser');return;}
  $("liveStatusText").textContent='Requesting GPS permission…'; $("liveDot").className='liveDot warn';
  if(gpsWatchId!==null) navigator.geolocation.clearWatch(gpsWatchId);
  gpsWatchId=navigator.geolocation.watchPosition(pos=>{
    gpsLast=pos;
    const lat=pos.coords.latitude,lon=pos.coords.longitude,acc=pos.coords.accuracy;
    $("gpsCoords").textContent=`${lat.toFixed(6)}, ${lon.toFixed(6)}`;
    $("gpsAccuracy").textContent=`±${Math.round(acc)} m`;
    $("liveStatusText").textContent='Live GPS active'; $("liveDot").className='liveDot ok';
    // Campus reference is the public Joy University coordinate; GPS is shown as real-world position.
    // We do not silently claim exact indoor block positioning from GPS accuracy alone.
    if(CUR==null) showToast('GPS active — select a campus block for the 3D walking route');
  },err=>{
    $("liveStatusText").textContent='GPS unavailable'; $("liveDot").className='liveDot warn';
    showToast(err.code===1?'GPS permission denied': 'Could not read GPS location');
  },{enableHighAccuracy:true,maximumAge:3000,timeout:10000});
}

window.startWalkingTo = function(id){
  const b=bOf(id);
  if(!b){showToast("Select a valid campus block first");return;}
  openLiveWalk(id);
  showToast(`Walking route to ${b[1]}`);
};

window.setStart = function(id){
  const b=bOf(id);
  if(!b){showToast("Select a valid campus block first");return;}
  id=b[0];
  START = id;
  updateStats();
  showToast(`Start position set to #${id}`);
  if(CUR && CUR !== START) selectBlock(CUR);
};

window.closeCard = function(){
  cardEl.style.display = "none";
  $("directionsPanel").classList.remove("show");
  clearRoute();
  CUR = null;
  updateStats();
  renderList();
};

window.toggleFavorite=function(id){
  const k=String(id);
  if(favorites.has(k)) favorites.delete(k); else favorites.add(k);
  localStorage.setItem("joyCampusFavoritesV2",JSON.stringify([...favorites]));
  if(CUR!==null && String(CUR)===k) selectBlock(CUR); else renderList();
  showToast(favorites.has(k)?"Saved to Favorites":"Removed from Favorites");
};
function showToast(msg){
  toastEl.textContent=msg; toastEl.classList.add("show");
  clearTimeout(showToast.t); showToast.t=setTimeout(()=>toastEl.classList.remove("show"),1800);
}
function updateStats(){
  $("stSelected").textContent=CUR===null?"None":("#"+CUR+" "+(bOf(CUR)?bOf(CUR)[1]:""));
  $("stStart").textContent="#"+START;
  $("stRoute").textContent=fmt(routeLen);
}
function setNightState(value){
  NIGHT=!!value;
  $("bNight").classList.toggle("on",NIGHT);
  scene.fog.color.setHex(NIGHT ? 0x030a12 : 0xbfe0ff);
  skyU.top.value.setHex(NIGHT ? 0x02060d : 0x2a8cff);
  skyU.bot.value.setHex(NIGHT ? 0x081626 : 0xd5ecff);
  sun.intensity = NIGHT ? 0.1 : 1.15;
  hemi.intensity = NIGHT ? 0.15 : 0.85;
  stars.material.opacity = NIGHT ? 0.8 : 0;
  winMats.forEach(m => m.emissiveIntensity = NIGHT ? 1 : 0);
  emis.forEach(m => m.emissiveIntensity = NIGHT ? 0.6 : 0);
  glows.forEach(g => g.material.opacity = NIGHT ? 0.8 : 0);
}
let lbIdx = 0;
window.openLB = function(i){
  const idx = PHOTOS.findIndex(p => p.i === i);
  if(idx < 0) return;
  lbIdx = idx;
  updateLB();
  $("lb").classList.add("show");
};

function updateLB(){
  const p = PHOTOS[lbIdx];
  $("lbi").src = PH(p.i);
  $("lbt").textContent = p.t;
}

$("lx").onclick = () => $("lb").classList.remove("show");
$("lp").onclick = () => { lbIdx = (lbIdx - 1 + PHOTOS.length) % PHOTOS.length; updateLB(); };
$("ln").onclick = () => { lbIdx = (lbIdx + 1) % PHOTOS.length; updateLB(); };
$("l3").onclick = () => {
  const p = PHOTOS[lbIdx];
  $("lb").classList.remove("show");
  if(p.b) selectBlock(p.b);
};

let orbitAuto = false, tourIdx = 0, tourActive = false;

$("bList").onclick = () => $("side").classList.toggle("hide");

$("bOrbit").onclick = function(){
  orbitAuto = !orbitAuto;
  controls.autoRotate = orbitAuto;
  this.classList.toggle("on", orbitAuto);
};

$("bTop").onclick = () => flyTo(new THREE.Vector3(0, 220, 1), new THREE.Vector3(0, 0, 0));
$("bReset").onclick = () => flyTo(HOME[0], HOME[1]);

$("bNight").onclick = function(){
  setNightState(!NIGHT);
};

$("bLab").onclick = function(){
  markers.visible = !markers.visible;
  this.classList.toggle("on", markers.visible);
};

$("bWalk").onclick = () => { if(CUR===null){ showToast("Select a destination block first"); return; } startWalkingTo(CUR); };
$("bShare").onclick = async () => {
  try{
    if(navigator.share){ await navigator.share({title:"Joy University 3D Smart Campus",text:"Explore Joy University 3D Smart Campus",url:location.href}); }
    else if(navigator.clipboard){ await navigator.clipboard.writeText(location.href); showToast("URL copied to clipboard"); }
    else showToast("Share is not available in this browser");
  }catch(e){}
};
$("bFull").onclick = async () => {
  try{
    if(!document.fullscreenElement) await document.documentElement.requestFullscreen();
    else await document.exitFullscreen();
  }catch(e){showToast("Fullscreen is not supported here");}
};
$("bShot").onclick = () => {
  try{
    renderer.render(scene,cam);
    const a=document.createElement("a");
    a.download="joy-university-campus-"+new Date().toISOString().slice(0,19).replace(/[:T]/g,"-")+".png";
    a.href=renderer.domElement.toDataURL("image/png");
    a.click();
    showToast("3D snapshot saved");
  }catch(e){showToast("Snapshot could not be created");}
};
const profilePanel=$("profilePanel");
async function hashPassword(value){
  if(!value) return "";
  if(window.crypto&&crypto.subtle){
    const data=new TextEncoder().encode(value);
    const hash=await crypto.subtle.digest("SHA-256",data);
    return Array.from(new Uint8Array(hash)).map(x=>x.toString(16).padStart(2,"0")).join("");
  }
  const bytes=new TextEncoder().encode(value);
  const constants=[
    0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,
    0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,
    0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,
    0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,
    0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,
    0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,
    0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,
    0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2
  ];
  const state=[0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19];
  const bitLength=bytes.length*8;
  const paddedLength=Math.ceil((bytes.length+9)/64)*64;
  const padded=new Uint8Array(paddedLength);
  padded.set(bytes);padded[bytes.length]=0x80;
  const view=new DataView(padded.buffer);
  view.setUint32(paddedLength-8,Math.floor(bitLength/0x100000000),false);
  view.setUint32(paddedLength-4,bitLength>>>0,false);
  const words=new Uint32Array(64),rotate=(x,n)=>(x>>>n)|(x<<(32-n));
  for(let offset=0;offset<paddedLength;offset+=64){
    for(let i=0;i<16;i++) words[i]=view.getUint32(offset+i*4,false);
    for(let i=16;i<64;i++){
      const a=words[i-15],b=words[i-2];
      const s0=rotate(a,7)^rotate(a,18)^(a>>>3),s1=rotate(b,17)^rotate(b,19)^(b>>>10);
      words[i]=(words[i-16]+s0+words[i-7]+s1)>>>0;
    }
    let [a,b,c,d,e,f,g,h]=state;
    for(let i=0;i<64;i++){
      const s1=rotate(e,6)^rotate(e,11)^rotate(e,25),choice=(e&f)^(~e&g);
      const t1=(h+s1+choice+constants[i]+words[i])>>>0;
      const s0=rotate(a,2)^rotate(a,13)^rotate(a,22),majority=(a&b)^(a&c)^(b&c);
      const t2=(s0+majority)>>>0;
      h=g;g=f;f=e;e=(d+t1)>>>0;d=c;c=b;b=a;a=(t1+t2)>>>0;
    }
    state[0]=(state[0]+a)>>>0;state[1]=(state[1]+b)>>>0;state[2]=(state[2]+c)>>>0;state[3]=(state[3]+d)>>>0;
    state[4]=(state[4]+e)>>>0;state[5]=(state[5]+f)>>>0;state[6]=(state[6]+g)>>>0;state[7]=(state[7]+h)>>>0;
  }
  return state.map(x=>x.toString(16).padStart(8,"0")).join("");
}
function loadProfile(){
  try{
    const p=JSON.parse(localStorage.getItem("joyCampusProfileV2")||"null");
    if(!p) return;
    $("profileName").value=p.name||""; $("profileRole").value=p.role||"Student";
    $("profileDept").value=p.dept||""; $("profileYear").value=p.year||"";
    renderProfile();
  }catch(e){}
}
function showProfileSetupIfNeeded(){
  let saved=null;
  try{saved=JSON.parse(localStorage.getItem("joyCampusProfileV2")||"null");}
  catch(e){$("setupError").textContent="Could not read the saved local profile. Clear this site's browser storage and try again.";return;}
  if(saved&&saved.name&&saved.passwordHash){
    $("loadUser").textContent=`Welcome, ${saved.name}`;
    $("loadUser").style.display="block";
    return;
  }
  if(saved&&saved.name) $("setupName").value=saved.name;
  $("setupGate").classList.add("show");
  $("setupName").focus();
}
$("setupCreate").onclick=async()=>{
  const name=$("setupName").value.trim();
  const password=$("setupPassword").value;
  const confirm=$("setupPasswordConfirm").value;
  const error=$("setupError");
  error.textContent="";
  if(!name){error.textContent="Enter your name to continue.";return;}
  if(password.length<6){error.textContent="Use a password with at least 6 characters.";return;}
  if(password!==confirm){error.textContent="The passwords do not match.";return;}
  const button=$("setupCreate");
  button.disabled=true;
  try{
    const saltBytes=new Uint8Array(16);
    if(window.crypto&&crypto.getRandomValues) crypto.getRandomValues(saltBytes);
    else for(let i=0;i<saltBytes.length;i++) saltBytes[i]=Math.floor(Math.random()*256);
    const passwordSalt=Array.from(saltBytes,x=>x.toString(16).padStart(2,"0")).join("");
    const profile={name,role:"Student",dept:"",year:"",passwordSalt,passwordHash:await hashPassword(passwordSalt+":"+password)};
    localStorage.setItem("joyCampusProfileV2",JSON.stringify(profile));
    $("profileName").value=name;
    $("profileRole").value=profile.role;
    $("profileDept").value="";
    $("profileYear").value="";
    $("setupPassword").value="";
    $("setupPasswordConfirm").value="";
    $("setupGate").classList.remove("show");
    renderProfile();
    showToast("Local campus profile created");
  }catch(e){
    error.textContent="Could not save your profile in this browser. Check browser storage settings and try again.";
  }finally{
    button.disabled=false;
  }
};
["setupName","setupPassword","setupPasswordConfirm"].forEach(id=>$(id).addEventListener("keydown",event=>{
  if(event.key==="Enter") $("setupCreate").click();
}));
function renderProfile(){
  const n=$("profileName").value.trim(), r=$("profileRole").value, d=$("profileDept").value.trim(), y=$("profileYear").value.trim();
  const saved=(()=>{try{return JSON.parse(localStorage.getItem("joyCampusProfileV2")||"null")}catch(e){return null}})();
  const hasPass=!!(saved&&saved.passwordHash);
  const fields=[n,r,d,y,hasPass].filter(Boolean).length, pct=Math.round(fields/5*100);
  const initials=(n||"JU").split(/\s+/).filter(Boolean).slice(0,2).map(x=>x[0]).join("").toUpperCase();
  $("profileAvatar").textContent=initials||"JU"; $("profileNameView").textContent=n||"New Campus Member";
  $("profileMeta").textContent=[r,d,y].filter(Boolean).join(" • ")||"Complete your local campus profile";
  $("profileRoleView").textContent=r||"Student"; $("profilePasswordView").textContent=hasPass?"Protected":"Not set";
  $("profileMeterBar").style.width=pct+"%"; $("profileCompletion").textContent=pct+"% profile complete";
  $("profilePreview").innerHTML=n?`<b>${n}</b><br>${r}${d?" • "+d:""}${y?" • "+y:""}<br><small style="color:#5eead4">${hasPass?"🔐 Local password protected":"⚠ Create a local password to finish setup"}</small>`:"Professional profile preview will appear here.";
  const loadUser=$("loadUser"); if(loadUser){loadUser.textContent=n?`Welcome, ${n} • Loading your campus`:"Loading your personalized campus"; loadUser.style.display="block";}
}
$("bProfile").onclick=()=>{profilePanel.classList.toggle("show");renderProfile();};
$("profileClose").onclick=()=>profilePanel.classList.remove("show");
["profileName","profileRole","profileDept","profileYear"].forEach(id=>$(id).addEventListener("input",renderProfile));
$("profileSave").onclick=async()=>{
  const password=$("profilePassword").value;
  const p={name:$("profileName").value.trim(),role:$("profileRole").value,dept:$("profileDept").value.trim(),year:$("profileYear").value.trim(),passwordHash:await hashPassword(password)};
  if(!p.name){showToast("Enter your name first");return;}
  if(password.length<4 && !localStorage.getItem("joyCampusProfileV2")){showToast("Create a password of at least 4 characters");return;}
  localStorage.setItem("joyCampusProfileV2",JSON.stringify(p));
  $("profilePassword").value=""; renderProfile(); showToast("Profile and password saved on this device");
};
$("profileClear").onclick=()=>{
  localStorage.removeItem("joyCampusProfileV2");
  $("profileName").value="";$("profileDept").value="";$("profileYear").value="";$("profilePassword").value="";
  $("profileRole").value="Student";renderProfile();showToast("Profile cleared");
};
loadProfile(); renderProfile();

$("bLive").onclick=()=>{$("livePanel").classList.toggle("show");renderLiveInfo();};
$("liveClose").onclick=()=>$("livePanel").classList.remove("show");
$("directionsClose").onclick=()=>$("directionsPanel").classList.remove("show");
$("bGPS").onclick=useGPS;
$("bSim").onclick=startWalkSimulation;
$("bPause").onclick=()=>{if(!currentPathRes){showToast("Select a destination first");return;}walkPaused=!walkPaused;$("bPause").textContent=walkPaused?"▶ Resume":"⏸ Pause";$("liveStatusText").textContent=walkPaused?"Walking paused":"Walking simulation";};
$("bFollow").onclick=()=>{followWalker=!followWalker;$("bFollow").classList.toggle("on",followWalker);showToast(followWalker?"Camera following walker":"Camera follow disabled");};
$("bStopWalk").onclick=()=>{stopWalkSimulation(true);$("bPause").textContent="⏸ Pause";$("liveStatusText").textContent=currentPathRes?"Route ready":"Ready";$("liveDot").className=currentPathRes?"liveDot ok":"liveDot";renderLiveInfo();showToast("Walking mode stopped");};

$("bMore").onclick=()=>morePanel.classList.toggle("show");
$("moreClose").onclick=()=>morePanel.classList.remove("show");
$("bClearRoute").onclick=()=>{clearRoute();updateStats();showToast("Walking route cleared");};
$("bFav").onclick=()=>{showFavorites=!showFavorites;$("bFav").classList.toggle("on",showFavorites);renderList();showToast(showFavorites?"Showing favorites":"Showing all places");};
$("bClear").onclick=()=>{qInput.value="";showFavorites=false;$("bFav").classList.remove("on");activeCat="All";renderChips();renderList();};
$("bVoice").onclick=()=>{
  const SR=window.SpeechRecognition||window.webkitSpeechRecognition;
  if(!SR){showToast("Voice search is not supported in this browser");return;}
  const r=new SR(); r.lang="en-IN"; r.interimResults=false; r.maxAlternatives=1;
  r.onstart=()=>showToast("Listening… say a block or facility name");
  r.onresult=e=>{qInput.value=e.results[0][0].transcript;renderList();};
  r.onerror=()=>showToast("Voice search stopped");
  r.start();
};
$("bAutoDay").onclick=()=>{
  autoDay=!autoDay; $("bAutoDay").classList.toggle("on",autoDay);
  clearInterval(autoTimer);
  if(autoDay){
    const tick=()=>{const h=new Date().getHours();setNightState(h<6||h>=18);};
    tick(); autoTimer=setInterval(tick,60000); showToast("Automatic day/night enabled");
  }else showToast("Automatic day/night disabled");
};
$("bHelp").onclick=()=>{morePanel.classList.add("show");showToast("Keyboard shortcuts shown in Control Center");};

$("bTour").onclick = function(){
  tourActive = !tourActive;
  this.classList.toggle("on", tourActive);
  if(tourActive){ tourIdx=0; nextTourStep(); showToast("Campus tour started"); }
  else showToast("Campus tour stopped");
};

function nextTourStep(){
  if(!tourActive) return;
  const b = BLOCKS[tourIdx % BLOCKS.length];
  selectBlock(b[0]);
  tourIdx++;
  setTimeout(() => { if(tourActive) nextTourStep(); }, 5000);
}

const raycaster = new THREE.Raycaster(), mouse = new THREE.Vector2();
function pickPlace(clientX,clientY){
  mouse.x=(clientX/innerWidth)*2-1; mouse.y=-(clientY/innerHeight)*2+1;
  raycaster.setFromCamera(mouse,cam);
  const intersects=raycaster.intersectObjects(pick,true);
  if(intersects.length){
    let obj=intersects[0].object;
    while(obj && obj.userData.id===undefined) obj=obj.parent;
    if(obj && obj.userData.id!==undefined){selectBlock(obj.userData.id);return true;}
  }
  let best=null,bestD=42;
  for(const b of BLOCKS){
    const g=nodes[b[0]]; if(!g) continue;
    const p=g.position.clone(); p.y=(g.userData.top||4)*.55; p.project(cam);
    if(p.z<0||p.z>1) continue;
    const sx=(p.x*.5+.5)*innerWidth, sy=(-p.y*.5+.5)*innerHeight, d=Math.hypot(clientX-sx,clientY-sy);
    if(d<bestD){bestD=d;best=b[0];}
  }
  if(best!==null){selectBlock(best);return true;}
  return false;
}
let downX=0,downY=0;
canvas.addEventListener("pointerdown",e=>{downX=e.clientX;downY=e.clientY;});
canvas.addEventListener("pointerup",e=>{if(Math.hypot(e.clientX-downX,e.clientY-downY)<8) pickPlace(e.clientX,e.clientY);});

document.addEventListener("keydown",e=>{
  if(e.target && ["INPUT","TEXTAREA"].includes(e.target.tagName)) return;
  const k=e.key.toLowerCase();
  if(k==="f") $("bFull").click();
  else if(k==="h") $("bReset").click();
  else if(k==="t") $("bTop").click();
  else if(k==="o") $("bOrbit").click();
  else if(k==="n") $("bNight").click();
  else if(k==="m") $("bLab").click();
  else if(k==="l") $("bLive").click();
  else if(k==="r") {clearRoute();updateStats();showToast("Route cleared");}
  else if(k==="escape"){ $("lb").classList.remove("show"); morePanel.classList.remove("show"); profilePanel.classList.remove("show"); $("livePanel").classList.remove("show"); cardEl.style.display="none"; }
});
window.addEventListener("beforeunload",()=>{clearInterval(autoTimer);});

function animate(){
  requestAnimationFrame(animate);
  const t = clock.getElapsedTime();
  fpsFrames++;
  const nowFPS=performance.now();
  if(nowFPS-fpsLast>=1000){
    $("stFPS").textContent=Math.round(fpsFrames*1000/(nowFPS-fpsLast));
    fpsFrames=0; fpsLast=nowFPS;
  }
  if(fly){
    const progress = Math.min(1, (t - fly.s) / fly.d);
    const ease = 0.5 - Math.cos(progress * Math.PI) / 2;
    cam.position.lerpVectors(fly.p0, fly.p1, ease);
    controls.target.lerpVectors(fly.t0, fly.t1, ease);
    if(progress >= 1) fly = null;
  }
  controls.update();
  rotors.forEach(r => r.rotation.z += 0.04);
  cars.forEach(c => {
    c.position.x += c.userData.v;
    if(c.position.x > 40) c.position.x = -75;
    if(c.position.x < -75) c.position.x = 40;
  });
  if(curve && flow.length > 0){
    flow.forEach((dot, idx) => {
      const u = (t * 0.25 + idx / flow.length) % 1;
      dot.position.copy(curve.getPoint(u));
    });
  }
  if(walkRunning && !walkPaused && curve){
    walkU += (WALK_MS / Math.max(1,routeLen)) / 60;
    if(walkU >= 1){walkU=1;walkRunning=false;$("liveStatusText").textContent='Arrived at destination';$("liveDot").className='liveDot ok';showToast('Arrived at '+(bOf(currentDestination)?.[1]||'destination'));}
    updateWalker();
  }
  const dir = new THREE.Vector3();
  cam.getWorldDirection(dir);
  const angle = Math.atan2(dir.x, dir.z) * (180 / Math.PI);
  $("needle").style.transform = `rotate(${angle}deg)`;
  renderer.render(scene, cam);
}

window.addEventListener("resize", () => {
  cam.aspect = innerWidth / innerHeight;
  cam.updateProjectionMatrix();
  renderer.setSize(innerWidth, innerHeight);
});

renderChips();
renderList();
renderLiveInfo();
function startLoading(){
  const loadEl=$("load"), bar=$("loadBar"), pct=$("loadPct"), txt=$("loadText");
  const stages=[
    [18,"Starting 3D renderer"],
    [38,"Loading campus buildings"],
    [58,"Preparing roads and walking paths"],
    [74,"Preparing markers, trees and lighting"],
    [88,"Preparing campus controls"],
    [100,"Campus ready"]
  ];
  let i=0;
  const step=()=>{
    if(i>=stages.length){
      setTimeout(()=>{
        loadEl.style.opacity="0";
        setTimeout(()=>{loadEl.remove();showProfileSetupIfNeeded();},800);
      },250);
      return;
    }
    const [n,s]=stages[i++];
    bar.style.width=n+"%";pct.textContent=n+"%";txt.textContent=s;
    setTimeout(step,350);
  };
  step();
}
updateStats();
startLoading();
animate();
</script></body></html>
'''


def main():
    args = sys.argv[1:]
    extract_photos()
    
    index_file = HERE / "index.html"
    index_file.write_text(HTML, encoding="utf-8")
    
    if "--export" in args:
        print(f"[+] Successfully exported site to {index_file}")
        print("[+] You can deploy this folder directly to Netlify or GitHub Pages.")
        return

    port = 8000
    host = "0.0.0.0" if "--lan" in args else "127.0.0.1"
    
    class Handler(SimpleHTTPRequestHandler):
        def __init__(self, *a, **kw):
            super().__init__(*a, directory=str(HERE), **kw)
        def log_message(self, format, *args):
            pass

    server = ThreadingHTTPServer((host, port), Handler)
    
    if "--lan" in args:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            url = f"http://{local_ip}:{port}"
        except Exception:
            url = f"http://127.0.0.1:{port}"
    else:
        url = f"http://127.0.0.1:{port}"

    print(f"\n[🚀] Joy University 3D Smart Campus running at: {url}")
    print("[+] Press Ctrl+C to stop the server.\n")

    threading.Thread(target=lambda: webbrowser.open(url), daemon=True).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[!] Server stopped.")


if __name__ == "__main__":
    main()