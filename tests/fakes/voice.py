from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator


class FakeTTSProvider:
    def synthesize(self, text: str) -> AsyncIterator[bytes]:
        async def stream() -> AsyncIterator[bytes]:
            yield text.encode("utf-8")

        return stream()


class FakeTelephonyProvider:
    def __init__(self) -> None:
        self.send_started = asyncio.Event()
        self.release_send = asyncio.Event()
        self.stop_calls: list[str] = []
        self.transfer_calls: list[str] = []

    async def stop_playback(self, call_id: str) -> None:
        self.stop_calls.append(call_id)

    async def send_audio(self, call_id: str, audio: AsyncIterator[bytes]) -> None:
        del call_id
        self.send_started.set()
        await self.release_send.wait()
        async for _ in audio:
            pass

    async def transfer_to_human(self, call_id: str, context: dict[str, object]) -> None:
        del context
        self.transfer_calls.append(call_id)
