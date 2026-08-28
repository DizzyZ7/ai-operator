from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Protocol


class STTProvider(Protocol):
    def transcribe(self, audio: AsyncIterator[bytes]) -> AsyncIterator[str]: ...


class TTSProvider(Protocol):
    def synthesize(self, text: str) -> AsyncIterator[bytes]: ...


class TelephonyProvider(Protocol):
    async def stop_playback(self, call_id: str) -> None: ...

    async def send_audio(self, call_id: str, audio: AsyncIterator[bytes]) -> None: ...

    async def transfer_to_human(self, call_id: str, context: dict[str, object]) -> None: ...
