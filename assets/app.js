// ============================================================
// SKYGUARDIAN WEB UI
// LIVE FUSION DASHBOARD
// ============================================================

const ui = new WebUI();

let aircraftStore = {};
let selectedIcao = null;

// ============================================================
// CONNECTION
// ============================================================

ui.on_connect(() => {
    console.log("SkyGuardian dashboard connected");
    setSystemStatus("LIVE", true);
});

ui.on_disconnect(() => {
    console.log("SkyGuardian dashboard disconnected");
    setSystemStatus("OFFLINE", false);
});


// ============================================================
// RECEIVE LIVE AIRCRAFT DATA
// ============================================================

ui.on_message("aircraft_update", (message) => {

    if (!message || !Array.isArray(message.aircraft)) {
        console.warn("Invalid aircraft_update message", message);
        return;
    }

    aircraftStore = {};

    message.aircraft.forEach((plane) => {

        if (!plane) return;

        const icao =
            plane.icao ||
            plane.icao24 ||
            plane.hex ||
            "";

        if (!icao) return;

        const normalizedIcao = String(icao).toUpperCase();

        plane.icao = normalizedIcao;

        aircraftStore[normalizedIcao] = plane;
    });

    renderDashboard();
});


// ============================================================
// AIRCRAFT SELECTED MESSAGE
// ============================================================

ui.on_message("aircraft_selected", (message) => {
    console.log("Aircraft selected:", message);
});


// ============================================================
// MAIN DASHBOARD RENDER
// ============================================================

function renderDashboard() {

    const aircraft = Object.values(aircraftStore);

    updateSummary(aircraft);
    updateRadar(aircraft);
    updateTable(aircraft);

    // Keep current selection if aircraft is still present.
    if (selectedIcao && aircraftStore[selectedIcao]) {
        selectAircraft(selectedIcao);
    }
    else if (aircraft.length > 0) {
        selectAircraft(aircraft[0].icao);
    }
    else {
        clearAircraftDetails();
    }
}


// ============================================================
// SYSTEM STATUS
// ============================================================

function setSystemStatus(status, live) {

    const element =
        document.getElementById("systemStatus") ||
        document.querySelector(".system-status");

    if (!element) return;

    element.textContent = status;

    element.classList.toggle("offline", !live);
    element.classList.toggle("live", live);
}


// ============================================================
// SUMMARY CARDS
// ============================================================

function updateSummary(aircraft) {

    const total = aircraft.length;

    let anomalies = 0;
    let highestScore = 0;

    aircraft.forEach((plane) => {

        const score = getRiskScore(plane);

        if (score > highestScore) {
            highestScore = score;
        }

        const risk = getRiskLevel(plane);

        if (risk === "ANOMALY") {
            anomalies++;
        }
    });

    setText("aircraftCount", total);
    setText("anomalyCount", anomalies);
    setText("riskScore", highestScore.toFixed(0));

    // Alternative IDs used by some dashboard versions.
    setText("totalAircraft", total);
    setText("activeAircraft", total);
    setText("highestRisk", highestScore.toFixed(0));
}


// ============================================================
// RADAR
// ============================================================

function updateRadar(aircraft) {

    const radar = document.getElementById("radar");

    if (!radar) return;

    radar.querySelectorAll(".aircraft").forEach((element) => {
        element.remove();
    });

    aircraft.forEach((plane) => {

        const x = Number(plane.x);
        const y = Number(plane.y);

        if (!Number.isFinite(x) || !Number.isFinite(y)) {
            return;
        }

        const marker = document.createElement("div");

        const risk = getRiskLevel(plane);

        marker.className = `aircraft ${risk.toLowerCase()}`;

        if (plane.icao === selectedIcao) {
            marker.classList.add("selected");
        }

        marker.style.left = `${clamp(x, 2, 98)}%`;
        marker.style.top = `${clamp(y, 2, 98)}%`;

        const callsign =
            plane.callsign ||
            plane.flight ||
            plane.aviation?.registration ||
            plane.icao;

        marker.innerHTML = `
            <div class="aircraft-dot"></div>
            <div class="aircraft-label">
                ${escapeHTML(String(callsign).trim())}
            </div>
        `;

        marker.addEventListener("click", () => {
            selectAircraft(plane.icao);
        });

        radar.appendChild(marker);
    });
}


// ============================================================
// SELECT AIRCRAFT
// ============================================================

function selectAircraft(icao) {

    const plane = aircraftStore[icao];

    if (!plane) return;

    selectedIcao = icao;

    // Basic flight information.
    setText("selectedIcao", plane.icao || "—");

    setText(
        "selectedAltitude",
        formatAltitude(plane)
    );

    setText(
        "selectedSpeed",
        formatSpeed(plane)
    );

    setText(
        "selectedHeading",
        formatHeading(plane)
    );

    setText(
        "flightStatus",
        getRiskLevel(plane)
    );

    updateOptionalDetails(plane);
    updateAviationDetails(plane);

    updateRadarSelection();
    updateTableSelection();

    // Send selection to backend if supported.
    try {
        ui.send_message("select_aircraft", {
            icao: plane.icao
        });
    }
    catch (error) {
        console.warn("Unable to send aircraft selection:", error);
    }
}


// ============================================================
// UPDATE RADAR SELECTION
// ============================================================

function updateRadarSelection() {

    document.querySelectorAll(".aircraft").forEach((marker) => {

        marker.classList.remove("selected");

        const planeLabel =
            marker.querySelector(".aircraft-label");

        if (!planeLabel) return;

        const plane = Object.values(aircraftStore).find((p) => {

            const callsign =
                p.callsign ||
                p.flight ||
                p.aviation?.registration ||
                p.icao;

            return String(callsign).trim() ===
                   String(planeLabel.textContent).trim();
        });

        if (plane && plane.icao === selectedIcao) {
            marker.classList.add("selected");
        }
    });
}


// ============================================================
// OPTIONAL DETAILS
// ============================================================

function updateOptionalDetails(plane) {

    const finalScore = getRiskScore(plane);

    const ruleScore =
        numberValue(
            plane.rule_score ??
            plane.ruleScore ??
            plane.risk_rule_score
        );

    const mlScore =
        numberValue(
            plane.ml_score ??
            plane.mlScore
        );

    const mlClass =
        plane.ml_class ||
        plane.mlClass ||
        plane.ml_status ||
        "";

    const explanation =
        plane.explanation ||
        plane.indicator ||
        plane.reason ||
        "";

    const trajectory =
        plane.trajectory ||
        {};

    setText(
        "finalScore",
        Number.isFinite(finalScore)
            ? finalScore.toFixed(1)
            : "—"
    );

    setText(
        "ruleScore",
        Number.isFinite(ruleScore)
            ? ruleScore.toFixed(1)
            : "—"
    );

    setText(
        "mlScore",
        Number.isFinite(mlScore)
            ? mlScore.toFixed(1)
            : "—"
    );

    setText(
        "mlClass",
        mlClass || "—"
    );

    setText(
        "riskExplanation",
        explanation || "No active anomaly indicators."
    );

    setText(
        "distancePrevious",
        formatNumber(
            plane.distance_from_previous_m ??
            trajectory.distance_from_previous_m,
            " m"
        )
    );

    setText(
        "timeDelta",
        formatNumber(
            plane.time_delta_s ??
            trajectory.time_delta_s,
            " s"
        )
    );

    setText(
        "altitudeChange",
        formatNumber(
            plane.altitude_change_m ??
            trajectory.altitude_change_m,
            " m"
        )
    );

    setText(
        "speedChange",
        formatNumber(
            plane.speed_change_mps ??
            trajectory.speed_change_mps,
            " m/s"
        )
    );

    setText(
        "headingChange",
        formatNumber(
            plane.heading_change_deg ??
            trajectory.heading_change_deg,
            "°"
        )
    );

    setText(
        "calculatedSpeed",
        formatNumber(
            plane.calculated_speed_mps ??
            trajectory.calculated_speed_mps,
            " m/s"
        )
    );

    setText(
        "acceleration",
        formatNumber(
            plane.acceleration_mps2 ??
            trajectory.acceleration_mps2,
            " m/s²"
        )
    );
}


// ============================================================
// AVIATION DATABASE DETAILS
// ============================================================

function updateAviationDetails(plane) {

    const detailsPanel =
        document.querySelector(".details");

    if (!detailsPanel) return;

    let panel =
        document.getElementById("aviationDetails");

    if (!panel) {

        panel = document.createElement("section");

        panel.id = "aviationDetails";
        panel.className = "aviation-details";

        detailsPanel.appendChild(panel);
    }

    const aviation = plane.aviation || {};

    const registration =
        aviation.registration ||
        plane.registration ||
        "—";

    const country =
        aviation.country ||
        plane.country ||
        "—";

    const typecode =
        aviation.typecode ||
        plane.typecode ||
        "—";

    const aircraftType =
        aviation.aircraft_type ||
        plane.aircraft_type ||
        "—";

    const manufacturer =
        aviation.manufacturer ||
        plane.manufacturer ||
        "—";

    const model =
        aviation.model ||
        plane.model ||
        "—";

    const operator =
        aviation.operator ||
        plane.operator ||
        "—";

    const operatorCallsign =
        aviation.operator_callsign ||
        plane.operator_callsign ||
        "—";

    const operatorIcao =
        aviation.operator_icao ||
        plane.operator_icao ||
        "—";

    const operatorIata =
        aviation.operator_iata ||
        plane.operator_iata ||
        "—";

    const serialNumber =
        aviation.serial_number ||
        plane.serial_number ||
        "—";

    panel.innerHTML = `
        <div class="aviation-header">
            <div>
                <span class="aviation-kicker">AVIATION DATABASE</span>
                <h3>Aircraft Identity</h3>
            </div>

            <div class="aviation-live-dot"></div>
        </div>

        <div class="aviation-grid">

            ${aviationItem(
                "REGISTRATION",
                registration
            )}

            ${aviationItem(
                "AIRCRAFT TYPE",
                aircraftType
            )}

            ${aviationItem(
                "TYPECODE",
                typecode
            )}

            ${aviationItem(
                "MANUFACTURER",
                manufacturer
            )}

            ${aviationItem(
                "MODEL",
                model,
                "wide"
            )}

            ${aviationItem(
                "OPERATOR",
                operator,
                "wide"
            )}

            ${aviationItem(
                "COUNTRY",
                country
            )}

            ${aviationItem(
                "OPERATOR ICAO",
                operatorIcao
            )}

            ${aviationItem(
                "OPERATOR IATA",
                operatorIata
            )}

            ${aviationItem(
                "OPERATOR CALLSIGN",
                operatorCallsign,
                "wide"
            )}

            ${aviationItem(
                "SERIAL NUMBER",
                serialNumber
            )}

            ${aviationItem(
                "ICAO24",
                plane.icao || "—"
            )}

        </div>
    `;
}


function aviationItem(label, value, extraClass = "") {

    return `
        <div class="aviation-item ${extraClass}">
            <span class="aviation-label">
                ${escapeHTML(label)}
            </span>

            <span class="aviation-value">
                ${escapeHTML(String(value))}
            </span>
        </div>
    `;
}


// ============================================================
// AIRCRAFT TABLE
// ============================================================

function updateTable(aircraft) {

    const tbody =
        document.querySelector("#aircraftTable tbody") ||
        document.querySelector("#aircraft-table-body");

    if (!tbody) return;

    tbody.innerHTML = "";

    aircraft.forEach((plane) => {

        const row = document.createElement("tr");

        const risk = getRiskLevel(plane);

        if (plane.icao === selectedIcao) {
            row.classList.add("selected-row");
        }

        const callsign =
            plane.callsign ||
            plane.flight ||
            plane.aviation?.registration ||
            plane.icao;

        row.innerHTML = `
            <td>
                <div class="table-callsign">
                    ${escapeHTML(String(callsign || "—").trim())}
                </div>
                <small>
                    ${escapeHTML(plane.icao || "—")}
                </small>
            </td>

            <td>${escapeHTML(formatAltitude(plane))}</td>

            <td>${escapeHTML(formatSpeed(plane))}</td>

            <td>${escapeHTML(formatHeading(plane))}</td>

            <td>
                <span class="table-status ${risk.toLowerCase()}">
                    ${escapeHTML(risk)}
                </span>
            </td>
        `;

        row.addEventListener("click", () => {
            selectAircraft(plane.icao);
        });

        tbody.appendChild(row);
    });
}


// ============================================================
// TABLE SELECTION
// ============================================================

function updateTableSelection() {

    document.querySelectorAll("#aircraftTable tbody tr")
        .forEach((row) => {

            row.classList.remove("selected-row");

            const firstCell =
                row.querySelector("td");

            if (!firstCell) return;

            const icaoElement =
                row.querySelector("small");

            if (
                icaoElement &&
                icaoElement.textContent.trim() === selectedIcao
            ) {
                row.classList.add("selected-row");
            }
        });
}


// ============================================================
// CLEAR DETAILS
// ============================================================

function clearAircraftDetails() {

    selectedIcao = null;

    setText("selectedIcao", "—");
    setText("selectedAltitude", "—");
    setText("selectedSpeed", "—");
    setText("selectedHeading", "—");
    setText("flightStatus", "NO AIRCRAFT");

    setText("finalScore", "—");
    setText("ruleScore", "—");
    setText("mlScore", "—");
    setText("mlClass", "—");

    setText(
        "riskExplanation",
        "Waiting for live aircraft data..."
    );

    const aviationPanel =
        document.getElementById("aviationDetails");

    if (aviationPanel) {
        aviationPanel.innerHTML = `
            <div class="aviation-empty">
                <div class="aviation-empty-icon">✈</div>
                <strong>NO AIRCRAFT SELECTED</strong>
                <span>Select an aircraft from the radar.</span>
            </div>
        `;
    }
}


// ============================================================
// FORMAT HELPERS
// ============================================================

function formatAltitude(plane) {

    let value =
        plane.altitude_ft ??
        plane.altitude ??
        plane.altitude_m;

    if (!Number.isFinite(Number(value))) {
        return "—";
    }

    value = Number(value);

    // altitude_m is explicitly metres.
    if (
        plane.altitude_m !== undefined &&
        plane.altitude_ft === undefined
    ) {
        return `${Math.round(value * 3.28084)} ft`;
    }

    return `${Math.round(value).toLocaleString()} ft`;
}


function formatSpeed(plane) {

    let value =
        plane.speed_kt ??
        plane.speed ??
        plane.speed_mps;

    if (!Number.isFinite(Number(value))) {
        return "—";
    }

    value = Number(value);

    // speed_mps is explicitly metres/sec.
    if (
        plane.speed_mps !== undefined &&
        plane.speed_kt === undefined
    ) {
        return `${Math.round(value * 1.94384)} kt`;
    }

    return `${Math.round(value)} kt`;
}


function formatHeading(plane) {

    const value =
        plane.heading_deg ??
        plane.heading;

    if (!Number.isFinite(Number(value))) {
        return "—";
    }

    return `${Math.round(Number(value))}°`;
}


function getRiskScore(plane) {

    const score =
        plane.final_score ??
        plane.risk_score ??
        plane.risk;

    const value = Number(score);

    if (Number.isFinite(value)) {
        return value;
    }

    return 0;
}


function getRiskLevel(plane) {

    const explicit =
        plane.risk_level ||
        plane.status ||
        plane.final_status;

    if (explicit) {

        const value =
            String(explicit).toUpperCase();

        if (value.includes("ANOMALY")) {
            return "ANOMALY";
        }

        if (value.includes("MONITOR")) {
            return "MONITOR";
        }

        if (value.includes("NORMAL")) {
            return "NORMAL";
        }
    }

    const score = getRiskScore(plane);

    if (score >= 80) {
        return "ANOMALY";
    }

    if (score >= 60) {
        return "MONITOR";
    }

    return "NORMAL";
}


function numberValue(value) {

    if (
        value === null ||
        value === undefined ||
        value === ""
    ) {
        return NaN;
    }

    const number = Number(value);

    return Number.isFinite(number)
        ? number
        : NaN;
}


function formatNumber(value, suffix = "") {

    const number = numberValue(value);

    if (!Number.isFinite(number)) {
        return "—";
    }

    return `${number.toFixed(1)}${suffix}`;
}


function setText(id, value) {

    const element =
        document.getElementById(id);

    if (!element) return;

    element.textContent =
        value === undefined ||
        value === null ||
        value === ""
            ? "—"
            : value;
}


function clamp(value, min, max) {

    return Math.min(
        Math.max(value, min),
        max
    );
}


function escapeHTML(value) {

    return String(value)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}


// ============================================================
// INITIAL STATE
// ============================================================

document.addEventListener("DOMContentLoaded", () => {

    setSystemStatus("CONNECTING", false);

    // Create the aviation panel even before aircraft selection.
    const detailsPanel =
        document.querySelector(".details");

    if (
        detailsPanel &&
        !document.getElementById("aviationDetails")
    ) {

        const panel =
            document.createElement("section");

        panel.id = "aviationDetails";
        panel.className = "aviation-details";

        panel.innerHTML = `
            <div class="aviation-empty">
                <div class="aviation-empty-icon">✈</div>
                <strong>WAITING FOR AIRCRAFT</strong>
                <span>Live aviation metadata will appear here.</span>
            </div>
        `;

        detailsPanel.appendChild(panel);
    }
});
