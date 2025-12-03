(function () {
  // ─────────────────────────────────────────────────────────
  // 카테고리 정의
  // ─────────────────────────────────────────────────────────
  const CATEGORIES = [
    { key: 'comfy_cafe',         label: '쾌좋카',       color: '#6C5CE7' },
    { key: 'solo_cafe',          label: '혼좋카',       color: '#0984E3' },
    { key: 'book_cafe',          label: '책좋카',       color: '#00A8FF' },
    { key: 'unique_cafe',        label: '이걸안카',       color: '#8E44AD' },
    { key: 'group_cafe',         label: '단좋카',       color: '#D35400' },
    { key: 'coffee_taste_cafe',  label: '커맛카',     color: '#2ECC71' },
    { key: 'study_cafe',         label: '카공카',         color: '#00B894' },
    { key: 'bright_cafe',        label: '화청카',         color: '#F1C40F' },
    { key: 'mood_cafe',          label: '분좋카',       color: '#E84393' },
    { key: 'dessert_taste_cafe', label: '디맛카',   color: '#E17055' },
    { key: 'cheap_cafe',         label: '가좋카',       color: '#2D3436' },
    { key: 'animal_cafe',        label: '반동카',     color: '#6D214F' },
    { key: 'night_cafe',         label: '밤샘카',         color: '#34495E' },
    { key: 'hanok_cafe',         label: '한옼카',         color: '#A3CB38' },
  ];
  const CAT_KEYS = CATEGORIES.map(c => c.key);
  const isTrue = v => (v === 1 || v === '1' || v === true || v === 'true' || v === 'True');
  const getCafeName = r => (r.crawled_store_name || r.name || '(이름 없음)');
  const getCafeCats  = r => CAT_KEYS.filter(k => isTrue(r[k]));
  const primaryColorOf = cats => {
    if (!cats.length) return '#636E72';
    const c = CATEGORIES.find(x => x.key === cats[0]); return c ? c.color : '#636E72';
  };
  const svgPin = color => ({
    content: `<svg xmlns="http://www.w3.org/2000/svg" width="28" height="40" viewBox="0 0 24 24">
      <path fill="${color}" d="M12 2C8.14 2 5 5.06 5 8.83C5 13.5 12 22 12 22s7-8.5 7-13.17C19 5.06 15.86 2 12 2zm0 9.75a2.92 2.92 0 1 1 0-5.84a2.92 2.92 0 0 1 0 5.84z"/></svg>`,
    size: new naver.maps.Size(28, 40),
    anchor: new naver.maps.Point(14, 40),
  });

  // 부트스트랩
  document.addEventListener('DOMContentLoaded', () => {
    const cfgEl = document.getElementById('findbymap-config');
    if (!cfgEl) return console.error('[findbymap] config element 없음');
    let cfg = {};
    try { cfg = JSON.parse(cfgEl.textContent || '{}'); } catch (e) {
      return console.error('[findbymap] config JSON 파싱 실패', e);
    }
    if (!cfg.apiUrl) return console.error('[findbymap] apiUrl 없음');
    waitForGeocoder().then(() => init(cfg)).catch(err => {
      console.error('[findbymap] geocoder 준비 실패:', err);
      alert('지오코더 submodules=geocoder 확인하세요.');
    });
  });

  function waitForGeocoder(timeoutMs = 7000) {
    return new Promise((resolve, reject) => {
      const t0 = Date.now();
      const timer = setInterval(() => {
        const ok = window.naver && naver.maps && naver.maps.Service && typeof naver.maps.Service.geocode === 'function';
        if (ok) { clearInterval(timer); return resolve(); }
        if (Date.now() - t0 > timeoutMs) { clearInterval(timer); return reject(new Error('naver.maps.Service.geocode 없음')); }
      }, 50);
    });
  }

  // 메인
  async function init(cfg) {
    const mapEl   = document.getElementById('fm-map');
    const stageEl = document.querySelector('.fm-stage');
    if (!mapEl) return console.error('[findbymap] #fm-map 없음');

    // 지도 보이기 안전가드
    const ensureMapVisible = () => {
      const h = mapEl.offsetHeight || (stageEl ? stageEl.offsetHeight : 0);
      if (h < 100) {
        if (stageEl) stageEl.style.height = '60vh';
        mapEl.style.minHeight = '60vh';
      }
    };
    ensureMapVisible();

    // 서울 경계 + 지도 제한
    const SEOUL_BOUNDS = new naver.maps.LatLngBounds(
      new naver.maps.LatLng(37.42829747263545, 126.76620435615891),
      new naver.maps.LatLng(37.7010174173061,  127.18379493229875)
    );
    const SEOUL_BBOX = [126.76620435615891, 37.42829747263545, 127.18379493229875, 37.7010174173061];

    // 지도
    const map = new naver.maps.Map('fm-map', {
      center: new naver.maps.LatLng(37.5665, 126.9780),
      zoom: 12, minZoom: 10, maxZoom: 18, maxBounds: SEOUL_BOUNDS
    });
    map.fitBounds(SEOUL_BOUNDS);

    const refreshMapSize = () => {
      try {
        const w = mapEl.clientWidth, h = mapEl.clientHeight;
        if (w && h && typeof map.setSize === 'function') {
          map.setSize(new naver.maps.Size(w, h));
        }
        naver.maps.Event.trigger(map, 'resize');
      } catch {}
    };
    window.addEventListener('resize', () => { ensureMapVisible(); refreshMapSize(); });
    setTimeout(() => { ensureMapVisible(); refreshMapSize(); }, 0);

    // 네이버 지도 검색 URL 빌더
    function buildNaverSearchUrl(name, address) {
      const q = address ? `${name} ${address}` : (name || '');
      const encoded = encodeURIComponent(q);
      const z = map.getZoom();
      const center = map.getCenter();
      const c = `${z.toFixed(2)},${center.y},${center.x},0,dh`;
      return `https://map.naver.com/v5/search/${encoded}?c=${c}`;
    }

    // 공유 InfoWindow
    const sharedIW = new naver.maps.InfoWindow({ borderWidth: 0 });
    function buildInfoHTML(r, cats) {
      const name = getCafeName(r);
      const addr = r.address || '';
      const chips = cats.map(k => {
        const c = CATEGORIES.find(x => x.key === k);
        return c ? `<span class="fm-badge" style="border:1px solid ${c.color};color:${c.color};border-radius:12px;padding:2px 6px;margin-right:4px;font-size:11px;display:inline-block">${c.label}</span>` : '';
      }).join('');
      const naverUrl = buildNaverSearchUrl(name, addr);
      return `
        <div style="padding:8px 10px;min-width:220px">
          <div style="font-weight:600">${name}</div>
          ${addr ? `<div style="font-size:12px;color:#555">${addr}</div>` : ''}
          ${r.rating!=null ? `<div style="font-size:12px;color:#666;margin-top:4px">★ ${r.rating}</div>` : ''}
          <div class="fm-badges" style="margin-top:6px">${chips}</div>
          <div style="margin-top:8px">
            <a href="${naverUrl}" target="_blank" rel="noopener"
               style="display:inline-block;font-size:12px;padding:6px 10px;border:1px solid #03C75A;color:#03C75A;border-radius:8px;background:#fff;text-decoration:none">
              네이버로 열기
            </a>
          </div>
        </div>`;
    }
    function openInfoOn(item) {
      sharedIW.setContent(buildInfoHTML(item.cafe, item.categories));
      sharedIW.open(map, item.marker);
    }

    // 요소 참조
    const filterHost = document.getElementById('fm-filter-host');
    const listEl = document.getElementById('fm-info-boxes');

    // ✅ 필터바 DOM: CSS가 인식하도록 .fm-filter-bar 클래스 부여 + 한 줄
    const filterWrap = document.createElement('div');
    filterWrap.innerHTML = `
      <div class="fm-filter-actions" style="display:inline-flex;gap:6px;margin-right:8px;white-space:nowrap;">
        <button type="button" id="fm-filter-all" class="fm-filter-pill fm-filter-pill--primary">전체</button>
        <button type="button" id="fm-filter-none" class="fm-filter-pill">해제</button>
      </div>
      <div class="fm-filter-row" style="display:flex;flex-wrap:nowrap;gap:6px;align-items:center;white-space:nowrap;overflow-x:auto;overflow-y:hidden;">
        ${CATEGORIES.map(c => `
          <label class="fm-filter-item" style="white-space:nowrap;">
            <input type="checkbox" class="fm-cat-check" data-key="${c.key}" checked>
            <span class="fm-dot" style="display:inline-block;width:10px;height:10px;border-radius:50%;background:${c.color}"></span>
            <span>${c.label}</span>
          </label>
        `).join('')}
      </div>`;
    if (filterHost) {
      filterHost.appendChild(filterWrap);
    } else {
      console.warn('[findbymap] #fm-filter-host 없음 — 필터바 부착 실패');
    }

    // 지오코딩
    const geoCache = new Map();
    async function geocode(addr) {
      if (!addr) return null;
      if (geoCache.has(addr)) return geoCache.get(addr);
      const p = new Promise(resolve => {
        naver.maps.Service.geocode({ query: addr }, (status, res) => {
          if (status !== naver.maps.Service.Status.OK) return resolve(null);
          const a = res?.v2?.addresses?.[0]; if (!a) return resolve(null);
          resolve(new naver.maps.LatLng(parseFloat(a.y), parseFloat(a.x)));
        });
      });
      const ll = await p; geoCache.set(addr, ll); return ll;
    }

    // 상태
    let items = [];                 // { id, cafe, latlng, marker, categories[], hidden:boolean }
    const byId = new Map();
    let activeId = null;
    let loading = false;
    let nextToken = null;           // 뷰포트 기반 토큰
    let listNextToken = null;       // 전역 리스트 토큰
    const PAGE_SIZE = 1000;
    let lastQueryKey = '';
    let didInitViewport = false;
    const FETCH_DEBOUNCE_MS = 250;
    const CLICK_FOCUS_ZOOM = 16;

    // 🔔 리스트 즉시 반영 스케줄러 (지연 렌더)
    let renderTimer = null;
    function scheduleRender() {
      if (renderTimer) return;
      renderTimer = setTimeout(() => {
        renderTimer = null;
        renderListFiltered();
      }, 80);
    }

    function getBbox(map) {
      const b = map.getBounds(); if (!b) return null;
      const sw = b.getSW(); const ne = b.getNE();
      return [sw.lng(), sw.lat(), ne.lng(), ne.lat()];
    }
    function getZoom(map) { return map.getZoom(); }
    function getActiveKeys() {
      return Array.from(document.querySelectorAll('.fm-cat-check'))
        .filter(chk => chk.checked)
        .map(chk => chk.dataset.key);
    }
    function matchesFilter(it, activeSet) {
      if (!activeSet || activeSet.size === 0) return true;
      return it.categories.some(k => activeSet.has(k));
    }

    // 리스트 활성화 (중앙 스크롤)
    function activateCard(id, scroll = true) {
      activeId = id;
      const prev = document.querySelector('.fm-info-card.fm-active');
      if (prev) prev.classList.remove('fm-active');
      const card = document.querySelector(`.fm-info-card[data-id="${id}"]`);
      if (card) {
        card.classList.add('fm-active');
        if (scroll) {
          const container = document.querySelector('.fm-list');
          const containerTop = container.getBoundingClientRect().top;
          const cardTop = card.getBoundingClientRect().top;
          const scrollOffset = cardTop - containerTop - container.clientHeight / 2 + card.clientHeight / 2;
          container.scrollBy({ top: scrollOffset, behavior: 'smooth' });
        }
      }
    }
    function ensureActiveVisible() {
      if (!activeId) return;
      const card = document.querySelector(`.fm-info-card[data-id="${activeId}"]`);
      if (card) card.classList.add('fm-active');
    }

    // 리스트 렌더
    function renderListFiltered() {
      const active = new Set(getActiveKeys());
      const filtered = items.filter(it => matchesFilter(it, active));
      listEl.innerHTML = filtered.map(({ id, cafe, categories }) => {
        const badges = categories.map(k => {
          const c = CATEGORIES.find(x => x.key === k);
          return c ? `<span class="fm-badge" style="border-color:${c.color};color:${c.color}">${c.label}</span>` : '';
        }).join(' ');
        return `
          <div class="fm-info-card${id===activeId?' fm-active':''}" data-id="${id}">
            <div class="fm-title">${getCafeName(cafe)}</div>
            <div class="fm-meta">${cafe.address || ''}${cafe.rating!=null?` · ★ ${cafe.rating}`:''}</div>
            <div class="fm-badges">${badges}</div>
          </div>`;
      }).join('');
      ensureActiveVisible();
    }
    function inViewport(map, latlng) {
      if (!map || !latlng) return false;
      const b  = map.getBounds();
      if (!b) return false;
      const sw = b.getSW(), ne = b.getNE();
      const lat = latlng.lat(), lng = latlng.lng();
      return (lat >= sw.lat() && lat <= ne.lat() && lng >= sw.lng() && lng <= ne.lng());
    }
    function applyFilterToMap() {
      const active = new Set(getActiveKeys());
      const b = map.getBounds();

      for (const it of items) {
        const passFilter = matchesFilter(it, active);
        const passViewport = !!b && inViewport(map, it.latlng);
        const shouldShow = passFilter && passViewport;

        if (shouldShow) {
          if (!it.marker.getMap()) it.marker.setMap(map);
          it.hidden = false;
        } else {
          if (it.marker.getMap()) it.marker.setMap(null);
          it.hidden = true;
        }
      }
      renderListFiltered();
    }
    
    // // 지도 토글
    // function applyFilterToMap() {
    //   const active = new Set(getActiveKeys());
    //   for (const it of items) {
    //     const shouldShow = matchesFilter(it, active);
    //     if (shouldShow) {
    //       if (!it.marker.getMap()) it.marker.setMap(map);
    //       it.hidden = false;
    //     } else {
    //       if (it.marker.getMap()) it.marker.setMap(null);
    //       it.hidden = true;
    //     }
    //   }
    //   renderListFiltered();
    // }

    // 항목/마커 생성
    function addMarkerItem(r, latlng) {
      const name = getCafeName(r);
      const id = r.id || `${name}|${r.address||''}`;
      if (byId.has(id)) return null;

      const cats = getCafeCats(r);
      const color = primaryColorOf(cats);

      const activeSet = new Set(getActiveKeys());
      const shouldShow = matchesFilter({ categories: cats }, activeSet);

      const marker = new naver.maps.Marker({
        position: latlng, map: shouldShow ? map : null, title: name, icon: svgPin(color), zIndex: 10
      });

      const item = { id, cafe: r, latlng, marker, categories: cats, hidden: !shouldShow };
      items.push(item); byId.set(id, item);

      // 리스트를 되도록 즉시 체감되게
      scheduleRender();

      naver.maps.Event.addListener(marker, 'click', () => {
        openInfoOn(item);
        activateCard(id, true);
      });

      return item;
    }

    // API
    async function fetchPage({ bbox, zoom, cats, pageToken }) {
      const url = new URL(cfg.apiUrl, window.location.origin);
      url.searchParams.set('bbox', bbox.join(','));
      url.searchParams.set('zoom', String(zoom));
      if (cats.length) url.searchParams.set('cats', cats.join(','));
      url.searchParams.set('page_size', String(PAGE_SIZE));
      if (pageToken) url.searchParams.set('page_token', pageToken);
      const r = await fetch(url);
      if (!r.ok) throw new Error('API 실패 ' + r.status);
      return r.json();
    }

    // 뷰포트 로드(누적) — 좌표있는 건 즉시, 나머진 병렬 지오코딩 후 일괄 반영
    let debTimer = null;
    async function refreshForViewport() {
      const b = map.getBounds(); if (!b) return;
      const bbox = [b.getSW().lng(), b.getSW().lat(), b.getNE().lng(), b.getNE().lat()];
      const zoom = map.getZoom();
      const cats = getActiveKeys();

      clearTimeout(debTimer);
      debTimer = setTimeout(async () => {
        if (loading) return;
        loading = true;
        try {
          const { results, next_page_token } = await fetchPage({ bbox, zoom, cats, pageToken: null });
          nextToken = next_page_token || null;

          // 좌표 있는 건 즉시 생성
          for (const r of (results || [])) {
            if (r.lat != null && r.lng != null) {
              addMarkerItem(r, new naver.maps.LatLng(Number(r.lat), Number(r.lng)));
            }
          }
          scheduleRender();

          // 좌표 없는 건 병렬 지오코딩
          const jobs = (results || []).filter(r => r.lat == null || r.lng == null).map(async (r) => {
            const latlng = await geocode(r.address || '');
            if (!latlng) return;
            addMarkerItem(r, latlng);
          });
          await Promise.allSettled(jobs);
          applyFilterToMap();

          if (!didInitViewport) didInitViewport = true;
        } catch (e) {
          console.error('[findbymap] 첫 페이지 로드 실패', e);
          if (!items.length) listEl.innerHTML = `<div class="fm-error">데이터를 불러오지 못했습니다.</div>`;
        } finally {
          loading = false;
        }
      }, FETCH_DEBOUNCE_MS);
    }

    // 카테고리 변경 시: 전역(서울) 리스트 초기 로드 — 동일 전략
    async function refreshForCategoryGlobal() {
      const cats = getActiveKeys();
      const zoom = map.getZoom();
      listNextToken = null;
      try {
        const { results, next_page_token } = await fetchPage({ bbox: SEOUL_BBOX, zoom, cats, pageToken: null });
        listNextToken = next_page_token || null;

        for (const r of (results || [])) {
          if (r.lat != null && r.lng != null) {
            addMarkerItem(r, new naver.maps.LatLng(Number(r.lat), Number(r.lng)));
          }
        }
        scheduleRender();

        const jobs = (results || []).filter(r => r.lat == null || r.lng == null).map(async (r) => {
          const latlng = await geocode(r.address || '');
          if (!latlng) return;
          addMarkerItem(r, latlng);
        });
        await Promise.allSettled(jobs);
        applyFilterToMap();
      } catch (e) {
        console.error('[findbymap] 카테고리 전역 로드 실패', e);
      }
    }

    // 뷰포트 추가 로드
    async function loadMoreIfNeeded() {
      if (loading || !nextToken) return;
      const b = map.getBounds(); if (!b) return;
      const bbox = [b.getSW().lng(), b.getSW().lat(), b.getNE().lng(), b.getNE().lat()];
      const zoom = map.getZoom();
      const cats = getActiveKeys();

      loading = true;
      try {
        const { results, next_page_token } = await fetchPage({ bbox, zoom, cats, pageToken: nextToken });
        nextToken = next_page_token || null;

        for (const r of (results || [])) {
          if (r.lat != null && r.lng != null) {
            addMarkerItem(r, new naver.maps.LatLng(Number(r.lat), Number(r.lng)));
          }
        }
        scheduleRender();

        const jobs = (results || []).filter(r => r.lat == null || r.lng == null).map(async (r) => {
          const latlng = await geocode(r.address || '');
          if (!latlng) return;
          addMarkerItem(r, latlng);
        });
        await Promise.allSettled(jobs);
        applyFilterToMap();
      } catch (e) {
        console.error('[findbymap] 추가 페이지 로드 실패', e);
      } finally {
        loading = false;
      }
    }

    // 리스트 전용: 전역 추가 로드
    async function loadMoreListIfNeeded() {
      if (loading || !listNextToken) return;
      const zoom = map.getZoom();
      const cats = getActiveKeys();

      loading = true;
      try {
        const { results, next_page_token } = await fetchPage({ bbox: SEOUL_BBOX, zoom, cats, pageToken: listNextToken });
        listNextToken = next_page_token || null;

        for (const r of (results || [])) {
          if (r.lat != null && r.lng != null) {
            addMarkerItem(r, new naver.maps.LatLng(Number(r.lat), Number(r.lng)));
          }
        }
        scheduleRender();

        const jobs = (results || []).filter(r => r.lat == null || r.lng == null).map(async (r) => {
          const latlng = await geocode(r.address || '');
          if (!latlng) return;
          addMarkerItem(r, latlng);
        });
        await Promise.allSettled(jobs);
        applyFilterToMap();
      } catch (e) {
        console.error('[findbymap] 리스트 전역 추가 로드 실패', e);
      } finally {
        loading = false;
      }
    }

    // 리스트 클릭 → 포커스
    listEl.addEventListener('click', (e) => {
      const card = e.target.closest('.fm-info-card'); if (!card) return;
      const id = card.dataset.id;
      const it = byId.get(id); if (!it) return;

      if (it.marker && !it.marker.getMap()) it.marker.setMap(map);
      it.hidden = false;

      if (map.getZoom() < CLICK_FOCUS_ZOOM) map.setZoom(CLICK_FOCUS_ZOOM);
      map.panTo(it.latlng);
      openInfoOn(it);
      activateCard(id, false);
    });

    // 리스트 무한 스크롤 → 전역 로드
    listEl.addEventListener('scroll', () => {
      const nearBottom = listEl.scrollTop + listEl.clientHeight >= listEl.scrollHeight - 200;
      if (nearBottom) loadMoreListIfNeeded();
    });

    // 필터 변경
    const btnAll  = document.getElementById('fm-filter-all');
    const btnNone = document.getElementById('fm-filter-none');
    const catChecks = Array.from(document.querySelectorAll('.fm-cat-check'));

    /** 전체 버튼 색깔 갱신 */
    function updateAllButtonUI() {
      if (!btnAll) return;
      const allOn = catChecks.length > 0 && catChecks.every(chk => chk.checked);
      if (allOn) {
        btnAll.classList.add('is-active');   // 노랭이 ON
      } else {
        btnAll.classList.remove('is-active'); // 흰색으로
      }
    }

    // 체크박스 개별 변경 시
    catChecks.forEach(chk => {
      chk.addEventListener('change', () => {
        applyFilterToMap();
        refreshForCategoryGlobal();
        updateAllButtonUI();
      });
    });

    // 전체
    btnAll?.addEventListener('click', () => {
      catChecks.forEach(chk => chk.checked = true);
      applyFilterToMap();
      refreshForCategoryGlobal();
      updateAllButtonUI();
    });

    // 해제
    btnNone?.addEventListener('click', () => {
      catChecks.forEach(chk => chk.checked = false);
      applyFilterToMap();
      listNextToken = null;
      updateAllButtonUI();
    });

// 초기 상태도 한 번 맞춰주기
updateAllButtonUI();

    // 지도 이동 시: 뷰포트 로드
    naver.maps.Event.addListener(map, 'idle', () => {
      applyFilterToMap();      // ← 먼저 화면 밖 마커 숨김
      refreshForViewport();    // ← 그 다음 화면 안 데이터 fetch + 반영
    });

    // 최초 호출
    refreshForViewport();
  }
})();