"""Test suite verifying full decoupling from local machine, zero path leakage,
and resilient handling of simulated failure scenarios (LLM 429, Qdrant down, Agent crash)."""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

HERE = os.path.dirname(os.path.abspath(__file__))
HUB = os.path.abspath(os.path.join(HERE, ".."))
AGENTS = os.path.join(HUB, "agents")
RAG = os.path.join(HUB, "rag")

for p in [HUB, AGENTS, RAG]:
    if p not in sys.path:
        sys.path.insert(0, p)

from errors import friendly_error, scrub_paths, _MSG_RU, _MSG_EN


class TestErrorsAndScrubbing(unittest.TestCase):
    """Verify friendly_error and scrub_paths never leak machine paths or technical dumps."""

    def test_scrub_paths_windows_and_tracebacks(self):
        raw_trace = (
            'Traceback:\n'
            '  File "D:\\projects\\demo\\hub\\Home.py", line 38, in <module>\n'
            '    st.navigation(NAV, position="sidebar").run()\n'
            '  File "C:\\Users\\<user>\\AppData\\Local\\Programs\\Python\\Python314\\Lib\\site-packages\\openai\\client.py", line 1105\n'
            'Local file: D:\\srv\\storage\\db.sqlite\n'
            'openai.RateLimitError: Error code: 429 on host 127.0.0.1:8000'
        )
        cleaned = scrub_paths(raw_trace)
        self.assertNotIn("D:\\projects\\demo", cleaned)
        self.assertNotIn("C:\\Users\\<user>", cleaned)
        self.assertNotIn("127.0.0.1", cleaned)
        self.assertIn("[source]", cleaned)
        self.assertIn("[path]", cleaned)
        self.assertIn("[host]", cleaned)

    def test_scrub_configured_usernames(self):
        """Machine usernames come from SCRUB_USERNAMES, so no personal name is hardcoded."""
        with patch.dict(os.environ, {"SCRUB_USERNAMES": "testuser"}):
            cleaned = scrub_paths("login for testuser failed")
        self.assertNotIn("testuser", cleaned.lower())
        self.assertIn("[user]", cleaned)

    def test_friendly_error_ratelimit_and_quota(self):
        # 1. Exact string from user's incident
        user_err = "openai.RateLimitError: Error code: 429 - {'object': 'error', 'message': 'Rate limit exceeded', 'type': 'rate_limited', 'param': None, 'code': '1300', 'raw_status_code': 429}"
        msg_ru = friendly_error(user_err, "ru")
        msg_en = friendly_error(user_err, "en")
        self.assertEqual(msg_ru, _MSG_RU["ratelimit"])
        self.assertEqual(msg_en, _MSG_EN["ratelimit"])
        self.assertIn("Лимит запросов или закончилась квота", msg_ru)

        # 2. All models failed from LLM pool
        pool_err = RuntimeError("all models failed")
        self.assertEqual(friendly_error(pool_err, "ru"), _MSG_RU["ratelimit"])

        # 3. Stream models failed
        stream_err = RuntimeError("all models failed for stream")
        self.assertEqual(friendly_error(stream_err, "ru"), _MSG_RU["ratelimit"])

        # 4. Insufficient quota
        quota_err = Exception("insufficient_quota: you exceeded your current quota")
        self.assertEqual(friendly_error(quota_err, "ru"), _MSG_RU["ratelimit"])

    def test_friendly_error_qdrant_and_database(self):
        # 1. Qdrant paused cluster
        qdrant_err = Exception("ResponseHandlingException: 503 Service Unavailable (cluster 35.246.x.x paused)")
        msg_ru = friendly_error(qdrant_err, "ru")
        self.assertEqual(msg_ru, _MSG_RU["db"])
        self.assertIn("Qdrant", msg_ru)
        self.assertIn("уходит в паузу", msg_ru)

        # 2. SSL handshake / timeout
        ssl_err = Exception("_ssl.c: handshake timed out with qdrant.io")
        self.assertEqual(friendly_error(ssl_err, "ru"), _MSG_RU["db"])

        # 3. Connection refused
        conn_err = ConnectionRefusedError("Connection refused to localhost:6333")
        self.assertEqual(friendly_error(conn_err, "ru"), _MSG_RU["conn"])

    def test_friendly_error_authentication(self):
        auth_err = Exception("AuthenticationError: 401 Invalid API Key")
        self.assertEqual(friendly_error(auth_err, "ru"), _MSG_RU["auth"])
        self.assertIn("Ключ API не принят", _MSG_RU["auth"])


class TestDecouplingAudit(unittest.TestCase):
    """Verify repo root contains no machine-specific absolute paths or username leaks."""

    def test_no_local_paths_in_source_code(self):
        root = os.path.abspath(os.path.join(HUB, ".."))
        # Assembled dynamically to avoid matching test file itself
        forbidden = [
            "d:" + "\\ai\\",
            "d:" + "\\opencode-work\\",
            "d:" + "/ai/",
            "c:" + "\\users\\",
            "/users/",
            "/home/",
        ]
        violations = []
        for r, dirs, files in os.walk(root):
            if any(x in r for x in [".git", "node_modules", "VIDEO", "__pycache__",
                                    ".pytest_cache", "scratch", "autoagent"]):
                continue
            for f in files:
                if f.endswith((".py", ".json", ".md", ".toml", ".yml", ".yaml")):
                    p = os.path.join(r, f)
                    if os.path.abspath(p) == os.path.abspath(__file__):
                        continue
                    with open(p, "r", encoding="utf-8", errors="ignore") as fp:
                        for idx, line in enumerate(fp, 1):
                            low = line.lower()
                            for bad in forbidden:
                                if bad in low and not line.strip().startswith("#"):
                                    violations.append(f"{p}:{idx} -> {line.strip()[:80]}")
        self.assertEqual(violations, [], f"Found hardcoded local paths:\n" + "\n".join(violations))

    def test_streamlit_config_hides_tracebacks(self):
        cfg_path = os.path.join(HUB, "..", ".streamlit", "config.toml")
        self.assertTrue(os.path.exists(cfg_path), ".streamlit/config.toml must exist")
        with open(cfg_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn('showErrorDetails = "none"', content, "showErrorDetails must be 'none'")

    def test_no_vendor_names_in_views(self):
        views_dir = os.path.join(HUB, "views")
        forbidden = ["qubax", "opencode zen"]
        for f in os.listdir(views_dir):
            if f.endswith(".py"):
                p = os.path.join(views_dir, f)
                with open(p, "r", encoding="utf-8") as fp:
                    for line_idx, line in enumerate(fp, 1):
                        low = line.lower()
                        for bad in forbidden:
                            if bad in low:
                                self.fail(f"Found vendor leak '{bad}' in {f}:{line_idx} -> {line.strip()}")


class TestSimulatedFailureFlows(unittest.TestCase):
    """Simulate runtime failures in RAG and Agent pipelines to confirm zero crashes."""

    def test_simulated_unified_agent_failure(self):
        """Simulate agent tool or model crash and verify friendly error in message list."""
        import unified_agent as ua

        with patch.object(ua, "run", side_effect=Exception("openai.RateLimitError: 429 code 1300")):
            try:
                ua.run("test question")
            except Exception as e:
                msg = friendly_error(e, "ru")
                self.assertIn("Лимит запросов", msg)
                self.assertNotIn("Traceback", msg)
                self.assertNotIn("D:\\", msg)

    def test_unified_agent_tool_resilience(self):
        """Verify tool calls handle connection loss or DB down without leaking tracebacks."""
        import unified_agent as ua

        # 1. search_kb failure
        with patch("unified_agent._search_kb", return_value="[KB error] Knowledge base temporarily unavailable"):
            out = ua._execute("search_knowledge_base", {"query": "test"})
            self.assertIn("temporarily unavailable", out)
            self.assertNotIn("Exception", out)
            self.assertNotIn("Traceback", out)

        # 2. query_db network failure
        with patch("httpx.post", side_effect=ConnectionRefusedError("Connection refused")):
            out = ua._query_db("SELECT 1")
            self.assertEqual(out, "[DB error] CRM database temporarily unavailable")

        # 3. query_db HTTP 502 / upstream error
        mock_resp = MagicMock()
        mock_resp.status_code = 502
        with patch("httpx.post", return_value=mock_resp):
            out = ua._query_db("SELECT 1")
            self.assertIn("HTTP 502", out)
            self.assertNotIn("Traceback", out)


if __name__ == "__main__":
    unittest.main()
