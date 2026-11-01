"""Optional Gemini commentary with server-owned fact references and no raw numbers."""

import json
import logging
import os
import re


def facts_for(report):
    facts = {}
    for name, p in report["portfolios"].items():
        for metric, value in p["metrics"].items():
            facts[f"{name}.{metric}"] = f"{value*100:.2f}%"
        for row in (p["allocations"] if name != "benchmark" else []):
            facts[f'{name}.weight.{row["symbol"]}'] = f'{row["weight_percent"]:.2f}%'
    for key in ("start", "end", "observations"):
        facts[f"period.{key}"] = str(report["period"][key])
    return facts


def fact_label(ref):
    labels = {
        "total_return": "total return",
        "cagr": "CAGR",
        "annualized_volatility": "annualized volatility",
        "max_drawdown": "maximum drawdown",
    }
    parts = ref.split(".")
    return parts[0].capitalize() + " " + labels.get(parts[1], " ".join(parts[1:]))


def validate_response(raw, facts):
    obj = json.loads(raw)
    if not isinstance(obj, dict) or set(obj) != {"performance", "risk", "comparison"}:
        raise ValueError("Invalid structured commentary")
    output = {}
    for topic, text in obj.items():
        if isinstance(text, dict):
            if set(text) != {"summary", "fact_ids"} or not isinstance(
                text["summary"], str
            ):
                raise ValueError("Invalid structured section")
            ids = text["fact_ids"]
            summary = text["summary"]
            if (
                not isinstance(ids, list)
                or not 1 <= len(ids) <= 4
                or any(not isinstance(ref, str) or ref not in facts for ref in ids)
            ):
                raise ValueError("Unknown fact reference")
            if any(c in summary for c in "{}"):
                raise ValueError("Placeholders are not allowed in summary")
            # Reuse the numerical-prose check below before inserting server facts.
            temporary = summary + " {{" + ids[0] + "}}"
            validate_response(
                json.dumps(
                    {name: temporary for name in ("performance", "risk", "comparison")}
                ),
                facts,
            )
            output[topic] = (
                summary
                + " "
                + "; ".join(
                    fact_label(ref) + ": " + facts[ref] for ref in dict.fromkeys(ids)
                )
                + "."
            )
            continue
        if not isinstance(text, str) or not 10 <= len(text) <= 700:
            raise ValueError("Invalid commentary length")
        refs = re.findall(r"\{\{([^{}]+)\}\}", text)
        clean = re.sub(r"\{\{[^{}]+\}\}", "", text)
        if (
            not refs
            or any(ref not in facts for ref in refs)
            or re.search(
                r"\d|[%％{}]|\b(zero|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety|hundred|thousand|million|billion|dozen|double|doubled|twice|half|quarter|triple|tripled)\b",
                clean,
                re.I,
            )
        ):
            raise ValueError("Unverified numerical statement")
        output[topic] = re.sub(r"\{\{([^{}]+)\}\}", lambda m: facts[m[1]], text)
    return output


def commentary_schema(facts):
    properties = {}
    for topic in ("performance", "risk", "comparison"):
        relevant = [
            ref
            for ref in facts
            if ".weight." not in ref
            and (
                topic == "comparison"
                or (
                    topic == "risk"
                    and ref.endswith(("annualized_volatility", "max_drawdown"))
                )
                or (
                    topic == "performance"
                    and ref.startswith(
                        ("current.total_return", "current.cagr", "period.")
                    )
                )
            )
        ]
        properties[topic] = {
            "type": "object",
            "properties": {
                "summary": {
                    "type": "string",
                    "description": "Concise qualitative historical interpretation; no numbers, dates or placeholders.",
                },
                "fact_ids": {
                    "type": "array",
                    "items": {"type": "string", "enum": relevant},
                    "minItems": 1,
                    "maxItems": 4,
                },
            },
            "required": ["summary", "fact_ids"],
            "additionalProperties": False,
        }
    return {
        "type": "object",
        "properties": properties,
        "required": list(properties),
        "additionalProperties": False,
    }


def interpret(report):
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        return {
            "status": "unavailable",
            "message": "Gemini is not configured. All historical calculations and charts remain available.",
        }
    stage = "sdk"
    model = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash-lite")
    try:
        from google import genai
        from google.genai import types

        model = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash-lite")
        facts = facts_for(report)
        schema = commentary_schema(facts)
        context = {
            k: report[k]
            for k in ("period", "coverage", "excluded_dates", "assumptions")
        }
        context["portfolios"] = {
            n: {"metrics": p["metrics"], "allocations": p["allocations"]}
            for n, p in report["portfolios"].items()
        }
        prompt = (
            "Write concise qualitative historical portfolio commentary about performance, risk and comparison. "
            "No advice, predictions or causal claims. Summaries must contain NO numbers, dates, percentages, numeric words or placeholders. "
            "Select relevant fact_ids from the supplied vocabulary exactly; the server will append verified numeric values separately. "
            "Do not invent fact IDs. Acknowledge limitations. Alternative means an alternative allocation ONLY if supplied; "
            "benchmark means the NIFTY ETF reference, never an alternative allocation. "
            "Benchmark includes fund fees/tracking effects and is not the official total-return index. "
            "Facts: " + json.dumps(facts) + " Context: " + json.dumps(context)
        )
        stage = "provider"
        with genai.Client(
            api_key=key,
            http_options=types.HttpOptions(
                timeout=60000, retry_options=types.HttpRetryOptions(attempts=1)
            ),
        ) as client:
            response = client.models.generate_content(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json", response_json_schema=schema
                ),
            )
        stage = "validation"
        sections = validate_response(response.text, facts)
        details = {}
        raw_sections = json.loads(response.text)
        for topic, section in raw_sections.items():
            if isinstance(section, dict):
                details[topic] = {
                    "summary": section["summary"],
                    "facts": [
                        {"label": fact_label(ref), "value": facts[ref]}
                        for ref in dict.fromkeys(section["fact_ids"])
                    ],
                }
        return {
            "status": "ready",
            "model": model,
            "sections": sections,
            "section_details": details,
            "message": "LLM-assisted interpretation. Fact references checked; qualitative wording is not independently certified.",
        }
    except Exception as exc:
        # Classify locally; never return/log exception text, response bodies or keys.
        code = getattr(exc, "code", None)
        code = code if isinstance(code, int) and 100 <= code <= 599 else None
        if stage == "sdk":
            category = "sdk_setup"
            message = "Gemini SDK setup failed. Install requirements-ai.txt in the server environment."
        elif stage == "validation":
            category = "response_validation"
            message = "Google returned a response, but it failed our structured or numerical fact checks. No commentary was displayed."
        elif code in (401, 403):
            category = "authentication_or_access"
            message = "Google rejected authentication or access. Check the key and project/API restrictions in AI Studio."
        elif code == 400:
            category = "request_rejected"
            message = "Google rejected the request (HTTP 400). Check key validity, model settings and project eligibility in AI Studio."
        elif code == 404:
            category = "model_unavailable"
            message = "Google could not find the configured model (HTTP 404). Select an available Gemini API model using GEMINI_MODEL and restart."
        elif code == 429:
            category = "quota_or_rate_limit"
            message = "Google reported a quota or rate limit (HTTP 429). Check this model’s project quota in AI Studio; repeated clicks may not resolve an exhausted or zero quota."
        elif (
            code == 504
            or isinstance(exc, TimeoutError)
            or type(exc).__name__
            in ("ReadTimeout", "ConnectTimeout", "TimeoutException")
        ):
            category = "request_timeout"
            message = "The Gemini request timed out. The app allows a 60-second request timeout. Try once more later; persistent timeouts can be a provider or connectivity problem."
        elif code is not None and code >= 500:
            category = "provider_unavailable"
            message = "Google’s service is temporarily unavailable. Try again later."
        else:
            category = "connection_or_sdk_error"
            message = "The Gemini request did not complete. Check connectivity, request timeout and the installed SDK."
        logging.getLogger(__name__).warning(
            "Gemini interpretation failed: category=%s http_status=%s", category, code
        )
        return {
            "status": "unavailable",
            "reason": category,
            "http_status": code,
            "message": message + " Calculated results are unchanged.",
        }
