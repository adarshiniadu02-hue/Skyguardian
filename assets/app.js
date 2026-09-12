const ui = new WebUI();

let aircraft = {};
let selectedIcao = null;

ui.on_connect(() => console.log("SKYGUARDIAN UI CONNECTED"));
ui.on_disconnect(() => console.log("SKYGUARDIAN UI DISCONNECTED"));

ui.on_message("aircraft_update", (message) => {
    if (!message || !Array.isArray(message.aircraft)) return;

    aircraft = {};
    message.aircraft.forEach(p => {
        if (!p || !p.icao) return;
        const icao = String(p.icao).trim().toUpperCase();
        aircraft[icao] = p;
    });

    if (message.receiver) {
        setText("receiverStatus", "LIVE");
        setText("sdrHealth", "ONLINE");
        setText("readsbHealth", "CONNECTED");
    }

    setText("lastUpdate", new Date().toLocaleTimeString());
    renderDashboard();
});

ui.on_message("aircraft_selected", (plane) => {
    if (!plane || !plane.icao) return;
    const icao = String(plane.icao).trim().toUpperCase();
    if (aircraft[icao]) selectAircraft(icao, false);
});

function renderDashboard() {
    const list = Object.values(aircraft);
    updateSummary(list);
    updateRadar(list);
    updateTable(list);

    if (selectedIcao && aircraft[selectedIcao]) {
        selectAircraft(selectedIcao, false);
    } else if (list.length) {
        selectAircraft(list[0].icao, false);
    }
}

function updateSummary(list) {
    setText("aircraftCount", list.length);

    let anomalies = 0;
    let highest = 0;

    list.forEach(p => {
        if (getRiskLevel(p) === "ANOMALY") anomalies++;
        highest = Math.max(highest, getFinalScore(p));
    });

    setText("anomalyCount", anomalies);
    setText("riskScore", Math.round(highest));

    const level = scoreLevel(highest);
    const el = document.getElementById("riskLevel");
    if (el) {
        el.textContent = level;
        el.className = "metric-caption " + statusClass(level);
    }
}

function updateRadar(list) {
    const radar = document.getElementById("radar");
    if (!radar) return;

    radar.querySelectorAll(".aircraft").forEach(e => e.remove());

    list.forEach(p => {
        const e = document.createElement("div");
        const icao = String(p.icao).trim().toUpperCase();
        const status = getRiskLevel(p).toLowerCase();

        e.id = "plane-" + icao;
        e.className = "aircraft " + status;
        e.dataset.icao = icao;

        let x = Number(p.x);
        let y = Number(p.y);
        if (!Number.isFinite(x)) x = 50;
        if (!Number.isFinite(y)) y = 50;

        e.style.left = Math.max(5, Math.min(95, x)) + "%";
        e.style.top = Math.max(5, Math.min(95, y)) + "%";

        const icon = document.createElement("div");
        icon.className = "aircraft-icon";
        icon.textContent = "✈";

        const label = document.createElement("span");
        label.className = "aircraft-label";
        label.textContent = p.callsign || icao;

        e.append(icon, label);
        e.addEventListener("click", ev => {
            ev.stopPropagation();
            selectAircraft(icao);
        });

        radar.appendChild(e);
    });
}

function selectAircraft(icao, sendToPython = true) {
    const id = String(icao || "").trim().toUpperCase();
    const p = aircraft[id];
    if (!p) return;

    selectedIcao = id;

    setText("selectedAircraft", p.callsign || id);
    setText("icao", id);

    const meta = p.aviation || p.metadata || {};
    setText("registration", meta.registration || p.registration || "--");
    setText("country", meta.country || p.country || "--");
    setText("airline", meta.airline || p.airline || "--");
    setText("typecode", meta.typecode || p.typecode || "--");
    setText("aircraftType", meta.aircraft_name || p.aircraft_name || meta.typecode || "Aircraft type unavailable");

    setText("altitude", formatAltitude(p.altitude_ft));
    setText("speed", formatSpeed(p.speed_kt));
    setText("heading", formatHeading(p.heading_deg));
    setText("verticalRate", formatVerticalRate(p.vertical_rate_fpm));

    const nearest = meta.nearest_airport || p.nearest_airport || {};
    if (typeof nearest === "object") {
        setText("nearestAirport", nearest.name ? `${nearest.name} (${nearest.icao || "--"})` : "--");
        setText("distanceNm", nearest.distance_nm != null ? `${Number(nearest.distance_nm).toFixed(1)} NM` : "--");
    } else {
        setText("nearestAirport", nearest || "--");
        setText("distanceNm", meta.nearest_airport_distance_nm != null ? `${Number(meta.nearest_airport_distance_nm).toFixed(1)} NM` : "--");
    }

    setText("routeContext", meta.route_context || p.route_context || "--");

    const status = getRiskLevel(p);
    const statusEl = document.getElementById("detailStatus");
    if (statusEl) {
        statusEl.textContent = "● " + status;
        statusEl.className = "detail-status " + statusClass(status);
    }

    const finalScore = getFinalScore(p);
    setText("fusionScore", Math.round(finalScore));
    setText("ruleScore", Math.round(num(p.rule_score)));
    setText("mlScore", Math.round(num(p.ml_score)));
    setText("mlClass", String(p.ml_class || status).toUpperCase());
    setText("anomalyExplanation", p.explanation || p.indicator || "No significant anomaly detected.");

    const bar = document.getElementById("fusionBar");
    if (bar) bar.style.width = Math.max(0, Math.min(100, finalScore)) + "%";

    document.querySelectorAll(".aircraft").forEach(e => e.classList.remove("selected"));
    const marker = document.getElementById("plane-" + id);
    if (marker) marker.classList.add("selected");

    document.querySelectorAll("#aircraftTable tr").forEach(r => r.classList.remove("selected-row"));
    const row = document.querySelector(`#aircraftTable tr[data-icao="${CSS.escape(id)}"]`);
    if (row) row.classList.add("selected-row");

    if (sendToPython) {
        try {
            ui.send_message("select_aircraft", { icao: id });
        } catch (e) {
            console.error("Selection send failed:", e);
        }
    }
}

function updateTable(list) {
    const tbody = document.getElementById("aircraftTable");
    if (!tbody) return;

    tbody.innerHTML = "";

    list.forEach(p => {
        const icao = String(p.icao || "--").trim().toUpperCase();
        const meta = p.aviation || p.metadata || {};
        const status = getRiskLevel(p);

        const tr = document.createElement("tr");
        tr.dataset.icao = icao;

        tr.innerHTML = `
            <td class="callsign-cell">${esc(p.callsign || icao)}</td>
            <td class="icao-cell">${esc(icao)}</td>
            <td>${esc(meta.typecode || p.typecode || "--")}</td>
            <td>${esc(meta.registration || p.registration || "--")}</td>
            <td>${esc(formatAltitude(p.altitude_ft))}</td>
            <td>${esc(formatSpeed(p.speed_kt))}</td>
            <td>${esc(formatHeading(p.heading_deg))}</td>
            <td class="${statusClass(status)}">● ${esc(status)}</td>
        `;

        tr.addEventListener("click", () => selectAircraft(icao));
        tbody.appendChild(tr);
    });
}

function getFinalScore(p) {
    return num(p.final_score ?? p.fusion_score ?? p.risk_score ?? p.risk);
}

function getRiskLevel(p) {
    const s = String(p.risk_level || p.status || "").toUpperCase();
    if (s === "ANOMALY") return "ANOMALY";
    if (s === "MONITOR") return "MONITOR";
    if (s === "NORMAL") return "NORMAL";
    return scoreLevel(getFinalScore(p));
}

function scoreLevel(s) {
    if (s >= 80) return "ANOMALY";
    if (s >= 60) return "MONITOR";
    return "NORMAL";
}

function statusClass(s) {
    s = String(s).toUpperCase();
    if (s === "NORMAL" || s === "LOW") return "status-normal";
    if (s === "MONITOR" || s === "MEDIUM") return "status-monitor";
    return "status-anomaly";
}

function formatAltitude(v) {
    const n = Number(v);
    return Number.isFinite(n) ? Math.round(n).toLocaleString() + " ft" : "--";
}

function formatSpeed(v) {
    const n = Number(v);
    return Number.isFinite(n) ? Math.round(n) + " kt" : "--";
}

function formatHeading(v) {
    const n = Number(v);
    if (!Number.isFinite(n)) return "--";
    return Math.round(((n % 360) + 360) % 360).toString().padStart(3, "0") + "°";
}

function formatVerticalRate(v) {
    const n = Number(v);
    if (!Number.isFinite(n)) return "--";
    return (n > 0 ? "+" : "") + Math.round(n).toLocaleString() + " fpm";
}

function num(v) {
    const n = Number(v);
    return Number.isFinite(n) ? n : 0;
}

function setText(id, value) {
    const e = document.getElementById(id);
    if (e) e.textContent = value;
}

function esc(v) {
    return String(v ?? "--").replace(/[&<>"']/g, c => ({
        "&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"
    }[c]));
}

setInterval(() => {
    const e = document.getElementById("liveClock");
    if (e) e.textContent = new Date().toLocaleTimeString();
}, 1000);

console.log("SkyGuardian Dashboard V2 loaded.");
