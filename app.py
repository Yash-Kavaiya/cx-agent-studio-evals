"""
CX Agent Studio Evaluations Dashboard — Flask Backend
Covers: evaluationDatasets, evaluationExpectations, evaluationRuns,
        evaluations, evaluation results, scheduledEvaluationRuns
"""

from flask import Flask, render_template, jsonify, request
import uuid, random, datetime, json

app = Flask(__name__)

# ──────────────────────────────────────────────────────────
# Mock data generators
# ──────────────────────────────────────────────────────────

def _ts(days_ago=0):
    dt = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=days_ago)
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")

def _id():
    return uuid.uuid4().hex[:12]

# --- Evaluation Datasets ---
DATASETS = [
    {"name": f"projects/gai-guru/locations/us-central1/apps/cymbal-cars/evaluationDatasets/ds-{i}",
     "displayName": name,
     "description": desc,
     "evaluationCount": random.randint(5, 40),
     "createTime": _ts(random.randint(10, 90)),
     "updateTime": _ts(random.randint(0, 9))}
    for i, (name, desc) in enumerate([
        ("Golden – Service Center", "Golden test cases for service center lookup agent"),
        ("Scenario – Appointment Booking", "End-to-end appointment booking scenarios"),
        ("Golden – Parts Ordering", "Parts ordering golden conversations"),
        ("Scenario – Complaint Escalation", "Escalation path scenario tests"),
        ("Golden – Vehicle Recall", "Vehicle recall notification golden tests"),
        ("Scenario – Payment Processing", "Payment flow scenario evaluations"),
    ])
]

# --- Evaluations ---
EVAL_TYPES = ["GOLDEN", "SCENARIO"]
EVAL_STATUSES = ["PASSED", "FAILED", "PARTIAL"]
EVALUATIONS = []
for i in range(12):
    etype = random.choice(EVAL_TYPES)
    EVALUATIONS.append({
        "name": f"projects/gai-guru/locations/us-central1/apps/cymbal-cars/evaluations/eval-{_id()}",
        "displayName": f"{'Golden' if etype == 'GOLDEN' else 'Scenario'} Eval #{i+1}",
        "evaluationType": etype,
        "datasetName": random.choice(DATASETS)["name"],
        "status": random.choice(EVAL_STATUSES),
        "passRate": round(random.uniform(0.55, 1.0), 3),
        "turnCount": random.randint(3, 20),
        "createTime": _ts(random.randint(1, 60)),
        "updateTime": _ts(random.randint(0, 5)),
    })

# --- Evaluation Runs ---
RUN_STATES = ["COMPLETED", "RUNNING", "FAILED", "QUEUED"]
EVAL_RUNS = []
for i in range(18):
    state = random.choices(RUN_STATES, weights=[60, 15, 10, 15])[0]
    EVAL_RUNS.append({
        "name": f"projects/gai-guru/locations/us-central1/apps/cymbal-cars/evaluationRuns/run-{_id()}",
        "evaluationName": random.choice(EVALUATIONS)["name"],
        "state": state,
        "progress": {"completedCount": random.randint(1, 40), "totalCount": 40} if state != "QUEUED" else {"completedCount": 0, "totalCount": 40},
        "passRate": round(random.uniform(0.5, 1.0), 3) if state == "COMPLETED" else None,
        "duration": f"{random.randint(12, 300)}s" if state == "COMPLETED" else None,
        "createTime": _ts(random.randint(0, 30)),
    })

# --- Evaluation Expectations ---
EXPECTATIONS = []
for i in range(8):
    EXPECTATIONS.append({
        "name": f"projects/gai-guru/locations/us-central1/apps/cymbal-cars/evaluationExpectations/exp-{_id()}",
        "displayName": random.choice([
            "Agent greets user", "Tool invoked correctly", "No hallucination",
            "Escalation triggered", "Session var set", "Guardrail blocks abuse",
            "Correct service center returned", "Appointment confirmed"
        ]),
        "type": random.choice(["LLM_CRITERIA", "TOOL_EXPECTATION"]),
        "llmCriteria": {"criteria": "Agent response is polite and factual"} if random.random() > 0.5 else None,
        "createTime": _ts(random.randint(5, 60)),
    })

# --- Evaluation Results ---
RESULTS = []
for run in EVAL_RUNS:
    if run["state"] == "COMPLETED":
        for j in range(random.randint(2, 6)):
            RESULTS.append({
                "name": run["name"].replace("evaluationRuns", "evaluations") + f"/results/res-{_id()}",
                "runName": run["name"],
                "outcome": random.choice(["PASSED", "FAILED"]),
                "semanticSimilarity": round(random.uniform(0.6, 1.0), 3),
                "hallucinationDetected": random.choice([True, False]),
                "toolCallMatch": random.choice([True, False, True, True]),
                "latencyMs": random.randint(200, 4500),
                "turnCount": random.randint(2, 12),
            })

# --- Scheduled Evaluation Runs ---
SCHEDULED = [
    {"name": f"projects/gai-guru/locations/us-central1/apps/cymbal-cars/scheduledEvaluationRuns/sched-{_id()}",
     "displayName": f"Nightly {t}", "schedule": f"0 {h} * * *",
     "evaluationName": random.choice(EVALUATIONS)["name"],
     "enabled": random.choice([True, True, False]),
     "lastRunTime": _ts(random.randint(0, 2)),
     "nextRunTime": _ts(-1)}
    for t, h in [("Golden Suite", 2), ("Scenario Suite", 3), ("Regression", 4), ("Smoke Test", 6)]
]

# ──────────────────────────────────────────────────────────
# Aggregate stats
# ──────────────────────────────────────────────────────────

def compute_stats():
    total_runs = len(EVAL_RUNS)
    completed = [r for r in EVAL_RUNS if r["state"] == "COMPLETED"]
    running = [r for r in EVAL_RUNS if r["state"] == "RUNNING"]
    failed_runs = [r for r in EVAL_RUNS if r["state"] == "FAILED"]
    avg_pass = round(sum(r["passRate"] for r in completed if r["passRate"]) / max(len(completed), 1), 3)
    total_results = len(RESULTS)
    passed_results = len([r for r in RESULTS if r["outcome"] == "PASSED"])
    hallucinations = len([r for r in RESULTS if r["hallucinationDetected"]])
    avg_latency = round(sum(r["latencyMs"] for r in RESULTS) / max(len(RESULTS), 1))
    avg_similarity = round(sum(r["semanticSimilarity"] for r in RESULTS) / max(len(RESULTS), 1), 3)

    # Pass rate by day (last 7 days)
    pass_rate_trend = []
    for d in range(6, -1, -1):
        day_label = (datetime.datetime.now() - datetime.timedelta(days=d)).strftime("%b %d")
        pass_rate_trend.append({"day": day_label, "rate": round(random.uniform(0.65, 0.98), 3)})

    # Type distribution
    golden_count = len([e for e in EVALUATIONS if e["evaluationType"] == "GOLDEN"])
    scenario_count = len(EVALUATIONS) - golden_count

    return {
        "totalDatasets": len(DATASETS),
        "totalEvaluations": len(EVALUATIONS),
        "totalRuns": total_runs,
        "completedRuns": len(completed),
        "runningRuns": len(running),
        "failedRuns": len(failed_runs),
        "avgPassRate": avg_pass,
        "totalResults": total_results,
        "passedResults": passed_results,
        "failedResults": total_results - passed_results,
        "hallucinationCount": hallucinations,
        "avgLatencyMs": avg_latency,
        "avgSimilarity": avg_similarity,
        "totalExpectations": len(EXPECTATIONS),
        "totalScheduled": len(SCHEDULED),
        "enabledScheduled": len([s for s in SCHEDULED if s["enabled"]]),
        "passRateTrend": pass_rate_trend,
        "goldenCount": golden_count,
        "scenarioCount": scenario_count,
    }

# ──────────────────────────────────────────────────────────
# Routes
# ──────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")

# --- API: Stats ---
@app.route("/api/stats")
def api_stats():
    return jsonify(compute_stats())

# --- API: Datasets ---
@app.route("/api/datasets")
def api_datasets():
    return jsonify(DATASETS)

# --- API: Evaluations ---
@app.route("/api/evaluations")
def api_evaluations():
    return jsonify(EVALUATIONS)

# --- API: Evaluation Runs ---
@app.route("/api/runs")
def api_runs():
    return jsonify(EVAL_RUNS)

# --- API: Expectations ---
@app.route("/api/expectations")
def api_expectations():
    return jsonify(EXPECTATIONS)

# --- API: Results ---
@app.route("/api/results")
def api_results():
    run_name = request.args.get("run")
    if run_name:
        filtered = [r for r in RESULTS if r["runName"] == run_name]
        return jsonify(filtered)
    return jsonify(RESULTS)

# --- API: Scheduled Runs ---
@app.route("/api/scheduled")
def api_scheduled():
    return jsonify(SCHEDULED)

# --- API Endpoint reference ---
@app.route("/api/reference")
def api_reference():
    return jsonify({
        "resources": [
            {
                "name": "evaluationDatasets",
                "basePath": "v1beta.projects.locations.apps.evaluationDatasets",
                "methods": [
                    {"verb": "POST", "action": "create", "path": "/v1beta/{parent=projects/*/locations/*/apps/*}/evaluationDatasets"},
                    {"verb": "DELETE", "action": "delete", "path": "/v1beta/{name=projects/*/locations/*/apps/*/evaluationDatasets/*}"},
                    {"verb": "GET", "action": "get", "path": "/v1beta/{name=projects/*/locations/*/apps/*/evaluationDatasets/*}"},
                    {"verb": "GET", "action": "list", "path": "/v1beta/{parent=projects/*/locations/*/apps/*}/evaluationDatasets"},
                    {"verb": "PATCH", "action": "patch", "path": "/v1beta/{evaluationDataset.name=projects/*/locations/*/apps/*/evaluationDatasets/*}"},
                ]
            },
            {
                "name": "evaluationExpectations",
                "basePath": "v1beta.projects.locations.apps.evaluationExpectations",
                "methods": [
                    {"verb": "POST", "action": "create", "path": "/v1beta/{parent=projects/*/locations/*/apps/*}/evaluationExpectations"},
                    {"verb": "DELETE", "action": "delete", "path": "/v1beta/{name=projects/*/locations/*/apps/*/evaluationExpectations/*}"},
                    {"verb": "GET", "action": "get", "path": "/v1beta/{name=projects/*/locations/*/apps/*/evaluationExpectations/*}"},
                    {"verb": "GET", "action": "list", "path": "/v1beta/{parent=projects/*/locations/*/apps/*}/evaluationExpectations"},
                    {"verb": "PATCH", "action": "patch", "path": "/v1beta/{evaluationExpectation.name=projects/*/locations/*/apps/*/evaluationExpectations/*}"},
                ]
            },
            {
                "name": "evaluationRuns",
                "basePath": "v1beta.projects.locations.apps.evaluationRuns",
                "methods": [
                    {"verb": "DELETE", "action": "delete", "path": "/v1beta/{name=projects/*/locations/*/apps/*/evaluationRuns/*}"},
                    {"verb": "GET", "action": "get", "path": "/v1beta/{name=projects/*/locations/*/apps/*/evaluationRuns/*}"},
                    {"verb": "GET", "action": "list", "path": "/v1beta/{parent=projects/*/locations/*/apps/*}/evaluationRuns"},
                ]
            },
            {
                "name": "evaluations",
                "basePath": "v1beta.projects.locations.apps.evaluations",
                "methods": [
                    {"verb": "POST", "action": "create", "path": "/v1beta/{parent=projects/*/locations/*/apps/*}/evaluations"},
                    {"verb": "DELETE", "action": "delete", "path": "/v1beta/{name=projects/*/locations/*/apps/*/evaluations/*}"},
                    {"verb": "POST", "action": "export", "path": "/v1beta/{parent=projects/*/locations/*/apps/*}/evaluations:export"},
                    {"verb": "GET", "action": "get", "path": "/v1beta/{name=projects/*/locations/*/apps/*/evaluations/*}"},
                    {"verb": "GET", "action": "list", "path": "/v1beta/{parent=projects/*/locations/*/apps/*}/evaluations"},
                    {"verb": "PATCH", "action": "patch", "path": "/v1beta/{evaluation.name=projects/*/locations/*/apps/*/evaluations/*}"},
                    {"verb": "POST", "action": "uploadEvaluationAudio", "path": "/v1beta/{name=projects/*/locations/*/apps/*/evaluations/*}:uploadEvaluationAudio"},
                ]
            },
            {
                "name": "evaluations.results",
                "basePath": "v1beta.projects.locations.apps.evaluations.results",
                "methods": [
                    {"verb": "DELETE", "action": "delete", "path": "/v1beta/{name=projects/*/locations/*/apps/*/evaluations/*/results/*}"},
                    {"verb": "GET", "action": "get", "path": "/v1beta/{name=projects/*/locations/*/apps/*/evaluations/*/results/*}"},
                    {"verb": "GET", "action": "list", "path": "/v1beta/{parent=projects/*/locations/*/apps/*/evaluations/*}/results"},
                ]
            },
            {
                "name": "scheduledEvaluationRuns",
                "basePath": "v1beta.projects.locations.apps.scheduledEvaluationRuns",
                "methods": [
                    {"verb": "POST", "action": "create", "path": "/v1beta/{parent=projects/*/locations/*/apps/*}/scheduledEvaluationRuns"},
                    {"verb": "DELETE", "action": "delete", "path": "/v1beta/{name=projects/*/locations/*/apps/*/scheduledEvaluationRuns/*}"},
                    {"verb": "GET", "action": "get", "path": "/v1beta/{name=projects/*/locations/*/apps/*/scheduledEvaluationRuns/*}"},
                    {"verb": "GET", "action": "list", "path": "/v1beta/{parent=projects/*/locations/*/apps/*}/scheduledEvaluationRuns"},
                    {"verb": "PATCH", "action": "patch", "path": "/v1beta/{scheduledEvaluationRun.name=projects/*/locations/*/apps/*/scheduledEvaluationRuns/*}"},
                ]
            },
        ]
    })

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
