# Realtime voice and barge-in

Natural conversation requires interruption handling in infrastructure, not only prompt wording.

## Playback ownership

The voice layer owns the currently active assistant playback task.

```text
response text
   |
streaming TTS
   |
playback task
   |
telephony media
```

When VAD detects patient speech while playback is active:

1. cancel the local playback task;
2. clear/stop provider playback;
3. mark the old assistant turn interrupted;
4. accept the patient's new speech;
5. never resume the old audio automatically.

The initial `PlaybackController` establishes cancellable playback semantics independently of any specific TTS or telephony vendor.

## Provider-neutral rule

Core voice code depends only on `TTSProvider` and `TelephonyProvider` contracts. Vendor buffer-clearing semantics belong in the concrete telephony adapter.

## Failure rule

If audio output cannot continue, the system follows deterministic fallback/handoff policy. It must not leave an indefinitely silent call while the backend waits for an unavailable AI provider.
