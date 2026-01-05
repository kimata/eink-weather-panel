// メトリクス表示用JavaScript（Chart.js）

function generateHourlyCharts() {
    // 画像生成パネル 時間別パフォーマンス
    const drawPanelCtx = document.getElementById("drawPanelHourlyChart");
    if (drawPanelCtx && window.hourlyData?.draw_panel) {
        new Chart(drawPanelCtx, {
            type: "line",
            data: {
                labels: window.hourlyData.draw_panel.map((d) => d.hour + "時"),
                datasets: [
                    {
                        label: "平均処理時間（秒）",
                        data: window.hourlyData.draw_panel.map((d) => d.avg_elapsed_time),
                        borderColor: "rgb(75, 192, 192)",
                        backgroundColor: "rgba(75, 192, 192, 0.2)",
                        tension: 0.1,
                        yAxisID: "y",
                        borderWidth: 3,
                        pointRadius: 4,
                        pointHoverRadius: 6,
                    },
                    {
                        label: "最小処理時間（秒）",
                        data: window.hourlyData.draw_panel.map((d) => d.min_elapsed_time),
                        borderColor: "rgb(34, 197, 94)",
                        backgroundColor: "rgba(34, 197, 94, 0.1)",
                        tension: 0.1,
                        yAxisID: "y",
                        borderDash: [8, 4],
                        borderWidth: 2,
                        pointRadius: 3,
                        pointHoverRadius: 5,
                    },
                    {
                        label: "最大処理時間（秒）",
                        data: window.hourlyData.draw_panel.map((d) => d.max_elapsed_time),
                        borderColor: "rgb(239, 68, 68)",
                        backgroundColor: "rgba(239, 68, 68, 0.1)",
                        tension: 0.1,
                        yAxisID: "y",
                        borderDash: [4, 4],
                        borderWidth: 2,
                        pointRadius: 3,
                        pointHoverRadius: 5,
                    },
                    {
                        label: "エラー率（%）",
                        data: window.hourlyData.draw_panel.map((d) => d.error_rate || 0),
                        borderColor: "rgb(255, 99, 132)",
                        backgroundColor: "rgba(255, 99, 132, 0.2)",
                        tension: 0.1,
                        yAxisID: "y1",
                    },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    mode: "index",
                    intersect: false,
                },
                plugins: {
                    legend: {
                        position: "top",
                        labels: {
                            usePointStyle: true,
                            padding: 8,
                            font: { size: 12 },
                        },
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
                                    if (context.dataset.yAxisID === "y1") {
                                        label += context.parsed.y.toFixed(1) + "%";
                                    } else {
                                        label += context.parsed.y.toFixed(2) + "秒";
                                    }
                                }
                                return label;
                            },
                            afterBody: function (context) {
                                if (context.length > 0) {
                                    const dataIndex = context[0].dataIndex;
                                    const hourData = window.hourlyData.draw_panel[dataIndex];
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
                        title: { display: true, text: "処理時間（秒）", font: { size: 14, weight: "bold" } },
                        grid: { color: "rgba(75, 192, 192, 0.2)" },
                    },
                    y1: {
                        type: "linear",
                        display: true,
                        position: "right",
                        title: { display: true, text: "エラー率（%）", font: { size: 14, weight: "bold" } },
                        grid: { drawOnChartArea: false, color: "rgba(255, 99, 132, 0.2)" },
                    },
                },
            },
        });
    }

    // 表示実行 時間別パフォーマンス
    const displayImageCtx = document.getElementById("displayImageHourlyChart");
    if (displayImageCtx && window.hourlyData?.display_image) {
        new Chart(displayImageCtx, {
            type: "line",
            data: {
                labels: window.hourlyData.display_image.map((d) => d.hour + "時"),
                datasets: [
                    {
                        label: "平均処理時間（秒）",
                        data: window.hourlyData.display_image.map((d) => d.avg_elapsed_time),
                        borderColor: "rgb(54, 162, 235)",
                        backgroundColor: "rgba(54, 162, 235, 0.2)",
                        tension: 0.1,
                        yAxisID: "y",
                        borderWidth: 3,
                        pointRadius: 4,
                        pointHoverRadius: 6,
                    },
                    {
                        label: "最小処理時間（秒）",
                        data: window.hourlyData.display_image.map((d) => d.min_elapsed_time),
                        borderColor: "rgb(34, 197, 94)",
                        backgroundColor: "rgba(34, 197, 94, 0.1)",
                        tension: 0.1,
                        yAxisID: "y",
                        borderDash: [8, 4],
                        borderWidth: 2,
                        pointRadius: 3,
                        pointHoverRadius: 5,
                    },
                    {
                        label: "最大処理時間（秒）",
                        data: window.hourlyData.display_image.map((d) => d.max_elapsed_time),
                        borderColor: "rgb(239, 68, 68)",
                        backgroundColor: "rgba(239, 68, 68, 0.1)",
                        tension: 0.1,
                        yAxisID: "y",
                        borderDash: [4, 4],
                        borderWidth: 2,
                        pointRadius: 3,
                        pointHoverRadius: 5,
                    },
                    {
                        label: "エラー率（%）",
                        data: window.hourlyData.display_image.map((d) => d.error_rate || 0),
                        borderColor: "rgb(255, 99, 132)",
                        backgroundColor: "rgba(255, 99, 132, 0.2)",
                        tension: 0.1,
                        yAxisID: "y1",
                    },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
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
                                    if (context.dataset.yAxisID === "y1") {
                                        label += context.parsed.y.toFixed(1) + "%";
                                    } else {
                                        label += context.parsed.y.toFixed(2) + "秒";
                                    }
                                }
                                return label;
                            },
                            afterBody: function (context) {
                                if (context.length > 0) {
                                    const dataIndex = context[0].dataIndex;
                                    const hourData = window.hourlyData.display_image[dataIndex];
                                    if (hourData) return "実行回数: " + (hourData.count || 0) + "回";
                                }
                                return "";
                            },
                        },
                    },
                },
                scales: {
                    y: {
                        type: "linear",
                        display: true,
                        position: "left",
                        max: 30,
                        title: { display: true, text: "処理時間（秒）" },
                        ticks: {
                            callback: function (value) {
                                if (value === 30) return "30以上";
                                return value;
                            },
                        },
                    },
                    y1: {
                        type: "linear",
                        display: true,
                        position: "right",
                        title: { display: true, text: "エラー率（%）" },
                        grid: { drawOnChartArea: false },
                    },
                },
            },
        });
    }
}

// パーマリンク機能
function copyPermalink(elementId) {
    const currentUrl = window.location.origin + window.location.pathname;
    const permalink = currentUrl + "#" + elementId;

    navigator.clipboard
        .writeText(permalink)
        .then(function () {
            showCopyNotification("パーマリンクをコピーしました");
            history.pushState(null, null, "#" + elementId);
        })
        .catch(function (err) {
            const textArea = document.createElement("textarea");
            textArea.value = permalink;
            document.body.appendChild(textArea);
            textArea.select();
            document.execCommand("copy");
            document.body.removeChild(textArea);
            showCopyNotification("パーマリンクをコピーしました");
            history.pushState(null, null, "#" + elementId);
        });
}

function showCopyNotification(message) {
    const existingNotification = document.querySelector(".copy-notification");
    if (existingNotification) existingNotification.remove();

    const notification = document.createElement("div");
    notification.className = "copy-notification";
    notification.textContent = message;
    document.body.appendChild(notification);

    setTimeout(() => notification.classList.add("show"), 10);
    setTimeout(() => {
        notification.classList.remove("show");
        setTimeout(() => notification.parentNode?.removeChild(notification), 300);
    }, 3000);
}

// 初期化
document.addEventListener("DOMContentLoaded", function () {
    if (window.location.hash) {
        const element = document.querySelector(window.location.hash);
        if (element) {
            setTimeout(() => {
                element.scrollIntoView({ behavior: "smooth", block: "start" });
            }, 500);
        }
    }
});
