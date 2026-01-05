// Chart.js用の重いチャート生成関数（page_js.pyの内容を移動）

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

// 箱ひげ図の統計量をクランプする（元の値も保持）
function clampBoxplotStats(stats) {
    if (!stats) return stats;
    return {
        min: clampValue(stats.min),
        q1: clampValue(stats.q1),
        median: clampValue(stats.median),
        q3: clampValue(stats.q3),
        max: clampValue(stats.max),
        outliers: (stats.outliers || []).map(clampValue),
        // 元の値を保持（ツールチップ用）
        _originalMin: stats.min,
        _originalQ1: stats.q1,
        _originalMedian: stats.median,
        _originalQ3: stats.q3,
        _originalMax: stats.max,
        _originalOutliers: stats.outliers || [],
    };
}

// 箱ひげ図の統計量に元の値を追加（クランプなし、ツールチップ用）
function addOriginalStats(stats) {
    if (!stats) return stats;
    return {
        ...stats,
        // 元の値を保持（ツールチップ用）
        _originalMin: stats.min,
        _originalQ1: stats.q1,
        _originalMedian: stats.median,
        _originalQ3: stats.q3,
        _originalMax: stats.max,
        _originalOutliers: stats.outliers || [],
    };
}

// パネル別処理時間用に箱ひげ図の統計量をクランプする（元の値も保持）
function clampPanelBoxplotStats(stats) {
    if (!stats) return stats;
    return {
        min: clampPanelValue(stats.min),
        q1: clampPanelValue(stats.q1),
        median: clampPanelValue(stats.median),
        q3: clampPanelValue(stats.q3),
        max: clampPanelValue(stats.max),
        outliers: (stats.outliers || []).map(clampPanelValue),
        count: stats.count,
        // 元の値を保持（ツールチップ用）
        _originalMin: stats.min,
        _originalQ1: stats.q1,
        _originalMedian: stats.median,
        _originalQ3: stats.q3,
        _originalMax: stats.max,
        _originalOutliers: stats.outliers || [],
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
    btn.className = "button is-small is-light zoom-reset-btn";
    btn.innerHTML = '<span class="icon is-small"><i class="fas fa-undo"></i></span><span>リセット</span>';
    btn.style.cssText = "display:none; position:absolute; top:25px; right:10px; z-index:10;";
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
        // 元のデータ配列を保持（クロージャでアクセス可能）
        const diffSecData = window.hourlyData.diff_sec;
        const chartLabels = diffSecData.map((d) => d.hour + "時");

        new Chart(diffSecCtx, {
            type: "line",
            data: {
                labels: chartLabels,
                datasets: [
                    {
                        label: "平均タイミング差（秒）",
                        data: diffSecData.map((d) => Math.min(d.avg_diff_sec, MAX_ELAPSED_TIME)),
                        borderColor: "rgb(255, 159, 64)",
                        backgroundColor: "rgba(255, 159, 64, 0.2)",
                        tension: 0.1,
                        borderWidth: 3,
                        pointRadius: 4,
                        pointHoverRadius: 6,
                    },
                    {
                        label: "最小タイミング差（秒）",
                        data: diffSecData.map((d) => Math.min(d.min_diff_sec, MAX_ELAPSED_TIME)),
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
                        data: diffSecData.map((d) => Math.min(d.max_diff_sec, MAX_ELAPSED_TIME)),
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
                                const idx = context[0].dataIndex;
                                return "時刻: " + chartLabels[idx];
                            },
                            label: function (context) {
                                const datasetLabel = context.dataset.label || "";
                                let prefix = datasetLabel ? datasetLabel + ": " : "";
                                // dataIndexから直接元のデータを取得
                                const hourData = diffSecData[context.dataIndex];
                                if (!hourData) {
                                    return prefix + context.parsed.y.toFixed(1) + "秒";
                                }
                                // 元の値を表示
                                let originalValue = 0;
                                if (datasetLabel.includes("平均")) {
                                    originalValue = hourData.avg_diff_sec;
                                } else if (datasetLabel.includes("最小")) {
                                    originalValue = hourData.min_diff_sec;
                                } else if (datasetLabel.includes("最大")) {
                                    originalValue = hourData.max_diff_sec;
                                }
                                return prefix + originalValue.toFixed(1) + "秒";
                            },
                            afterBody: function (context) {
                                if (context.length > 0) {
                                    const hourData = diffSecData[context[0].dataIndex];
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
                        max: MAX_ELAPSED_TIME,
                        title: {
                            display: true,
                            text: "タイミング差（秒）",
                            font: { size: 14, weight: "bold" },
                        },
                        grid: { color: "rgba(255, 159, 64, 0.2)" },
                        ticks: {
                            callback: function (value) {
                                if (value === MAX_ELAPSED_TIME) return MAX_ELAPSED_TIME + "以上";
                                return value;
                            },
                        },
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
                const original = window.hourlyData.diff_sec_boxplot[hour];
                const label = hour + "時";
                boxplotData.push({
                    x: label,
                    y: clampBoxplotStats(original), // 元の値は _original* プロパティに保持
                });
            }
        }
        const chartLabels = boxplotData.map((d) => d.x);

        new Chart(diffSecBoxplotCtx, {
            type: "boxplot",
            data: {
                labels: chartLabels,
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
                                const idx = context[0].dataIndex;
                                return "時刻: " + chartLabels[idx];
                            },
                            label: function (context) {
                                // context.raw から元の値（_original* プロパティ）を取得
                                const raw = context.raw;
                                if (!raw) return [];
                                return [
                                    "最小値: " + raw._originalMin.toFixed(1) + "秒",
                                    "第1四分位: " + raw._originalQ1.toFixed(1) + "秒",
                                    "中央値: " + raw._originalMedian.toFixed(1) + "秒",
                                    "第3四分位: " + raw._originalQ3.toFixed(1) + "秒",
                                    "最大値: " + raw._originalMax.toFixed(1) + "秒",
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
                    y: getElapsedTimeYAxisConfig("タイミング差（秒）"),
                },
            },
        });
    }
}

function generateBoxplotCharts() {
    // 共通のツールチップコールバック生成関数（context.raw の _original* プロパティを使用）
    function createBoxplotTooltipConfig(labels) {
        return {
            backgroundColor: "rgba(0, 0, 0, 0.8)",
            titleColor: "white",
            bodyColor: "white",
            callbacks: {
                title: function (context) {
                    const idx = context[0].dataIndex;
                    return "時刻: " + labels[idx];
                },
                label: function (context) {
                    // context.raw から元の値（_original* プロパティ）を取得
                    const raw = context.raw;
                    if (!raw) return [];
                    return [
                        "最小値: " + raw._originalMin.toFixed(2) + "秒",
                        "第1四分位: " + raw._originalQ1.toFixed(2) + "秒",
                        "中央値: " + raw._originalMedian.toFixed(2) + "秒",
                        "第3四分位: " + raw._originalQ3.toFixed(2) + "秒",
                        "最大値: " + raw._originalMax.toFixed(2) + "秒",
                    ];
                },
            },
        };
    }

    // 画像生成処理 箱ひげ図
    const drawPanelBoxplotCtx = document.getElementById("drawPanelBoxplotChart");
    if (drawPanelBoxplotCtx && window.hourlyData?.draw_panel_boxplot) {
        const boxplotData = [];
        for (let hour = 0; hour < 24; hour++) {
            if (window.hourlyData.draw_panel_boxplot[hour]) {
                const original = window.hourlyData.draw_panel_boxplot[hour];
                const label = hour + "時";
                boxplotData.push({
                    x: label,
                    y: clampBoxplotStats(original), // 元の値は _original* プロパティに保持
                });
            }
        }
        const labels = boxplotData.map((d) => d.x);

        new Chart(drawPanelBoxplotCtx, {
            type: "boxplot",
            data: {
                labels: labels,
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
                    tooltip: createBoxplotTooltipConfig(labels),
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
                const original = window.hourlyData.display_image_boxplot[hour];
                const label = hour + "時";
                boxplotData.push({
                    x: label,
                    y: clampBoxplotStats(original), // 元の値は _original* プロパティに保持
                });
            }
        }
        const labels = boxplotData.map((d) => d.x);

        new Chart(displayImageBoxplotCtx, {
            type: "boxplot",
            data: {
                labels: labels,
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
                    tooltip: createBoxplotTooltipConfig(labels),
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
    // 箱ひげ図用の日本語ツールチップコールバックを生成（context.raw の _original* プロパティを使用）
    function createBoxplotTooltipCallback(unit = "秒") {
        return {
            backgroundColor: "rgba(0, 0, 0, 0.8)",
            titleColor: "white",
            bodyColor: "white",
            callbacks: {
                title: function (context) {
                    return "日付: " + context[0].label;
                },
                label: function (context) {
                    // context.raw から元の値（_original* プロパティ）を取得
                    const raw = context.raw;
                    if (!raw) return [];
                    return [
                        "最小値: " + raw._originalMin.toFixed(2) + unit,
                        "第1四分位: " + raw._originalQ1.toFixed(2) + unit,
                        "中央値: " + raw._originalMedian.toFixed(2) + unit,
                        "第3四分位: " + raw._originalQ3.toFixed(2) + unit,
                        "最大値: " + raw._originalMax.toFixed(2) + unit,
                    ];
                },
            },
        };
    }

    // 画像生成処理 - 日別推移（新しい統計量形式に対応）
    const drawPanelTrendsCtx = document.getElementById("drawPanelTrendsChart");
    if (drawPanelTrendsCtx && window.trendsData?.draw_panel_boxplot) {
        const boxplotData = window.trendsData.draw_panel_boxplot.map((d) => ({
            x: d.date,
            y: clampBoxplotStats(d.stats), // 元の値は _original* プロパティに保持
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
                    tooltip: createBoxplotTooltipCallback(),
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
            y: clampBoxplotStats(d.stats), // 元の値は _original* プロパティに保持
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
                    tooltip: createBoxplotTooltipCallback(),
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
            y: addOriginalStats(d.stats), // タイミング差は30秒制限なし、_original* プロパティを追加
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
                    tooltip: createBoxplotTooltipCallback(),
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

    // パネル名と統計量をリストに変換（元の値は _original* プロパティに保持）
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
                        data: panelStats, // 統計量オブジェクト（_original* プロパティ含む）
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
                                // context.raw から元の値（_original* プロパティ）を取得
                                const raw = context.raw;
                                if (!raw) return [];
                                const count = raw.count || 0;
                                return [
                                    "最小値: " + raw._originalMin.toFixed(2) + "秒",
                                    "第1四分位: " + raw._originalQ1.toFixed(2) + "秒",
                                    "中央値: " + raw._originalMedian.toFixed(2) + "秒",
                                    "第3四分位: " + raw._originalQ3.toFixed(2) + "秒",
                                    "最大値: " + raw._originalMax.toFixed(2) + "秒",
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

// パネル別日別推移グラフを生成
function generatePanelDailyTrendsCharts() {
    const container = document.getElementById("panelDailyTrendsContainer");
    console.log(
        "generatePanelDailyTrendsCharts: container=",
        container,
        "data=",
        window.panelDailyTrendsData
    );

    if (!container) {
        console.warn("generatePanelDailyTrendsCharts: container not found");
        return;
    }

    if (!window.panelDailyTrendsData || Object.keys(window.panelDailyTrendsData).length === 0) {
        console.warn("generatePanelDailyTrendsCharts: panelDailyTrendsData is empty or undefined");
        container.innerHTML = `
            <div class="column is-full">
                <div class="notification is-warning is-light">
                    <span class="icon"><i class="fas fa-info-circle"></i></span>
                    パネル別日別推移データがありません。
                </div>
            </div>
        `;
        return;
    }

    // コンテナをクリア
    container.innerHTML = "";

    const panelNames = Object.keys(window.panelDailyTrendsData);
    console.log("generatePanelDailyTrendsCharts: panelNames=", panelNames);

    // 各パネルのグラフを生成
    panelNames.forEach((panelName, index) => {
        const panelData = window.panelDailyTrendsData[panelName];
        if (!panelData || panelData.length === 0) return;

        // カラム作成（2列レイアウト）
        const columnDiv = document.createElement("div");
        columnDiv.className = "column is-6";
        columnDiv.innerHTML = `
            <div class="card metrics-card" id="panel-daily-${index}">
                <i class="fas fa-link card-permalink" onclick="copyPermalink('panel-daily-${index}')"></i>
                <div class="card-header">
                    <p class="card-header-title">${panelName} - 日別推移</p>
                </div>
                <div class="card-content">
                    <div class="chart-container" style="height: 300px; position: relative;">
                        <canvas id="panelDailyChart-${index}"></canvas>
                    </div>
                </div>
            </div>
        `;
        container.appendChild(columnDiv);

        // boxplotデータを準備（クランプ付き）
        const boxplotData = panelData.map((d) => ({
            x: d.date,
            y: clampPanelBoxplotStats(d.stats),
        }));

        // グラフ作成
        const canvas = document.getElementById(`panelDailyChart-${index}`);
        const resetBtnId = `panelDailyChart-${index}-reset`;

        try {
            const chart = new Chart(canvas, {
                type: "boxplot",
                data: {
                    labels: boxplotData.map((d) => d.x),
                    datasets: [
                        {
                            label: "処理時間分布（秒）",
                            data: boxplotData.map((d) => d.y),
                            backgroundColor: getBoxplotColor(index),
                            borderColor: getBorderColor(index),
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
                        zoom: getZoomPluginConfig(resetBtnId),
                        tooltip: {
                            backgroundColor: "rgba(0, 0, 0, 0.8)",
                            titleColor: "white",
                            bodyColor: "white",
                            callbacks: {
                                title: function (context) {
                                    return panelName + " - " + context[0].label;
                                },
                                label: function (context) {
                                    // context.raw から元の値（_original* プロパティ）を取得
                                    const raw = context.raw;
                                    if (!raw) return [];
                                    return [
                                        "最小値: " + raw._originalMin.toFixed(2) + "秒",
                                        "第1四分位: " + raw._originalQ1.toFixed(2) + "秒",
                                        "中央値: " + raw._originalMedian.toFixed(2) + "秒",
                                        "第3四分位: " + raw._originalQ3.toFixed(2) + "秒",
                                        "最大値: " + raw._originalMax.toFixed(2) + "秒",
                                    ];
                                },
                            },
                        },
                    },
                    scales: {
                        x: {
                            display: true,
                            title: { display: true, text: "日付", font: { size: 12, weight: "bold" } },
                            ticks: { maxRotation: 45, minRotation: 45 },
                        },
                        y: getPanelElapsedTimeYAxisConfig(),
                    },
                },
            });

            // リセットボタンを追加
            createZoomResetButton(canvas.parentElement, chart, resetBtnId);
            console.log(`generatePanelDailyTrendsCharts: ${panelName} chart created successfully`);
        } catch (error) {
            console.error(`generatePanelDailyTrendsCharts: ${panelName} chart creation failed:`, error);
        }
    });
}

// パネル別処理時間用Y軸設定を取得
function getPanelElapsedTimeYAxisConfig(titleText = "処理時間（秒）") {
    return {
        display: true,
        max: MAX_PANEL_ELAPSED_TIME,
        title: { display: true, text: titleText, font: { size: 12, weight: "bold" } },
        ticks: {
            callback: function (value) {
                if (value === MAX_PANEL_ELAPSED_TIME) return MAX_PANEL_ELAPSED_TIME + "以上";
                return value;
            },
        },
    };
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

// ============================================
// プラグイン登録確認（デバッグ用）
// ============================================
(function () {
    console.log("chart-functions.js: Checking Chart.js plugins...");
    console.log("  - Chart.js:", typeof Chart !== "undefined" ? "loaded" : "NOT LOADED");

    if (typeof Chart !== "undefined" && Chart.registry?.plugins) {
        // Chart.registry.plugins.items は Map オブジェクト
        const pluginIds = [];
        Chart.registry.plugins.items.forEach((plugin, id) => {
            pluginIds.push(id);
        });
        console.log("  - Registered plugins:", pluginIds.join(", "));

        // zoom プラグインが登録されているか確認
        const zoomRegistered = pluginIds.includes("zoom");
        console.log("  - Zoom plugin registered:", zoomRegistered);
        if (!zoomRegistered) {
            console.warn("  - WARNING: Drag zoom will not work without zoom plugin!");
        }
    }
})();
