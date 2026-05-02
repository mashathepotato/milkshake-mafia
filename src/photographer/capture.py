from __future__ import annotations

import asyncio
import base64
import io
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from PIL import Image

from .contracts import CaptureRequest, ErrorInfo, ScreenshotArtifact


async def _capture_async(
    req: CaptureRequest,
    out_dir: Optional[Path] = None,
) -> ScreenshotArtifact:
    from playwright.async_api import async_playwright
    from playwright.async_api import TimeoutError as PlaywrightTimeout

    warnings: list[str] = []
    error: Optional[ErrorInfo] = None
    png_base64: Optional[str] = None
    png_path: Optional[str] = None
    http_status: Optional[int] = None
    final_url = req.url

    async with async_playwright() as p:
        try:
            browser = await p.chromium.launch(headless=True)
        except Exception as exc:
            return ScreenshotArtifact(
                request_id=req.request_id,
                url=req.url,
                captured_at=datetime.now(timezone.utc).isoformat(),
                viewport=req.viewport,
                full_page=req.full_page,
                final_url=req.url,
                warnings=warnings,
                error=ErrorInfo(type="browser_launch_failed", message=str(exc)),
            )
        try:
            context = await browser.new_context(
                viewport={"width": req.viewport.width, "height": req.viewport.height},
                user_agent=req.user_agent or "Mozilla/5.0 (compatible; PhotographerBot/1.0)",
                extra_http_headers=req.headers or {},
            )
            page = await context.new_page()

            response = None
            wait_until = req.wait_until
            try:
                response = await page.goto(req.url, wait_until=wait_until, timeout=30_000)
            except PlaywrightTimeout:
                warnings.append(
                    f"Timed out waiting for '{wait_until}'; falling back to 'domcontentloaded'"
                )
                wait_until = "domcontentloaded"
                try:
                    response = await page.goto(req.url, wait_until=wait_until, timeout=15_000)
                except PlaywrightTimeout as exc:
                    error = ErrorInfo(type="timeout", message=str(exc))
            except Exception as exc:
                err_type = (
                    "dns_error"
                    if any(kw in str(exc) for kw in ("net::ERR", "Name or service not known"))
                    else type(exc).__name__
                )
                error = ErrorInfo(type=err_type, message=str(exc))

            if error is None and response is not None:
                http_status = response.status
                final_url = page.url

                if req.wait_ms > 0:
                    await asyncio.sleep(req.wait_ms / 1000)

                screenshot_bytes = await page.screenshot(full_page=req.full_page)

                # Cap height to 6000px
                img = Image.open(io.BytesIO(screenshot_bytes))
                if img.height > 6000:
                    warnings.append(f"Image height {img.height}px clipped to 6000px")
                    img = img.crop((0, 0, img.width, 6000))
                    buf = io.BytesIO()
                    img.save(buf, format="PNG")
                    screenshot_bytes = buf.getvalue()

                png_base64 = base64.b64encode(screenshot_bytes).decode()

                if out_dir is not None:
                    out_dir = Path(out_dir)
                    out_dir.mkdir(parents=True, exist_ok=True)
                    p_out = out_dir / f"{req.request_id}.png"
                    p_out.write_bytes(screenshot_bytes)
                    png_path = str(p_out)

        finally:
            await browser.close()

    return ScreenshotArtifact(
        request_id=req.request_id,
        url=req.url,
        captured_at=datetime.now(timezone.utc).isoformat(),
        viewport=req.viewport,
        full_page=req.full_page,
        png_base64=png_base64,
        png_path=png_path,
        http_status=http_status,
        final_url=final_url,
        warnings=warnings,
        error=error,
    )


def capture(req: CaptureRequest, out_dir: Optional[Path] = None) -> ScreenshotArtifact:
    return asyncio.run(_capture_async(req, out_dir))
