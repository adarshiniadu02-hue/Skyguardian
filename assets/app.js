// ==================================================
// SKYGUARDIAN WEB UI
// ==================================================

const ui = new WebUI();


// ==================================================
// AIRCRAFT DATA
// ==================================================

const aircraft = {

    ABC123: {
        altitude: "28,000 ft",
        speed: "440 kt",
        heading: "275°",
        status: "NORMAL"
    },

    DEF456: {
        altitude: "32,000 ft",
        speed: "470 kt",
        heading: "180°",
        status: "NORMAL"
    },

    A1B2C3: {
        altitude: "12,000 ft",
        speed: "280 kt",
        heading: "090°",
        status: "MONITOR"
    },

    F4E5D6: {
        altitude: "22,000 ft",
        speed: "510 kt",
        heading: "315°",
        status: "ANOMALY"
    },

    B7C8D9: {
        altitude: "35,000 ft",
        speed: "460 kt",
        heading: "040°",
        status: "NORMAL"
    }

};


// ==================================================
// CONNECT
// ==================================================

ui.on_connect(() => {

    console.log("SkyGuardian Web UI connected");

    buildAircraftTable();

    selectAircraft("ABC123");

});


// ==================================================
// DISCONNECT
// ==================================================

ui.on_disconnect(() => {

    console.log("Web UI disconnected");

});


// ==================================================
// SELECT AIRCRAFT
// ==================================================

function selectAircraft(icao) {

    console.log("Selecting aircraft:", icao);

    const data = aircraft[icao];

    if (!data) {

        console.log("Aircraft not found:", icao);

        return;
    }


    // ----------------------------------------------
    // Update selected aircraft
    // ----------------------------------------------

    document.getElementById(
        "selectedAircraft"
    ).textContent = icao;


    document.getElementById(
        "icao"
    ).textContent = icao;


    document.getElementById(
        "altitude"
    ).textContent = data.altitude;


    document.getElementById(
        "speed"
    ).textContent = data.speed;


    document.getElementById(
        "heading"
    ).textContent = data.heading;


    // ----------------------------------------------
    // Update status
    // ----------------------------------------------

    const statusElement =
        document.getElementById("flightStatus");


    statusElement.textContent =
        "● " + data.status;


    statusElement.className = "";


    if (data.status === "NORMAL") {

        statusElement.classList.add(
            "status-normal"
        );

    }

    else if (data.status === "MONITOR") {

        statusElement.classList.add(
            "status-monitor"
        );

    }

    else {

        statusElement.classList.add(
            "status-anomaly"
        );

    }


    // ----------------------------------------------
    // Highlight radar aircraft
    // ----------------------------------------------

    document
        .querySelectorAll(".aircraft")
        .forEach(plane => {

            plane.classList.remove("selected");

        });


    const selectedPlane =
        document.getElementById(
            getPlaneId(icao)
        );


    if (selectedPlane) {

        selectedPlane.classList.add(
            "selected"
        );

    }


    // ----------------------------------------------
    // Highlight table row
    // ----------------------------------------------

    document
        .querySelectorAll("#aircraftTable tr")
        .forEach(row => {

            row.classList.remove(
                "selected-row"
            );

        });


    const row =
        document.querySelector(
            `[data-icao="${icao}"]`
        );


    if (row) {

        row.classList.add(
            "selected-row"
        );

    }


    // ----------------------------------------------
    // SEND SELECTION TO PYTHON
    // ----------------------------------------------

    console.log(
        "Sending selection to Python:",
        icao
    );


    ui.send_message(
        "select_aircraft",
        {
            icao: icao
        }
    );

}


// ==================================================
// MAP ICAO → RADAR PLANE
// ==================================================

function getPlaneId(icao) {

    const map = {

        "ABC123": "plane0",

        "DEF456": "plane1",

        "A1B2C3": "plane2",

        "F4E5D6": "plane3",

        "B7C8D9": "plane4"

    };

    return map[icao];

}


// ==================================================
// CLICK EVENTS FOR RADAR AIRCRAFT
// ==================================================

document
    .querySelectorAll(".aircraft")
    .forEach(plane => {

        plane.addEventListener(
            "click",
            () => {

                const label =
                    plane.querySelector(
                        ".aircraft-label"
                    );

                if (!label) {
                    return;
                }

                const icao =
                    label.textContent.trim();

                selectAircraft(icao);

            }
        );

    });


// ==================================================
// AIRCRAFT TABLE
// ==================================================

function buildAircraftTable() {

    const table =
        document.getElementById(
            "aircraftTable"
        );


    table.innerHTML = "";


    Object.keys(aircraft)
        .forEach(icao => {

            const data =
                aircraft[icao];


            const row =
                document.createElement("tr");


            row.setAttribute(
                "data-icao",
                icao
            );


            row.innerHTML = `

                <td>${icao}</td>

                <td>${data.altitude}</td>

                <td>${data.speed}</td>

                <td>${data.heading}</td>

                <td class="${getStatusClass(data.status)}">
                    ● ${data.status}
                </td>

            `;


            row.addEventListener(
                "click",
                () => {

                    selectAircraft(icao);

                }
            );


            table.appendChild(row);

        });

}


// ==================================================
// STATUS CLASS
// ==================================================

function getStatusClass(status) {

    if (status === "NORMAL") {

        return "status-normal";

    }

    if (status === "MONITOR") {

        return "status-monitor";

    }

    return "status-anomaly";

}


// ==================================================
// RECEIVE CONFIRMATION FROM PYTHON
// ==================================================

ui.on_message(
    "aircraft_selected",
    message => {

        console.log(
            "Python confirmed:",
            message
        );

    }
);