// Chart.js用の重いチャート生成関数（page_js.pyの内容を移動）

// ============================================
// プラグインの登録と確認
// ============================================

// chartjs-plugin-zoom の登録状態を確認・登録
(function () {
    console.log("chart-functions.js: Checking Chart.js plugins...");
    console.log("  - Chart:", typeof Chart !== "undefined" ? "loaded" : "NOT LOADED");
    console.log("  - ChartZoom:", typeof ChartZoom !== "undefined" ? "loaded" : "NOT LOADED");

    // Chart.js が読み込まれているか確認
    if (typeof Chart === "undefined") {
        console.error("chart-functions.js: Chart.js is not loaded!");
        return;
    }

    // chartjs-plugin-zoom が読み込まれている場合、明示的に登録
    if (typeof ChartZoom !== "undefined") {
        // 既に登録されているかチェック
        const registeredPlugins = Chart.registry?.plugins?.items || [];
        const zoomRegistered = Array.from(registeredPlugins).some(
            (p) => p.id === "zoom" || p.name === "zoom"
        );
        console.log("  - Zoom plugin already registered:", zoomRegistered);

        if (!zoomRegistered) {
            try {
                Chart.register(ChartZoom);
                console.log("  - Zoom plugin registered successfully");
            } catch (e) {
                console.error("  - Failed to register zoom plugin:", e);
            }
        }
    } else {
        console.warn("chart-functions.js: ChartZoom is not available. Drag zoom will not work.");
    }

    // 登録されているプラグインを表示
    if (Chart.registry?.plugins) {
        const pluginIds = [];
        Chart.registry.plugins.items.forEach((p) => pluginIds.push(p.id));
        console.log("  - Registered plugins:", pluginIds.join(", "));
    }
})();

// ============================================
// 定数とユーティリティ関数
// ============================================

// 処理時間のY軸最大値（秒）
const MAX_ELAPSED_TIME = 30;

// パネル別処理時間のX軸最大値（秒）
const MAX_PANEL_ELAPSED_TIME = 15;

// 値を最大値でクランプする
function clampValue(value) {
    return Math.min(value, MAX_ELAPSED_TIME);
}

// パネル別処理時間用に値をクランプする
function clampPanelValue(value) {
    return Math.min(value, MAX_PANEL_ELAPSED_TIME);
}

// 箱ひげ図の統計量をクランプする
function clampBoxplotStats(stats) {
    if (!stats) return stats;
    return {
        ...stats,
        min: clampValue(stats.min),
        q1: clampValue(stats.q1),
        median: clampValue(stats.median),
        q3: clampValue(stats.q3),
        max: clampValue(stats.max),
        outliers: (stats.outliers || []).map(clampValue),
    };
}

// パネル別処理時間用に箱ひげ図の統計量をクランプする
function clampPanelBoxplotStats(stats) {
    if (!stats) return stats;
    return {
        ...stats,
        min: clampPanelValue(stats.min),
        q1: clampPanelValue(stats.q1),
        median: clampPanelValue(stats.median),
        q3: clampPanelValue(stats.q3),
        max: clampPanelValue(stats.max),
        outliers: (stats.outliers || []).map(clampPanelValue),
    };
}

// 処理時間用Y軸設定を取得
function getElapsedTimeYAxisConfig(titleText = "処理時間（秒）") {
    return {
        display: true,
        max: MAX_ELAPSED_TIME,
        title: { display: true, text: titleText, font: { size: 14, weight: "bold" } },
        ticks: {
            callback: function (value) {
                if (value === MAX_ELAPSED_TIME) return MAX_ELAPSED_TIME + "以上";
                return value;
            },
        },
    };
}

// 処理時間用X軸設定を取得（横向きboxplot用）
function getElapsedTimeXAxisConfig(titleText = "処理時間（秒）") {
    return {
        display: true,
        max: MAX_ELAPSED_TIME,
        title: { display: true, text: titleText, font: { size: 14, weight: "bold" } },
        ticks: {
            callback: function (value) {
                if (value === MAX_ELAPSED_TIME) return MAX_ELAPSED_TIME + "以上";
                return value;
            },
        },
    };
}

// パネル別処理時間用X軸設定を取得（横向きboxplot用）
function getPanelElapsedTimeXAxisConfig(titleText = "処理時間（秒）") {
    return {
        display: true,
        max: MAX_PANEL_ELAPSED_TIME,
        title: { display: true, text: titleText, font: { size: 14, weight: "bold" } },
        ticks: {
            callback: function (value) {
                if (value === MAX_PANEL_ELAPSED_TIME) return MAX_PANEL_ELAPSED_TIME + "以上";
                return value;
            },
        },
    };
}

// ズームプラグイン設定を取得
function getZoomPluginConfig(resetButtonId) {
    return {
        pan: { enabled: true, mode: "x" },
        zoom: {
            drag: {
                enabled: true,
                backgroundColor: "rgba(54, 162, 235, 0.3)",
                borderColor: "rgba(54, 162, 235, 0.8)",
                borderWidth: 1,
            },
            mode: "x",
            onZoomComplete: function () {
                const btn = document.getElementById(resetButtonId);
                if (btn) btn.style.display = "inline-block";
            },
        },
    };
}

// ズームリセットボタンを作成
function createZoomResetButton(container, chartInstance, buttonId) {
    const btn = document.createElement("button");
    btn.id = buttonId;
    btn.className = "button is-small is-info zoom-reset-btn";
    btn.innerHTML = '<span class="icon is-small"><i class="fas fa-undo"></i></span><span>リセット</span>';
    btn.style.cssText = "display:none; position:absolute; top:10px; right:10px; z-index:10;";
    btn.onclick = function () {
        chartInstance.resetZoom();
        btn.style.display = "none";
    };
    container.style.position = "relative";
    container.appendChild(btn);
    return btn;
}

// ============================================
// チャート生成関数
// ============================================

function generateDiffSecCharts() {
    // 表示タイミング 時間別パフォーマンス
    const diffSecCtx = document.getElementById("diffSecHourlyChart");
    if (diffSecCtx && window.hourlyData?.diff_sec) {
        new Chart(diffSecCtx, {
            type: "line",
            data: {
                labels: window.hourlyData.diff_sec.map((d) => d.hour + "時"),
                datasets: [
                    {
                        label: "平均タイミング差（秒）",
                        data: window.hourlyData.diff_sec.map((d) => d.avg_diff_sec),
                        borderColor: "rgb(255, 159, 64)",
                        backgroundColor: "rgba(255, 159, 64, 0.2)",
                        tension: 0.1,
                        borderWidth: 3,
                        pointRadius: 4,
                        pointHoverRadius: 6,
                    },
                    {
                        label: "最小タイミング差（秒）",
                        data: window.hourlyData.diff_sec.map((d) => d.min_diff_sec),
                        borderColor: "rgb(34, 197, 94)",
                        backgroundColor: "rgba(34, 197, 94, 0.1)",
                        tension: 0.1,
                        borderDash: [8, 4],
                        borderWidth: 2,
                        pointRadius: 3,
                        pointHoverRadius: 5,
                    },
                    {
                        label: "最大タイミング差（秒）",
                        data: window.hourlyData.diff_sec.map((d) => d.max_diff_sec),
                        borderColor: "rgb(239, 68, 68)",
                        backgroundColor: "rgba(239, 68, 68, 0.1)",
                        tension: 0.1,
                        borderDash: [4, 4],
                        borderWidth: 2,
                        pointRadius: 3,
                        pointHoverRadius: 5,
                    },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: { mode: "index", intersect: false },
                plugins: {
                    legend: {
                        position: "top",
                        labels: { usePointStyle: true, padding: 8, font: { size: 12 } },
                    },
                    tooltip: {
                        mode: "index",
                        intersect: false,
                        backgroundColor: "rgba(0, 0, 0, 0.8)",
                        titleColor: "white",
                        bodyColor: "white",
                        borderColor: "rgba(255, 255, 255, 0.3)",
                        borderWidth: 1,
                        callbacks: {
                            title: function (context) {
                                return "時刻: " + context[0].label;
                            },
                            label: function (context) {
                                let label = context.dataset.label || "";
                                if (label) label += ": ";
                                if (context.parsed.y !== null) {
                                    label += context.parsed.y.toFixed(1) + "秒";
                                }
                                return label;
                            },
                            afterBody: function (context) {
                                if (context.length > 0) {
                                    const dataIndex = context[0].dataIndex;
                                    const hourData = window.hourlyData.diff_sec[dataIndex];
                                    if (hourData) return "実行回数: " + (hourData.count || 0) + "回";
                                }
                                return "";
                            },
                        },
                    },
                },
                scales: {
                    x: {
                        display: true,
                        grid: { color: "rgba(0, 0, 0, 0.1)", display: true },
                        title: { display: true, text: "時間", font: { size: 14, weight: "bold" } },
                    },
                    y: {
                        type: "linear",
                        display: true,
                        position: "left",
                        title: {
                            display: true,
                            text: "タイミング差（秒）",
                            font: { size: 14, weight: "bold" },
                        },
                        grid: { color: "rgba(255, 159, 64, 0.2)" },
                    },
                },
            },
        });
    }

    // 箱ひげ図も同様に軽量化
    const diffSecBoxplotCtx = document.getElementById("diffSecBoxplotChart");
    if (diffSecBoxplotCtx && window.hourlyData?.diff_sec_boxplot) {
        const boxplotData = [];
        for (let hour = 0; hour < 24; hour++) {
            if (window.hourlyData.diff_sec_boxplot[hour]) {
                boxplotData.push({
                    x: hour + "時",
                    y: window.hourlyData.diff_sec_boxplot[hour],
                });
            }
        }

        new Chart(diffSecBoxplotCtx, {
            type: "boxplot",
            data: {
                labels: boxplotData.map((d) => d.x),
                datasets: [
                    {
                        label: "タイミング差分布（秒）",
                        data: boxplotData.map((d) => d.y),
                        backgroundColor: "rgba(255, 159, 64, 0.6)",
                        borderColor: "rgb(255, 159, 64)",
                        borderWidth: 2,
                        outlierColor: "rgb(239, 68, 68)",
                        medianColor: "rgb(255, 193, 7)",
                    },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: "top" },
                    tooltip: {
                        backgroundColor: "rgba(0, 0, 0, 0.8)",
                        titleColor: "white",
                        bodyColor: "white",
                        callbacks: {
                            title: function (context) {
                                return "時刻: " + context[0].label;
                            },
                            label: function (context) {
                                const stats = context.parsed;
                                return [
                                    "最小値: " + stats.min.toFixed(1) + "秒",
                                    "第1四分位: " + stats.q1.toFixed(1) + "秒",
                                    "中央値: " + stats.median.toFixed(1) + "秒",
                                    "第3四分位: " + stats.q3.toFixed(1) + "秒",
                                    "最大値: " + stats.max.toFixed(1) + "秒",
                                ];
                            },
                        },
                    },
                },
                scales: {
                    x: {
                        display: true,
                        title: { display: true, text: "時間", font: { size: 14, weight: "bold" } },
                    },
                    y: {
                        display: true,
                        title: {
                            display: true,
                            text: "タイミング差（秒）",
                            font: { size: 14, weight: "bold" },
                        },
                    },
                },
            },
        });
    }
}

function generateBoxplotCharts() {
    // 画像生成処理 箱ひげ図
    const drawPanelBoxplotCtx = document.getElementById("drawPanelBoxplotChart");
    if (drawPanelBoxplotCtx && window.hourlyData?.draw_panel_boxplot) {
        const boxplotData = [];
        for (let hour = 0; hour < 24; hour++) {
            if (window.hourlyData.draw_panel_boxplot[hour]) {
                boxplotData.push({
                    x: hour + "時",
                    y: clampBoxplotStats(window.hourlyData.draw_panel_boxplot[hour]),
                });
            }
        }

        new Chart(drawPanelBoxplotCtx, {
            type: "boxplot",
            data: {
                labels: boxplotData.map((d) => d.x),
                datasets: [
                    {
                        label: "処理時間分布（秒）",
                        data: boxplotData.map((d) => d.y),
                        backgroundColor: "rgba(75, 192, 192, 0.6)",
                        borderColor: "rgb(75, 192, 192)",
                        borderWidth: 2,
                        outlierColor: "rgb(239, 68, 68)",
                        medianColor: "rgb(255, 193, 7)",
                    },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: "top" },
                    tooltip: {
                        backgroundColor: "rgba(0, 0, 0, 0.8)",
                        titleColor: "white",
                        bodyColor: "white",
                        callbacks: {
                            title: function (context) {
                                return "時刻: " + context[0].label;
                            },
                            label: function (context) {
                                const stats = context.parsed;
                                return [
                                    "最小値: " + stats.min.toFixed(2) + "秒",
                                    "第1四分位: " + stats.q1.toFixed(2) + "秒",
                                    "中央値: " + stats.median.toFixed(2) + "秒",
                                    "第3四分位: " + stats.q3.toFixed(2) + "秒",
                                    "最大値: " + stats.max.toFixed(2) + "秒",
                                ];
                            },
                        },
                    },
                },
                scales: {
                    x: {
                        display: true,
                        title: { display: true, text: "時間", font: { size: 14, weight: "bold" } },
                    },
                    y: getElapsedTimeYAxisConfig(),
                },
            },
        });
    }

    // 表示実行処理 箱ひげ図
    const displayImageBoxplotCtx = document.getElementById("displayImageBoxplotChart");
    if (displayImageBoxplotCtx && window.hourlyData?.display_image_boxplot) {
        const boxplotData = [];
        for (let hour = 0; hour < 24; hour++) {
            if (window.hourlyData.display_image_boxplot[hour]) {
                boxplotData.push({
                    x: hour + "時",
                    y: clampBoxplotStats(window.hourlyData.display_image_boxplot[hour]),
                });
            }
        }

        new Chart(displayImageBoxplotCtx, {
            type: "boxplot",
            data: {
                labels: boxplotData.map((d) => d.x),
                datasets: [
                    {
                        label: "処理時間分布（秒）",
                        data: boxplotData.map((d) => d.y),
                        backgroundColor: "rgba(54, 162, 235, 0.6)",
                        borderColor: "rgb(54, 162, 235)",
                        borderWidth: 2,
                        outlierColor: "rgb(239, 68, 68)",
                        medianColor: "rgb(255, 193, 7)",
                    },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: "top" },
                    tooltip: {
                        backgroundColor: "rgba(0, 0, 0, 0.8)",
                        titleColor: "white",
                        bodyColor: "white",
                        callbacks: {
                            title: function (context) {
                                return "時刻: " + context[0].label;
                            },
                            label: function (context) {
                                const stats = context.parsed;
                                return [
                                    "最小値: " + stats.min.toFixed(2) + "秒",
                                    "第1四分位: " + stats.q1.toFixed(2) + "秒",
                                    "中央値: " + stats.median.toFixed(2) + "秒",
                                    "第3四分位: " + stats.q3.toFixed(2) + "秒",
                                    "最大値: " + stats.max.toFixed(2) + "秒",
                                ];
                            },
                        },
                    },
                },
                scales: {
                    x: {
                        display: true,
                        title: { display: true, text: "時間", font: { size: 14, weight: "bold" } },
                    },
                    y: getElapsedTimeYAxisConfig(),
                },
            },
        });
    }
}

function generateTrendsCharts() {
    // 画像生成処理 - 日別推移（新しい統計量形式に対応）
    const drawPanelTrendsCtx = document.getElementById("drawPanelTrendsChart");
    if (drawPanelTrendsCtx && window.trendsData?.draw_panel_boxplot) {
        const boxplotData = window.trendsData.draw_panel_boxplot.map((d) => ({
            x: d.date,
            y: clampBoxplotStats(d.stats), // 統計量をクランプ
        }));

        const drawPanelResetBtnId = "drawPanelTrendsChart-reset";
        const drawPanelChart = new Chart(drawPanelTrendsCtx, {
            type: "boxplot",
            data: {
                labels: boxplotData.map((d) => d.x),
                datasets: [
                    {
                        label: "処理時間分布（秒）",
                        data: boxplotData.map((d) => d.y),
                        backgroundColor: "rgba(75, 192, 192, 0.6)",
                        borderColor: "rgb(75, 192, 192)",
                        borderWidth: 2,
                        outlierColor: "rgb(239, 68, 68)",
                        medianColor: "rgb(255, 193, 7)",
                    },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    zoom: getZoomPluginConfig(drawPanelResetBtnId),
                },
                scales: {
                    x: {
                        display: true,
                        title: { display: true, text: "日付", font: { size: 12, weight: "bold" } },
                        ticks: { maxRotation: 45, minRotation: 45 },
                    },
                    y: getElapsedTimeYAxisConfig("時間（秒）"),
                },
            },
        });
        // リセットボタンを追加
        createZoomResetButton(drawPanelTrendsCtx.parentElement, drawPanelChart, drawPanelResetBtnId);
    }

    // 表示実行処理 - 日別推移（新しい統計量形式に対応）
    const displayImageTrendsCtx = document.getElementById("displayImageTrendsChart");
    if (displayImageTrendsCtx && window.trendsData?.display_image_boxplot) {
        const boxplotData = window.trendsData.display_image_boxplot.map((d) => ({
            x: d.date,
            y: clampBoxplotStats(d.stats), // 統計量をクランプ
        }));

        const displayImageResetBtnId = "displayImageTrendsChart-reset";
        const displayImageChart = new Chart(displayImageTrendsCtx, {
            type: "boxplot",
            data: {
                labels: boxplotData.map((d) => d.x),
                datasets: [
                    {
                        label: "処理時間分布（秒）",
                        data: boxplotData.map((d) => d.y),
                        backgroundColor: "rgba(54, 162, 235, 0.6)",
                        borderColor: "rgb(54, 162, 235)",
                        borderWidth: 2,
                        outlierColor: "rgb(239, 68, 68)",
                        medianColor: "rgb(255, 193, 7)",
                    },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    zoom: getZoomPluginConfig(displayImageResetBtnId),
                },
                scales: {
                    x: {
                        display: true,
                        title: { display: true, text: "日付", font: { size: 12, weight: "bold" } },
                        ticks: { maxRotation: 45, minRotation: 45 },
                    },
                    y: getElapsedTimeYAxisConfig("時間（秒）"),
                },
            },
        });
        // リセットボタンを追加
        createZoomResetButton(displayImageTrendsCtx.parentElement, displayImageChart, displayImageResetBtnId);
    }

    // 表示タイミング - 日別推移（新しい統計量形式に対応）
    const diffSecTrendsCtx = document.getElementById("diffSecTrendsChart");
    if (diffSecTrendsCtx && window.trendsData?.diff_sec_boxplot) {
        const boxplotData = window.trendsData.diff_sec_boxplot.map((d) => ({
            x: d.date,
            y: d.stats, // タイミング差は60秒制限なし
        }));

        const diffSecResetBtnId = "diffSecTrendsChart-reset";
        const diffSecChart = new Chart(diffSecTrendsCtx, {
            type: "boxplot",
            data: {
                labels: boxplotData.map((d) => d.x),
                datasets: [
                    {
                        label: "タイミング差分布（秒）",
                        data: boxplotData.map((d) => d.y),
                        backgroundColor: "rgba(255, 159, 64, 0.6)",
                        borderColor: "rgb(255, 159, 64)",
                        borderWidth: 2,
                        outlierColor: "rgb(239, 68, 68)",
                        medianColor: "rgb(255, 193, 7)",
                    },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    zoom: getZoomPluginConfig(diffSecResetBtnId),
                },
                scales: {
                    x: {
                        display: true,
                        title: { display: true, text: "日付", font: { size: 12, weight: "bold" } },
                        ticks: { maxRotation: 45, minRotation: 45 },
                    },
                    y: {
                        display: true,
                        title: {
                            display: true,
                            text: "タイミング差（秒）",
                            font: { size: 12, weight: "bold" },
                        },
                    },
                },
            },
        });
        // リセットボタンを追加
        createZoomResetButton(diffSecTrendsCtx.parentElement, diffSecChart, diffSecResetBtnId);
    }
}

function generatePanelTrendsCharts() {
    const container = document.getElementById("panelTrendsContainer");
    console.log(
        "generatePanelTrendsCharts: container=",
        container,
        "panelTrendsData=",
        window.panelTrendsData
    );

    if (!container) {
        console.warn("generatePanelTrendsCharts: container not found");
        return;
    }

    if (!window.panelTrendsData || Object.keys(window.panelTrendsData).length === 0) {
        console.warn("generatePanelTrendsCharts: panelTrendsData is empty or undefined");
        container.innerHTML = `
            <div class="column is-full">
                <div class="notification is-warning is-light">
                    <span class="icon"><i class="fas fa-info-circle"></i></span>
                    パネル別処理時間データがありません。
                </div>
            </div>
        `;
        return;
    }

    // パネル名と統計量をリストに変換（パネル別処理時間用クランプ適用）
    const panelNames = Object.keys(window.panelTrendsData);
    const panelStats = panelNames.map((name) => clampPanelBoxplotStats(window.panelTrendsData[name]));
    console.log("generatePanelTrendsCharts: panelNames=", panelNames, "panelStats count=", panelStats.length);

    // 全パネルをまとめた単一のboxplotチャートを作成
    const columnDiv = document.createElement("div");
    columnDiv.className = "column is-full";
    columnDiv.innerHTML = `
        <div class="card metrics-card">
            <div class="card-header">
                <p class="card-header-title">パネル別処理時間分布</p>
            </div>
            <div class="card-content">
                <div class="chart-container" style="height: 400px;">
                    <canvas id="panelBoxplotChart"></canvas>
                </div>
            </div>
        </div>
    `;
    container.appendChild(columnDiv);

    // boxplotチャートを作成（統計量オブジェクトをそのまま使用）
    const canvas = document.getElementById("panelBoxplotChart");
    try {
        new Chart(canvas, {
            type: "boxplot",
            data: {
                labels: panelNames,
                datasets: [
                    {
                        label: "処理時間分布（秒）",
                        data: panelStats, // 統計量オブジェクト {min, q1, median, q3, max, outliers}
                        backgroundColor: panelNames.map((_, i) => getBoxplotColor(i)),
                        borderColor: panelNames.map((_, i) => getBorderColor(i)),
                        borderWidth: 2,
                        outlierColor: "rgb(239, 68, 68)",
                        medianColor: "rgb(255, 193, 7)",
                    },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                indexAxis: "y", // 横向きboxplot
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: "rgba(0, 0, 0, 0.8)",
                        titleColor: "white",
                        bodyColor: "white",
                        callbacks: {
                            title: function (context) {
                                return context[0].label + " パネル";
                            },
                            label: function (context) {
                                const stats = context.parsed;
                                const count = window.panelTrendsData[context.label]?.count || 0;
                                return [
                                    "最小値: " + stats.min.toFixed(2) + "秒",
                                    "第1四分位: " + stats.q1.toFixed(2) + "秒",
                                    "中央値: " + stats.median.toFixed(2) + "秒",
                                    "第3四分位: " + stats.q3.toFixed(2) + "秒",
                                    "最大値: " + stats.max.toFixed(2) + "秒",
                                    "データ数: " + count + "件",
                                ];
                            },
                        },
                    },
                },
                scales: {
                    x: getPanelElapsedTimeXAxisConfig(),
                    y: {
                        display: true,
                        title: { display: true, text: "パネル", font: { size: 14, weight: "bold" } },
                    },
                },
            },
        });
        console.log("generatePanelTrendsCharts: Chart created successfully");
    } catch (error) {
        console.error("generatePanelTrendsCharts: Chart creation failed:", error);
        container.innerHTML = `
            <div class="column is-full">
                <div class="notification is-danger is-light">
                    <span class="icon"><i class="fas fa-exclamation-triangle"></i></span>
                    パネル別グラフの生成に失敗しました: ${error.message}
                </div>
            </div>
        `;
    }
}

function generatePanelTimeSeriesChart() {
    // 統計量形式では時系列データがないため、棒グラフで中央値を比較表示
    const panelTimeSeriesCtx = document.getElementById("panelTimeSeriesChart");
    console.log("generatePanelTimeSeriesChart: ctx=", panelTimeSeriesCtx);

    if (!panelTimeSeriesCtx) {
        console.warn("generatePanelTimeSeriesChart: canvas not found");
        return;
    }
    if (!window.panelTrendsData || Object.keys(window.panelTrendsData).length === 0) {
        console.warn("generatePanelTimeSeriesChart: panelTrendsData is empty");
        return;
    }

    const panelNames = Object.keys(window.panelTrendsData);
    const medians = panelNames.map((name) => window.panelTrendsData[name]?.median || 0);
    const counts = panelNames.map((name) => window.panelTrendsData[name]?.count || 0);

    try {
        new Chart(panelTimeSeriesCtx, {
            type: "bar",
            data: {
                labels: panelNames,
                datasets: [
                    {
                        label: "中央値（秒）",
                        data: medians,
                        backgroundColor: panelNames.map((_, i) => getBoxplotColor(i)),
                        borderColor: panelNames.map((_, i) => getBorderColor(i)),
                        borderWidth: 2,
                    },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: "rgba(0, 0, 0, 0.8)",
                        titleColor: "white",
                        bodyColor: "white",
                        callbacks: {
                            title: function (context) {
                                return context[0].label + " パネル";
                            },
                            label: function (context) {
                                const stats = window.panelTrendsData[context.label];
                                return [
                                    "中央値: " + (stats?.median || 0).toFixed(2) + "秒",
                                    "データ数: " + (stats?.count || 0) + "件",
                                ];
                            },
                        },
                    },
                },
                scales: {
                    x: {
                        display: true,
                        title: { display: true, text: "パネル", font: { size: 14, weight: "bold" } },
                    },
                    y: {
                        display: true,
                        title: {
                            display: true,
                            text: "処理時間 中央値（秒）",
                            font: { size: 14, weight: "bold" },
                        },
                        beginAtZero: true,
                    },
                },
            },
        });
        console.log("generatePanelTimeSeriesChart: Chart created successfully");
    } catch (error) {
        console.error("generatePanelTimeSeriesChart: Chart creation failed:", error);
    }
}

function getBoxplotColor(index) {
    const colors = [
        "rgba(75, 192, 192, 0.6)",
        "rgba(54, 162, 235, 0.6)",
        "rgba(255, 99, 132, 0.6)",
        "rgba(255, 205, 86, 0.6)",
        "rgba(153, 102, 255, 0.6)",
        "rgba(255, 159, 64, 0.6)",
        "rgba(46, 204, 113, 0.6)",
        "rgba(52, 152, 219, 0.6)",
    ];
    return colors[index % colors.length];
}

function getBorderColor(index) {
    const colors = [
        "rgb(75, 192, 192)",
        "rgb(54, 162, 235)",
        "rgb(255, 99, 132)",
        "rgb(255, 205, 86)",
        "rgb(153, 102, 255)",
        "rgb(255, 159, 64)",
        "rgb(46, 204, 113)",
        "rgb(52, 152, 219)",
    ];
    return colors[index % colors.length];
}
