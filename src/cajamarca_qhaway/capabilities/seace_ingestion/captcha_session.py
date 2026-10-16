"""Obtiene un token reCAPTCHA v3 mediante el runtime oficial y la misma sesión JSF."""

from __future__ import annotations

import asyncio
import re
from typing import Any

import httpx

from cajamarca_qhaway.capabilities.seace_ingestion.official_sources import (
    SEACE_PUBLIC_URL,
    OfficialSourceUnavailable,
)


class BrowserCaptchaSolver:
    """Usa un contexto efímero; cookies y tokens nunca se persisten ni se registran."""

    def __init__(self, timeout_seconds: float = 40) -> None:
        self.timeout_seconds = timeout_seconds

    async def __call__(self, html: str, http: httpx.AsyncClient, attempt: int) -> str:
        if not 1 <= attempt <= 3:
            raise ValueError("Intento CAPTCHA fuera del límite de tres")
        key = re.search(r'id=["\']claveRecaptchav3SitioWeb["\'][^>]*value=["\']([^"\']+)', html)
        if key is None:
            raise OfficialSourceUnavailable("CAPTCHA_COMPONENT_UNSUPPORTED")
        try:
            from playwright.async_api import async_playwright
        except ImportError as error:
            raise OfficialSourceUnavailable("CAPTCHA_BROWSER_UNAVAILABLE") from error
        try:
            async with asyncio.timeout(self.timeout_seconds), async_playwright() as runtime:
                browser = await runtime.chromium.launch(headless=True)
                try:
                    context = await browser.new_context()
                    cookies: list[Any] = [
                        {"name": cookie.name, "value": cookie.value,
                         "domain": cookie.domain, "path": cookie.path,
                         "secure": cookie.secure}
                        for cookie in http.cookies.jar
                        if cookie.domain.lstrip(".") == "prod2.seace.gob.pe"
                    ]
                    await context.add_cookies(cookies)
                    page = await context.new_page()
                    # Servir el documento capturado evita crear otra vista/sesión JSF.
                    async def document(route: Any) -> None:
                        await route.fulfill(status=200, content_type="text/html; charset=utf-8", body=html)
                    await page.route(SEACE_PUBLIC_URL, document)
                    await page.goto(SEACE_PUBLIC_URL, wait_until="domcontentloaded")
                    await page.wait_for_function("typeof grecaptcha !== 'undefined'", timeout=20_000)
                    token = await page.evaluate("""key => new Promise((resolve, reject) => {
                        grecaptcha.ready(() => grecaptcha.execute(key, {
                            action: 'frmBuscadorProcedimientosSeleccion'
                        }).then(resolve, () => reject(new Error('CAPTCHA_PROVIDER_REJECTED'))));
                    })""", key.group(1))
                    if not isinstance(token, str) or not token.strip():
                        raise OfficialSourceUnavailable("CAPTCHA_TOKEN_UNAVAILABLE")
                    for cookie in await context.cookies(SEACE_PUBLIC_URL):
                        domain = cookie.get('domain', '')
                        name, value = cookie.get('name'), cookie.get('value')
                        if domain.lstrip('.') == 'prod2.seace.gob.pe' and name and value:
                            http.cookies.set(name, value, domain=domain, path=cookie.get('path', '/'))
                    return token
                finally:
                    await browser.close()
        except OfficialSourceUnavailable:
            raise
        except TimeoutError as error:
            raise OfficialSourceUnavailable("CAPTCHA_PROVIDER_TIMEOUT") from error
        except Exception as error:
            # Las excepciones de navegador pueden contener cookies o cuerpos de solicitud.
            raise OfficialSourceUnavailable("CAPTCHA_BROWSER_OR_PROVIDER_UNAVAILABLE") from error
