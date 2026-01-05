// メトリクスデータの非同期読み込みとレンダリング

// 現在選択中の期間（日数）
let currentDaysLimit = 30;

// 期間選択ボタンのクリックハンドラ
function selectPeriod(days) {
    currentDaysLimit = days;

    // ボタンのスタイルを更新
    const buttons = document.querySelectorAll("#period-selector button");
    buttons.forEach((button) => {
        const buttonDays = parseInt(button.getAttribute("data-days"));
        if (buttonDays === days) {
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
    window.history.replaceState({}, "", url);

    // サブタイトルを初期状態にリセット
    window.subtitleUpdated = false;

    // データを再読み込み
    loadMetricsData();
}

// URLパラメータから初期の期間を取得
function getInitialDaysLimit() {
    const urlParams = new URLSearchParams(window.location.search);
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
            true,
            ++currentSection,
            mainSections
        );

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
        const urlWithParams = `/api/metrics/anomalies?days=${currentDaysLimit}`;
        console.log(`異常検知データの取得開始: ${urlWithParams}`);

        const response = await fetch(window.metricsApiBaseUrl + urlWithParams);

        if (!response.ok) {
            throw new Error(`データの取得に失敗しました (${response.status})`);
        }

        const data = await response.json();
        console.log("異常検知データの取得完了");

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
                    <i class="fas fa-exclamation-triangle" style="margin-right: 0.5rem; color: #721c24;"></i>
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
        const urlWithParams = `${apiUrl}?days=${currentDaysLimit}`;
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
                    <i class="fas fa-exclamation-triangle" style="margin-right: 0.5rem; color: #721c24;"></i>
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
            <span class="icon"><i class="fas fa-exclamation-triangle"></i></span>
            <div>${message}</div>
        </div>
    `;
    errorContainer.style.display = "block";
}

// 各セクションのレンダリング関数
function renderAlerts(data) {
    const alerts = data.alerts;
    if (!alerts || alerts.length === 0) {
        return `
            <div class="notification is-success" id="alerts" style="margin-bottom: 1rem; padding: 0.75rem;">
                <span class="icon"><i class="fas fa-check-circle"></i></span>
                パフォーマンスアラートは検出されていません。
            </div>
        `;
    }

    let alertsHtml = `
        <div class="section" id="alerts">
            <h2 class="title is-4 section-header">
                <div class="permalink-container">
                    <span class="icon"><i class="fas fa-exclamation-triangle"></i></span>
                    パフォーマンスアラート
                    <i class="fas fa-link permalink-icon" onclick="copyPermalink('alerts')"></i>
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
                    <span class="icon"><i class="fas fa-chart-bar"></i></span>
                    基本統計
                    <i class="fas fa-link permalink-icon" onclick="copyPermalink('basic-stats')"></i>
                </div>
            </h2>

            <div class="columns">
                <div class="column">
                    <div class="card metrics-card" id="draw-panel-stats">
                        <i class="fas fa-link card-permalink" onclick="copyPermalink('draw-panel-stats')"></i>
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
                        <i class="fas fa-link card-permalink" onclick="copyPermalink('display-image-stats')"></i>
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
                    <span class="icon"><i class="fas fa-clock"></i></span>
                    時間別パフォーマンスパターン
                    <i class="fas fa-link permalink-icon" onclick="copyPermalink('hourly-patterns')"></i>
                </div>
            </h2>

            <div class="columns">
                <div class="column is-half">
                    <div class="card metrics-card" id="draw-panel-hourly">
                        <i class="fas fa-link card-permalink" onclick="copyPermalink('draw-panel-hourly')"></i>
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
                        <i class="fas fa-link card-permalink" onclick="copyPermalink('draw-panel-boxplot')"></i>
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
                        <i class="fas fa-link card-permalink" onclick="copyPermalink('display-image-hourly')"></i>
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
                        <i class="fas fa-link card-permalink" onclick="copyPermalink('display-image-box')"></i>
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
                    <span class="icon"><i class="fas fa-clock"></i></span> 表示タイミング
                    <i class="fas fa-link permalink-icon" onclick="copyPermalink('display-timing')"></i>
                </div>
            </h2>
            <p class="subtitle is-6">表示実行時の分単位での秒数の偏差（0秒が理想的なタイミング）</p>

            <div class="columns">
                <div class="column is-half">
                    <div class="card metrics-card" id="diff-sec-hourly">
                        <i class="fas fa-link card-permalink" onclick="copyPermalink('diff-sec-hourly')"></i>
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
                        <i class="fas fa-link card-permalink" onclick="copyPermalink('diff-sec-boxplot')"></i>
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
                    <span class="icon"><i class="fas fa-chart-area"></i></span>
                    パフォーマンス推移
                    <i class="fas fa-link permalink-icon" onclick="copyPermalink('performance-trends')"></i>
                </div>
            </h2>
            <p class="subtitle is-6">平均処理時間の箱ヒゲ図（実行回数は非表示）</p>

            <div class="columns">
                <div class="column is-6">
                    <div class="card metrics-card" id="draw-panel-trends">
                        <i class="fas fa-link card-permalink" onclick="copyPermalink('draw-panel-trends')"></i>
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
                        <i class="fas fa-link card-permalink" onclick="copyPermalink('display-image-trends')"></i>
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
                        <i class="fas fa-link card-permalink" onclick="copyPermalink('diff-sec-trends')"></i>
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
                    <span class="icon"><i class="fas fa-puzzle-piece"></i></span>
                    パネル別処理時間ヒストグラム
                    <i class="fas fa-link permalink-icon" onclick="copyPermalink('panel-trends')"></i>
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
                    <span class="icon"><i class="fas fa-chart-line"></i></span>
                    パネル別処理時間推移
                    <i class="fas fa-link permalink-icon" onclick="copyPermalink('panel-timeseries')"></i>
                </div>
            </h2>
            <p class="subtitle is-6">各パネルの処理時間の時系列推移グラフ（時間軸での処理時間変化）</p>

            <div class="columns">
                <div class="column">
                    <div class="card metrics-card" id="panel-time-series">
                        <i class="fas fa-link card-permalink" onclick="copyPermalink('panel-time-series')"></i>
                        <div class="card-header">
                            <p class="card-header-title">パネル別処理時間推移</p>
                        </div>
                        <div class="card-content">
                            <div class="chart-container">
                                <canvas id="panelTimeSeriesChart"></canvas>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;

    // DOMに追加後、チャートを生成
    setTimeout(() => {
        generatePanelTrendsCharts();
        generatePanelTimeSeriesChart();
    }, 100);

    return html;
}

function renderAnomalies(data) {
    const anomalies = data.anomalies;
    const performanceStats = data.performance_stats;
    // 既存のgenerate_anomalies_sectionの内容をJavaScript化
    // （長いので省略しますが、page.pyのgenerate_anomalies_sectionと同じロジック）
    return `
        <div class="section" id="anomaly-detection">
            <h2 class="title is-4 section-header">
                <div class="permalink-container">
                    <span class="icon"><i class="fas fa-search"></i></span> 異常検知
                    <i class="fas fa-link permalink-icon" onclick="copyPermalink('anomaly-detection')"></i>
                </div>
            </h2>
            <div class="notification is-info is-light">
                <p><strong>異常検知について：</strong></p>
                <p>機械学習の<strong>Isolation Forest</strong>アルゴリズムを使用して、
                   以下の要素から異常なパターンを検知しています：</p>
                <ul>
                    <li><strong>処理時間</strong>：通常より極端に長い、または短い処理時間</li>
                    <li><strong>エラー発生</strong>：エラーの有無も考慮要素</li>
                </ul>
                <p>例：異常に長い処理時間、エラーを伴う異常な処理時間など</p>
            </div>
            <!-- 簡略化のため詳細は省略 -->
        </div>
    `;
}

// ページ読み込み時に実行
document.addEventListener("DOMContentLoaded", function () {
    // URLパラメータから初期の期間を取得
    currentDaysLimit = getInitialDaysLimit();

    // 期間選択ボタンの初期状態を設定
    const buttons = document.querySelectorAll("#period-selector button");
    buttons.forEach((button) => {
        const buttonDays = parseInt(button.getAttribute("data-days"));
        if (buttonDays === currentDaysLimit) {
            button.classList.remove("is-light");
            button.classList.add("is-primary");
        } else {
            button.classList.remove("is-primary");
            button.classList.add("is-light");
        }
    });

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
