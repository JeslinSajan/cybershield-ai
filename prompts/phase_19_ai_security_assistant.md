# Phase 19 — AI Security Assistant

**Status:** Not Started  
*(Change to "Done" when this phase is complete)*

---

## Prompt

```text
CYBERSHIELD AI — PHASE 19: AI Security Assistant

Repo: https://github.com/JeslinSajan/cybershield-ai

IMPORTANT: This is NOT a cloud AI / LLM / ChatGPT integration.
This is a LOCAL rule-based explanation engine.
Label it "Local Security Explanation Engine" in the UI.
No external API calls. No paid services.

=======================================================================
WHAT TO BUILD
=======================================================================

A simple backend service that generates human-readable explanations 
for alerts, vulnerabilities, and risk scores using templates and 
the actual data from the database.

Think of it as a smart template engine, not AI.

=======================================================================
BACKEND ARCHITECTURE
=======================================================================

Create backend/app/services/ai_service.py:

  class LocalRuleAI:
      
      def explain_alert(self, alert) -> str:
          """
          Uses the alert's type, severity, source_ip, description, 
          and related device to generate a human-readable explanation.
          
          Example for BruteForce alert:
          "A brute force attack was detected from IP 192.168.1.99 
           targeting device 192.168.1.10. There were 8 failed login 
           attempts in 10 minutes. This is a High severity event. 
           Recommendation: Block IP 192.168.1.99 on your firewall and 
           review SSH access logs for any successful logins from this 
           source."
          """
      
      def explain_vulnerability(self, vulnerability) -> str:
          """
          Uses CVE ID, severity, service, version, and recommendation.
          
          Example:
          "CVE-2021-41773 was detected on device 192.168.1.10 
           (Apache 2.4.41 on port 80). This is a Critical severity 
           path traversal vulnerability that allows attackers to read 
           files outside the web root. Recommendation: Upgrade Apache 
           to version 2.4.51 or later immediately."
          """
      
      def explain_risk_score(self, risk_score, factor_breakdown) -> str:
          """
          Uses the score, band, and factor_breakdown components.
          
          Example:
          "Device 192.168.1.10 has a risk score of 60 (High). 
           The score is composed of: 30 points from 1 Critical 
           vulnerability, 20 points from 1 open Brute Force alert, 
           and 10 points from 12 open ports. Priority actions: 
           resolve the open alert and patch the Critical vulnerability."
          """

=======================================================================
BACKEND ENDPOINTS
=======================================================================

POST /api/v1/ai/explain-alert
  - Body: { "alert_id": "uuid" }
  - Returns: { "explanation": "<generated text>" }
  - All roles (read).

POST /api/v1/ai/explain-vulnerability
  - Body: { "vulnerability_id": "uuid" }
  - Returns: { "explanation": "<generated text>" }
  - All roles.

POST /api/v1/ai/explain-risk
  - Body: { "device_id": "uuid" }
  - Returns: { "explanation": "<generated text>" }
  - All roles.

POST /api/v1/ai/chat
  - Body: { "message": "Why was this alert generated?", 
            "context_type": "alert", "context_id": "uuid" }
  - Returns: { "response": "<generated text>" }
  - For the MVP: map common questions to the explain_* methods above.
  - If the question doesn't match a pattern: return a helpful 
    fallback message like "I can explain alerts, vulnerabilities, 
    and risk scores. Please select one from the dashboard."
  - All roles.

=======================================================================
IMPORTANT: This MUST be designed to be replaceable
=======================================================================

Create an abstract base class:

  class AIService(ABC):
      @abstractmethod
      def explain_alert(self, alert) -> str: ...
      
      @abstractmethod  
      def explain_vulnerability(self, vulnerability) -> str: ...
      
      @abstractmethod
      def explain_risk_score(self, risk_score, factors) -> str: ...

LocalRuleAI implements AIService. This means in a future version, 
you could swap in OllamaAI or OpenAI without changing the endpoints.

=======================================================================
TEST BEFORE PUSHING
=======================================================================

1. Call POST /ai/explain-alert with a real alert_id.
2. Confirm the response contains a meaningful explanation with 
   actual data (not placeholder text).
3. Call POST /ai/explain-risk with a device that has vulnerabilities.
4. Confirm the explanation references actual vulnerability counts.
5. pytest tests/ — no regressions.

=======================================================================
COMMIT MESSAGE
=======================================================================
"feat: Phase 19 — local rule-based AI security explanation engine"
```
