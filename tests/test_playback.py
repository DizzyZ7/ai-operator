import pytest

from app.voice.playback import PlaybackController
from tests.fakes.voice import FakeTelephonyProvider, FakeTTSProvider


@pytest.mark.asyncio
async def test_barge_in_cancels_tts_and_stops_provider_playback() -> None:
    telephony = FakeTelephonyProvider()
    controller = PlaybackController(tts=FakeTTSProvider(), telephony=telephony)

    await controller.start(call_id="call-1", text="old response")
    await telephony.send_started.wait()

    interrupted = await controller.interrupt()

    assert interrupted is True
    assert controller.is_playing is False
    assert telephony.stop_calls == ["call-1"]


@pytest.mark.asyncio
async def test_starting_new_response_interrupts_previous_audio() -> None:
    telephony = FakeTelephonyProvider()
    controller = PlaybackController(tts=FakeTTSProvider(), telephony=telephony)

    await controller.start(call_id="call-1", text="first")
    await telephony.send_started.wait()

    telephony.send_started.clear()
    await controller.start(call_id="call-1", text="second")

    assert telephony.stop_calls == ["call-1"]
    assert controller.is_playing is True

    await controller.interrupt()
