// メトリクスデータの非同期読み込みとレンダリング

// Heroicons SVG definitions
const ICONS = {
    "arrow-path":
        '<svg class="hero-icon" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0 3.181 3.183a8.25 8.25 0 0 0 13.803-3.7M4.031 9.865a8.25 8.25 0 0 1 13.803-3.7l3.181 3.182m0-4.991v4.99" /></svg>',
    check: '<svg class="hero-icon" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" d="m4.5 12.75 6 6 9-13.5" /></svg>',
    "exclamation-triangle":
        '<svg class="hero-icon" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z" /></svg>',
    link: '<svg class="hero-icon" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" d="M13.19 8.688a4.5 4.5 0 0 1 1.242 7.244l-4.5 4.5a4.5 4.5 0 0 1-6.364-6.364l1.757-1.757m13.35-.622 1.757-1.757a4.5 4.5 0 0 0-6.364-6.364l-4.5 4.5a4.5 4.5 0 0 0 1.242 7.244" /></svg>',
    "chart-bar":
        '<svg class="hero-icon" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 0 1 3 19.875v-6.75ZM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V8.625ZM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V4.125Z" /></svg>',
    clock: '<svg class="hero-icon" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" /></svg>',
    "magnifying-glass":
        '<svg class="hero-icon" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" d="m21 21-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 5.196a7.5 7.5 0 0 0 10.607 10.607Z" /></svg>',
    "puzzle-piece":
        '<svg class="hero-icon" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" d="M14.25 6.087c0-.355.186-.676.401-.959.221-.29.349-.634.349-1.003 0-1.036-1.007-1.875-2.25-1.875s-2.25.84-2.25 1.875c0 .369.128.713.349 1.003.215.283.401.604.401.959v0a.64.64 0 0 1-.657.643 48.39 48.39 0 0 1-4.163-.3c.186 1.613.293 3.25.315 4.907a.656.656 0 0 1-.658.663v0c-.355 0-.676-.186-.959-.401a1.647 1.647 0 0 0-1.003-.349c-1.036 0-1.875 1.007-1.875 2.25s.84 2.25 1.875 2.25c.369 0 .713-.128 1.003-.349.283-.215.604-.401.959-.401v0c.31 0 .555.26.532.57a48.039 48.039 0 0 1-.642 5.056c1.518.19 3.058.309 4.616.354a.64.64 0 0 0 .657-.643v0c0-.355-.186-.676-.401-.959a1.647 1.647 0 0 1-.349-1.003c0-1.035 1.008-1.875 2.25-1.875 1.243 0 2.25.84 2.25 1.875 0 .369-.128.713-.349 1.003-.215.283-.4.604-.4.959v0c0 .333.277.599.61.58a48.1 48.1 0 0 0 5.427-.63 48.05 48.05 0 0 0 .582-4.717.532.532 0 0 0-.533-.57v0c-.355 0-.676.186-.959.401-.29.221-.634.349-1.003.349-1.035 0-1.875-1.007-1.875-2.25s.84-2.25 1.875-2.25c.37 0 .713.128 1.003.349.283.215.604.401.96.401v0a.656.656 0 0 0 .658-.663 48.422 48.422 0 0 0-.37-5.36c-1.886.342-3.81.574-5.766.689a.578.578 0 0 1-.61-.58v0Z" /></svg>',
    "chart-line":
        '<svg class="hero-icon" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" d="M3.75 3v11.25A2.25 2.25 0 0 0 6 16.5h2.25M3.75 3h-1.5m1.5 0h16.5m0 0h1.5m-1.5 0v11.25A2.25 2.25 0 0 1 18 16.5h-2.25m-7.5 0h7.5m-7.5 0-1 3m8.5-3 1 3m0 0 .5 1.5m-.5-1.5h-9.5m0 0-.5 1.5M9 11.25v1.5M12 9v3.75m3-6v6" /></svg>',
    "bars-arrow-down":
        '<svg class="hero-icon" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" d="M3 4.5h14.25M3 9h9.75M3 13.5h9.75m4.5-4.5v12m0 0-3.75-3.75M17.25 21l3.75-3.75" /></svg>',
    calendar:
        '<svg class="hero-icon" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" d="M6.75 3v2.25M17.25 3v2.25M3 18.75V7.5a2.25 2.25 0 0 1 2.25-2.25h13.5A2.25 2.25 0 0 1 21 7.5v11.25m-18 0A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75m-18 0v-7.5A2.25 2.25 0 0 1 5.25 9h13.5A2.25 2.25 0 0 1 21 11.25v7.5" /></svg>',
};

// 現在選択中の期間（日数）または カスタム期間
let currentDaysLimit = 30;
let customStartDate = null;
let customEndDate = null;
let isCustomPeriod = false;
let hasCustomChanges = false;

// 期間選択ボタンのクリックハンドラ
function selectPeriod(days) {
    currentDaysLimit = days;
    isCustomPeriod = false;
    customStartDate = null;
    customEndDate = null;

    // カスタムフォームを非表示
    const customForm = document.getElementById("custom-period-form");
    if (customForm) customForm.style.display = "none";

    // ボタンのスタイルを更新
    const buttons = document.querySelectorAll("#period-selector button");
    buttons.forEach((button) => {
        const buttonDays = button.getAttribute("data-days");
        if (buttonDays === String(days)) {
            button.classList.remove("is-light");
            button.classList.add("is-primary");
        } else {
            button.classList.remove("is-primary");
            button.classList.add("is-light");
        }
    });

    // URLパラメータを更新
    const url = new URL(window.location.href);
    url.searchParams.set("days", days);
    url.searchParams.delete("start");
    url.searchParams.delete("end");
    window.history.replaceState({}, "", url);

    // サブタイトルを初期状態にリセット
    window.subtitleUpdated = false;

    // データを再読み込み
    loadMetricsData();
}

// カスタム期間ボタンのトグル
function toggleCustomPeriod() {
    const customForm = document.getElementById("custom-period-form");
    const customBtn = document.getElementById("custom-period-btn");

    if (customForm.style.display === "none") {
        // フォームを表示
        customForm.style.display = "block";

        // 他のボタンを非選択状態に
        const buttons = document.querySelectorAll("#period-selector button");
        buttons.forEach((button) => {
            button.classList.remove("is-primary");
            button.classList.add("is-light");
        });
        customBtn.classList.remove("is-light");
        customBtn.classList.add("is-primary");

        // 初期値を設定（現在選択中の期間に基づく）
        initializeCustomDateInputs();

        // 開始日時入力にフォーカス
        setTimeout(() => {
            const startInput = document.getElementById("custom-start");
            if (startInput) startInput.focus();
        }, 100);
    } else {
        // フォームを非表示
        customForm.style.display = "none";
        customBtn.classList.remove("is-primary");
        customBtn.classList.add("is-light");

        // 以前の期間ボタンを再選択
        if (!isCustomPeriod) {
            const buttons = document.querySelectorAll("#period-selector button");
            buttons.forEach((button) => {
                const buttonDays = button.getAttribute("data-days");
                if (buttonDays === String(currentDaysLimit)) {
                    button.classList.remove("is-light");
                    button.classList.add("is-primary");
                }
            });
        }
    }
}

// カスタム日時入力の初期化
function initializeCustomDateInputs() {
    const startInput = document.getElementById("custom-start");
    const endInput = document.getElementById("custom-end");

    if (!startInput || !endInput) return;

    // 終了日時は現在
    const now = new Date();
    now.setSeconds(0, 0);

    // 開始日時は現在の期間設定に基づく
    const start = new Date(now);
    start.setDate(start.getDate() - currentDaysLimit);
    start.setSeconds(0, 0);

    // datetime-local形式に変換
    startInput.value = formatDateForInput(start);
    endInput.value = formatDateForInput(now);

    // 変更フラグをリセット
    hasCustomChanges = false;
    updateApplyButtonState();
}

// 日付をdatetime-local入力用にフォーマット
function formatDateForInput(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, "0");
    const day = String(date.getDate()).padStart(2, "0");
    const hours = String(date.getHours()).padStart(2, "0");
    const minutes = String(date.getMinutes()).padStart(2, "0");
    return `${year}-${month}-${day}T${hours}:${minutes}`;
}

// カスタム日時変更時のハンドラ
function onCustomDateChange() {
    hasCustomChanges = true;
    updateApplyButtonState();
}

// Enterキー押下時のハンドラ
function onCustomKeyPress(event) {
    if (event.key === "Enter" && hasCustomChanges) {
        applyCustomPeriod();
    }
}

// 適用ボタンの状態を更新
function updateApplyButtonState() {
    const applyBtn = document.getElementById("apply-custom-period");
    if (!applyBtn) return;

    if (hasCustomChanges) {
        applyBtn.disabled = false;
        applyBtn.classList.remove("is-light");
        applyBtn.classList.add("is-info");
        applyBtn.innerHTML =
            '<span class="icon is-small">' + ICONS["arrow-path"] + "</span><span>期間を確定して更新</span>";
    } else {
        applyBtn.disabled = true;
        applyBtn.classList.remove("is-info");
        applyBtn.classList.add("is-light");
        applyBtn.innerHTML =
            '<span class="icon is-small">' + ICONS["check"] + "</span><span>期間を確定して更新</span>";
    }
}

// カスタム期間を適用
function applyCustomPeriod() {
    const startInput = document.getElementById("custom-start");
    const endInput = document.getElementById("custom-end");

    if (!startInput || !endInput) return;

    const start = new Date(startInput.value);
    const end = new Date(endInput.value);

    // バリデーション
    if (isNaN(start.getTime()) || isNaN(end.getTime())) {
        alert("有効な日時を入力してください");
        return;
    }

    if (start >= end) {
        alert("開始日時は終了日時より前に設定してください");
        return;
    }

    // カスタム期間を設定
    customStartDate = start;
    customEndDate = end;
    isCustomPeriod = true;
    hasCustomChanges = false;

    // URLパラメータを更新
    const url = new URL(window.location.href);
    url.searchParams.delete("days");
    url.searchParams.set("start", start.toISOString());
    url.searchParams.set("end", end.toISOString());
    window.history.replaceState({}, "", url);

    // ボタン状態を更新
    updateApplyButtonState();

    // サブタイトルを初期状態にリセット
    window.subtitleUpdated = false;

    // データを再読み込み
    loadMetricsData();
}

// APIリクエスト用のパラメータを取得
function getApiParams() {
    if (isCustomPeriod && customStartDate && customEndDate) {
        return `start=${customStartDate.toISOString()}&end=${customEndDate.toISOString()}`;
    }
    return `days=${currentDaysLimit}`;
}

// URLパラメータから初期の期間を取得
function getInitialDaysLimit() {
    const urlParams = new URLSearchParams(window.location.search);

    // カスタム期間のパラメータをチェック
    const startParam = urlParams.get("start");
    const endParam = urlParams.get("end");
    if (startParam && endParam) {
        const start = new Date(startParam);
        const end = new Date(endParam);
        if (!isNaN(start.getTime()) && !isNaN(end.getTime())) {
            customStartDate = start;
            customEndDate = end;
            isCustomPeriod = true;
            return null; // カスタム期間を使用
        }
    }

    // 日数パラメータをチェック
    const days = urlParams.get("days");
    if (days) {
        const parsedDays = parseInt(days);
        if (!isNaN(parsedDays) && parsedDays >= 1 && parsedDays <= 365) {
            return parsedDays;
        }
    }
    return 30; // デフォルトは30日
}

// データ取得とレンダリングのメイン処理
async function loadMetricsData() {
    try {
        // コンテンツを表示
        document.getElementById("metrics-content").style.display = "block";

        // 総セクション数を定義（メイン6 + 異常検知1）
        const mainSections = 6; // alerts, basic-stats, hourly-patterns, diff-sec, trends, panel-trends
        let currentSection = 0;

        // メインセクションを順次読み込み（高速）
        await loadAndRenderSection(
            "alerts",
            "/api/metrics/alerts",
            renderAlerts,
            false,
            ++currentSection,
            mainSections
        );
        await loadAndRenderSection(
            "basic-stats",
            "/api/metrics/basic-stats",
            renderBasicStats,
            false,
            ++currentSection,
            mainSections
        );
        await loadAndRenderSection(
            "hourly-patterns",
            "/api/metrics/hourly-patterns",
            renderHourlyPatterns,
            false,
            ++currentSection,
            mainSections
        );
        await loadAndRenderSection(
            "diff-sec",
            "/api/metrics/hourly-patterns",
            renderDiffSec,
            false,
            ++currentSection,
            mainSections
        ); // 同じデータを使用
        await loadAndRenderSection(
            "trends",
            "/api/metrics/trends",
            renderTrends,
            false,
            ++currentSection,
            mainSections
        );
        await loadAndRenderSection(
            "panel-trends",
            "/api/metrics/panel-trends",
            renderPanelTrends,
            false,
            ++currentSection,
            mainSections
        );

        // パネル別日別推移データを追加で読み込み
        await loadPanelDailyTrendsAsync();

        // メインセクション完了 - 進捗表示を更新
        const progressDisplay = document.getElementById("progress-display");
        if (progressDisplay) {
            const progressText = document.getElementById("progress-text");
            if (progressText) {
                progressText.textContent = "異常検知データを読み込み中...";
            }
        }

        console.log("メインセクションの読み込み完了 - 異常検知を非同期で読み込み開始");

        // 異常検知セクションを非同期で読み込み（ブロックしない）
        loadAnomaliesAsync();
    } catch (error) {
        console.error("メトリクスデータの読み込みエラー:", error);
        showError(error.message);
    }
}

// パネル別日別推移データを読み込み
async function loadPanelDailyTrendsAsync() {
    try {
        const urlWithParams = `/api/metrics/panel-daily-trends?${getApiParams()}`;
        console.log(`パネル別日別推移データの取得開始: ${urlWithParams}`);

        const response = await fetch(window.metricsApiBaseUrl + urlWithParams);

        if (!response.ok) {
            throw new Error(`データの取得に失敗しました (${response.status})`);
        }

        const data = await response.json();
        console.log("パネル別日別推移データの取得完了:", data);

        // データをグローバル変数に設定
        window.panelDailyTrendsData = data.panel_daily_trends;

        // グラフを生成（chart-functions.js の関数を呼び出し）
        if (typeof generatePanelDailyTrendsCharts === "function") {
            generatePanelDailyTrendsCharts();
        }
    } catch (error) {
        console.error("パネル別日別推移データの読み込みエラー:", error);
    }
}

// 異常検知セクションを非同期で読み込み
async function loadAnomaliesAsync() {
    const container = document.getElementById("anomalies-container");
    if (!container) return;

    // ローディング表示
    container.innerHTML = `
        <div style="display: flex; align-items: center; justify-content: center; min-height: 200px; color: #666;">
            <div style="display: flex; align-items: center;">
                <span class="loading-spinner" style="margin-right: 0.8rem;"></span>
                <span style="font-size: 1rem;">異常検知データを分析中...</span>
            </div>
        </div>
    `;

    try {
        const urlWithParams = `/api/metrics/anomalies?${getApiParams()}`;
        console.log(`異常検知データの取得開始: ${urlWithParams}`);

        const response = await fetch(window.metricsApiBaseUrl + urlWithParams);

        if (!response.ok) {
            throw new Error(`データの取得に失敗しました (${response.status})`);
        }

        const data = await response.json();
        console.log("異常検知データの取得完了:", data);
        console.log("anomalies:", data.anomalies);
        console.log("performance_stats:", data.performance_stats);

        // データをグローバル変数に設定
        window.anomaliesData = data.anomalies;
        window.performanceStats = data.performance_stats;
        if (!window.subtitleUpdated && data.data_range) {
            updateSubtitle(data.data_range);
            window.subtitleUpdated = true;
        }

        // コンテンツをレンダリング
        const content = await renderAnomalies(data);
        container.innerHTML = content;

        // 進捗表示を非表示
        const progressDisplay = document.getElementById("progress-display");
        if (progressDisplay) {
            progressDisplay.style.display = "none";
        }

        console.log("全てのメトリクスデータの読み込み完了");
    } catch (error) {
        console.error("異常検知データのレンダリングエラー:", error);
        container.innerHTML = `
            <div style="display: flex; align-items: center; justify-content: center; min-height: 200px;">
                <div class="error-message" style="padding: 2rem; text-align: center; color: #721c24; background-color: #f8d7da; border: 1px solid #f5c6cb; border-radius: 6px;">
                    ${ICONS["exclamation-triangle"]}
                    異常検知データの表示に失敗しました
                </div>
            </div>
        `;
        // エラーでも進捗表示は非表示に
        const progressDisplay = document.getElementById("progress-display");
        if (progressDisplay) {
            progressDisplay.style.display = "none";
        }
    }
}

// 個別セクションの読み込みとレンダリング
async function loadAndRenderSection(
    sectionId,
    apiUrl,
    renderFunc,
    isLast = false,
    currentStep = 0,
    totalSteps = 0
) {
    const container = document.getElementById(`${sectionId}-container`);
    if (!container) return;

    // 統一進捗表示を更新
    updateProgressDisplay(getSectionName(sectionId), currentStep, totalSteps);

    // セクション内にローディング表示を追加
    container.innerHTML = `
        <div style="display: flex; align-items: center; justify-content: center; min-height: 200px; color: #666;">
            <div style="display: flex; align-items: center;">
                <span class="loading-spinner" style="margin-right: 0.8rem;"></span>
                <span style="font-size: 1rem;">${getSectionName(sectionId)}を準備中...</span>
            </div>
        </div>
    `;

    try {
        // 期間パラメータを追加
        const urlWithParams = `${apiUrl}?${getApiParams()}`;
        console.log(`${sectionId}データの取得開始: ${urlWithParams}`);

        const response = await fetch(window.metricsApiBaseUrl + urlWithParams);

        if (!response.ok) {
            const errorData = await response.json().catch(() => null);
            if (errorData && errorData.error === "database_not_found") {
                throw new Error(
                    `メトリクスデータベースが見つかりません。<br>
                    ${errorData.message}<br>
                    <small>${errorData.details}</small>`
                );
            }
            throw new Error(`データの取得に失敗しました (${response.status})`);
        }

        const data = await response.json();
        console.log(`${sectionId}データの取得完了`);

        // データをグローバル変数に設定（既存のチャート生成関数用）
        setGlobalData(sectionId, data);

        // コンテンツをレンダリング
        const content = await renderFunc(data);
        container.innerHTML = content;

        // 少し遅延を入れて次のセクションを読み込む
        await new Promise((resolve) => setTimeout(resolve, 100));
    } catch (error) {
        console.error(`${sectionId}のレンダリングエラー:`, error);
        container.innerHTML = `
            <div style="display: flex; align-items: center; justify-content: center; min-height: 200px;">
                <div class="error-message" style="padding: 2rem; text-align: center; color: #721c24; background-color: #f8d7da; border: 1px solid #f5c6cb; border-radius: 6px;">
                    ${ICONS["exclamation-triangle"]}
                    ${getSectionName(sectionId)}の表示に失敗しました
                </div>
            </div>
        `;
        updateProgressDisplay(`${getSectionName(sectionId)}でエラーが発生しました`, currentStep, totalSteps);
    }
}

// 統一進捗表示を更新
function updateProgressDisplay(sectionName, currentStep, totalSteps) {
    const progressText = document.getElementById("progress-text");
    if (progressText) {
        if (currentStep > 0 && totalSteps > 0) {
            progressText.textContent = `${sectionName}を読み込み中... (${currentStep}/${totalSteps})`;
        } else {
            progressText.textContent = `${sectionName}を読み込み中...`;
        }
    }
}

// セクション名を取得
function getSectionName(sectionId) {
    const names = {
        alerts: "アラート",
        "basic-stats": "基本統計",
        "hourly-patterns": "時間別パターン",
        "diff-sec": "表示タイミング",
        trends: "パフォーマンス推移",
        "panel-trends": "パネル別推移",
        anomalies: "異常検知",
    };
    return names[sectionId] || sectionId;
}

// データをグローバル変数に設定
function setGlobalData(sectionId, data) {
    switch (sectionId) {
        case "hourly-patterns":
        case "diff-sec":
            window.hourlyData = data.hourly_patterns;
            // サブタイトルも更新（初回のみ）
            if (!window.subtitleUpdated && data.data_range) {
                updateSubtitle(data.data_range);
                window.subtitleUpdated = true;
            }
            break;
        case "trends":
            window.trendsData = data.trends;
            break;
        case "panel-trends":
            window.panelTrendsData = data.panel_trends;
            break;
        case "panel-daily-trends":
            window.panelDailyTrendsData = data.panel_daily_trends;
            break;
        case "anomalies":
            window.anomaliesData = data.anomalies;
            window.performanceStats = data.performance_stats;
            // サブタイトル更新（まだの場合）
            if (!window.subtitleUpdated && data.data_range) {
                updateSubtitle(data.data_range);
                window.subtitleUpdated = true;
            }
            break;
    }
}

// セクションを順次レンダリング
async function renderSection(sectionId, renderFunc, isLast = false) {
    const container = document.getElementById(`${sectionId}-container`);
    if (!container) return;

    // ローディング表示を追加（最後のセクション以外）
    if (!isLast) {
        const loadingHtml = `
            <div class="loading-overlay" id="${sectionId}-loading">
                <div class="loading-spinner"></div>
                <span class="loading-text">読み込み中...</span>
            </div>
        `;
        container.innerHTML = loadingHtml;
    }

    // 少し遅延を入れて段階的に表示
    await new Promise((resolve) => setTimeout(resolve, 100));

    try {
        // コンテンツをレンダリング
        const content = await renderFunc();
        container.innerHTML = content;
    } catch (error) {
        console.error(`${sectionId}のレンダリングエラー:`, error);
        container.innerHTML = `<div class="error-message">セクションの表示に失敗しました</div>`;
    }
}

// サブタイトルを更新
function updateSubtitle(dataRange) {
    let subtitleText = "パフォーマンス監視と異常検知";

    if (dataRange && dataRange.overall && dataRange.overall.earliest) {
        try {
            const earliestStr = dataRange.overall.earliest;
            const latestStr = dataRange.overall.latest;

            // ISO形式の日時をパース
            const earliestDt = new Date(earliestStr);
            const latestDt = new Date(latestStr);

            // 日数を計算
            const daysDiff = Math.floor((latestDt - earliestDt) / (1000 * 60 * 60 * 24)) + 1;

            // 開始日をフォーマット
            const year = earliestDt.getFullYear();
            const month = earliestDt.getMonth() + 1;
            const day = earliestDt.getDate();
            const startDateFormatted = `${year}年${month}月${day}日`;

            subtitleText = `過去${daysDiff}日間（${startDateFormatted}〜）のパフォーマンス監視と異常検知`;
        } catch (e) {
            console.error("日付のパースエラー:", e);
        }
    }

    document.getElementById("subtitle").textContent = subtitleText;
}

// エラー表示
function showError(message) {
    document.getElementById("initial-loading").style.display = "none";
    const errorContainer = document.getElementById("error-container");
    errorContainer.innerHTML = `
        <div class="notification is-danger">
            <span class="icon">${ICONS["exclamation-triangle"]}</span>
            <div>${message}</div>
        </div>
    `;
    errorContainer.style.display = "block";
}

// 各セクションのレンダリング関数
function renderAlerts(data) {
    const alerts = data.alerts;
    if (!alerts || alerts.length === 0) {
        // アラートがない場合は何も表示しない
        return "";
    }

    let alertsHtml = `
        <div class="section" id="alerts">
            <h2 class="title is-4 section-header">
                <div class="permalink-container">
                    <span class="icon">${ICONS["exclamation-triangle"]}</span>
                    パフォーマンスアラート
                    <span class="permalink-icon" onclick="copyPermalink('alerts')">${ICONS["link"]}</span>
                </div>
            </h2>
    `;

    for (const alert of alerts) {
        const severityClass = {
            critical: "is-danger",
            warning: "is-warning",
            info: "is-info",
        }[alert.severity || "info"];

        const alertType = (alert.type || "アラート").replace("_", " ");
        const alertMessage = alert.message || "メッセージなし";

        alertsHtml += `
            <div class="notification ${severityClass} alert-item">
                <strong>${alertType}:</strong> ${alertMessage}
            </div>
        `;
    }

    alertsHtml += "</div>";
    return alertsHtml;
}

function renderBasicStats(data) {
    const basicStats = data.basic_stats;
    const drawPanel = basicStats.draw_panel || {};
    const displayImage = basicStats.display_image || {};

    return `
        <div class="section" id="basic-stats">
            <h2 class="title is-4 section-header">
                <div class="permalink-container">
                    <span class="icon">${ICONS["chart-bar"]}</span>
                    基本統計
                    <span class="permalink-icon" onclick="copyPermalink('basic-stats')">${ICONS["link"]}</span>
                </div>
            </h2>

            <div class="columns">
                <div class="column">
                    <div class="card metrics-card" id="draw-panel-stats">
                        <span class="card-permalink" onclick="copyPermalink('draw-panel-stats')">${ICONS["link"]}</span>
                        <div class="card-header">
                            <p class="card-header-title">画像生成処理</p>
                        </div>
                        <div class="card-content">
                            <div class="columns is-multiline">
                                <div class="column is-half">
                                    <div class="has-text-centered">
                                        <p class="heading">総実行回数</p>
                                        <p class="stat-number has-text-primary">
                                            ${(drawPanel.total_operations || 0).toLocaleString()}
                                        </p>
                                    </div>
                                </div>
                                <div class="column is-half">
                                    <div class="has-text-centered">
                                        <p class="heading">エラー回数</p>
                                        <p class="stat-number has-text-danger">
                                            ${(drawPanel.error_count || 0).toLocaleString()}
                                        </p>
                                    </div>
                                </div>
                                <div class="column is-half">
                                    <div class="has-text-centered">
                                        <p class="heading">平均処理時間（秒）</p>
                                        <p class="stat-number has-text-info">
                                            ${(drawPanel.avg_elapsed_time || 0).toFixed(2)}
                                        </p>
                                    </div>
                                </div>
                                <div class="column is-half">
                                    <div class="has-text-centered">
                                        <p class="heading">最大処理時間（秒）</p>
                                        <p class="stat-number has-text-warning">
                                            ${(drawPanel.max_elapsed_time || 0).toFixed(2)}
                                        </p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="column">
                    <div class="card metrics-card" id="display-image-stats">
                        <span class="card-permalink" onclick="copyPermalink('display-image-stats')">${ICONS["link"]}</span>
                        <div class="card-header">
                            <p class="card-header-title">表示実行処理</p>
                        </div>
                        <div class="card-content">
                            <div class="columns is-multiline">
                                <div class="column is-half">
                                    <div class="has-text-centered">
                                        <p class="heading">総実行回数</p>
                                        <p class="stat-number has-text-primary">
                                            ${(displayImage.total_operations || 0).toLocaleString()}
                                        </p>
                                    </div>
                                </div>
                                <div class="column is-half">
                                    <div class="has-text-centered">
                                        <p class="heading">失敗回数</p>
                                        <p class="stat-number has-text-danger">
                                            ${(displayImage.failure_count || 0).toLocaleString()}
                                        </p>
                                    </div>
                                </div>
                                <div class="column is-half">
                                    <div class="has-text-centered">
                                        <p class="heading">平均処理時間（秒）</p>
                                        <p class="stat-number has-text-info">
                                            ${(displayImage.avg_elapsed_time || 0).toFixed(2)}
                                        </p>
                                    </div>
                                </div>
                                <div class="column is-half">
                                    <div class="has-text-centered">
                                        <p class="heading">最大処理時間（秒）</p>
                                        <p class="stat-number has-text-warning">
                                            ${(displayImage.max_elapsed_time || 0).toFixed(2)}
                                        </p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
}

function renderHourlyPatterns() {
    const html = `
        <div class="section" id="hourly-patterns">
            <h2 class="title is-4 section-header">
                <div class="permalink-container">
                    <span class="icon">${ICONS["clock"]}</span>
                    時間別パフォーマンスパターン
                    <span class="permalink-icon" onclick="copyPermalink('hourly-patterns')">${ICONS["link"]}</span>
                </div>
            </h2>

            <div class="columns">
                <div class="column is-half">
                    <div class="card metrics-card" id="draw-panel-hourly">
                        <span class="card-permalink" onclick="copyPermalink('draw-panel-hourly')">${ICONS["link"]}</span>
                        <div class="card-header">
                            <p class="card-header-title">画像生成処理 - 時間別パフォーマンス</p>
                        </div>
                        <div class="card-content">
                            <div class="chart-container">
                                <canvas id="drawPanelHourlyChart"></canvas>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="column is-half">
                    <div class="card metrics-card" id="draw-panel-boxplot">
                        <span class="card-permalink" onclick="copyPermalink('draw-panel-boxplot')">${ICONS["link"]}</span>
                        <div class="card-header">
                            <p class="card-header-title">画像生成処理 - 時間別分布</p>
                        </div>
                        <div class="card-content">
                            <div class="chart-container">
                                <canvas id="drawPanelBoxplotChart"></canvas>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <div class="columns">
                <div class="column is-half">
                    <div class="card metrics-card" id="display-image-hourly">
                        <span class="card-permalink" onclick="copyPermalink('display-image-hourly')">${ICONS["link"]}</span>
                        <div class="card-header">
                            <p class="card-header-title">表示実行処理 - 時間別パフォーマンス</p>
                        </div>
                        <div class="card-content">
                            <div class="chart-container">
                                <canvas id="displayImageHourlyChart"></canvas>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="column is-half">
                    <div class="card metrics-card" id="display-image-box">
                        <span class="card-permalink" onclick="copyPermalink('display-image-box')">${ICONS["link"]}</span>
                        <div class="card-header">
                            <p class="card-header-title">表示実行処理 - 時間別分布</p>
                        </div>
                        <div class="card-content">
                            <div class="chart-container">
                                <canvas id="displayImageBoxplotChart"></canvas>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;

    // DOMに追加後、チャートを生成
    setTimeout(() => {
        generateHourlyCharts();
        generateBoxplotCharts();
    }, 100);

    return html;
}

function renderDiffSec() {
    const html = `
        <div class="section" id="display-timing">
            <h2 class="title is-4 section-header">
                <div class="permalink-container">
                    <span class="icon">${ICONS["clock"]}</span> 表示タイミング
                    <span class="permalink-icon" onclick="copyPermalink('display-timing')">${ICONS["link"]}</span>
                </div>
            </h2>
            <p class="subtitle is-6">表示実行時の分単位での秒数の偏差（0秒が理想的なタイミング）</p>

            <div class="columns">
                <div class="column is-half">
                    <div class="card metrics-card" id="diff-sec-hourly">
                        <span class="card-permalink" onclick="copyPermalink('diff-sec-hourly')">${ICONS["link"]}</span>
                        <div class="card-header">
                            <p class="card-header-title">表示タイミング - 時間別パフォーマンス</p>
                        </div>
                        <div class="card-content">
                            <div class="chart-container">
                                <canvas id="diffSecHourlyChart"></canvas>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="column is-half">
                    <div class="card metrics-card" id="diff-sec-boxplot">
                        <span class="card-permalink" onclick="copyPermalink('diff-sec-boxplot')">${ICONS["link"]}</span>
                        <div class="card-header">
                            <p class="card-header-title">表示タイミング - 時間別分布</p>
                        </div>
                        <div class="card-content">
                            <div class="chart-container">
                                <canvas id="diffSecBoxplotChart"></canvas>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;

    // DOMに追加後、チャートを生成
    setTimeout(() => {
        generateDiffSecCharts();
    }, 100);

    return html;
}

function renderTrends() {
    const html = `
        <div class="section" id="performance-trends">
            <h2 class="title is-4 section-header">
                <div class="permalink-container">
                    <span class="icon">${ICONS["chart-line"]}</span>
                    パフォーマンス推移
                    <span class="permalink-icon" onclick="copyPermalink('performance-trends')">${ICONS["link"]}</span>
                </div>
            </h2>
            <p class="subtitle is-6">平均処理時間の箱ヒゲ図（実行回数は非表示）</p>

            <div class="columns">
                <div class="column is-6">
                    <div class="card metrics-card" id="draw-panel-trends">
                        <span class="card-permalink" onclick="copyPermalink('draw-panel-trends')">${ICONS["link"]}</span>
                        <div class="card-header">
                            <p class="card-header-title">画像生成処理 - 日別推移</p>
                        </div>
                        <div class="card-content">
                            <div class="chart-container">
                                <canvas id="drawPanelTrendsChart"></canvas>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="column is-6">
                    <div class="card metrics-card" id="display-image-trends">
                        <span class="card-permalink" onclick="copyPermalink('display-image-trends')">${ICONS["link"]}</span>
                        <div class="card-header">
                            <p class="card-header-title">表示実行処理 - 日別推移</p>
                        </div>
                        <div class="card-content">
                            <div class="chart-container">
                                <canvas id="displayImageTrendsChart"></canvas>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <div class="columns">
                <div class="column is-6">
                    <div class="card metrics-card" id="diff-sec-trends">
                        <span class="card-permalink" onclick="copyPermalink('diff-sec-trends')">${ICONS["link"]}</span>
                        <div class="card-header">
                            <p class="card-header-title">表示タイミング - 日別推移</p>
                        </div>
                        <div class="card-content">
                            <div class="chart-container">
                                <canvas id="diffSecTrendsChart"></canvas>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;

    // DOMに追加後、チャートを生成
    setTimeout(() => {
        generateTrendsCharts();
    }, 100);

    return html;
}

function renderPanelTrends() {
    const html = `
        <div class="section" id="panel-trends">
            <h2 class="title is-4 section-header">
                <div class="permalink-container">
                    <span class="icon">${ICONS["puzzle-piece"]}</span>
                    パネル別処理時間ヒストグラム
                    <span class="permalink-icon" onclick="copyPermalink('panel-trends')">${ICONS["link"]}</span>
                </div>
            </h2>
            <p class="subtitle is-6">各パネルの処理時間分布をヒストグラムで表示（横軸：時間、縦軸：割合）</p>

            <div class="columns is-multiline is-variable is-1" id="panelTrendsContainer"
                 style="justify-content: flex-start;">
                <!-- パネル別ヒストグラムがJavaScriptで動的に生成される -->
            </div>
        </div>

        <div class="section" id="panel-timeseries">
            <h2 class="title is-4 section-header">
                <div class="permalink-container">
                    <span class="icon">${ICONS["chart-line"]}</span>
                    パネル別処理時間推移
                    <span class="permalink-icon" onclick="copyPermalink('panel-timeseries')">${ICONS["link"]}</span>
                </div>
            </h2>
            <p class="subtitle is-6">各パネルの日別処理時間推移（ドラッグでズーム可能）</p>

            <div class="columns is-multiline" id="panelDailyTrendsContainer">
                <!-- パネル別日別推移グラフがJavaScriptで動的に生成される -->
                <div class="column is-full" style="display: flex; align-items: center; justify-content: center; min-height: 200px; color: #666;">
                    <div style="display: flex; align-items: center;">
                        <span class="loading-spinner" style="margin-right: 0.8rem;"></span>
                        <span style="font-size: 1rem;">パネル別推移データを読み込み中...</span>
                    </div>
                </div>
            </div>
        </div>
    `;

    // DOMに追加後、チャートを生成
    setTimeout(() => {
        generatePanelTrendsCharts();
    }, 100);

    return html;
}

function renderAnomalies(data) {
    const anomalies = data.anomalies || {};
    const performanceStats = data.performance_stats || {};

    const drawPanelAnomalies = anomalies.draw_panel || {};
    const displayImageAnomalies = anomalies.display_image || {};

    const dpAnomalyCount = (drawPanelAnomalies.anomalies_detected || 0).toLocaleString();
    const diAnomalyCount = (displayImageAnomalies.anomalies_detected || 0).toLocaleString();

    // データをグローバルに保存（ソート切り替え用）
    window.anomalyData = {
        drawPanel: {
            list: drawPanelAnomalies.anomalies || [],
            stats: performanceStats.draw_panel || {},
        },
        displayImage: {
            list: displayImageAnomalies.anomalies || [],
            stats: performanceStats.display_image || {},
        },
    };

    const dpItems = renderAnomalyItemsGlobal(
        drawPanelAnomalies.anomalies,
        performanceStats.draw_panel,
        "draw_panel",
        "sigma"
    );
    const diItems = renderAnomalyItemsGlobal(
        displayImageAnomalies.anomalies,
        performanceStats.display_image,
        "display_image",
        "sigma"
    );

    // ソート選択ボタンのHTML
    const sortButtons = `
        <div class="buttons has-addons mb-3">
            <button class="button is-small anomaly-sort-btn is-info" data-sort="sigma" data-target="draw-panel">
                <span class="icon is-small">${ICONS["bars-arrow-down"]}</span>
                <span>外れ幅順</span>
            </button>
            <button class="button is-small anomaly-sort-btn" data-sort="date" data-target="draw-panel">
                <span class="icon is-small">${ICONS["calendar"]}</span>
                <span>日付順</span>
            </button>
        </div>
    `;
    const sortButtonsDi = `
        <div class="buttons has-addons mb-3">
            <button class="button is-small anomaly-sort-btn is-info" data-sort="sigma" data-target="display-image">
                <span class="icon is-small">${ICONS["bars-arrow-down"]}</span>
                <span>外れ幅順</span>
            </button>
            <button class="button is-small anomaly-sort-btn" data-sort="date" data-target="display-image">
                <span class="icon is-small">${ICONS["calendar"]}</span>
                <span>日付順</span>
            </button>
        </div>
    `;

    return `
        <div class="section" id="anomaly-detection">
            <h2 class="title is-4 section-header">
                <div class="permalink-container">
                    <span class="icon">${ICONS["magnifying-glass"]}</span> 異常検知
                    <span class="permalink-icon" onclick="copyPermalink('anomaly-detection')">${ICONS["link"]}</span>
                </div>
            </h2>

            <div class="columns">
                <div class="column">
                    <div class="card metrics-card" id="draw-panel-anomalies">
                        <span class="card-permalink" onclick="copyPermalink('draw-panel-anomalies')">${ICONS["link"]}</span>
                        <div class="card-header">
                            <p class="card-header-title">画像生成処理の異常</p>
                        </div>
                        <div class="card-content">
                            <div class="has-text-centered" style="margin-bottom: 1rem;">
                                <p class="heading">検出された異常数</p>
                                <p class="stat-number has-text-warning">${dpAnomalyCount}</p>
                            </div>
                            ${sortButtons}
                            <div id="draw-panel-anomaly-list">${dpItems}</div>
                        </div>
                    </div>
                </div>

                <div class="column">
                    <div class="card metrics-card" id="display-anomalies">
                        <span class="card-permalink" onclick="copyPermalink('display-anomalies')">${ICONS["link"]}</span>
                        <div class="card-header">
                            <p class="card-header-title">表示実行処理の異常</p>
                        </div>
                        <div class="card-content">
                            <div class="has-text-centered" style="margin-bottom: 1rem;">
                                <p class="heading">検出された異常数</p>
                                <p class="stat-number has-text-warning">${diAnomalyCount}</p>
                            </div>
                            ${sortButtonsDi}
                            <div id="display-image-anomaly-list">${diItems}</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
}

// 異常アイテムのHTML生成（グローバル関数）
function renderAnomalyItemsGlobal(anomalyList, stats, type, sortBy = "sigma") {
    if (!anomalyList || anomalyList.length === 0) return "";

    const avgTime = stats?.avg_time || 0;
    const stdTime = stats?.std_time || 0;

    // σ値を計算してリストに追加
    const itemsWithSigma = anomalyList.map((anomaly) => {
        const sigma = stdTime > 0 ? Math.abs((anomaly.elapsed_time - avgTime) / stdTime) : 0;
        return { ...anomaly, _sigma: sigma };
    });

    // ソート（デフォルトはσの絶対値が大きい順）
    let sorted;
    if (sortBy === "date") {
        sorted = [...itemsWithSigma].sort((a, b) => (b.timestamp || "").localeCompare(a.timestamp || ""));
    } else {
        sorted = [...itemsWithSigma].sort((a, b) => b._sigma - a._sigma);
    }

    let html = '<div class="content">';
    for (const anomaly of sorted.slice(0, 20)) {
        const elapsedTime = anomaly.elapsed_time || 0;
        const reasons = [];
        const details = [];

        if (type === "draw_panel") {
            if (elapsedTime > 60) {
                reasons.push('<span class="tag is-small is-warning">長時間処理</span>');
            } else if (elapsedTime < 1) {
                reasons.push('<span class="tag is-small is-info">短時間処理</span>');
            }
            if (anomaly.error_code > 0) {
                reasons.push('<span class="tag is-small is-danger">エラー発生</span>');
                details.push(`エラーコード: <strong>${anomaly.error_code}</strong>`);
            }
        } else {
            if (elapsedTime > 120) {
                reasons.push('<span class="tag is-small is-warning">長時間処理</span>');
            } else if (elapsedTime < 5) {
                reasons.push('<span class="tag is-small is-info">短時間処理</span>');
            }
            if (anomaly.success === false || anomaly.success === 0) {
                reasons.push('<span class="tag is-small is-danger">実行失敗</span>');
                details.push("実行結果: <strong>失敗</strong>");
            }
        }

        if (stdTime > 0) {
            const sigma = (elapsedTime - avgTime) / stdTime;
            const sign = sigma >= 0 ? "+" : "";
            details.push(`平均値から<strong>${sign}${sigma.toFixed(1)}σ</strong>乖離`);
        }
        details.push(`実行時間: <strong>${elapsedTime.toFixed(2)}秒</strong>`);

        if (reasons.length === 0) {
            reasons.push('<span class="tag is-small is-light">パターン異常</span>');
        }

        // 日時フォーマット
        let formattedTime = "不明";
        try {
            if (anomaly.timestamp) {
                const dt = new Date(anomaly.timestamp);
                const year = dt.getFullYear();
                const month = dt.getMonth() + 1;
                const day = dt.getDate();
                const hour = dt.getHours();
                const min = dt.getMinutes();
                formattedTime = `${year}年${month}月${day}日 ${hour}時${min}分`;

                const now = new Date();
                const elapsed = now - dt;
                const elapsedDays = Math.floor(elapsed / (1000 * 60 * 60 * 24));
                const elapsedHours = Math.floor(elapsed / (1000 * 60 * 60));
                const elapsedMins = Math.floor(elapsed / (1000 * 60));

                if (elapsedDays > 0) {
                    formattedTime += ` (${elapsedDays}日前)`;
                } else if (elapsedHours > 0) {
                    formattedTime += ` (${elapsedHours}時間前)`;
                } else if (elapsedMins > 0) {
                    formattedTime += ` (${elapsedMins}分前)`;
                } else {
                    formattedTime += " (たった今)";
                }
            }
        } catch (e) {
            formattedTime = anomaly.timestamp || "不明";
        }

        html += `<div class="anomaly-item">
            <div class="mb-2">
                <span class="tag is-warning">${formattedTime}</span>
                ${reasons.join(" ")}
            </div>
            <div class="pl-3 has-text-grey-dark" style="font-size: 0.9rem;">
                ${details.join(" | ")}
            </div>
        </div>`;
    }
    html += "</div>";
    return html;
}

// ソートボタンのクリックハンドラを設定
function setupAnomalySortButtons() {
    document.addEventListener("click", function (e) {
        const btn = e.target.closest(".anomaly-sort-btn");
        if (!btn) return;

        const sortBy = btn.getAttribute("data-sort");
        const target = btn.getAttribute("data-target");

        // ボタングループ内のボタン状態を更新
        const buttonGroup = btn.closest(".buttons");
        if (buttonGroup) {
            buttonGroup.querySelectorAll(".anomaly-sort-btn").forEach((b) => {
                b.classList.remove("is-info");
            });
            btn.classList.add("is-info");
        }

        // 対象のリストを再レンダリング
        if (target === "draw-panel" && window.anomalyData?.drawPanel) {
            const container = document.getElementById("draw-panel-anomaly-list");
            if (container) {
                container.innerHTML = renderAnomalyItemsGlobal(
                    window.anomalyData.drawPanel.list,
                    window.anomalyData.drawPanel.stats,
                    "draw_panel",
                    sortBy
                );
            }
        } else if (target === "display-image" && window.anomalyData?.displayImage) {
            const container = document.getElementById("display-image-anomaly-list");
            if (container) {
                container.innerHTML = renderAnomalyItemsGlobal(
                    window.anomalyData.displayImage.list,
                    window.anomalyData.displayImage.stats,
                    "display_image",
                    sortBy
                );
            }
        }
    });
}

// ページ読み込み時に実行
document.addEventListener("DOMContentLoaded", function () {
    // ソートボタンのイベントハンドラを設定
    setupAnomalySortButtons();
    // URLパラメータから初期の期間を取得
    const initialDays = getInitialDaysLimit();
    if (initialDays !== null) {
        currentDaysLimit = initialDays;
    }

    // 期間選択ボタンの初期状態を設定
    const buttons = document.querySelectorAll("#period-selector button");
    buttons.forEach((button) => {
        const buttonDays = button.getAttribute("data-days");
        if (isCustomPeriod && buttonDays === "custom") {
            // カスタム期間が選択されている場合
            button.classList.remove("is-light");
            button.classList.add("is-primary");
        } else if (!isCustomPeriod && buttonDays === String(currentDaysLimit)) {
            button.classList.remove("is-light");
            button.classList.add("is-primary");
        } else {
            button.classList.remove("is-primary");
            button.classList.add("is-light");
        }
    });

    // カスタム期間の場合、フォームを表示して値を設定
    if (isCustomPeriod && customStartDate && customEndDate) {
        const customForm = document.getElementById("custom-period-form");
        const startInput = document.getElementById("custom-start");
        const endInput = document.getElementById("custom-end");

        if (customForm && startInput && endInput) {
            customForm.style.display = "block";
            startInput.value = formatDateForInput(customStartDate);
            endInput.value = formatDateForInput(customEndDate);
        }
    }

    // 進捗表示を表示
    const progressDisplay = document.getElementById("progress-display");
    if (progressDisplay) {
        progressDisplay.style.display = "flex";
    }

    // データを非同期で読み込み
    loadMetricsData();

    // 既存のパーマリンク処理
    if (window.location.hash) {
        const element = document.querySelector(window.location.hash);
        if (element) {
            setTimeout(() => {
                element.scrollIntoView({ behavior: "smooth", block: "start" });
            }, 1000);
        }
    }
});
