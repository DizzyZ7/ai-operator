# Trust and canonicalization

Natural-language entities and trusted business identifiers are different data classes.

## Untrusted candidates

The LLM may extract:

```text
service = "чистка"
clinic = "Невский"
date = "пятница"
```

These values are stored as conversation candidates only.

They must not directly populate canonical fields such as:

```text
service_id
clinic_id
doctor_id
slot_id
appointment_id
patient_id
```

Canonical IDs come only from approved provider/tool results.

## Why

A model can misunderstand speech, hallucinate an identifier, receive a malicious transcript, or be influenced by prompt injection. Converting model text directly into privileged resource identifiers would turn an NLU error into a business action.

## Resource grants

When Scheduling returns real slots, the backend converts them into offered options. Tool execution context derives a call-scoped resource grant from those trusted options.

A create-appointment mutation must use a slot contained in that grant.

```text
Scheduling response
      |
trusted AvailableSlot
      |
backend OfferedOption
      |
patient chooses / confirms
      |
call-scoped slot grant
      |
create_appointment
```

An allowlisted tool name is therefore not enough. The specific resource must also be authorized for the current conversation.
