// ── Predictions ───────────────────────────────────────────────────────────────
// Changes from old version:
// - fillCostFromPat field names updated to match normalized Patient columns:
//   p.Age → p.age, p.Patient_Gender → p.gender, p.Patient_Smoker → p.smoker
//   p.Patient_Children → p.children, p.Patient_Region → p.region
//   p.Patient_Height → p.height, p.Patient_Weight → p.weight
// - predictCostFromPatInfo: smoker value now comes directly as "Yes"/"No"
//   so we lowercase it before sending to match backend expectation

// ── Stress Predictor ──────────────────────────────────────────────────────────
async function doStress() {
    const body = {
        age: 25, // stress model doesn't use patient age directly
        sleep_duration: parseInt(document.getElementById('s-sleep').value) || 7,
        quality_of_sleep: parseInt(document.getElementById('s-qual').value) || 7,
        bmi_category: document.getElementById('s-bmi').value,
        physical_activity: parseInt(document.getElementById('s-act').value) || 30,
        heart_rate: parseFloat(document.getElementById('s-hr').value) || 72,
        daily_steps: parseInt(document.getElementById('s-steps').value) || 8000,
        systolic: parseInt(document.getElementById('s-sys').value) || 120,
        diastolic: parseInt(document.getElementById('s-dia').value) || 80,
    };

    const r = await fetch('/api/predict/stress', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
    });
    const d = await r.json();

    document.getElementById('stress-val').textContent = d.stress_level;
    document.getElementById('stress-box').classList.add('show');
}


// ── Cost Predictor ────────────────────────────────────────────────────────────
async function doCost() {
    const pid = document.getElementById('c-patsel').value || undefined;

    const body = {
        age: parseInt(document.getElementById('c-age').value) || 35,
        sex: document.getElementById('c-sex').value,
        bmi: parseFloat(document.getElementById('c-bmi').value) || 25,
        children: parseInt(document.getElementById('c-children').value) || 0,
        smoker: document.getElementById('c-smoker').value,
        region: document.getElementById('c-region').value,
    };

    let url = '/api/predict/cost';
    if (pid) url += `?patient_id=${pid}`;

    const r = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
    });
    const d = await r.json();

    document.getElementById('cost-val').textContent = `$${d.predicted_cost.toLocaleString()}`;
    document.getElementById('cost-box').classList.add('show');
}


// ── Cost prediction from Patient Info panel ───────────────────────────────────
async function predictCostFromPatInfo() {
    const pid = document.getElementById('pi-sel').value;

    const body = {
        age: parseInt(document.getElementById('pi-age').value) || 35,
        sex: (radio.gender || 'male').toLowerCase(),
        bmi: computeBMI(),
        children: parseInt(document.getElementById('pi-children').value) || 0,
        smoker: (radio.smoker || 'no').toLowerCase(), // "Yes"/"No" → "yes"/"no"
        region: document.getElementById('pi-region').value,
    };

    let url = '/api/predict/cost';
    if (pid) url += `?patient_id=${pid}`;

    const r = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
    });
    const d = await r.json();

    document.getElementById('pi-pred-val').textContent = `$${d.predicted_cost.toLocaleString()}`;
    document.getElementById('pi-pred-box').classList.add('show');
}


// ── Auto-fill cost form from selected patient ─────────────────────────────────
async function fillCostFromPat() {
    const pid = document.getElementById('c-patsel').value;
    if (!pid) return;

    const r = await fetch(`/api/patient/${pid}`);
    const p = await r.json();

    // All field names now use normalized lowercase names
    document.getElementById('c-age').value = p.age || '';
    document.getElementById('c-sex').value = (p.gender || 'male').toLowerCase();
    document.getElementById('c-children').value = p.children || 0;
    document.getElementById('c-smoker').value = (p.smoker || 'no').toLowerCase();
    document.getElementById('c-region').value = (p.region || 'northeast').toLowerCase();

    if (p.height && p.weight) {
        const h = p.height / 100;
        document.getElementById('c-bmi').value = (p.weight / (h * h)).toFixed(1);
    }
}


// ── BMI calculator ────────────────────────────────────────────────────────────
function computeBMI() {
    const h = parseFloat(document.getElementById('pi-height').value) || 170;
    const w = parseFloat(document.getElementById('pi-weight').value) || 70;
    return parseFloat((w / ((h / 100) ** 2)).toFixed(1));
}