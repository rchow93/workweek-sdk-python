"""WorkWeekSwitch — decorator-based switch implementation for external tenants.

Tenants register capability handlers via @switch.capability(), then call
switch.as_fastapi_app() to get a fully-wired FastAPI application that
implements the switch contract:

  GET  /switch/manifest  — returns registered capabilities + version hash
  POST /dispatch         — routes to the matching handler, returns output
  GET  /health           — liveness check

The router polls /switch/manifest to discover capabilities. When a user
invokes a capability, the gateway dispatches to /dispatch. If the
capability has been removed (handler unregistered), the switch returns
410 GONE so the router fails over to the next-best team.
"""
import asyncio
import hashlib
import inspect
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable, Optional

logger = logging.getLogger("workweek_switch")


@dataclass
class _CapabilityHandler:
    name: str
    description: str
    handler: Callable
    is_primary: bool
    agent_name: Optional[str]
    agent_role: Optional[str]


class WorkWeekSwitch:
    """Switch SDK entry point.

    Args:
        team_id: The WorkWeek team UUID this switch serves.
        team_name: Human-readable team name (shown in manifest).
        webhook_secret: HMAC secret for signature verification. If set,
            all /dispatch requests must carry a valid X-Webhook-Signature
            header. Omit for development / internal use.
        gateway_url: WorkWeek gateway base URL (e.g., "https://gw.askvai.com").
            Required for self-registration via register().
        api_key: WorkWeek API key for authentication.
            Required for self-registration via register().
    """

    def __init__(
        self,
        team_id: str,
        team_name: str = "External Team",
        webhook_secret: Optional[str] = None,
        gateway_url: Optional[str] = None,
        api_key: Optional[str] = None,
    ) -> None:
        self.team_id = team_id
        self.team_name = team_name
        self.webhook_secret = webhook_secret
        self.gateway_url = gateway_url
        self.api_key = api_key
        self._capabilities: dict[str, _CapabilityHandler] = {}

    def capability(
        self,
        name: str,
        *,
        description: str = "",
        is_primary: bool = True,
        agent_name: Optional[str] = None,
        agent_role: Optional[str] = None,
    ) -> Callable:
        """Register a capability handler.

        The decorated function receives (message: str, context: dict) and
        must return a str (the agent's response text).

        Args:
            name: Capability name (must match what's registered in the
                router's capability registry).
            description: Short description shown in the manifest.
            is_primary: Whether this is the primary handler for the capability.
            agent_name: Display name for the agent handling this capability.
                Defaults to the function name.
            agent_role: Agent role description (e.g., "Weather Analyst").
        """
        def decorator(fn: Callable) -> Callable:
            self._capabilities[name] = _CapabilityHandler(
                name=name,
                description=description,
                handler=fn,
                is_primary=is_primary,
                agent_name=agent_name or fn.__name__,
                agent_role=agent_role or "",
            )
            return fn
        return decorator

    @property
    def version(self) -> str:
        """SHA-256 hash of registered capability names — changes when
        capabilities are added or removed, enabling efficient poll-skip."""
        cap_str = ",".join(sorted(self._capabilities.keys()))
        return hashlib.sha256(cap_str.encode()).hexdigest()[:16]

    @property
    def capability_names(self) -> list[str]:
        return sorted(self._capabilities.keys())

    def build_manifest(self) -> dict:
        """Build the manifest response dict."""
        capabilities = []
        for cap in self._capabilities.values():
            capabilities.append({
                "name": cap.name,
                "description": cap.description,
                "is_primary": cap.is_primary,
                "status": "active",
                "agent": {
                    "id": f"{self.team_id}:{cap.name}",
                    "name": cap.agent_name,
                    "display_name": cap.agent_name,
                    "role": cap.agent_role,
                },
            })

        health = "healthy" if capabilities else "empty"
        return {
            "team_id": self.team_id,
            "team_name": self.team_name,
            "version": self.version,
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "health": health,
            "capabilities": capabilities,
        }

    async def register(self, switch_url: str) -> "RegisterResult":
        """Register this switch with the WorkWeek platform.

        Calls POST /api/v1/apps/register with the switch_url where this
        app serves /switch/manifest and /dispatch. Idempotent — safe to
        call on every startup. First registration provisions an API key;
        subsequent calls are no-ops that confirm existing state.

        Args:
            switch_url: Externally-reachable base URL where this switch
                serves its manifest and dispatch endpoints.

        Returns:
            RegisterResult with app_id, team_id, api_key (first time only).

        Raises:
            ValueError: If gateway_url or api_key not configured.
            httpx.HTTPStatusError: If the platform rejects the registration.
        """
        if not self.gateway_url:
            raise ValueError(
                "gateway_url is required for registration. "
                "Pass it to WorkWeekSwitch() or set before calling register()."
            )
        if not self.api_key:
            raise ValueError(
                "api_key is required for registration. "
                "Pass it to WorkWeekSwitch() or set before calling register()."
            )

        import httpx
        from workweek_switch._models import RegisterResult

        url = f"{self.gateway_url.rstrip('/')}/api/v1/apps/register"
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                url,
                json={"switch_url": switch_url},
                headers={
                    "X-API-Key": self.api_key,
                    "Content-Type": "application/json",
                },
            )
            resp.raise_for_status()
            data = resp.json()

        result = RegisterResult(**data)

        if result.team_id and result.team_id != self.team_id:
            self.team_id = result.team_id

        logger.info(
            "Registered with platform: app_id=%d team_id=%s caps=%s existed=%s",
            result.app_id, result.team_id[:8],
            result.capabilities_registered, result.already_existed,
        )

        return result

    async def dispatch(self, capability: str, message: str, context: dict, parameters: dict | None = None) -> dict:
        """Route a dispatch request to the matching handler.

        Returns a DispatchResponse-compatible dict on success.
        Raises KeyError if the capability is not registered.

        If the handler is an async generator (streaming handler), this method
        consumes it and concatenates all token content into a single output
        string. Use dispatch_stream() for actual streaming.
        """
        handler_entry = self._capabilities.get(capability)
        if not handler_entry:
            raise KeyError(capability)

        t0 = time.time()

        fn = handler_entry.handler
        sig = inspect.signature(fn)
        accepts_parameters = len(sig.parameters) >= 3

        if inspect.isasyncgenfunction(fn):
            if accepts_parameters and parameters:
                gen = fn(message, context, parameters)
            else:
                gen = fn(message, context)
            chunks = []
            async for event in gen:
                if isinstance(event, dict) and event.get("type") == "token":
                    chunks.append(event.get("content", ""))
                elif isinstance(event, str):
                    chunks.append(event)
            output = "".join(chunks)
        elif accepts_parameters and parameters:
            if inspect.iscoroutinefunction(fn):
                output = await fn(message, context, parameters)
            else:
                output = await asyncio.to_thread(fn, message, context, parameters)
        else:
            if inspect.iscoroutinefunction(fn):
                output = await fn(message, context)
            else:
                output = await asyncio.to_thread(fn, message, context)

        latency_ms = int((time.time() - t0) * 1000)

        return {
            "output": str(output),
            "agent_id": f"{self.team_id}:{capability}",
            "agent_name": handler_entry.agent_name,
            "latency_ms": latency_ms,
        }

    async def dispatch_stream(self, capability: str, message: str, context: dict, parameters: dict | None = None):
        """Route a dispatch request to a streaming handler (async generator).

        Yields SSE event dicts. The handler must be an async generator that
        yields dicts with at least a "type" key. This method wraps the stream
        with session/done events and latency tracking.

        Raises KeyError if the capability is not registered.
        Raises TypeError if the handler is not an async generator.
        """
        handler_entry = self._capabilities.get(capability)
        if not handler_entry:
            raise KeyError(capability)

        fn = handler_entry.handler
        if not inspect.isasyncgenfunction(fn):
            raise TypeError(
                f"Handler for '{capability}' is not an async generator. "
                f"Streaming requires 'async def handler(...): yield ...'"
            )

        t0 = time.time()
        agent_id = f"{self.team_id}:{capability}"

        yield {"type": "session", "session_id": context.get("session_id", "")}

        sig = inspect.signature(fn)
        accepts_parameters = len(sig.parameters) >= 3

        if accepts_parameters and parameters:
            gen = fn(message, context, parameters)
        else:
            gen = fn(message, context)

        tokens_used = 0
        async for event in gen:
            if isinstance(event, dict):
                if event.get("type") == "token":
                    tokens_used += 1
                yield event
            else:
                yield {"type": "token", "content": str(event)}
                tokens_used += 1

        latency_ms = int((time.time() - t0) * 1000)
        yield {
            "type": "done",
            "agent_id": agent_id,
            "agent_name": handler_entry.agent_name,
            "latency_ms": latency_ms,
            "tokens_used": tokens_used,
        }

    def as_fastapi_app(self, **kwargs) -> "fastapi.FastAPI":
        """Build a fully-wired FastAPI application implementing the switch contract.

        Pass extra kwargs to FastAPI() (e.g., title, docs_url).
        Returns a FastAPI app ready for uvicorn.run().
        """
        from fastapi import FastAPI, Query, Request
        from fastapi.responses import JSONResponse, StreamingResponse

        from workweek_switch._hmac import verify_signature
        from workweek_switch._models import DispatchRequest

        app_kwargs = {
            "title": f"WorkWeek Switch — {self.team_name}",
            "version": self.version,
            **kwargs,
        }
        app = FastAPI(**app_kwargs)

        switch = self

        @app.get("/switch/manifest")
        async def get_manifest(
            team_id: str = Query(None, description="Team ID (ignored, uses configured team)"),
        ):
            return switch.build_manifest()

        @app.post("/dispatch")
        async def dispatch(raw_request: Request):
            body = await raw_request.body()

            if switch.webhook_secret:
                sig = raw_request.headers.get("X-Webhook-Signature", "")
                if not verify_signature(body, switch.webhook_secret, sig):
                    return JSONResponse(
                        status_code=401,
                        content={"error": "invalid_signature", "message": "HMAC verification failed"},
                    )

            import json
            try:
                payload = json.loads(body)
            except (json.JSONDecodeError, TypeError):
                return JSONResponse(status_code=400, content={"error": "invalid_json"})

            req = DispatchRequest(**payload)
            capability = req.capability

            handler_entry = switch._capabilities.get(capability)
            if not handler_entry:
                logger.warning(
                    "Capability '%s' not registered — returning 410 GONE", capability,
                )
                return JSONResponse(
                    status_code=410,
                    content={
                        "error": "capability_unavailable",
                        "message": f"Capability '{capability}' not available",
                        "available_capabilities": switch.capability_names,
                        "forwarding_table_version": switch.version,
                    },
                )

            is_streaming = req.stream and inspect.isasyncgenfunction(handler_entry.handler)

            if is_streaming:
                async def _sse_generator():
                    try:
                        async for event in switch.dispatch_stream(
                            capability=capability,
                            message=req.message,
                            context=req.routing_metadata,
                            parameters=req.parameters or None,
                        ):
                            yield f"data: {json.dumps(event)}\n\n"
                    except Exception as exc:
                        logger.exception("Streaming handler error for '%s'", capability)
                        yield f"data: {json.dumps({'type': 'error', 'message': str(exc)[:200]})}\n\n"

                return StreamingResponse(
                    _sse_generator(),
                    media_type="text/event-stream",
                    headers={
                        "Cache-Control": "no-cache, no-transform",
                        "X-Accel-Buffering": "no",
                        "Connection": "keep-alive",
                    },
                )

            try:
                result = await switch.dispatch(
                    capability=capability,
                    message=req.message,
                    context=req.routing_metadata,
                    parameters=req.parameters or None,
                )
                return result
            except KeyError:
                logger.warning(
                    "Capability '%s' not registered — returning 410 GONE", capability,
                )
                return JSONResponse(
                    status_code=410,
                    content={
                        "error": "capability_unavailable",
                        "message": f"Capability '{capability}' not available",
                        "available_capabilities": switch.capability_names,
                        "forwarding_table_version": switch.version,
                    },
                )

        @app.get("/health")
        async def health():
            return {
                "status": "ok",
                "team_id": switch.team_id,
                "capabilities": len(switch._capabilities),
                "version": switch.version,
            }

        return app

    def as_fastapi_router(self, prefix: str = "") -> "fastapi.routing.APIRouter":
        """Return an APIRouter implementing the switch contract.

        Use this when adding switch endpoints to an existing FastAPI app:

            app.include_router(switch.as_fastapi_router(prefix="/api"))
        """
        from fastapi import APIRouter, Query, Request
        from fastapi.responses import JSONResponse, StreamingResponse

        from workweek_switch._hmac import verify_signature
        from workweek_switch._models import DispatchRequest

        api_router = APIRouter(prefix=prefix, tags=["workweek-switch"])
        switch = self

        @api_router.get("/switch/manifest")
        async def get_manifest(
            team_id: str = Query(None, description="Team ID (ignored, uses configured team)"),
        ):
            return switch.build_manifest()

        @api_router.post("/dispatch")
        async def dispatch(raw_request: Request):
            body = await raw_request.body()

            if switch.webhook_secret:
                sig = raw_request.headers.get("X-Webhook-Signature", "")
                if not verify_signature(body, switch.webhook_secret, sig):
                    return JSONResponse(
                        status_code=401,
                        content={"error": "invalid_signature", "message": "HMAC verification failed"},
                    )

            import json
            try:
                payload = json.loads(body)
            except (json.JSONDecodeError, TypeError):
                return JSONResponse(status_code=400, content={"error": "invalid_json"})

            req = DispatchRequest(**payload)
            capability = req.capability

            handler_entry = switch._capabilities.get(capability)
            if not handler_entry:
                logger.warning(
                    "Capability '%s' not registered — returning 410 GONE", capability,
                )
                return JSONResponse(
                    status_code=410,
                    content={
                        "error": "capability_unavailable",
                        "message": f"Capability '{capability}' not available",
                        "available_capabilities": switch.capability_names,
                        "forwarding_table_version": switch.version,
                    },
                )

            is_streaming = req.stream and inspect.isasyncgenfunction(handler_entry.handler)

            if is_streaming:
                async def _sse_generator():
                    try:
                        async for event in switch.dispatch_stream(
                            capability=capability,
                            message=req.message,
                            context=req.routing_metadata,
                            parameters=req.parameters or None,
                        ):
                            yield f"data: {json.dumps(event)}\n\n"
                    except Exception as exc:
                        logger.exception("Streaming handler error for '%s'", capability)
                        yield f"data: {json.dumps({'type': 'error', 'message': str(exc)[:200]})}\n\n"

                return StreamingResponse(
                    _sse_generator(),
                    media_type="text/event-stream",
                    headers={
                        "Cache-Control": "no-cache, no-transform",
                        "X-Accel-Buffering": "no",
                        "Connection": "keep-alive",
                    },
                )

            try:
                result = await switch.dispatch(
                    capability=capability,
                    message=req.message,
                    context=req.routing_metadata,
                    parameters=req.parameters or None,
                )
                return result
            except KeyError:
                logger.warning(
                    "Capability '%s' not registered — returning 410 GONE", capability,
                )
                return JSONResponse(
                    status_code=410,
                    content={
                        "error": "capability_unavailable",
                        "message": f"Capability '{capability}' not available",
                        "available_capabilities": switch.capability_names,
                        "forwarding_table_version": switch.version,
                    },
                )

        return api_router
