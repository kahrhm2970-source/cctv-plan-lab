# CCTV Plan Lab | تخطيط تخزين كاميرات المراقبة وPoE

**الحسين علي أبو طالب — Alhussin Ali Abutalib**

Educational CCTV / Network Technician portfolio built with AI assistance. All inputs are fictional; no customer system, recording, employer information or production deployment is represented.

## Purpose

أداة Python تعمل محليًا لتقدير تخزين التسجيلات ومراجعة ميزانية طاقة PoE وعدد المنافذ، وتصدر تقرير HTML وJSON. لا تتصل بالكاميرات ولا تطلب عناوين أو كلمات مرور أو تسجيلات.

## Run (Python 3.10+, no dependencies)

```sh
python cctv_plan.py examples/plan.json --out reports/demo
python -m unittest discover -s tests -v
```

Open reports/demo/report.html. Use python3 or Windows py -3 if needed. Codespaces supports these commands; download HTML for mobile viewing. Exit 0 means no modeled shortfall, 1 means review findings with reports generated, 2 means invalid input/I/O failure. Old reports may remain after failure: check exit code. Outputs with the same names are overwritten.

## Synthetic example

8 cameras × 4 Mbps, recording 24 h/day for 30 days, with 4 TB usable storage; one 8-port switch with 120 W budget and 30 W per-port limit. Camera demand is assumed to be 15 W **at the PSE/switch**, including an allowance for cable losses. Added storage and total PoE planning margins are both 20% (lab choices, not standards).

| Result | Value |
|---|---:|
| Sum of stream bitrates | 32 Mbps |
| Raw video per day | 0.3456 TB |
| Raw video for 30 days | 10.368 TB |
| Planned storage including margin | 12.4416 TB |
| PSE load / with margin | 120 W / 144 W |
| Findings | Storage shortfall + PoE budget shortfall |

Changing usable storage to 16 TB and switch budget to 180 W removes these modeled findings. This is not a product recommendation or guarantee.

## Formulas and assumptions

Decimal Mbps = 10^6 bits/s; TB = 10^12 bytes. Daily video TB = sum(count × bitrate Mbps × 10^6 ÷ 8 × recording hours/day × 3600) ÷ 10^12. Required planned TB = daily TB × target days × (1 + storage margin/100). Planning retention days = usable TB ÷ [daily TB × (1 + storage margin/100)]. This retention includes a planning allowance; it is not measured playback retention.

PoE load per switch = sum(camera count × PSE watts/camera). Planned load = load × (1 + PoE margin/100), compared to the switch's total available PoE budget. Each group's un-margined PSE watts/camera is checked against the supplied PSE per-port limit. Camera count is compared with available camera ports; exclude uplinks and reserved ports from the supplied port count.

Use validated device specifications and worst-case demand for IR illumination, heaters, PTZ movement and startup. A camera-side watt rating is not automatically a switch-side allocation: account for losses/class reservations using vendor documentation before entering PSE watts. The tool does not determine IEEE class negotiation, PD/PSE compatibility, cable losses, UPS runtime, temperature derating or actual startup behavior.

The bitrate sum is a stream payload estimate, not link sizing: it excludes protocol overhead, live viewing, playback, secondary streams and other network traffic. Supply a measured or approved planning bitrate, including audio if recorded. Resolution and codec are not automatically translated into bitrate. Scene activity and compression affect real recordings. Recording hours are an assumption; motion recording is not guaranteed to achieve that duty cycle.

Usable storage must already account for RAID, filesystem and reserved space. This utility does not calculate raw-disk capacity or RAID. Storage margin is an additional user-selected allowance, not an automatic estimate of actual overhead. Equality with a limit passes; comparisons use unrounded values, displayed results are rounded.

## Input contract

Exact JSON fields are shown in examples/plan.json; extra fields and duplicate keys are rejected. Switch IDs SW-number and group IDs GROUP-number are synthetic and unique; each group uses one switch, one port per camera. 1–128 switches, 1–1000 groups; integer counts 1–10000; ports 1–256. Finite numeric bounds: bitrate 0.001–1000 Mbps, recording time 0.001–24 h/day, PSE demand 0.001–1000 W, switch budget 0–10000 W, port limit 0–1000 W, target days 1–3650, usable storage 0–100000 TB, margins 0–100%. File limit 1 MiB. Booleans are not accepted as numbers.

## Privacy and limitations

Only fictional plans belong in public GitHub. Real camera counts, storage and power topology can be sensitive: keep plans and reports private. No CCTV footage, passwords, personal names or site locations are needed. No face recognition, surveillance analytics, network scanning, remote access, automatic configuration or compliance assessment. The retention target is supplied by the user; no Saudi legal retention requirement is implied. A successful calculation does not validate image quality, coverage, operational continuity or security.

See [Arabic field checklist](docs/CHECKLIST_AR.md) for an interview demo and human verification steps.

## Primary references

- [Axis: bitrate control for IP video](https://whitepapers.axis.com/en-us/bitrate-control-for-ip-video)
- [Axis: bitrate modes and retention/storage settings](https://help.axis.com/en-us/axis-os-web-interface-help)
- [Python unittest](https://docs.python.org/3/library/unittest.html)

References explain technical context; the example, formulas' planning margins and limits are this lab's assumptions. AI assistance was used for code, tests and documentation. This is a training estimator, not an engineered design or certified installation.
