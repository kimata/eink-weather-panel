// Chart.js用の重いチャート生成関数（page_js.pyの内容を移動）

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
                    y: window.hourlyData.draw_panel_boxplot[hour],
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
                    y: {
                        display: true,
                        title: { display: true, text: "処理時間（秒）", font: { size: 14, weight: "bold" } },
                    },
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
                    y: window.hourlyData.display_image_boxplot[hour],
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
                    y: {
                        display: true,
                        title: { display: true, text: "処理時間（秒）", font: { size: 14, weight: "bold" } },
                    },
                },
            },
        });
    }
}

function generateTrendsCharts() {
    // 画像生成処理 - 日別推移
    const drawPanelTrendsCtx = document.getElementById("drawPanelTrendsChart");
    if (drawPanelTrendsCtx && window.trendsData?.draw_panel_boxplot) {
        const boxplotData = window.trendsData.draw_panel_boxplot.map((d) => ({
            x: d.date,
            y: d.elapsed_times,
        }));

        new Chart(drawPanelTrendsCtx, {
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
                plugins: { legend: { display: false } },
                scales: {
                    x: {
                        display: true,
                        title: { display: true, text: "日付", font: { size: 12, weight: "bold" } },
                        ticks: { maxRotation: 45, minRotation: 45 },
                    },
                    y: {
                        display: true,
                        title: { display: true, text: "時間（秒）", font: { size: 12, weight: "bold" } },
                    },
                },
            },
        });
    }

    // 表示実行処理 - 日別推移
    const displayImageTrendsCtx = document.getElementById("displayImageTrendsChart");
    if (displayImageTrendsCtx && window.trendsData?.display_image_boxplot) {
        const boxplotData = window.trendsData.display_image_boxplot.map((d) => ({
            x: d.date,
            y: d.elapsed_times,
        }));

        new Chart(displayImageTrendsCtx, {
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
                plugins: { legend: { display: false } },
                scales: {
                    x: {
                        display: true,
                        title: { display: true, text: "日付", font: { size: 12, weight: "bold" } },
                        ticks: { maxRotation: 45, minRotation: 45 },
                    },
                    y: {
                        display: true,
                        title: { display: true, text: "時間（秒）", font: { size: 12, weight: "bold" } },
                    },
                },
            },
        });
    }

    // 表示タイミング - 日別推移
    const diffSecTrendsCtx = document.getElementById("diffSecTrendsChart");
    if (diffSecTrendsCtx && window.trendsData?.diff_sec_boxplot) {
        const boxplotData = window.trendsData.diff_sec_boxplot.map((d) => ({
            x: d.date,
            y: d.diff_secs,
        }));

        new Chart(diffSecTrendsCtx, {
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
                plugins: { legend: { display: false } },
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
    }
}

function generatePanelTrendsCharts() {
    const container = document.getElementById("panelTrendsContainer");
    if (!container || !window.panelTrendsData) return;

    const binCount = 20;
    let index = 0;

    for (const panelName in window.panelTrendsData) {
        const data = window.panelTrendsData[panelName];

        // ヒストグラム生成の軽量化版
        const panelMin = Math.min(...data);
        const panelMax = Math.max(...data);
        const binWidth = (panelMax - panelMin) / binCount;

        const histogram = new Array(binCount).fill(0);
        const binLabels = [];

        for (let i = 0; i < binCount; i++) {
            const binStart = panelMin + i * binWidth;
            const binEnd = panelMin + (i + 1) * binWidth;
            binLabels.push(`${binStart.toFixed(1)}-${binEnd.toFixed(1)}`);
        }

        for (const value of data) {
            let binIndex = Math.floor((value - panelMin) / binWidth);
            if (binIndex >= binCount) binIndex = binCount - 1;
            if (binIndex >= 0) histogram[binIndex]++;
        }

        const totalCount = data.length;
        const histogramPercent = histogram.map((count) => (count / totalCount) * 100);

        // DOM要素の効率的な作成
        const columnDiv = document.createElement("div");
        columnDiv.className = "column is-half";
        columnDiv.innerHTML = `
            <div class="card metrics-card">
                <div class="card-header">
                    <p class="card-header-title">${panelName} パネル</p>
                </div>
                <div class="card-content">
                    <div class="chart-container" style="height: 350px;">
                        <canvas id="panelChart${index}"></canvas>
                    </div>
                </div>
            </div>
        `;

        container.appendChild(columnDiv);

        // チャート作成
        const canvas = document.getElementById(`panelChart${index}`);
        new Chart(canvas, {
            type: "bar",
            data: {
                labels: binLabels,
                datasets: [
                    {
                        label: "割合",
                        data: histogramPercent,
                        backgroundColor: getBoxplotColor(index),
                        borderColor: getBorderColor(index),
                        borderWidth: 1,
                    },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    x: {
                        title: { display: true, text: "処理時間（秒）", font: { size: 12, weight: "bold" } },
                        ticks: { maxRotation: 45, minRotation: 45 },
                    },
                    y: {
                        beginAtZero: true,
                        title: { display: true, text: "割合（%）", font: { size: 12, weight: "bold" } },
                    },
                },
            },
        });

        index++;
    }
}

function generatePanelTimeSeriesChart() {
    const panelTimeSeriesCtx = document.getElementById("panelTimeSeriesChart");
    if (!panelTimeSeriesCtx || !window.panelTrendsData) return;

    const datasets = [];
    const panelNames = Object.keys(window.panelTrendsData);

    panelNames.forEach((panelName, index) => {
        const data = window.panelTrendsData[panelName];
        if (!data || data.length === 0) return;

        const timeSeriesData = data.map((value, i) => ({ x: i, y: value }));

        datasets.push({
            label: panelName + " パネル",
            data: timeSeriesData,
            borderColor: getBorderColor(index),
            backgroundColor: getBoxplotColor(index),
            tension: 0.1,
            borderWidth: 2,
            pointRadius: 1,
            pointHoverRadius: 4,
            fill: false,
        });
    });

    new Chart(panelTimeSeriesCtx, {
        type: "line",
        data: { datasets: datasets },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: "top", labels: { usePointStyle: true, padding: 8, font: { size: 12 } } },
            },
            scales: {
                x: {
                    type: "linear",
                    display: true,
                    title: {
                        display: true,
                        text: "データポイント（時系列順）",
                        font: { size: 14, weight: "bold" },
                    },
                },
                y: {
                    type: "linear",
                    display: true,
                    title: { display: true, text: "処理時間（秒）", font: { size: 14, weight: "bold" } },
                },
            },
        },
    });
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
