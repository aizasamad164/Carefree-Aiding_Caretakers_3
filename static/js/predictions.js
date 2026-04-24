// ── Predictions ───────────────────────────────────────────────────────────────
// Changes from old version:
// - fillCostFromPat field names updated to match normalized Patient columns:
//   p.Age → p.age, p.Patient_Gender → p.gender, p.Patient_Smoker → p.smoker
//   p.Patient_Children → p.children, p.Patient_Region → p.region
//   p.Patient_Height → p.height, p.Patient_Weight → p.weight
// - predictCostFromPatInfo: smoker value now comes directly as "Yes"/"No"
//   so we lowercase it before sending to match backend expectation

// ── Predictions ───────────────────────────────────────────────────────────────

function handleCostModeChange() {
    const pid = document.getElementById('c-patsel').value;

    if (!pid) {
        resetCostForm();   // manual entry
        return;
    }

    fillCostFromPat();     // patient selected
}

function resetCostForm() {
    document.getElementById('c-age').value = '';
    document.getElementById('c-bmi').value = '';
    document.getElementById('c-children').value = '';
    document.getElementById('c-sex').value = 'male';
    document.getElementById('c-smoker').value = 'no';
    document.getElementById('c-region').value = 'northeast';

    document.getElementById('cost-val').textContent = '';
    document.getElementById('cost-box').classList.remove('show');
}

function validateInt(value) {
    const n = Number(value);
    return Number.isInteger(n) && n > 0;
}

function validatePositiveFloat(value) {
    const n = Number(value);
    return !isNaN(n) && n > 0;
}

function validateRange(value, min, max) {
    const n = Number(value);
    return !isNaN(n) && n >= min && n <= max;
}

// ── Stress Predictor ──────────────────────────────────────────────────────────
async function doStress() {
    try {
        const sleep = document.getElementById('s-sleep').value;
        const quality = document.getElementById('s-qual').value;
        const activity = document.getElementById('s-act').value;
        const heart = document.getElementById('s-hr').value;
        const steps = document.getElementById('s-steps').value;
        const systolic = document.getElementById('s-sys').value;
        const diastolic = document.getElementById('s-dia').value;

        if (!validateInt(sleep) || !validateRange(sleep, 1, 24))
            throw new Error('Sleep must be 1–24');

        if (!validateInt(quality) || !validateRange(quality, 1, 10))
            throw new Error('Sleep quality must be 1–10');

        if (!validateInt(activity) || !validateRange(activity, 1, 100))
            throw new Error('Activity must be 1–100');

        if (!validateInt(heart) || !validateRange(heart, 30, 250))
            throw new Error('Heart rate must be 30–250');

        if (!validateInt(steps) || steps < 0)
            throw new Error('Steps must be positive');

        if (!validateInt(systolic) || !validateRange(systolic, 70, 250))
            throw new Error('Systolic must be a whole number (70–250)');

        if (!validateInt(diastolic) || !validateRange(diastolic, 40, 150))
            throw new Error('Diastolic must be a whole number (40–150)');

        const body = {
            age: 25,
            sleep_duration: parseInt(sleep),
            quality_of_sleep: parseInt(quality),
            bmi_category: document.getElementById('s-bmi').value,
            physical_activity: parseInt(activity),
            heart_rate: parseInt(heart),
            daily_steps: parseInt(steps),
            systolic: parseInt(systolic),
            diastolic: parseInt(diastolic),
        };

        const r = await fetch('/api/predict/stress', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        });

        let d;
        try {
            d = await r.json();
        } catch {
            throw new Error('Server returned invalid response');
        }

        if (!r.ok) throw new Error(d.detail || 'Stress prediction failed');

        document.getElementById('stress-val').textContent = d.stress_level;
        document.getElementById('stress-box').classList.add('show');

    } catch (err) {
        toast(err.message, 'err');
        console.error(err);
    }
}


// ── Cost Predictor ────────────────────────────────────────────────────────────
async function doCost() {

    try {
        const age = document.getElementById('c-age').value;
        const bmi = document.getElementById('c-bmi').value;
        const children = document.getElementById('c-children').value;

        if (!validateInt(age) || !validateRange(age, 1, 120))
            throw new Error('Age must be 1–120');

        if (!validatePositiveFloat(bmi))
            throw new Error('BMI must be positive');

        if (!validateInt(children) || children < 0)
            throw new Error('Children must be 0+');

        const body = {
            age: parseInt(age),
            sex: document.getElementById('c-sex').value,
            bmi: parseFloat(bmi).toFixed(1),
            children: parseInt(children),
            smoker: document.getElementById('c-smoker').value,
            region: document.getElementById('c-region').value,
        };

        const pid = document.getElementById('c-patsel').value;
        let url = '/api/predict/cost';
        if (pid) url += `?patient_id=${pid}`;

        const r = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        });

        let d;
        try {
            d = await r.json();
        } catch {
            throw new Error('Invalid server response');
        }

        if (!r.ok) throw new Error(d.detail || 'Cost prediction failed');

        document.getElementById('cost-val').textContent =
            `$${d.predicted_cost.toLocaleString()}`;

        document.getElementById('cost-box').classList.add('show');

    } catch (err) {
        toast(err.message, 'err');
        console.error(err);
    }
}

// ── Cost prediction from Patient Info panel ───────────────────────────────────
async function predictCostFromPatInfo() {
    const pid = document.getElementById('pi-sel').value;

    // 1. Get inputs from the DOM
    const age = parseInt(document.getElementById('pi-age').value);
    const children = parseInt(document.getElementById('pi-children').value) || 0;
    const region = document.getElementById('pi-region').value;
    const bmi = computeBMI();

    // 2. Validation before sending
    if (isNaN(age) || !validateRange(age, 1, 120)) {
        toast('Patient age must be between 1 and 120', 'err');
        return;
    }

    // 3. Robust way to get Radio/Selection values 
    // (Assuming you might not have a global 'radio' object)
    const genderInp = document.querySelector('input[name="gender"]:checked')?.value || 'male';
    const smokerInp = document.querySelector('input[name="smoker"]:checked')?.value || 'no';

    const body = {
        age: age,
        sex: genderInp.toLowerCase(),
        bmi: bmi,
        children: children,
        smoker: smokerInp.toLowerCase(),
        region: region,
    };

    let url = '/api/predict/cost';
    if (pid) url += `?patient_id=${pid}`;

    try {
        const r = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        });

        // Parse the JSON once, here.
        const d = await r.json();

        if (!r.ok) {
            // Now 'd' exists, so this will NOT crash
            toast(d.detail || 'Prediction failed', 'err');
            return;
        }

        // 4. Update UI on success
        document.getElementById('pi-pred-val').textContent = `$${d.predicted_cost.toLocaleString()}`;
        document.getElementById('pi-pred-box').classList.add('show');

    } catch (err) {
        // This catches network timeouts or server crashes
        console.error("Fetch Error:", err);
        toast('Connection lost or server error', 'err');
    }
}


// ── Auto-fill cost form from selected patient ─────────────────────────────────
async function fillCostFromPat() {
    const pid = document.getElementById('c-patsel').value;
    if (!pid) return;

    const r = await fetch(`/api/patient/${pid}`);
    const p = await r.json();

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
  