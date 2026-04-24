// ── Donut Chart ───────────────────────────────────────────────────────────────
let donutChart = null;

async function loadDonut() {
    const r = await fetch(`/api/tasks/donut/${CF.id}`);
    const d = await r.json();

    const done = d.done;
    const upcoming = d.upcoming;
    const total = d.total;
    const pct = total > 0 ? Math.round((done / total) * 100) : 0;

    document.getElementById('donutPct').textContent = `${pct}%`;

    if (donutChart) donutChart.destroy();
    donutChart = new Chart(document.getElementById('donutChart'), {
        type: 'doughnut',
        data: {
            labels: ['Done', 'Upcoming'],
            datasets: [{
                data: total > 0 ? [done, upcoming] : [0, 1],
                backgroundColor: ['#231942', '#a8f0e0'],
                borderWidth: 0,
                hoverOffset: 4
            }]
        },
        options: {
            cutout: '72%',
            responsive: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: ctx => ` ${ctx.label}: ${ctx.raw} task${ctx.raw !== 1 ? 's' : ''}`
                    }
                }
            }
        }
    });
}