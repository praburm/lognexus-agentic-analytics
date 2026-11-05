import json
import sys
import os

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "mcp-pipeline"))

from mcp.mcp_server import (
    fetch_sample_logs,
    parse_and_detect_anomalies,
    semantic_analysis,
    correlate_alerts,
    root_cause_analysis,
)


def _json(raw: str) -> dict:
    return json.loads(raw)


class TestFetchSampleLogs:
    def test_returns_known_scenarios(self):
        for scenario in ("error_spike", "timeout_spike", "normal", "complex_incident"):
            result = _json(fetch_sample_logs(scenario))
            assert result["scenario"] == scenario
            assert result["log_count"] > 0
            assert "logs" in result

    def test_unknown_scenario_returns_error(self):
        result = _json(fetch_sample_logs("does_not_exist"))
        assert "error" in result
        assert "available" in result


class TestParseAndDetectAnomalies:
    def _logs_for(self, scenario: str) -> str:
        return _json(fetch_sample_logs(scenario))["logs"]

    def test_error_spike_triggers_alert(self):
        result = _json(parse_and_detect_anomalies(self._logs_for("error_spike")))
        types = {a["type"] for a in result["alerts"]}
        assert "ErrorSpike" in types

    def test_timeout_spike_triggers_alert(self):
        result = _json(parse_and_detect_anomalies(self._logs_for("timeout_spike")))
        types = {a["type"] for a in result["alerts"]}
        assert "TimeoutSpike" in types

    def test_normal_logs_are_healthy(self):
        quiet_logs = "\n".join([
            json.dumps({"level": "info", "service": "api-gateway", "message": "health check OK"})
            for _ in range(5)
        ])
        result = _json(parse_and_detect_anomalies(quiet_logs))
        assert result["stats"]["is_healthy"] is True
        assert result["stats"]["alert_count"] == 0

    def test_complex_incident_has_multiple_alerts(self):
        result = _json(parse_and_detect_anomalies(self._logs_for("complex_incident")))
        assert result["stats"]["alert_count"] >= 2

    def test_stats_fields_present(self):
        result = _json(parse_and_detect_anomalies(self._logs_for("error_spike")))
        for field in ("total_logs", "error_count", "timeout_count", "alert_count", "is_healthy"):
            assert field in result["stats"]

    def test_empty_input_returns_healthy(self):
        result = _json(parse_and_detect_anomalies(""))
        assert result["stats"]["is_healthy"] is True

    def test_plain_text_logs_parse_without_crash(self):
        plain = "error: something went wrong\ninfo: all good\nerror: another failure"
        result = _json(parse_and_detect_anomalies(plain))
        assert "stats" in result


class TestSemanticAnalysis:
    def _logs_for(self, scenario: str) -> str:
        return _json(fetch_sample_logs(scenario))["logs"]

    def test_summary_fields_present(self):
        result = _json(semantic_analysis(self._logs_for("error_spike")))
        for field in ("total_analyzed", "avg_novelty_score", "avg_anomaly_score",
                      "avg_semantic_confidence", "high_anomaly_count"):
            assert field in result["summary"]

    def test_error_spike_has_high_anomaly_entries(self):
        result = _json(semantic_analysis(self._logs_for("error_spike")))
        assert result["summary"]["high_anomaly_count"] > 0

    def test_scores_in_valid_range(self):
        result = _json(semantic_analysis(self._logs_for("complex_incident")))
        for entry in result["enriched_logs"]:
            assert 0.0 <= entry["novelty_score"] <= 1.0
            assert 0.0 <= entry["anomaly_score"] <= 1.0

    def test_pattern_ids_are_unique_format(self):
        result = _json(semantic_analysis(self._logs_for("error_spike")))
        for entry in result["enriched_logs"]:
            assert entry["pattern_id"].startswith("PAT-")

    def test_empty_input_returns_error(self):
        result = _json(semantic_analysis(""))
        assert "error" in result


class TestCorrelateAlerts:
    def _alerts_for(self, scenario: str) -> str:
        logs = _json(fetch_sample_logs(scenario))["logs"]
        return parse_and_detect_anomalies(logs)

    def test_error_spike_creates_incident(self):
        result = _json(correlate_alerts(self._alerts_for("error_spike")))
        assert result.get("status") == "open"
        assert "incident_id" in result
        assert result["severity"] in ("low", "medium", "high", "critical")

    def test_complex_incident_is_critical(self):
        result = _json(correlate_alerts(self._alerts_for("complex_incident")))
        assert result.get("status") == "open"
        assert result["severity"] in ("high", "critical")

    def test_healthy_logs_return_healthy_status(self):
        quiet_logs = "\n".join([
            json.dumps({"level": "info", "service": "api-gateway", "message": "health check OK"})
            for _ in range(5)
        ])
        alerts = parse_and_detect_anomalies(quiet_logs)
        result = _json(correlate_alerts(alerts))
        assert result.get("status") == "healthy"

    def test_invalid_json_returns_error(self):
        result = _json(correlate_alerts("not json at all"))
        assert "error" in result

    def test_incident_id_has_expected_prefix(self):
        result = _json(correlate_alerts(self._alerts_for("timeout_spike")))
        if result.get("status") == "open":
            assert result["incident_id"].startswith("INC-")


class TestRootCauseAnalysis:
    def _incident_for(self, scenario: str) -> str:
        logs = _json(fetch_sample_logs(scenario))["logs"]
        alerts = parse_and_detect_anomalies(logs)
        return correlate_alerts(alerts)

    def test_application_category_produces_rca(self):
        incident = self._incident_for("error_spike")
        result = _json(root_cause_analysis(incident))
        assert len(result["rule_based_rca"]) > 0
        assert result["overall_confidence"] > 0

    def test_dependency_category_produces_rca(self):
        incident = self._incident_for("timeout_spike")
        if _json(incident).get("status") == "open":
            result = _json(root_cause_analysis(incident))
            assert any("dependency" in r.get("cause", "").lower() or
                       "downstream" in r.get("cause", "").lower()
                       for r in result["rule_based_rca"])

    def test_rca_fields_present(self):
        incident = self._incident_for("error_spike")
        if _json(incident).get("status") == "open":
            result = _json(root_cause_analysis(incident))
            for field in ("incident_id", "severity", "rule_based_rca",
                          "overall_confidence", "priority_action", "analyzed_at"):
                assert field in result

    def test_recommended_actions_are_non_empty(self):
        incident = self._incident_for("complex_incident")
        if _json(incident).get("status") == "open":
            result = _json(root_cause_analysis(incident))
            for cause in result["rule_based_rca"]:
                assert len(cause["recommended_actions"]) > 0

    def test_invalid_json_returns_error(self):
        result = _json(root_cause_analysis("{{broken"))
        assert "error" in result

    def test_confidence_bounded(self):
        incident = self._incident_for("error_spike")
        if _json(incident).get("status") == "open":
            result = _json(root_cause_analysis(incident))
            assert 0.0 <= result["overall_confidence"] <= 1.0
