# Issue contract — Rack Power Autopilot

## Problem
Power, hardware reliability, scheduling, checkpointing, recovery, and utilization at cluster scale.

## Desired outcome
A bounded, open, testable implementation of **Rack Power Autopilot** that demonstrates Close the loop from power/thermal telemetry to job admission decisions with hard refuse states.

## Non-goals
- CoreWeave affiliation or proprietary integration
- Portfolio-wide scale/performance claims
- UI marketing site

## Acceptance
1. Mechanism module implements allow + refuse with structured receipts
2. pytest behavioral suite green
3. operate.py cold-start produces JSON receipt
4. Non-affiliation disclaimer preserved
