import json
import sys


def _safe_str(value: object, limit: int = 800) -> str:
    try:
        s = str(value)
    except Exception:
        s = repr(value)
    return s[:limit]


def _print_result(payload: dict) -> None:
    print(json.dumps(payload, ensure_ascii=False))


def _test_openai_sdk(openai_api_key: str, openai_api_base: str, model_name: str) -> tuple[bool, dict]:
    try:
        from openai import OpenAI
    except Exception as e:
        return False, {"provider": "openai_sdk", "ok": False, "type": type(e).__name__, "error": _safe_str(e)}

    try:
        base_candidates = [openai_api_base]
        normalized = openai_api_base.rstrip("/")
        if not normalized.endswith("/v1"):
            base_candidates.append(normalized + "/v1")

        last = None
        for i, base_url in enumerate(base_candidates, start=1):
            try:
                client = OpenAI(api_key=openai_api_key, base_url=base_url)
                resp = client.chat.completions.create(
                    model=model_name,
                    messages=[{"role": "user", "content": "用一句中文回答：你是谁？"}],
                )
                choices = getattr(resp, "choices", None)
                if choices:
                    text = choices[0].message.content
                    return True, {"provider": "openai_sdk", "ok": True, "try": i, "base_url": base_url, "response": _safe_str(text, 2000)}
                raw = _safe_str(resp, 2000)
                last = {
                    "provider": "openai_sdk",
                    "ok": False,
                    "try": i,
                    "base_url": base_url,
                    "type": "UnexpectedResponse",
                    "error": raw,
                }
                continue
            except Exception as e:
                status_code = getattr(e, "status_code", None)
                code = getattr(e, "code", None)
                last = {
                    "provider": "openai_sdk",
                    "ok": False,
                    "try": i,
                    "base_url": base_url,
                    "type": type(e).__name__,
                    "error": _safe_str(e),
                }
                if status_code is not None:
                    last["status_code"] = status_code
                if code is not None:
                    last["code"] = code
                continue

        return False, last or {"provider": "openai_sdk", "ok": False, "type": "UnknownError", "error": "unknown"}
    except Exception as e:
        extra = {}
        status_code = getattr(e, "status_code", None)
        if status_code is not None:
            extra["status_code"] = status_code
        code = getattr(e, "code", None)
        if code is not None:
            extra["code"] = code
        return False, {"provider": "openai_sdk", "ok": False, "type": type(e).__name__, "error": _safe_str(e), **extra}


def _test_langchain(openai_api_key: str, openai_api_base: str, model_name: str) -> tuple[bool, dict]:
    try:
        from langchain_openai import ChatOpenAI
    except Exception as e:
        return False, {"provider": "langchain_openai", "ok": False, "type": type(e).__name__, "error": _safe_str(e)}

    prompt = "用一句中文回答：你是谁？"
    base_kwargs = {"openai_api_key": openai_api_key, "model_name": model_name, "temperature": 0}
    base_candidates = [openai_api_base]
    normalized = openai_api_base.rstrip("/")
    if not normalized.endswith("/v1"):
        base_candidates.append(normalized + "/v1")

    candidates = []
    for base_url in base_candidates:
        candidates.append({**base_kwargs, "base_url": base_url})
        candidates.append({**base_kwargs, "openai_api_base": base_url})
    candidates.append(base_kwargs)

    last = None
    attempts = []
    for i, kwargs in enumerate(candidates, start=1):
        try:
            llm = ChatOpenAI(**kwargs)
            resp = llm.invoke(prompt)
            content = getattr(resp, "content", resp)
            return True, {"provider": "langchain_openai", "ok": True, "try": i, "response": _safe_str(content, 2000)}
        except Exception as e:
            last = {"provider": "langchain_openai", "ok": False, "try": i, "type": type(e).__name__, "error": _safe_str(e)}
            attempts.append(last)
            continue

    if attempts:
        return False, {"provider": "langchain_openai", "ok": False, "attempts": attempts[:3], "last": attempts[-1]}
    return False, {"provider": "langchain_openai", "ok": False, "type": "UnknownError", "error": "unknown"}


def main() -> int:
    try:
        from src.settings.base_setting import model_name, openai_api_base, openai_api_key
    except Exception as e:
        print("读取配置失败:", type(e).__name__, _safe_str(e))
        return 2

    meta = {
        "openai_api_base": openai_api_base,
        "model_name": model_name,
        "has_openai_api_key": bool(openai_api_key),
        "openai_api_key_len": len(openai_api_key or ""),
    }
    _print_result(meta)

    ok_sdk, payload_sdk = _test_openai_sdk(
        openai_api_key=openai_api_key, openai_api_base=openai_api_base, model_name=model_name
    )
    _print_result(payload_sdk)

    ok_lc, payload_lc = _test_langchain(
        openai_api_key=openai_api_key, openai_api_base=openai_api_base, model_name=model_name
    )
    _print_result(payload_lc)
    return 0 if (ok_sdk or ok_lc) else 1


if __name__ == "__main__":
    sys.exit(main())
