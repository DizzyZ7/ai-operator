# ADR-0010: Patient identity and resource ownership

Status: Accepted

## DECISION

Existing patient resources are accessible only after two independent backend checks:

1. the caller is in a verified patient identity context;
2. the concrete resource was resolved by an approved backend as belonging to that verified patient.

The concrete verification mechanism (caller-ID matching, OTP, CRM challenge, operator verification, etc.) remains UNKNOWN until clinic policy is approved.

## WHY

Knowing an appointment identifier is not authorization to view, reschedule, confirm or cancel it.

LLM text, caller-provided IDs, phone-number appearance and tool arguments are insufficient proof of ownership.

## FLOW

```text
approved identity flow
      |
verified patient_id
      |
get_patient_appointments(patient_id)
      |
trusted backend result
      |
authorized appointment IDs
      |
specific mutation
      |
patient match + appointment grant + confirmation + idempotency
```

## INVARIANTS

- unverified callers cannot mutate existing patient appointments;
- requested patient_id must equal verified patient_id;
- appointment_id must have been resolved from a trusted backend for that patient;
- prompt instructions cannot create resource ownership;
- identity verification and resource ownership are separate checks;
- the repository does not assume which verification factor the clinic will approve.
