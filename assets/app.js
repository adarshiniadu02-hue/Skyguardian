// ============================================================
// SKYGUARDIAN WEB UI
// LIVE FUSION DASHBOARD
// ============================================================

const ui = new WebUI();


// ============================================================
// AIRCRAFT STORE
// ============================================================

let aircraft = {};

let selectedIcao = null;


// ============================================================
// CONNECTION
// ============================================================

ui.on_connect(() => {

    console.log(
        "======================================"
    );

    console.log(
        "SKYGUARDIAN WEB UI CONNECTED"
    );

    console.log(
        "Waiting for live aircraft_update..."
    );

    console.log(
        "======================================"
    );

});


// ============================================================
// DISCONNECTION
// ============================================================

ui.on_disconnect(() => {

    console.log(
        "SKYGUARDIAN WEB UI DISCONNECTED"
    );

});


// ============================================================
// RECEIVE LIVE AIRCRAFT DATA
// ============================================================

ui.on_message(
    "aircraft_update",
    (message) => {

        console.log(
            "======================================"
        );

        console.log(
            "LIVE AIRCRAFT UPDATE RECEIVED"
        );

        console.log(
            "Raw message:",
            message
        );


        // ----------------------------------------------------
        // Validate message
        // ----------------------------------------------------

        if (
            !message ||
            !Array.isArray(
                message.aircraft
            )
        ) {

            console.error(
                "INVALID AIRCRAFT MESSAGE"
            );

            console.error(
                message
            );

            return;

        }


        console.log(
            "Aircraft array length:",
            message.aircraft.length
        );


        // ----------------------------------------------------
        // Clear previous aircraft
        // ----------------------------------------------------

        aircraft = {};


        // ----------------------------------------------------
        // Store current aircraft
        // ----------------------------------------------------

        message.aircraft.forEach(
            (plane) => {

                if (
                    !plane ||
                    !plane.icao
                ) {

                    console.warn(
                        "Invalid aircraft:",
                        plane
                    );

                    return;

                }


                const icao =
                    String(
                        plane.icao
                    )
                    .trim()
                    .toUpperCase();


                aircraft[icao] = plane;

            }
        );


        console.log(
            "Aircraft stored:",
            Object.keys(
                aircraft
            ).length
        );


        // ----------------------------------------------------
        // Render dashboard
        // ----------------------------------------------------

        renderDashboard();


        console.log(
            "======================================"
        );

    }
);


// ============================================================
// RECEIVE SELECTED AIRCRAFT
// ============================================================

ui.on_message(
    "aircraft_selected",
    (plane) => {

        console.log(
            "Selected aircraft received from Python:",
            plane
        );

    }
);


// ============================================================
// RENDER DASHBOARD
// ============================================================

function renderDashboard() {

    const list =
        Object.values(
            aircraft
        );


    console.log(
        "Rendering:",
        list.length,
        "aircraft"
    );


    updateSummary(
        list
    );


    updateRadar(
        list
    );


    updateTable(
        list
    );


    // --------------------------------------------------------
    // Keep selected aircraft if still available
    // --------------------------------------------------------

    if (
        selectedIcao &&
        aircraft[selectedIcao]
    ) {

        selectAircraft(
            selectedIcao,
            false
        );

    }

    // --------------------------------------------------------
    // Select first aircraft when nothing is selected
    // --------------------------------------------------------

    else if (
        list.length > 0
    ) {

        selectAircraft(
            list[0].icao,
            false
        );

    }

}


// ============================================================
// SUMMARY
// ============================================================

function updateSummary(
    list
) {

    const count =
        document.getElementById(
            "aircraftCount"
        );


    const anomalies =
        document.getElementById(
            "anomalyCount"
        );


    const risk =
        document.getElementById(
            "riskScore"
        );


    const riskLevel =
        document.getElementById(
            "riskLevel"
        );


    // --------------------------------------------------------
    // Aircraft count
    // --------------------------------------------------------

    if (count) {

        count.textContent =
            list.length;

    }


    // --------------------------------------------------------
    // Calculate summary risk
    // --------------------------------------------------------

    let anomalyCount = 0;

    let highestRisk = 0;


    list.forEach(
        (plane) => {

            const status =
                getRiskLevel(
                    plane
                );


            if (
                status === "ANOMALY"
            ) {

                anomalyCount++;

            }


            const planeRisk =
                getFinalScore(
                    plane
                );


            if (
                planeRisk >
                highestRisk
            ) {

                highestRisk =
                    planeRisk;

            }

        }
    );


    // --------------------------------------------------------
    // Anomaly count
    // --------------------------------------------------------

    if (anomalies) {

        anomalies.textContent =
            anomalyCount;

    }


    // --------------------------------------------------------
    // Highest risk score
    // --------------------------------------------------------

    if (risk) {

        risk.textContent =
            Math.round(
                highestRisk
            );

    }


    // --------------------------------------------------------
    // Overall risk level
    // --------------------------------------------------------

    if (riskLevel) {

        if (
            highestRisk >= 80
        ) {

            riskLevel.textContent =
                "HIGH";

        }

        else if (
            highestRisk >= 60
        ) {

            riskLevel.textContent =
                "MEDIUM";

        }

        else {

            riskLevel.textContent =
                "LOW";

        }

    }

}


// ============================================================
// RADAR
// ============================================================

function updateRadar(
    list
) {

    const radar =
        document.getElementById(
            "radar"
        );


    if (!radar) {

        console.error(
            "Radar element not found"
        );

        return;

    }


    // --------------------------------------------------------
    // Remove only dynamically generated aircraft
    // --------------------------------------------------------

    radar
        .querySelectorAll(
            ".aircraft"
        )
        .forEach(
            (element) => {

                element.remove();

            }
        );


    // --------------------------------------------------------
    // Add current aircraft
    // --------------------------------------------------------

    list.forEach(
        (plane) => {

            const element =
                document.createElement(
                    "div"
                );


            const status =
                getRiskLevel(
                    plane
                )
                .toLowerCase();


            element.className =
                "aircraft " +
                status;


            element.id =
                "plane-" +
                plane.icao;


            // ------------------------------------------------
            // RADAR POSITION
            // ------------------------------------------------

            let x =
                Number(
                    plane.x
                );


            let y =
                Number(
                    plane.y
                );


            if (
                !Number.isFinite(x)
            ) {

                x = 50;

            }


            if (
                !Number.isFinite(y)
            ) {

                y = 50;

            }


            x =
                Math.max(
                    5,
                    Math.min(
                        95,
                        x
                    )
                );


            y =
                Math.max(
                    5,
                    Math.min(
                        95,
                        y
                    )
                );


            element.style.left =
                x + "%";


            element.style.top =
                y + "%";


            element.style.cursor =
                "pointer";


            element.dataset.icao =
                plane.icao;


            // ------------------------------------------------
            // ICON
            // ------------------------------------------------

            const icon =
                document.createElement(
                    "div"
                );


            icon.className =
                "aircraft-icon";


            icon.textContent =
                "✈";


            // ------------------------------------------------
            // LABEL
            // ------------------------------------------------

            const label =
                document.createElement(
                    "span"
                );


            label.className =
                "aircraft-label";


            label.textContent =
                plane.callsign ||
                plane.icao;


            // ------------------------------------------------
            // BUILD ELEMENT
            // ------------------------------------------------

            element.appendChild(
                icon
            );


            element.appendChild(
                label
            );


            // ------------------------------------------------
            // CLICK
            // ------------------------------------------------

            element.addEventListener(
                "click",
                (event) => {

                    event.stopPropagation();

                    selectAircraft(
                        plane.icao
                    );

                }
            );


            radar.appendChild(
                element
            );

        }
    );


    console.log(
        "Radar aircraft rendered:",
        list.length
    );

}


// ============================================================
// SELECT AIRCRAFT
// ============================================================

function selectAircraft(
    icao,
    sendToPython = true
) {

    if (!icao) {

        return;

    }


    const normalizedIcao =
        String(
            icao
        )
        .trim()
        .toUpperCase();


    const plane =
        aircraft[
            normalizedIcao
        ];


    if (!plane) {

        console.error(
            "Aircraft not found:",
            normalizedIcao
        );

        return;

    }


    selectedIcao =
        normalizedIcao;


    console.log(
        "Selected aircraft:",
        plane
    );


    // ========================================================
    // BASIC DETAILS
    // ========================================================

    const selected =
        document.getElementById(
            "selectedAircraft"
        );


    if (selected) {

        selected.textContent =
            plane.callsign ||
            plane.icao ||
            "--";

    }


    const icaoElement =
        document.getElementById(
            "icao"
        );


    if (icaoElement) {

        icaoElement.textContent =
            plane.icao ||
            "--";

    }


    // ========================================================
    // ALTITUDE
    // ========================================================

    const altitude =
        document.getElementById(
            "altitude"
        );


    if (altitude) {

        altitude.textContent =
            formatAltitude(
                getAltitudeMeters(
                    plane
                )
            );

    }


    // ========================================================
    // SPEED
    // ========================================================

    const speed =
        document.getElementById(
            "speed"
        );


    if (speed) {

        speed.textContent =
            formatSpeed(
                getSpeedMps(
                    plane
                )
            );

    }


    // ========================================================
    // HEADING
    // ========================================================

    const heading =
        document.getElementById(
            "heading"
        );


    if (heading) {

        heading.textContent =
            formatHeading(
                plane.heading ??
                plane.heading_deg
            );

    }


    // ========================================================
    // STATUS
    // ========================================================

    const status =
        getRiskLevel(
            plane
        );


    const statusElement =
        document.getElementById(
            "flightStatus"
        );


    if (statusElement) {

        statusElement.textContent =
            "● " + status;


        statusElement.className =
            getStatusClass(
                status
            );

    }


    // ========================================================
    // OPTIONAL RISK ELEMENTS
    // ========================================================

    updateOptionalDetails(
        plane
    );


    // ========================================================
    // RADAR HIGHLIGHT
    // ========================================================

    document
        .querySelectorAll(
            ".aircraft"
        )
        .forEach(
            (element) => {

                element.classList.remove(
                    "selected"
                );

            }
        );


    const selectedPlane =
        document.getElementById(
            "plane-" +
            normalizedIcao
        );


    if (selectedPlane) {

        selectedPlane.classList.add(
            "selected"
        );

    }


    // ========================================================
    // TABLE HIGHLIGHT
    // ========================================================

    document
        .querySelectorAll(
            "#aircraftTable tr"
        )
        .forEach(
            (row) => {

                row.classList.remove(
                    "selected-row"
                );

            }
        );


    const row =
        document.querySelector(
            `#aircraftTable tr[data-icao="${normalizedIcao}"]`
        );


    if (row) {

        row.classList.add(
            "selected-row"
        );

    }


    // ========================================================
    // SEND SELECTION TO PYTHON
    // ========================================================

    if (
        sendToPython
    ) {

        try {

            ui.send_message(
                "select_aircraft",
                {
                    icao: normalizedIcao
                }
            );

        }

        catch (error) {

            console.error(
                "Selection send error:",
                error
            );

        }

    }

}


// ============================================================
// OPTIONAL LIVE AI DETAILS
// ============================================================

function updateOptionalDetails(
    plane
) {

    const finalScore =
        getFinalScore(
            plane
        );


    const ruleScore =
        getNumber(
            plane.rule_score,
            0
        );


    const mlScore =
        getNumber(
            plane.ml_score,
            0
        );


    const mlClass =
        String(
            plane.ml_class ||
            "UNAVAILABLE"
        ).toUpperCase();


    const explanation =
        plane.explanation ||
        plane.indicator ||
        "NO_SIGNIFICANT_ANOMALY";


    // --------------------------------------------------------
    // Final score
    // --------------------------------------------------------

    updateElementIfExists(
        "finalScore",
        Math.round(
            finalScore
        )
    );


    updateElementIfExists(
        "fusionScore",
        Math.round(
            finalScore
        )
    );


    // --------------------------------------------------------
    // Rule score
    // --------------------------------------------------------

    updateElementIfExists(
        "ruleScore",
        Math.round(
            ruleScore
        )
    );


    // --------------------------------------------------------
    // ML score
    // --------------------------------------------------------

    updateElementIfExists(
        "mlScore",
        Math.round(
            mlScore
        )
    );


    // --------------------------------------------------------
    // ML classification
    // --------------------------------------------------------

    updateElementIfExists(
        "mlClass",
        mlClass
    );


    updateElementIfExists(
        "mlClassification",
        mlClass
    );


    // --------------------------------------------------------
    // Explanation
    // --------------------------------------------------------

    updateElementIfExists(
        "anomalyExplanation",
        explanation
    );


    updateElementIfExists(
        "explanation",
        explanation
    );


    // --------------------------------------------------------
    // Trajectory features
    // --------------------------------------------------------

    updateElementIfExists(
        "distancePrevious",
        formatNumber(
            plane.distance_from_previous_m
        ) + " m"
    );


    updateElementIfExists(
        "timeDelta",
        formatNumber(
            plane.time_delta_s
        ) + " s"
    );


    updateElementIfExists(
        "altitudeChange",
        formatNumber(
            plane.altitude_change_m
        ) + " m"
    );


    updateElementIfExists(
        "speedChange",
        formatNumber(
            plane.speed_change_mps
        ) + " m/s"
    );


    updateElementIfExists(
        "headingChange",
        formatNumber(
            plane.heading_change_deg
        ) + "°"
    );


    updateElementIfExists(
        "calculatedSpeed",
        formatNumber(
            plane.calculated_speed_mps
        ) + " m/s"
    );


    updateElementIfExists(
        "acceleration",
        formatNumber(
            plane.acceleration_mps2
        ) + " m/s²"
    );

}


// ============================================================
// TABLE
// ============================================================

function updateTable(
    list
) {

    const table =
        document.getElementById(
            "aircraftTable"
        );


    if (!table) {

        console.error(
            "Aircraft table not found"
        );

        return;

    }


    table.innerHTML = "";


    list.forEach(
        (plane) => {

            const row =
                document.createElement(
                    "tr"
                );


            row.dataset.icao =
                plane.icao;


            const status =
                getRiskLevel(
                    plane
                );


            const icao =
                plane.icao ||
                "--";


            const callsign =
                plane.callsign ||
                icao;


            row.innerHTML = `

                <td>
                    ${escapeHTML(callsign)}
                </td>

                <td>
                    ${escapeHTML(
                        formatAltitude(
                            getAltitudeMeters(
                                plane
                            )
                        )
                    )}
                </td>

                <td>
                    ${escapeHTML(
                        formatSpeed(
                            getSpeedMps(
                                plane
                            )
                        )
                    )}
                </td>

                <td>
                    ${escapeHTML(
                        formatHeading(
                            plane.heading ??
                            plane.heading_deg
                        )
                    )}
                </td>

                <td class="${getStatusClass(status)}">
                    ● ${escapeHTML(status)}
                </td>

            `;


            row.addEventListener(
                "click",
                () => {

                    selectAircraft(
                        plane.icao
                    );

                }
            );


            table.appendChild(
                row
            );

        }
    );


    console.log(
        "Table rows:",
        list.length
    );

}


// ============================================================
// GET ALTITUDE
// ============================================================

function getAltitudeMeters(
    plane
) {

    // New live format
    if (
        plane.altitude_m !== undefined &&
        plane.altitude_m !== null
    ) {

        return getNumber(
            plane.altitude_m,
            0
        );

    }


    // Existing dashboard format
    if (
        plane.altitude !== undefined &&
        plane.altitude !== null
    ) {

        return getNumber(
            plane.altitude,
            0
        );

    }


    // Fallback: feet → meters
    if (
        plane.altitude_ft !== undefined &&
        plane.altitude_ft !== null
    ) {

        return (
            getNumber(
                plane.altitude_ft,
                0
            )
            *
            0.3048
        );

    }


    return 0;

}


// ============================================================
// GET SPEED
// ============================================================

function getSpeedMps(
    plane
) {

    // New live format
    if (
        plane.speed_mps !== undefined &&
        plane.speed_mps !== null
    ) {

        return getNumber(
            plane.speed_mps,
            0
        );

    }


    // Existing dashboard format
    if (
        plane.speed !== undefined &&
        plane.speed !== null
    ) {

        return getNumber(
            plane.speed,
            0
        );

    }


    // Fallback: knots → m/s
    if (
        plane.speed_kt !== undefined &&
        plane.speed_kt !== null
    ) {

        return (
            getNumber(
                plane.speed_kt,
                0
            )
            *
            0.514444
        );

    }


    return 0;

}


// ============================================================
// GET FINAL RISK SCORE
// ============================================================

function getFinalScore(
    plane
) {

    if (
        plane.final_score !== undefined &&
        plane.final_score !== null
    ) {

        return getNumber(
            plane.final_score,
            0
        );

    }


    if (
        plane.risk !== undefined &&
        plane.risk !== null
    ) {

        return getNumber(
            plane.risk,
            0
        );

    }


    return 0;

}


// ============================================================
// GET RISK LEVEL
// ============================================================

function getRiskLevel(
    plane
) {

    const level =
        String(
            plane.risk_level ||
            plane.status ||
            ""
        )
        .trim()
        .toUpperCase();


    if (
        level === "ANOMALY"
    ) {

        return "ANOMALY";

    }


    if (
        level === "MONITOR"
    ) {

        return "MONITOR";

    }


    if (
        level === "NORMAL"
    ) {

        return "NORMAL";

    }


    // --------------------------------------------------------
    // Fallback based on final score
    // --------------------------------------------------------

    const score =
        getFinalScore(
            plane
        );


    if (
        score >= 80
    ) {

        return "ANOMALY";

    }


    if (
        score >= 60
    ) {

        return "MONITOR";

    }


    return "NORMAL";

}


// ============================================================
// ALTITUDE FORMAT
// ============================================================

function formatAltitude(
    meters
) {

    if (
        meters === null ||
        meters === undefined ||
        meters === ""
    ) {

        return "--";

    }


    const value =
        Number(
            meters
        );


    if (
        !Number.isFinite(value)
    ) {

        return "--";

    }


    const feet =
        value *
        3.28084;


    return (
        Math.round(
            feet
        )
        .toLocaleString() +
        " ft"
    );

}


// ============================================================
// SPEED FORMAT
// ============================================================

function formatSpeed(
    metersPerSecond
) {

    if (
        metersPerSecond === null ||
        metersPerSecond === undefined ||
        metersPerSecond === ""
    ) {

        return "--";

    }


    const value =
        Number(
            metersPerSecond
        );


    if (
        !Number.isFinite(value)
    ) {

        return "--";

    }


    const knots =
        value *
        1.94384;


    return (
        Math.round(
            knots
        ) +
        " kt"
    );

}


// ============================================================
// HEADING FORMAT
// ============================================================

function formatHeading(
    heading
) {

    if (
        heading === null ||
        heading === undefined ||
        heading === ""
    ) {

        return "--";

    }


    let value =
        Number(
            heading
        );


    if (
        !Number.isFinite(value)
    ) {

        return "--";

    }


    value =
        (
            value %
            360 +
            360
        ) %
        360;


    return (
        Math.round(
            value
        )
        .toString()
        .padStart(
            3,
            "0"
        ) +
        "°"
    );

}


// ============================================================
// STATUS CLASS
// ============================================================

function getStatusClass(
    status
) {

    status =
        String(
            status ||
            "NORMAL"
        )
        .toUpperCase();


    if (
        status === "NORMAL"
    ) {

        return "status-normal";

    }


    if (
        status === "MONITOR"
    ) {

        return "status-monitor";

    }


    return "status-anomaly";

}


// ============================================================
// NUMBER HELPER
// ============================================================

function getNumber(
    value,
    fallback = 0
) {

    const number =
        Number(
            value
        );


    if (
        Number.isFinite(
            number
        )
    ) {

        return number;

    }


    return fallback;

}


// ============================================================
// NUMBER DISPLAY
// ============================================================

function formatNumber(
    value
) {

    const number =
        Number(
            value
        );


    if (
        !Number.isFinite(
            number
        )
    ) {

        return "--";

    }


    return number.toFixed(
        2
    );

}


// ============================================================
// UPDATE ELEMENT IF IT EXISTS
// ============================================================

function updateElementIfExists(
    id,
    value
) {

    const element =
        document.getElementById(
            id
        );


    if (element) {

        element.textContent =
            value;

    }

}


// ============================================================
// HTML ESCAPE
// ============================================================

function escapeHTML(
    value
) {

    return String(
        value
    )
    .replace(
        /&/g,
        "&amp;"
    )
    .replace(
        /</g,
        "&lt;"
    )
    .replace(
        />/g,
        "&gt;"
    )
    .replace(
        /"/g,
        "&quot;"
    )
    .replace(
        /'/g,
        "&#039;"
    );

}


// ============================================================
// INITIAL MESSAGE
// ============================================================

console.log(
    "SkyGuardian LIVE app.js loaded successfully."
);

console.log(
    "Waiting for aircraft_update messages..."
);
