// ==========================================
// SKYGUARDIAN
// ==========================================


// WebUI
const ui = new WebUI();


// Socket.IO
const socket = io();


// Current aircraft
let aircraft = [];


// Selected aircraft
let selectedICAO = "ABC123";


// ==========================================
// WEB UI CONNECTION
// ==========================================

ui.on_connect(() => {

    console.log(
        "SkyGuardian WebUI connected"
    );

});


ui.on_disconnect(() => {

    console.log(
        "SkyGuardian WebUI disconnected"
    );

});


// ==========================================
// RECEIVE AIRCRAFT DATA
// ==========================================

socket.on(
    "aircraft_data",
    (data) => {

        console.log(
            "Received aircraft data",
            data
        );

        updateDashboard(data);

    }
);


// ==========================================
// UPDATE DASHBOARD
// ==========================================

function updateDashboard(data) {


    aircraft =
        data.aircraft || [];


    selectedICAO =
        data.selected_icao ||
        selectedICAO;


    // --------------------------------------
    // Summary
    // --------------------------------------

    document.getElementById(
        "aircraftCount"
    ).textContent =
        data.aircraft_count;


    document.getElementById(
        "anomalyCount"
    ).textContent =
        data.anomaly_count;


    // --------------------------------------
    // Selected aircraft
    // --------------------------------------

    const selected =
        aircraft.find(
            plane =>
                plane.icao ===
                selectedICAO
        );


    if (selected) {

        updateSelectedAircraft(
            selected
        );

    }


    // --------------------------------------
    // Radar
    // --------------------------------------

    aircraft.forEach(
        (plane, index) => {

            updateRadarPlane(
                plane,
                index
            );

        }
    );


    // --------------------------------------
    // Table
    // --------------------------------------

    updateTable();

}


// ==========================================
// UPDATE SELECTED AIRCRAFT
// ==========================================

function updateSelectedAircraft(
    plane
) {


    document.getElementById(
        "selectedAircraft"
    ).textContent =
        plane.icao;


    document.getElementById(
        "icao"
    ).textContent =
        plane.icao;


    document.getElementById(
        "altitude"
    ).textContent =
        `${Math.round(
            plane.altitude
        ).toLocaleString()} ft`;


    document.getElementById(
        "speed"
    ).textContent =
        `${Math.round(
            plane.speed
        )} kt`;


    document.getElementById(
        "heading"
    ).textContent =
        `${Math.round(
            plane.heading
        )}°`;


    const status =
        document.getElementById(
            "flightStatus"
        );


    status.textContent =
        `● ${plane.status}`;


    status.className =
        "";


    if (
        plane.status ===
        "NORMAL"
    ) {

        status.classList.add(
            "normal"
        );

    }

    else if (
        plane.status ===
        "ANOMALY"
    ) {

        status.classList.add(
            "anomaly"
        );

    }

    else {

        status.classList.add(
            "monitor"
        );

    }


    // --------------------------------------
    // Risk
    // --------------------------------------

    const risk =
        document.getElementById(
            "riskScore"
        );


    risk.textContent =
        plane.risk;


    const level =
        document.getElementById(
            "riskLevel"
        );


    if (plane.risk >= 70) {

        level.textContent =
            "HIGH";

        level.className =
            "small-label risk-high";

    }

    else if (plane.risk >= 40) {

        level.textContent =
            "MEDIUM";

        level.className =
            "small-label risk-medium";

    }

    else {

        level.textContent =
            "LOW";

        level.className =
            "small-label risk-low";

    }

}


// ==========================================
// UPDATE RADAR
// ==========================================

function updateRadarPlane(
    plane,
    index
) {


    const element =
        document.getElementById(
            `plane${index}`
        );


    if (!element) {

        console.warn(
            "Radar element missing:",
            index
        );

        return;

    }


    // Position
    element.style.left =
        `${plane.x}%`;

    element.style.top =
        `${plane.y}%`;


    // Status class

    element.classList.remove(
        "normal",
        "monitor",
        "anomaly",
        "selected"
    );


    element.classList.add(
        plane.status.toLowerCase()
    );


    // Selected

    if (
        plane.icao ===
        selectedICAO
    ) {

        element.classList.add(
            "selected"
        );

    }


    // --------------------------------------
    // Click
    // --------------------------------------

    element.onclick =
        function () {

            selectAircraft(
                plane.icao
            );

        };

}


// ==========================================
// SELECT AIRCRAFT
// ==========================================

function selectAircraft(
    icao
) {


    console.log(
        "✈ Selecting:",
        icao
    );


    selectedICAO =
        icao;


    // --------------------------------------
    // Find aircraft
    // --------------------------------------

    const plane =
        aircraft.find(
            p =>
                p.icao ===
                icao
        );


    if (plane) {

        updateSelectedAircraft(
            plane
        );

    }


    // --------------------------------------
    // Update radar
    // --------------------------------------

    aircraft.forEach(
        (p, index) => {

            const element =
                document.getElementById(
                    `plane${index}`
                );


            if (!element) {

                return;

            }


            element.classList.remove(
                "selected"
            );


            if (
                p.icao === icao
            ) {

                element.classList.add(
                    "selected"
                );

            }

        }
    );


    // --------------------------------------
    // Update table
    // --------------------------------------

    updateTable();


    // --------------------------------------
    // SEND TO PYTHON
    // --------------------------------------

    socket.emit(
        "aircraft_selected",
        {
            icao: icao
        }
    );


    console.log(
        "Sent aircraft_selected:",
        icao
    );

}


// ==========================================
// UPDATE TABLE
// ==========================================

function updateTable() {


    const tbody =
        document.getElementById(
            "aircraftTable"
        );


    tbody.innerHTML = "";


    aircraft.forEach(
        plane => {


            const row =
                document.createElement(
                    "tr"
                );


            if (
                plane.icao ===
                selectedICAO
            ) {

                row.classList.add(
                    "selected-row"
                );

            }


            row.innerHTML = `

                <td>
                    <strong>
                        ${plane.icao}
                    </strong>
                </td>

                <td>
                    ${Math.round(
                        plane.altitude
                    ).toLocaleString()} ft
                </td>

                <td>
                    ${Math.round(
                        plane.speed
                    )} kt
                </td>

                <td>
                    ${Math.round(
                        plane.heading
                    )}°
                </td>

                <td class="${getStatusClass(
                    plane.status
                )}">
                    ● ${plane.status}
                </td>

            `;


            row.onclick =
                function () {

                    selectAircraft(
                        plane.icao
                    );

                };


            tbody.appendChild(
                row
            );

        }
    );

}


// ==========================================
// STATUS CLASS
// ==========================================

function getStatusClass(
    status
) {

    if (
        status ===
        "NORMAL"
    ) {

        return "normal";

    }


    if (
        status ===
        "ANOMALY"
    ) {

        return "anomaly";

    }


    return "monitor";

}