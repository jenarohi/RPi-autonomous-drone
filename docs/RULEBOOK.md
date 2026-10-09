# AeroTHON 2026 - Track 1 rulebook (Rev 2, March 2026)

Full PDF: [`rulebook/AEROTHON-2026-Track-1-Rulebook_Rev2.pdf`](rulebook/AEROTHON-2026-Track-1-Rulebook_Rev2.pdf)

The rulebook is the source of truth for the mission. The sections below are the
parts our software depends on, with PDF page numbers. Anything in the stage docs
that is *not* listed here is a team design decision, not a rule.

## Aircraft limits (p.19, Table 1)

Multirotor, < 2 kg take-off weight (MTOW 2 kg), 100 g payload (10 x 5 x 5 cm),
electric, comms range >= 1 km.

## Mission 2 - SkyScan, fully autonomous (p.35-37, scoring p.42)

| # | Phase | Rule | Marks |
|---|-------|------|-------|
| 1 | Takeoff + start QR | Take off autonomously, climb to 5 m, move forward ~1 m, scan and decode the start QR (delivery location) | 10 |
| 2 | Corridor | Find the green AeroTHON 2026 banner at the corridor entrance, align, descend to 10 ft (~3 m), fly the 3.5 m wide corridor avoiding static obstacles | 15 |
| 3 | Target ID | In the delivery zone climb to ~10 m, find the QR that matches the start QR among several | 10 |
| 4 | Red zones | Detect and avoid restricted red zones. Each violation costs **-5** from the marks earned | 10 |
| 5 | Delivery | Descend to ~5 m, **lower** the payload with a controlled pulley and release it only once it reaches the ground at the target QR. Marked on drop accuracy, altitude compliance and stability | 15 |
| 6 | Return | Ascend, fly back through the corridor avoiding obstacles (return-lap banner detect + align) | 20 |
| 7 | Landing | Land at the take-off point with no manual intervention | 5 |
| 8 | Time | Whole mission inside 15 min; marks proportional to speed | 15 |

Other rules (p.36-37):

- Delivery zone is 40 m x 30 m in Figure 3. The **geo-fence coordinates are
  given to teams in Phase 2** and must be programmed into the ground station.
- Corridor is 10 m long, 3.5 m wide, 10 ft high. Figure 3 draws a green lane
  (forward lap) and an orange lane with black static obstacles (return lap).
  "Flight path and layout are subject to change on event day."
- Record flight data and hand it to the jury after the mission.
- Scoring criteria are preliminary; final criteria follow Phase 1 (p.42 note).

## Not in the rulebook

- Nothing says which sensors are allowed or required, and lidar is not mentioned.
  The rulebook only asks for "autonomous navigation, sensing, QR detection and
  precision payload delivery" (p.18). The camera / lidar / rangefinder choice
  is ours.
- Search pattern, strip overlap, red-zone evasion steps (halt, reverse 2 m,
  offset within 5 s) and the HSV thresholds are team design (Stage C spec), not
  rules. The rulebook only requires that red zones are detected and avoided.

## Ambiguities to confirm with the organisers

- p.36 "Return Flight" says ascend to *10-meter* altitude and fly back through
  the corridor, while the corridor height is 10 *feet*. Likely a typo for 10 ft.
  Stage D (return) must not climb above corridor height without confirmation.
- Release method: p.37 says the payload is *lowered* from 5 m and released on
  reaching the ground, i.e. a winch/pulley, not a drop.
