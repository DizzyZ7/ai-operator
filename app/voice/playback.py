from __future__ import annotations

import asyncio
from contextlib import suppress

from app.providers.voice import TTSProvider, TelephonyProvider


class PlaybackController:
    """Owns assistant playback so patient barge-in can cancel it immediately."""

    def __init__(
        self,
        *,
        tts: TTSProvider,
        telephony: TelephonyProvider,
    ) -> None:
        self._tts = tts
        self._telephony = telephony
        self._playback_task: asyncio.Task[None] | None = None
        self._call_id: str | None = None

    @property
    def is_playing(self) -> bool:
        return self._playback_task is not None and not self._playback_task.done()

    async def start(self, *, call_id: str, text: str) -> None:
        await self.interrupt()
        self._call_id = call_id
        audio = self._tts.synthesize(text)
        self._playback_task = asyncio.create_task(
            self._telephony.send_audio(call_id, audio),
            name=f"tts-playback:{call_id}",
        )

    async def wait_until_idle(self) -> None:
        task = self._playback_task
        if task is None:
            return
        await task
        if self._playback_task is task:
            self._playback_task = None

    async def interrupt(self) -> bool:
        task = self._playback_task
        call_id = self._call_id
        if task is None or task.done():
            self._playback_task = None
            self._call_id = None
            return False

        task.cancel()
        with suppress(asyncio.CancelledError):
            await task

        if call_id is not None:
            await self._telephony.stop_playback(call_id)

        self._playback_task = None
        self._call_id = None
        return True
