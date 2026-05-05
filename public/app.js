const API_BASE =
  (location.hostname === "localhost" || location.hostname === "127.0.0.1")
    ? "http://localhost:8000"
    : "";

const AGE_DIST = [
  { l: "10대", p: 20.6, c: "#7c3aed" },
  { l: "20대", p: 23.3, c: "#2563eb" },
  { l: "30대", p: 17.2, c: "#059669" },
  { l: "40대", p: 13.6, c: "#d97706" },
  { l: "50대+", p: 25.4, c: "#dc2626" },
];
const AGE_PREF = {
  all: ["예능/오락", "음악 MV", "먹방/쿡방", "여행 브이로그", "IT 리뷰", "뉴스/시사", "게임"],
  "10": ["게임", "뮤직비디오", "먹방", "뷰티", "브이로그", "IT 언박싱", "애니메이션"],
  "20": ["예능/오락", "게임", "먹방/맛집", "여행 브이로그", "IT 리뷰", "뮤직비디오", "자기계발"],
  "30": ["예능/오락", "먹방/요리", "여행", "IT 리뷰/꿀팁", "재테크", "뉴스/시사", "뮤직비디오"],
  "40": ["예능/오락", "뉴스/시사", "여행", "먹방/요리", "재테크", "IT 활용법", "스포츠"],
  "50": ["뉴스/시사", "건강/운동", "여행", "교양/다큐", "먹방/요리", "IT 쉬운 강의", "일상정보"],
};

// 연령대 → 카테고리 추천(스냅샷 재사용 목적)
const AGE_CATEGORY = {
  all: ["all"],
  "10": ["game", "music", "food", "beauty", "ent"],
  "20": ["ent", "game", "food", "travel", "it"],
  "30": ["ent", "food", "travel", "it", "news"],
  "40": ["news", "ent", "travel", "food"],
  "50": ["news", "edu", "travel", "food"],
};

let curP = "daily", curC = "all", curG = "daily", curA = "all", curChSort = "subs";
let curAllN = 10;
let curAllPage = 1;

function fmtInt(n) {
  if (n === null || n === undefined) return "-";
  const x = Number(n);
  if (!Number.isFinite(x)) return "-";
  return x.toLocaleString("ko-KR");
}
function fmtPct(p) {
  if (p === null || p === undefined) return "-";
  const x = Number(p);
  if (!Number.isFinite(x)) return "-";
  return `${x.toFixed(2)}%`;
}
function fmtDateTime(d = new Date()) {
  const yy = d.getFullYear();
  const mm = String(d.getMonth() + 1).padStart(2, "0");
  const dd = String(d.getDate()).padStart(2, "0");
  const hh = String(d.getHours()).padStart(2, "0");
  const mi = String(d.getMinutes()).padStart(2, "0");
  return `${yy}.${mm}.${dd} ${hh}:${mi}`;
}

function spark(t) {
  const arr = (t || []).map(Number);
  const mx = Math.max(...arr, 1);
  const w = 56, h = 18, pd = 2;
  const pts = arr.map((v, i) => {
    const x = (pd + i * (w - pd * 2) / Math.max(arr.length - 1, 1));
    const y = (h - pd - (v / mx) * (h - pd * 2));
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  }).join(" ");
  return `<svg width="${w}" height="${h}" viewBox="0 0 ${w} ${h}"><polyline points="${pts}" fill="none" stroke="#E24B4A" stroke-width="1.5" stroke-linejoin="round"/></svg>`;
}

async function apiGet(path) {
  const res = await fetch(`${API_BASE}${path}`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}
async function apiPost(path) {
  const res = await fetch(`${API_BASE}${path}`, { method: "POST" });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

function setSyncLabel(text) {
  document.getElementById("sync-lbl").textContent = text;
}

function playerHtml(item) {
  const watchUrl = `https://www.youtube.com/watch?v=${item.video_id}`;
  const embedUrl = `https://www.youtube.com/embed/${item.video_id}?autoplay=1&rel=0`;
  return `
    <div class="player-wrap">
      <div class="player-top">
        <div style="min-width:0">
          <div class="player-title">${escapeHtml(item.title)}</div>
          <div class="player-meta">${escapeHtml(item.channel_title)} · 조회수 ${fmtInt(item.view_count)}</div>
        </div>
        <a class="play-btn" href="${watchUrl}" target="_blank" rel="noreferrer">YouTube 열기</a>
      </div>
      <div class="player-media" data-embed="${embedUrl}">
        <img src="${item.thumbnail_url}" alt="thumbnail">
        <div class="overlay"><span>▶</span></div>
      </div>
    </div>
  `;
}

function escapeHtml(s) {
  return String(s || "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

async function loadTrending() {
  const lbl = { daily: "일간", weekly: "주간", monthly: "월간" };
  const n = (curC === "all" ? curAllN : 10);
  document.getElementById("vid-sec-title").textContent = `한국 인기 영상 TOP ${n} — ${lbl[curP]} · ${curC.toUpperCase()}`;
  document.getElementById("vid-list-title").textContent = (n === 100 ? "#2~100 (10개씩 보기)" : "#2~10");

  const data = await apiGet(`/api/trending?cat=${encodeURIComponent(curC)}&period=${encodeURIComponent(curP)}`);
  const items = data.items || [];

  const player = document.getElementById("player");
  const empty = document.getElementById("player-empty");
  if (!items.length) {
    player.innerHTML = "";
    empty.style.display = "block";
    document.getElementById("vid-tbody").innerHTML = `
      <tr>
        <td colspan="4" style="padding:14px 8px;color:var(--text2);font-size:12px;">
          오늘 KR 인기 TOP100 기준으로 <b>${escapeHtml(curC)}</b> 카테고리 영상이 부족하거나 존재하지 않아 표시할 데이터가 없습니다.
          (전체 탭은 항상 표시됩니다)
        </td>
      </tr>
    `;
    return;
  }
  empty.style.display = "none";

  // player: rank 1
  player.innerHTML = playerHtml(items[0]);
  player.querySelector(".player-media")?.addEventListener("click", (e) => {
    const el = e.currentTarget;
    const embed = el.getAttribute("data-embed");
    el.innerHTML = `<iframe src="${embed}" allow="autoplay; encrypted-media" allowfullscreen></iframe>`;
  }, { once: true });

  // list: #2.. (TOP10) or #2..#100 with pagination(10 per page)
  const pager = document.getElementById("vid-pager");
  const listAll = items.slice(1, n); // excludes #1 (player)
  let list = listAll;
  if (curC === "all" && n === 100) {
    const pageSize = 10;
    const totalPages = Math.max(1, Math.ceil(listAll.length / pageSize)); // 99 -> 10 pages
    curAllPage = Math.min(Math.max(curAllPage, 1), totalPages);
    const start = (curAllPage - 1) * pageSize;
    const end = start + pageSize;
    list = listAll.slice(start, end);

    // render pager
    pager.style.display = "flex";
    pager.innerHTML = Array.from({ length: totalPages }, (_, i) => {
      const p = i + 1;
      return `<button class="pgbtn ${p === curAllPage ? "on" : ""}" data-p="${p}">${p}</button>`;
    }).join("");
  } else {
    pager.style.display = "none";
    pager.innerHTML = "";
  }

  document.getElementById("vid-tbody").innerHTML = list.map((v, idx) => {
    // items already include rank, keep it stable even across pagination
    const rank = v.rank ?? (idx + 2);
    const watchUrl = `https://www.youtube.com/watch?v=${v.video_id}`;
    return `
      <tr>
        <td><span class="rn ${rank <= 3 ? "top" : ""}">${rank}</span></td>
        <td><a href="${watchUrl}" target="_blank" rel="noreferrer"><img class="thumbimg" src="${v.thumbnail_url}" alt="thumb"></a></td>
        <td>
          <div class="vid-title"><a href="${watchUrl}" target="_blank" rel="noreferrer" style="color:inherit;text-decoration:none">${escapeHtml(v.title)}</a></div>
          <div class="vid-meta">${escapeHtml(v.channel_title)}</div>
        </td>
        <td class="nr">${fmtInt(v.view_count)}</td>
      </tr>
    `;
  }).join("");
}

async function loadChannels() {
  const data = await apiGet(`/api/channels?sort=${encodeURIComponent(curChSort)}`);
  const items = data.items || [];
  document.getElementById("ch-count").textContent = items.length ? String(items.length) : "-";

  const empty = document.getElementById("ch-empty");
  if (!items.length) {
    empty.style.display = "block";
    document.getElementById("ch-tbody").innerHTML = "";
    return;
  }
  empty.style.display = "none";

  document.getElementById("ch-tbody").innerHTML = items.map((c) => `
    <tr>
      <td><span class="rn ${c.rank <= 3 ? "top" : ""}">${c.rank}</span></td>
      <td>${c.thumbnail_url ? `<img class="ch-thumb" src="${c.thumbnail_url}" alt="ch">` : ""}</td>
      <td><div class="vid-title">${escapeHtml(c.title)}</div></td>
      <td class="nr">${fmtInt(c.subscriber_count)}</td>
      <td class="nr">${fmtInt(c.view_count)}</td>
    </tr>
  `).join("");
}

async function loadGrowth() {
  const lbl = { daily: "일간", weekly: "주간", monthly: "월간" };
  document.getElementById("g-period-lbl").textContent = lbl[curG];

  const data = await apiGet(`/api/growth?period=${encodeURIComponent(curG)}`);
  const items = data.items || [];

  const empty = document.getElementById("grow-empty");
  if (!items.length) {
    empty.style.display = "block";
    document.getElementById("g-top-gain").textContent = "-";
    document.getElementById("grow-sec-title").textContent = `구독자 증가율 TOP 10 — ${lbl[curG]}`;
    document.getElementById("grow-tbody").innerHTML = "";
    return;
  }
  empty.style.display = "none";

  document.getElementById("g-top-gain").textContent = `+${fmtInt(items[0].gain)}`;
  document.getElementById("grow-sec-title").textContent = `구독자 증가율 TOP 10 — ${lbl[curG]}`;
  document.getElementById("grow-tbody").innerHTML = items.map((c) => `
    <tr>
      <td><span class="rn ${c.rank <= 3 ? "top" : ""}">${c.rank}</span></td>
      <td>${c.thumbnail_url ? `<img class="ch-thumb" src="${c.thumbnail_url}" alt="ch">` : ""}</td>
      <td><div class="vid-title">${escapeHtml(c.title)}</div></td>
      <td class="nr up">+${fmtInt(c.gain)}</td>
      <td class="nr up">${fmtPct(c.rate)}</td>
      <td style="text-align:right">${spark(c.sparkline)}</td>
    </tr>
  `).join("");
}

function renderAge() {
  document.getElementById("age-dist").innerHTML = AGE_DIST.map(a => `
    <div style="display:flex;align-items:center;gap:8px;padding:6px 0;border-bottom:0.5px solid var(--border);">
      <span style="font-size:12px;color:var(--text2);min-width:48px;">${a.l}</span>
      <div style="flex:1;height:8px;background:var(--border);border-radius:99px;overflow:hidden;">
        <div style="height:100%;width:${Math.min(a.p * 4, 100)}%;background:${a.c};border-radius:99px;"></div>
      </div>
      <span style="font-size:11px;font-weight:500;min-width:40px;text-align:right;">${a.p}%</span>
    </div>
  `).join("");

  const prefs = AGE_PREF[curA] || AGE_PREF.all;
  const clrs = ["#dc2626", "#2563eb", "#059669", "#d97706", "#7c3aed", "#be185d", "#0f766e"];
  document.getElementById("age-pref").innerHTML = prefs.map((p, i) => `
    <div style="display:flex;align-items:center;gap:8px;padding:6px 0;border-bottom:0.5px solid var(--border);">
      <span style="font-size:12px;color:var(--text2);min-width:48px;">${i + 1}위</span>
      <div style="flex:1;height:8px;background:var(--border);border-radius:99px;overflow:hidden;">
        <div style="height:100%;width:${100 - i * 11}%;background:${clrs[i]};border-radius:99px;"></div>
      </div>
      <span style="min-width:120px;text-align:left;font-size:12px;color:var(--text);">${escapeHtml(p)}</span>
    </div>
  `).join("");

  const lbl = { all: "전체", "10": "10대", "20": "20대", "30": "30대", "40": "40대", "50": "50대+" };
  document.getElementById("age-pref-title").textContent = `${lbl[curA]} 선호 콘텐츠`;
  document.getElementById("age-vid-title").textContent = `${lbl[curA]} — 추천 인기 영상 TOP 5`;
}

async function loadAgeVids() {
  // 스냅샷 재사용: 추천 카테고리 첫 번째의 daily trending에서 5개
  const cats = AGE_CATEGORY[curA] || ["all"];
  const empty = document.getElementById("age-vid-empty");
  const tbody = document.getElementById("age-vid-tbody");
  empty.style.display = "none";

  for (const cat of cats) {
    try {
      const data = await apiGet(`/api/trending?cat=${encodeURIComponent(cat)}&period=daily`);
      const items = (data.items || []).slice(0, 5);
      if (!items.length) continue;
      tbody.innerHTML = items.map((v, i) => {
        const watchUrl = `https://www.youtube.com/watch?v=${v.video_id}`;
        return `
          <tr>
            <td><span class="rn ${i < 3 ? "top" : ""}">${i + 1}</span></td>
            <td><a href="${watchUrl}" target="_blank" rel="noreferrer"><img class="thumbimg" src="${v.thumbnail_url}" alt="thumb"></a></td>
            <td>
              <div class="vid-title"><a href="${watchUrl}" target="_blank" rel="noreferrer" style="color:inherit;text-decoration:none">${escapeHtml(v.title)}</a></div>
              <div class="vid-meta">${escapeHtml(v.channel_title)}</div>
            </td>
            <td class="nr">${fmtInt(v.view_count)}</td>
          </tr>
        `;
      }).join("");
      return;
    } catch (_) {
      // ignore
    }
  }

  tbody.innerHTML = "";
  empty.style.display = "block";
}

async function refreshSnapshot() {
  const sp = document.getElementById("rspin");
  sp.classList.add("on");
  try {
    await apiPost("/api/snapshot/run");
    setSyncLabel(`${fmtDateTime()} 갱신`);
    await loadAllForCurrentPage();
  } catch (e) {
    alert(`스냅샷 갱신 실패: ${e.message || e}`);
  } finally {
    sp.classList.remove("on");
  }
}

async function loadAllForCurrentPage() {
  const curTab = document.querySelector(".nav-tab.on")?.dataset?.p || "video";
  if (curTab === "video") return loadTrending();
  if (curTab === "channel") return loadChannels();
  if (curTab === "growth") return loadGrowth();
  if (curTab === "age") { renderAge(); return loadAgeVids(); }
}

// navigation
document.getElementById("nav").addEventListener("click", async (e) => {
  const t = e.target.closest(".nav-tab"); if (!t) return;
  document.querySelectorAll(".nav-tab").forEach(x => x.classList.remove("on"));
  document.querySelectorAll(".page").forEach(x => x.classList.remove("on"));
  t.classList.add("on");
  document.getElementById("page-" + t.dataset.p).classList.add("on");
  await loadAllForCurrentPage();
});

document.getElementById("period-pills").addEventListener("click", async (e) => {
  const p = e.target.closest(".pill"); if (!p) return;
  document.querySelectorAll("#period-pills .pill").forEach(x => x.classList.remove("on"));
  p.classList.add("on"); curP = p.dataset.v;
  curAllPage = 1;
  await loadTrending();
});
document.getElementById("cat-pills").addEventListener("click", async (e) => {
  const p = e.target.closest(".pill"); if (!p) return;
  document.querySelectorAll("#cat-pills .pill").forEach(x => x.classList.remove("on"));
  p.classList.add("on"); curC = p.dataset.c;
  // 전체일 때만 TOP100 UI를 노출
  const allPills = document.getElementById("all-size-pills");
  const allSep = document.getElementById("all-size-sep");
  const showAll = (curC === "all");
  allPills.style.display = showAll ? "flex" : "none";
  allSep.style.display = showAll ? "block" : "none";
  if (!showAll) curAllN = 10;
  curAllPage = 1;
  await loadTrending();
});

document.getElementById("all-size-pills").addEventListener("click", async (e) => {
  const p = e.target.closest(".pill"); if (!p) return;
  document.querySelectorAll("#all-size-pills .pill").forEach(x => x.classList.remove("on"));
  p.classList.add("on");
  curAllN = Number(p.dataset.n || "10");
  curAllPage = 1;
  await loadTrending();
});

document.getElementById("vid-pager").addEventListener("click", async (e) => {
  const b = e.target.closest(".pgbtn");
  if (!b) return;
  curAllPage = Number(b.dataset.p || "1");
  await loadTrending();
});
document.getElementById("ch-sort-pills").addEventListener("click", async (e) => {
  const p = e.target.closest(".pill"); if (!p) return;
  document.querySelectorAll("#ch-sort-pills .pill").forEach(x => x.classList.remove("on"));
  p.classList.add("on"); curChSort = p.dataset.s;
  await loadChannels();
});
document.getElementById("grow-pills").addEventListener("click", async (e) => {
  const p = e.target.closest(".pill"); if (!p) return;
  document.querySelectorAll("#grow-pills .pill").forEach(x => x.classList.remove("on"));
  p.classList.add("on"); curG = p.dataset.g;
  await loadGrowth();
});
document.getElementById("age-pills").addEventListener("click", async (e) => {
  const p = e.target.closest(".pill"); if (!p) return;
  document.querySelectorAll("#age-pills .pill").forEach(x => x.classList.remove("on"));
  p.classList.add("on"); curA = p.dataset.a;
  renderAge();
  await loadAgeVids();
});

document.getElementById("refresh-btn").addEventListener("click", refreshSnapshot);

// init
(async function init() {
  try {
    await apiGet("/api/health");
    setSyncLabel(`${fmtDateTime()} 준비`);
  } catch (e) {
    setSyncLabel("백엔드 미실행");
  }
  renderAge();
  // init: 전체면 TOP100 토글 UI 노출
  const allPills = document.getElementById("all-size-pills");
  const allSep = document.getElementById("all-size-sep");
  allPills.style.display = (curC === "all") ? "flex" : "none";
  allSep.style.display = (curC === "all") ? "block" : "none";
  try { await loadTrending(); } catch (_) {}
})();

