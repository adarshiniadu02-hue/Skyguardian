#!/usr/bin/env python3

import json
import time
from pathlib import Path


# ============================================================
# SKYGUARDIAN — REALTIME FUSION ENGINE
# Rule-Based Risk + Edge AI Risk Fusion
# ============================================================


# ------------------------------------------------------------
# FILE PATHS
# ------------------------------------------------------------

TRAJECTORY_FILE = Path("data/live/realtime_trajectory.json")
ML_FILE = Path("data/live/realtime_ml_results.json")
OUTPUT_FILE = Path("data/live/realtime_fusion_results.json")


# ------------------------------------------------------------
# TIMING
# ------------------------------------------------------------

UPDATE_INTERVAL = 1.0

# Maximum acceptable age of ML result
MAX_ML_AGE_SECONDS = 15.0


# ------------------------------------------------------------
# RULE THRESHOLDS
# ------------------------------------------------------------

TIME_GAP_WARNING = 60.0

ALTITUDE_CHANGE_WARNING = 3000.0

SPEED_CHANGE_WARNING = 50.0

HEADING_CHANGE_WARNING = 90.0

CALCULATED_SPEED_WARNING = 300.0

ACCELERATION_WARNING = 10.0

POSITION_JUMP_WARNING = 10000.0


# ------------------------------------------------------------
# RULE SCORE WEIGHTS
# ------------------------------------------------------------

RULE_WEIGHT = 0.60

ML_WEIGHT = 0.40


# ------------------------------------------------------------
# FINAL RISK LEVELS
# ------------------------------------------------------------

MONITOR_THRESHOLD = 60.0

ANOMALY_THRESHOLD = 80.0


# ------------------------------------------------------------
# STATE
# ------------------------------------------------------------

latest_results = {}


# ============================================================
# SAFE CONVERSION FUNCTIONS
# ============================================================

def safe_float(value, default=0.0):
    """
    Safely convert a value to float.
    """

    try:
        if value is None:
            return default

        result = float(value)

        if result != result:  # NaN check
            return default

        return result

    except (ValueError, TypeError):
        return default


def safe_int(value, default=0):
    """
    Safely convert a value to integer.
    """

    try:
        return int(value)

    except (ValueError, TypeError):
        return default


# ============================================================
# FILE READING
# ============================================================

def read_json(path):
    """
    Read JSON file safely.
    """

    try:

        with open(path, "r") as f:
            return json.load(f)

    except (FileNotFoundError, json.JSONDecodeError):

        return None

    except Exception as e:

        print(f"\n[ERROR] Reading {path}: {e}")

        return None


# ============================================================
# RULE ENGINE
# ============================================================

def calculate_rule_risk(aircraft):
    """
    Calculate rule-based risk score.

    Maximum score = 100.

    Rules:

    CHECK / data-quality related indicators
    Time gap
    Altitude change
    Speed change
    Heading change
    Calculated speed
    Acceleration
    Position jump
    """

    score = 0.0

    reasons = []

    # --------------------------------------------------------
    # Extract features
    # --------------------------------------------------------

    time_delta = safe_float(
        aircraft.get("time_delta_s")
    )

    altitude_change = abs(
        safe_float(
            aircraft.get("altitude_change_m")
        )
    )

    speed_change = abs(
        safe_float(
            aircraft.get("speed_change_mps")
        )
    )

    heading_change = abs(
        safe_float(
            aircraft.get("heading_change_deg")
        )
    )

    calculated_speed = safe_float(
        aircraft.get("calculated_speed_mps")
    )

    acceleration = abs(
        safe_float(
            aircraft.get("acceleration_mps2")
        )
    )

    distance = safe_float(
        aircraft.get("distance_from_previous_m")
    )

    # --------------------------------------------------------
    # Rule 1 — Large time gap
    # --------------------------------------------------------

    if time_delta > TIME_GAP_WARNING:

        score += 20

        reasons.append(
            "LARGE_TIME_GAP"
        )

    # --------------------------------------------------------
    # Rule 2 — Large altitude change
    # --------------------------------------------------------

    if altitude_change > ALTITUDE_CHANGE_WARNING:

        score += 30

        reasons.append(
            "LARGE_ALTITUDE_CHANGE"
        )

    # --------------------------------------------------------
    # Rule 3 — Large speed change
    # --------------------------------------------------------

    if speed_change > SPEED_CHANGE_WARNING:

        score += 20

        reasons.append(
            "LARGE_SPEED_CHANGE"
        )

    # --------------------------------------------------------
    # Rule 4 — Large heading change
    # --------------------------------------------------------

    if heading_change > HEADING_CHANGE_WARNING:

        score += 20

        reasons.append(
            "LARGE_HEADING_CHANGE"
        )

    # --------------------------------------------------------
    # Rule 5 — Unrealistic calculated speed
    # --------------------------------------------------------

    if calculated_speed > CALCULATED_SPEED_WARNING:

        score += 30

        reasons.append(
            "HIGH_CALCULATED_SPEED"
        )

    # --------------------------------------------------------
    # Rule 6 — High acceleration
    # --------------------------------------------------------

    if acceleration > ACCELERATION_WARNING:

        score += 20

        reasons.append(
            "HIGH_ACCELERATION"
        )

    # --------------------------------------------------------
    # Rule 7 — Large position jump
    # --------------------------------------------------------

    if distance > POSITION_JUMP_WARNING:

        score += 30

        reasons.append(
            "LARGE_POSITION_JUMP"
        )

    # --------------------------------------------------------
    # Cap score
    # --------------------------------------------------------

    score = min(score, 100.0)

    # --------------------------------------------------------
    # No rules triggered
    # --------------------------------------------------------

    if not reasons:

        reasons.append(
            "NO_MAJOR_RULE_TRIGGER"
        )

    return score, reasons


# ============================================================
# RISK CLASSIFICATION
# ============================================================

def classify_risk(score):
    """
    Convert numerical score into risk level.
    """

    if score >= ANOMALY_THRESHOLD:

        return "ANOMALY"

    elif score >= MONITOR_THRESHOLD:

        return "MONITOR"

    else:

        return "NORMAL"


# ============================================================
# ML RESULT VALIDATION
# ============================================================

def ml_result_is_recent(ml_result, current_timestamp):
    """
    Check whether ML result is recent enough.
    """

    if not ml_result:

        return False

    ml_timestamp = ml_result.get("timestamp")

    if ml_timestamp is None:

        return True

    ml_timestamp = safe_float(
        ml_timestamp,
        None
    )

    if ml_timestamp is None:

        return False

    age = current_timestamp - ml_timestamp

    return age <= MAX_ML_AGE_SECONDS


# ============================================================
# EXPLANATION GENERATOR
# ============================================================

def generate_explanation(
    rule_score,
    ml_score,
    final_score,
    rule_reasons,
    ml_class,
    ml_available,
    fusion_indicators
):
    """
    Generate human-readable explanation.
    """

    explanations = []

    # --------------------------------------------------------
    # Rule explanations
    # --------------------------------------------------------

    for reason in rule_reasons:

        if reason != "NO_MAJOR_RULE_TRIGGER":

            explanations.append(reason)

    # --------------------------------------------------------
    # ML explanation
    # --------------------------------------------------------

    if ml_available:

        if ml_class == "ANOMALY":

            explanations.append(
                "ML_ANOMALY_INDICATOR"
            )

        elif ml_class == "MONITOR":

            explanations.append(
                "ML_MONITOR_INDICATOR"
            )

    else:

        explanations.append(
            "ML_UNAVAILABLE"
        )

    # --------------------------------------------------------
    # Fusion indicators
    # --------------------------------------------------------

    for indicator in fusion_indicators:

        if indicator not in explanations:

            explanations.append(indicator)

    # --------------------------------------------------------
    # Final fallback
    # --------------------------------------------------------

    if not explanations:

        explanations.append(
            "NO_SIGNIFICANT_ANOMALY"
        )

    return explanations


# ============================================================
# FUSION
# ============================================================

def process_aircraft(
    aircraft,
    ml_result,
    current_timestamp
):
    """
    Combine rule-based and ML evidence.
    """

    # --------------------------------------------------------
    # Rule score
    # --------------------------------------------------------

    rule_score, rule_reasons = calculate_rule_risk(
        aircraft
    )

    # --------------------------------------------------------
    # ML defaults
    # --------------------------------------------------------

    ml_available = False

    ml_score = 0.0

    ml_class = "UNAVAILABLE"

    ml_decision = None

    ml_prediction = None

    fusion_indicators = []

    # --------------------------------------------------------
    # Read ML result
    # --------------------------------------------------------

    if (
        ml_result is not None
        and ml_result_is_recent(
            ml_result,
            current_timestamp
        )
    ):

        ml_available = bool(
            ml_result.get(
                "ml_available",
                True
            )
        )

        # ====================================================
        # IMPORTANT:
        # These names match realtime_ml_detector.py
        # ====================================================

        ml_score = safe_float(
            ml_result.get(
                "ml_anomaly_score",
                0
            )
        )

        ml_class = ml_result.get(
            "ml_classification",
            "NORMAL"
        )

        ml_decision = ml_result.get(
            "decision_function"
        )

        ml_prediction = ml_result.get(
            "prediction"
        )

    # --------------------------------------------------------
    # ML unavailable
    # --------------------------------------------------------

    if not ml_available:

        final_score = rule_score

        fusion_indicators.append(
            "ML_UNAVAILABLE"
        )

    else:

        # ----------------------------------------------------
        # Weighted fusion
        # ----------------------------------------------------

        final_score = (
            rule_score * RULE_WEIGHT
            +
            ml_score * ML_WEIGHT
        )

        # ----------------------------------------------------
        # Evidence agreement
        # ----------------------------------------------------

        if (
            rule_score >= MONITOR_THRESHOLD
            and ml_score >= 70
        ):

            final_score += 10

            fusion_indicators.append(
                "RULE_ML_AGREEMENT"
            )

        # ----------------------------------------------------
        # Strong rule evidence
        # ----------------------------------------------------

        if (
            rule_score >= 70
            and ml_score < 50
        ):

            final_score = max(
                final_score,
                70
            )

            fusion_indicators.append(
                "RULE_DOMINANT_EVIDENCE"
            )

        # ----------------------------------------------------
        # Strong ML evidence
        # ----------------------------------------------------

        if (
            ml_score >= 80
            and rule_score < 50
        ):

            final_score = max(
                final_score,
                70
            )

            fusion_indicators.append(
                "ML_PATTERN_INDICATOR"
            )

        # ----------------------------------------------------
        # ML monitor indicator
        # ----------------------------------------------------

        if ml_class == "MONITOR":

            fusion_indicators.append(
                "ML_MONITOR_INDICATOR"
            )

        # ----------------------------------------------------
        # ML anomaly indicator
        # ----------------------------------------------------

        if ml_class == "ANOMALY":

            fusion_indicators.append(
                "ML_ANOMALY_INDICATOR"
            )

    # --------------------------------------------------------
    # Cap final score
    # --------------------------------------------------------

    final_score = min(
        max(final_score, 0.0),
        100.0
    )

    # --------------------------------------------------------
    # Final classification
    # --------------------------------------------------------

    risk_level = classify_risk(
        final_score
    )

    # --------------------------------------------------------
    # Explanation
    # --------------------------------------------------------

    explanations = generate_explanation(
        rule_score=rule_score,
        ml_score=ml_score,
        final_score=final_score,
        rule_reasons=rule_reasons,
        ml_class=ml_class,
        ml_available=ml_available,
        fusion_indicators=fusion_indicators
    )

    # --------------------------------------------------------
    # Output
    # --------------------------------------------------------

    result = {

        "icao": aircraft.get(
            "icao"
        ),

        "callsign": aircraft.get(
            "callsign",
            ""
        ),

        "timestamp": current_timestamp,

        # -----------------------------------------------
        # Position
        # -----------------------------------------------

        "latitude": aircraft.get(
            "latitude"
        ),

        "longitude": aircraft.get(
            "longitude"
        ),

        "altitude_ft": aircraft.get(
            "altitude_ft"
        ),

        "speed_kt": aircraft.get(
            "speed_kt"
        ),

        "heading_deg": aircraft.get(
            "heading_deg"
        ),

        # -----------------------------------------------
        # Trajectory features
        # -----------------------------------------------

        "distance_from_previous_m": safe_float(
            aircraft.get(
                "distance_from_previous_m"
            )
        ),

        "time_delta_s": safe_float(
            aircraft.get(
                "time_delta_s"
            )
        ),

        "altitude_change_m": safe_float(
            aircraft.get(
                "altitude_change_m"
            )
        ),

        "speed_change_mps": safe_float(
            aircraft.get(
                "speed_change_mps"
            )
        ),

        "heading_change_deg": safe_float(
            aircraft.get(
                "heading_change_deg"
            )
        ),

        "calculated_speed_mps": safe_float(
            aircraft.get(
                "calculated_speed_mps"
            )
        ),

        "acceleration_mps2": safe_float(
            aircraft.get(
                "acceleration_mps2"
            )
        ),

        # -----------------------------------------------
        # Rule engine
        # -----------------------------------------------

        "rule_score": round(
            rule_score,
            2
        ),

        "rule_reasons": rule_reasons,

        # -----------------------------------------------
        # ML engine
        # -----------------------------------------------

        "ml_available": ml_available,

        "ml_score": round(
            ml_score,
            2
        ),

        "ml_class": ml_class,

        "ml_decision": (
            safe_float(
                ml_decision
            )
            if ml_decision is not None
            else None
        ),

        "ml_prediction": ml_prediction,

        # -----------------------------------------------
        # Fusion
        # -----------------------------------------------

        "final_score": round(
            final_score,
            2
        ),

        "risk_level": risk_level,

        "fusion_indicators": fusion_indicators,

        "explanation": explanations
    }

    return result


# ============================================================
# MAIN FUSION LOOP
# ============================================================

def main():

    print("=" * 75)

    print(
        "SKYGUARDIAN — REALTIME FUSION ENGINE"
    )

    print(
        "Rule Engine + Edge AI + Evidence Fusion"
    )

    print("=" * 75)

    print(
        f"Trajectory : {TRAJECTORY_FILE}"
    )

    print(
        f"ML Results : {ML_FILE}"
    )

    print(
        f"Output     : {OUTPUT_FILE}"
    )

    print(
        f"Rule Weight: {RULE_WEIGHT}"
    )

    print(
        f"ML Weight  : {ML_WEIGHT}"
    )

    print("-" * 75)

    while True:

        # ----------------------------------------------------
        # Read trajectory
        # ----------------------------------------------------

        trajectory_data = read_json(
            TRAJECTORY_FILE
        )

        # ----------------------------------------------------
        # Read ML
        # ----------------------------------------------------

        ml_data = read_json(
            ML_FILE
        )

        # ----------------------------------------------------
        # If trajectory unavailable
        # ----------------------------------------------------

        if trajectory_data is None:

            print(
                "\r[FUSION] Waiting for trajectory data...",
                end="",
                flush=True
            )

            time.sleep(
                UPDATE_INTERVAL
            )

            continue

        # ----------------------------------------------------
        # Current timestamp
        # ----------------------------------------------------

        current_timestamp = safe_float(
            trajectory_data.get(
                "timestamp",
                time.time()
            ),
            time.time()
        )

        # ----------------------------------------------------
        # ML aircraft lookup
        # ----------------------------------------------------

        ml_aircraft_lookup = {}

        if ml_data is not None:

            for ml_aircraft in ml_data.get(
                "aircraft",
                []
            ):

                icao = ml_aircraft.get(
                    "icao"
                )

                if icao:

                    ml_aircraft_lookup[
                        icao
                    ] = ml_aircraft

        # ----------------------------------------------------
        # Process aircraft
        # ----------------------------------------------------

        current_results = {}

        aircraft_list = trajectory_data.get(
            "aircraft",
            []
        )

        for aircraft in aircraft_list:

            icao = aircraft.get(
                "icao"
            )

            if not icao:

                continue

            # ------------------------------------------------
            # Find ML result for aircraft
            # ------------------------------------------------

            ml_result = ml_aircraft_lookup.get(
                icao
            )

            # ------------------------------------------------
            # Process
            # ------------------------------------------------

            result = process_aircraft(
                aircraft,
                ml_result,
                current_timestamp
            )

            current_results[
                icao
            ] = result

        # ----------------------------------------------------
        # Replace latest results
        # ----------------------------------------------------

        latest_results = current_results

        # ----------------------------------------------------
        # Output JSON
        # ----------------------------------------------------

        output = {

            "timestamp": current_timestamp,

            "aircraft_count": len(
                latest_results
            ),

            "summary": {

                "normal": 0,

                "monitor": 0,

                "anomaly": 0
            },

            "aircraft": list(
                latest_results.values()
            )
        }

        # ----------------------------------------------------
        # Summary counts
        # ----------------------------------------------------

        for result in latest_results.values():

            risk = result.get(
                "risk_level",
                "NORMAL"
            )

            if risk == "ANOMALY":

                output["summary"][
                    "anomaly"
                ] += 1

            elif risk == "MONITOR":

                output["summary"][
                    "monitor"
                ] += 1

            else:

                output["summary"][
                    "normal"
                ] += 1

        # ----------------------------------------------------
        # Atomic file write
        # ----------------------------------------------------

        temp_file = OUTPUT_FILE.with_suffix(
            ".tmp"
        )

        try:

            with open(
                temp_file,
                "w"
            ) as f:

                json.dump(
                    output,
                    f,
                    indent=2
                )

            temp_file.replace(
                OUTPUT_FILE
            )

        except Exception as e:

            print(
                f"\n[ERROR] Writing output: {e}"
            )

        # ----------------------------------------------------
        # Console status
        # ----------------------------------------------------

        summary = output[
            "summary"
        ]

        print(
            "\r"
            f"[FUSION] "
            f"Aircraft: {output['aircraft_count']:3d} | "
            f"NORMAL: {summary['normal']:3d} | "
            f"MONITOR: {summary['monitor']:3d} | "
            f"ANOMALY: {summary['anomaly']:3d}",
            end="",
            flush=True
        )

        # ----------------------------------------------------
        # Print important detections
        # ----------------------------------------------------

        for result in latest_results.values():

            if result["risk_level"] in (
                "MONITOR",
                "ANOMALY"
            ):

                print()

                print(
                    f"[{result['risk_level']}] "
                    f"{result['icao']} "
                    f"{result['callsign']}"
                )

                print(
                    f"  Final Score : "
                    f"{result['final_score']:.2f}"
                )

                print(
                    f"  Rule Score  : "
                    f"{result['rule_score']:.2f}"
                )

                print(
                    f"  ML Score    : "
                    f"{result['ml_score']:.2f}"
                )

                print(
                    f"  ML Class    : "
                    f"{result['ml_class']}"
                )

                print(
                    f"  Reasons     : "
                    f"{', '.join(result['explanation'])}"
                )

        time.sleep(
            UPDATE_INTERVAL
        )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    try:

        main()

    except KeyboardInterrupt:

        print(
            "\n\n[FUSION] Stopped."
        )
