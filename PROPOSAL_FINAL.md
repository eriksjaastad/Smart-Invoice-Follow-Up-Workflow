# PROPOSAL_FINAL: Smart Invoice SaaS MVP

**Document Version:** 1.0  
**Date:** 2026-02-15  
**Status:** Approved (Super Manager Review Complete)
**Draft by:** Antigravity (Floor Manager)
**Reviewed by:** Claude Opus (Super Manager)

---

## Executive Summary

This document confirms the traceability and alignment between the **PRD.md** (Product Requirements Document) and the **Kiro specifications** (requirements.md, design.md, tasks.md) for the Smart Invoice SaaS MVP.

**Verdict: ✅ ALIGNED (with 3 gaps to address)**

24 of 27 functional requirements from the PRD are fully covered in the Kiro specs. The 3 gaps (FR-21, FR-23, FR-24) are all from the 2026-02-15 PRD update adding operational guardrails — they need to be added to Kiro specs before implementation begins. Architecture decisions and resolved questions are properly reflected in the Kiro design.

---

## Traceability Matrix: PRD → Kiro Requirements

### Authentication & User Management (FR-1 to FR-3)

| PRD Requirement | Kiro Coverage | Status |
|-----------------|---------------|--------|
| FR-1: Auth0 signup (email/password or magic link) | Requirement 1: User Account Management | ✅ Complete |
| FR-2: Google connection via Make.com verified OAuth | Requirement 2: Google Account Connection | ✅ Complete |
| FR-3: Make.com handles Google tokens (we never touch them) | Requirement 2, AC #4 | ✅ Complete |

**Notes:**
- Kiro Req 1 properly specifies Auth0 Universal Login with no homebrew auth (AC #7)
- Kiro Req 2 correctly implements stateless scenarios with only user_id stored (AC #7)

### Sheet Connection (FR-4 to FR-7)

| PRD Requirement | Kiro Coverage | Status |
|-----------------|---------------|--------|
| FR-4: User picks from list of Google Sheets | Requirement 3, AC #1 | ✅ Complete |
| FR-5: User can create from template | Requirement 3, AC #5 | ✅ Complete |
| FR-6: Validate required columns | Requirement 3, AC #2-3 | ✅ Complete |
| FR-7: Clear error if columns missing | Requirement 3, AC #4 | ✅ Complete |

**Notes:**
- Kiro Req 3 lists all 10 required columns explicitly
- Template sheet creation is covered

### Daily Processing (FR-8 to FR-12)

| PRD Requirement | Kiro Coverage | Status |
|-----------------|---------------|--------|
| FR-8: Make.com runs once daily per user | Requirement 5, AC #1 | ✅ Complete |
| FR-9: Determine escalation stage by days overdue | Requirement 6 (entire requirement) | ✅ Complete |
| FR-10: Create Gmail draft for appropriate stage | Requirement 7: Draft Creation Logic | ✅ Complete |
| FR-11: Update sheet to record stage sent | Requirement 9: Sheet Tracking Updates | ✅ Complete |
| FR-12: Skip invoices at stage 6 (42+ days) | Requirement 5, AC #6 | ✅ Complete |

**Notes:**
- Kiro Req 6 defines exact day ranges for each escalation stage (7-13, 14-20, etc.)
- Kiro Req 7 prevents duplicate drafts with proper logic checks
- Kiro Req 9 handles sheet write-back with error handling

### Email Drafts (FR-13 to FR-16)

| PRD Requirement | Kiro Coverage | Status |
|-----------------|---------------|--------|
| FR-13: Drafts use user's Gmail as sender | Requirement 8, AC #1 | ✅ Complete |
| FR-14: Drafts NOT auto-sent | Requirement 8, AC #5-6 | ✅ Complete |
| FR-15: 6-stage escalation templates (fixed) | Requirement 18: Email Template Content | ✅ Complete |
| FR-16: Templates include client name, amount, invoice #, sender info | Requirement 8, AC #2-3 | ✅ Complete |

**Notes:**
- Kiro Req 18 defines tone for each stage (friendly → direct → urgent → firm → final warning → last notice)
- Sender info collection covered in Requirement 4

### Billing (FR-17 to FR-20)

| PRD Requirement | Kiro Coverage | Status |
|-----------------|---------------|--------|
| FR-17: Free tier = 3 invoices, skip beyond limit | Requirement 10: Free Tier Limits | ✅ Complete |
| FR-18: Paid tier = unlimited (actually 100 cap), $15/month | Requirement 11: Paid Tier Processing | ✅ Complete |
| FR-19: Payment via Stripe Checkout | Requirement 12: Stripe Payment Integration | ✅ Complete |
| FR-20: Show upgrade prompt when limit reached | Requirement 10, AC #5 | ✅ Complete |

**Notes:**
- Kiro correctly implements 100-invoice hard cap for paid tier (per PRD operational guardrails)
- Free tier limit enforced via invoice_limit in config API

### Operational Guardrails (FR-21 to FR-24)

| PRD Requirement | Kiro Coverage | Status |
|-----------------|---------------|--------|
| FR-21: Global kill switch | ⚠️ **NOT IN KIRO SPECS** | ❌ Gap |
| FR-22: Per-run hard cap (100 invoices paid tier) | Requirement 10, AC #2 (invoice_limit=100) | ✅ Complete |
| FR-23: Fail closed on bad sheet format | ⚠️ **NOT EXPLICITLY IN KIRO** | ⚠️ Partial |
| FR-24: Serialize draft creation (no parallel bursts) | ⚠️ **NOT IN KIRO SPECS** | ❌ Gap |

**Notes:**
- **FR-21 (Kill Switch):** PRD added 2026-02-15. Not in Kiro specs or design.md. Must be added before implementation.
- **FR-23 (Fail Closed):** Kiro Req 3 covers onboarding validation only. PRD's FR-23 specifies "during a daily run, create zero drafts and zero sheet writes" — this daily-run behavior is not in Kiro.
- **FR-24 (Serialize):** Not mentioned in Kiro. Make.com scenarios run sequentially by default, but this should be explicit to prevent future parallel-processing changes from introducing Gmail rate-limit issues.

### Weekly Digest (FR-25 to FR-27)

| PRD Requirement | Kiro Coverage | Status |
|-----------------|---------------|--------|
| FR-25: Weekly summary email every Monday | Requirement 13, AC #1 | ✅ Complete |
| FR-26: Digest includes drafts count, outstanding amount, critical invoices | Requirement 13, AC #2-4 | ✅ Complete |
| FR-27: Digest proves value, justifies subscription | Requirement 13, AC #5 | ✅ Complete |

**Notes:**
- Kiro Req 13 fully implements digest with all required metrics

---

## Architecture Decisions: PRD → Kiro Design

### Resolved Questions from PRD (Section: Resolved Questions 2026-02-14)

| PRD Decision | Kiro Reflection | Status |
|--------------|-----------------|--------|
| 1. Hosting: Vercel serverless | design.md: Deployment section | ✅ Reflected |
| 2. Make.com API: Confirmed programmatic scenario creation | design.md: Make.com integration | ✅ Reflected |
| 3. Make.com pricing: Pro plan, 10k ops/month | design.md: Cost analysis | ✅ Reflected |
| 4. Sheet format: Fixed template for MVP | Requirement 3: Column validation | ✅ Reflected |
| 5. Product name: "Smart Invoice" | Throughout specs | ✅ Reflected |
| 6. Legal: ToS/Privacy needed (Task #4812) | ⚠️ Not in design.md | ⚠️ Deferred |
| 7. Sender info: Name + business during onboarding | Requirement 4 | ✅ Reflected |

### Make.com ↔ Backend Data Flow (PRD Section: Make.com ↔ Backend Data Flow)

| PRD Architecture | Kiro Implementation | Status |
|------------------|---------------------|--------|
| Stateless scenarios, backend as brain | Requirement 2, AC #7 | ✅ Implemented |
| GET /api/users/{user_id}/config | Requirement 21 | ✅ Implemented |
| POST /api/webhooks/make-results | Requirement 22 | ✅ Implemented |
| Config returns: sheet_id, sender_name, business_name, plan, invoice_limit | Requirement 21, AC #2 | ✅ Implemented |
| Webhook accepts: user_id, drafts_created, total_outstanding_amount | Requirement 22, AC #2 | ✅ Implemented |

**Notes:**
- Architecture is fully reflected in Kiro requirements
- API contracts match PRD specifications exactly

---

## Gaps & Recommendations

### Critical Gaps (Must Address Before Implementation)

1. **FR-21: Global Kill Switch**
   - **Issue:** PRD added operational guardrail on 2026-02-15, but Kiro specs not updated
   - **Impact:** Missing critical safety mechanism for production
   - **Recommendation:** Add to Kiro requirements.md as Requirement 23
   - **Implementation:** DB flag or env var `SYSTEM_PAUSED=true`, config API returns `paused=true`

2. **FR-24: Serialize Draft Creation**
   - **Issue:** PRD requires sequential draft creation to prevent Gmail rate issues
   - **Impact:** Risk of Gmail API rate limiting or blast radius if logic is wrong
   - **Recommendation:** Add to Kiro requirements.md, specify Make.com scenario must NOT use parallel processing

### Spec Quality Issues

3. **Kiro requirements.md Numbering Error**
   - **Issue:** Requirement 20 (Data Privacy) appears after Requirement 22 — out of order
   - **Impact:** Low, but creates confusion during traceability audits
   - **Recommendation:** Renumber requirements in sequence

### Minor Gaps (Should Address)

4. **FR-23: Fail Closed on Bad Sheet**
   - **Issue:** Kiro has validation but doesn't explicitly state "zero drafts on failure"
   - **Impact:** Could partially process malformed sheets
   - **Recommendation:** Update Requirement 3 to add AC: "WHEN validation fails, THE System SHALL create zero drafts and zero sheet writes"

5. **Legal Requirements (ToS/Privacy)**
   - **Issue:** PRD mentions Task #4812 for legal docs, but not in Kiro design.md
   - **Impact:** Can't launch without legal docs
   - **Recommendation:** Add to tasks.md or design.md as pre-launch requirement

### Non-Functional Requirements (NFR) Coverage

| PRD NFR | Kiro Coverage | Status |
|---------|---------------|--------|
| NFR-1: 99%+ uptime | ⚠️ Not explicitly in Kiro | ⚠️ Implicit |
| NFR-2: <30s processing per user | ⚠️ Not in Kiro | ⚠️ Missing |
| NFR-3: Security (Make.com OAuth) | Requirement 2 | ✅ Covered |
| NFR-4: Privacy (no invoice data stored) | Requirement 20 | ✅ Covered |
| NFR-5: Scalability (100 users) | ⚠️ Not in Kiro | ⚠️ Missing |
| NFR-6: Monitoring (log every run, alert on 3 failures) | Requirement 14, Requirement 17 | ✅ Covered |
| NFR-7: Monitoring expanded (dead-man switch, spike alerts) | ⚠️ Not in Kiro | ❌ Gap |
| NFR-8: Cost (<$30/month at launch) | ⚠️ Not in Kiro | ⚠️ Missing |

**Recommendation:** NFRs are typically handled in design.md or as system requirements. Most are implicitly covered, but NFR-7 (expanded monitoring) should be added.

---

## UX Requirements Coverage

All UX requirements (UX-1 through UX-11) from PRD are covered in Kiro:
- Landing page: Requirement 15
- Signup flow: Requirements 1-4, 16
- Onboarding completion: Requirement 16
- Invisible operation: Implicit in design
- Weekly digest: Requirement 13
- Error notifications: Requirement 14

**Status: ✅ Complete**

---

## Timeline & Go/No-Go Gates

**PRD Timeline:** 2.5 weeks (Design → Core → Frontend → Payment → Testing → Ship → Distribution)

**Kiro tasks.md:** Contains detailed task breakdown aligned with PRD phases

**Go/No-Go Gates (PRD Section):**
- Gate A (End of Design): DB schema, Make.com blueprint, API contracts
- Gate B (End of Core): E2E test user, kill switch, free tier cap
- Gate C (End of Testing): E2E both tiers, failure alerts, caps verified
- Gate D (Ship Day): DNS, monitoring, smoke test

**Recommendation:** Gates should be added to tasks.md as checkpoints

---

## Floor Manager Assessment

### Strengths
1. ✅ **Comprehensive coverage:** 24 of 27 functional requirements fully covered
2. ✅ **Architecture alignment:** Make.com data flow correctly implemented
3. ✅ **Privacy-first:** No invoice data stored (NFR-4, Req 20)
4. ✅ **User stories:** Kiro requirements use proper EARS format with clear acceptance criteria
5. ✅ **Escalation logic:** 6-stage sequence properly defined with day ranges

### Weaknesses
1. ❌ **Missing operational guardrails:** FR-21 (kill switch), FR-24 (serialize) not in Kiro
2. ⚠️ **NFR gaps:** Performance targets, scalability limits, cost caps not explicit
3. ⚠️ **Monitoring gaps:** NFR-7 expanded monitoring (dead-man switch, spike alerts) missing
4. ⚠️ **Legal deferred:** ToS/Privacy policy not in specs (Task #4812 exists but not in Kiro)
5. ⚠️ **Kiro spec quality:** Requirement numbering out of order (Req 20 appears after Req 22)

### Risks
1. **Operational safety:** Without FR-21 (kill switch) and FR-24 (serialize), production incidents could be harder to contain
2. **Scope creep:** PRD added guardrails on 2026-02-15 after Kiro specs were generated - need to sync
3. **Launch blockers:** Legal docs (ToS/Privacy) required before public launch

---

## Recommendations for Super Manager

### Immediate Actions (Before Implementation Starts)

1. **Update Kiro requirements.md:**
   - Add Requirement 23: Global Kill Switch (FR-21)
   - Add Requirement 24: Serialize Draft Creation (FR-24)
   - Update Requirement 3 to explicitly state "fail closed" behavior (FR-23)

2. **Update Kiro design.md:**
   - Add operational guardrails section
   - Add monitoring/alerting architecture (NFR-7)
   - Add legal requirements section (ToS/Privacy)

3. **Update Kiro tasks.md:**
   - Add Go/No-Go gate checkpoints from PRD
   - Add task for legal doc creation (Task #4812)
   - Add tasks for kill switch implementation

### Strategic Considerations

1. **Timeline Risk:** PRD says 2.5 weeks. Current date is 2026-02-15. PRD note says "SIW development starts week of Feb 17". That's **2 days from now**. Are we ready?

2. **Dependency Risk:** Make.com Pro plan ($16/mo) is critical path. Is account set up? API access confirmed?

3. **Scope Discipline:** PRD Non-Goals section is extensive. Recommend printing it and posting it visibly during implementation to prevent scope creep.

---

## Final Verdict

**Traceability Status: ✅ ALIGNED (with 3 gaps to address)**

The Kiro specifications correctly implement the PRD vision with 24 of 27 functional requirements fully covered. The 3 gaps (FR-21, FR-23, FR-24) are all from the 2026-02-15 PRD update (operational guardrails) and need to be added to Kiro specs before implementation begins.

**Recommendation:** 
1. Address the 3 critical gaps in Kiro specs (1-2 hour update)
2. Confirm Make.com account and API access
3. Proceed with implementation starting week of Feb 17

**Confidence Level:** High - The foundation is solid, gaps are well-defined and fixable.

---

## Appendix: Document References

- **PRD:** `PRD.md`
- **Kiro Requirements:** `.kiro/specs/smart-invoice/requirements.md`
- **Kiro Design:** `.kiro/specs/smart-invoice/design.md`
- **Kiro Tasks:** `.kiro/specs/smart-invoice/tasks.md`

**Analysis Date:** 2026-02-15
**Draft:** Antigravity (Floor Manager)
**Final Review:** Claude Opus (Super Manager)

---

*This proposal confirms the project is ready to proceed with implementation, pending resolution of the 3 identified gaps.*
