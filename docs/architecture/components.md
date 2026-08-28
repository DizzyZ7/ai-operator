# Component architecture

## Context

```text
Patient
  |
PSTN / SIP
  |
Telephony Provider
  |
Realtime Call Session
  |
Conversation Orchestrator
  +-- Conversation State
  +-- Policy Engine
  +-- LLM Gateway
  +-- Tool Router
  |
Backend Provider Adapters
  +-- Scheduling
  +-- CRM
  +-- Medical System
  +-- Notifications
```

## Core boundary

The LLM never owns state and never receives direct credentials to business systems.

```text
LLM structured proposal
        |
        v
schema validation
        |
policy validation
        |
authorization
        |
business-state validation
        |
tool execution
        |
CRM / MIS / Scheduling
```

## Voice path

```text
media -> VAD -> streaming STT -> turn manager
                                -> orchestrator
                                -> response plan
media <- streaming TTS <--------+
```

Barge-in is implemented in the realtime/voice layer. It must cancel playback immediately; it is not merely a prompt instruction.

## Provider interfaces

Planned provider boundaries:

- TelephonyProvider
- STTProvider
- TTSProvider
- LLMProvider
- CRMProvider
- MedicalSystemProvider
- SchedulingProvider
- NotificationProvider

No concrete provider is selected until discovery confirms the clinic's systems.

## Source-of-truth rules

- appointments: Scheduling/MIS;
- patient business identity: CRM/MIS;
- approved business facts: versioned approved sources;
- active conversation state: AI Operator backend;
- call/tool audit: AI Operator backend.

The LLM is never a source of truth.
