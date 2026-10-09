"""Stage C search geometry (skyscan/mission/search.py): strips, red grid, A* detours, route, evasion. Pure python."""
import math

import pytest

from skyscan.mission.search import (PathFollower, Zone, ZoneGrid, dist, footprint_m, make_strips, plan_evasion, route_points,
                                    strip_spacing_m, swath_m)

ZONE = Zone(22.0, 62.0, -12.0, 18.0)                  # sim/course.yaml delivery zone: 40 m x 30 m
RED1 = [(27.5, -4.5), (30.5, -4.5), (30.5, -1.5), (27.5, -1.5)]      # the two 3 x 3 m no-land zones of the sim course
RED2 = [(45.5, 6.5), (48.5, 6.5), (48.5, 9.5), (45.5, 9.5)]


def grid_with(*polys, margin=1.5):
    g = ZoneGrid(ZONE, res_m=0.5, margin_m=margin)
    for poly in polys:
        g.add_polygon(poly)
        g.add_polygon(poly)                             # confirm_hits = 2: a second sighting confirms the cells
    return g


def test_swath_and_spacing():
    assert swath_m(10.0, 60.0) == pytest.approx(11.547, abs=1e-3)
    assert strip_spacing_m(10.0, 60.0, 0.30) == pytest.approx(8.083, abs=1e-3)
    assert strip_spacing_m(1.0, 60.0, 0.30) == 3.0                       # never below the minimum
    along, across = footprint_m(10.0, 60.0)
    assert across == pytest.approx(11.547, abs=1e-3) and along == pytest.approx(8.660, abs=1e-3)


def test_strips_cover_the_zone_in_a_lawnmower_pattern():
    strips = make_strips(ZONE, 5.4, inset_m=1.0, start=(20.0, 0.0))
    assert len(strips) == 6                                              # ceil(30 / 5.4)
    rights = [s.right for s in strips]
    assert rights == pytest.approx([-9.5, -4.5, 0.5, 5.5, 10.5, 15.5])   # evenly spread, spacing 5.0 <= 5.4
    assert strips[0].start == (23.0, -9.5)                               # starts at the outer strip nearer to the entry
    for a, b in zip(strips[:-1], strips[1:]):                            # boustrophedon: each strip starts where the last ended
        assert b.f_start == a.f_end
    for s in strips:
        assert ZONE.inset(1.0).contains(s.start) and ZONE.inset(1.0).contains(s.end)
        assert s.length_m == pytest.approx(38.0)


def test_strips_start_from_the_nearer_side():
    strips = make_strips(ZONE, 5.4, start=(20.0, 17.0))
    assert strips[0].right == 15.5 and strips[-1].right == -9.5


def test_red_cells_need_two_sightings_and_get_a_margin():
    g = ZoneGrid(ZONE, res_m=0.5, margin_m=1.5)
    assert g.add_polygon(RED1) == 0 and not g.red.any()                  # one frame is not enough
    n = g.add_polygon(RED1)
    assert n > 0 and g.version == 1
    area = g.red.sum() * g.res ** 2
    assert 8.0 <= area <= 12.0                                           # a 3 x 3 m patch (+ the half-cell boundary rule)
    assert g.blocked((29.0, -3.0))                                       # in the red
    assert g.blocked((29.0, -0.2))                                       # 1.3 m from its edge: inside the 1.5 m margin
    assert not g.blocked((29.0, 1.0))                                    # clear of it
    assert g.blocked((10.0, 0.0))                                        # outside the zone = fenced
    assert g.dist_to_red((29.0, 1.5)) == pytest.approx(3.0, abs=0.6)
    boxes = g.red_boxes()
    assert len(boxes) == 1 and boxes[0][0] <= 27.6 and boxes[0][1] >= 30.4


def test_plan_goes_straight_when_clear_and_around_when_not():
    g = grid_with(RED1)
    clear = g.plan((24.0, 8.0), (40.0, 8.0))
    assert clear.ok and clear.path == [(40.0, 8.0)]
    blocked = g.plan((24.0, -3.0), (36.0, -3.0))                         # straight through red1
    assert blocked.ok and len(blocked.path) >= 2
    pts = [(24.0, -3.0)] + blocked.path
    assert all(g.segment_clear(a, b) for a, b in zip(pts[:-1], pts[1:]))
    assert blocked.length_m > 12.0 + 1.0                                 # longer than the blocked straight line
    assert blocked.path[-1] == (36.0, -3.0) and not blocked.goal_adjusted


def test_plan_moves_a_goal_inside_the_keepout_and_walks_out_of_it():
    g = grid_with(RED1)
    res = g.plan((24.0, 8.0), (29.0, -3.0))                              # the goal is the red zone itself
    assert res.ok and res.goal_adjusted and not g.blocked(res.path[-1])
    out = g.plan((29.0, -0.5), (40.0, 5.0))                              # the vehicle is inside the margin already
    assert out.ok and not g.blocked(out.path[-1])
    assert not g.blocked(out.path[0])                                    # first point is the escape cell


def test_route_never_crosses_a_red_zone_and_covers_the_zone():
    g = grid_with(RED1, RED2)
    strips = make_strips(ZONE, 5.4, start=(20.0, 0.0))
    legs = g.route((20.0, 0.0), strips, 0)
    pts = route_points((23.0, -9.5), legs)                               # starts on the first strip
    for a, b in zip(pts[:-1], pts[1:]):
        assert g.segment_clear(a, b), f"crosses the keep-out: {a} -> {b}"
    assert any(not leg.sweeping for leg in legs) and any(leg.sweeping for leg in legs)
    # fly the route with the camera footprint of the real belly camera at 10 m and count what was covered
    along, across = footprint_m(10.0, 60.0)
    for a, b in zip(pts[:-1], pts[1:]):
        n = max(1, int(math.hypot(b[0] - a[0], b[1] - a[1]) / 0.5))
        for k in range(n + 1):
            t = k / n
            g.mark_footprint((a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1])), along / 2, across / 2)
    assert g.coverage() >= 0.98


def test_route_detours_a_strip_that_runs_through_red():
    g = grid_with(RED1)
    strips = make_strips(ZONE, 5.4, start=(20.0, 0.0))
    strip = strips[1]                                                    # right = -4.5: along red1's left edge
    runs = g.free_runs(strip)
    assert len(runs) == 2                                                # split in two around the keep-out
    assert runs[0][1] < strip.along((27.5, -4.5)) and runs[1][0] > strip.along((30.5, -4.5))


def test_route_resumes_from_the_middle_of_a_strip():
    g = grid_with()
    strips = make_strips(ZONE, 5.4, start=(20.0, 0.0))
    legs = g.route((40.0, -9.5), strips, 0)
    assert legs[0].strip == 0 and legs[0].sweeping                       # only the rest of strip 0 comes first
    assert legs[0].pts == [strips[0].end]
    assert legs[1].strip == 1 and not legs[1].sweeping                   # then the hop to the next strip


def test_path_follower_carrot_and_remaining_length():
    f = PathFollower([(0.0, 0.0), (10.0, 0.0), (10.0, 5.0)], lookahead_m=1.5, reach_m=0.3)
    carrot, rem = f.update((0.0, 0.0))
    assert carrot == pytest.approx((1.5, 0.0)) and rem == pytest.approx(15.0)
    carrot, rem = f.update((9.9, 0.0))                                   # reached the corner: now heading to (10, 5)
    assert carrot[0] == pytest.approx(10.0, abs=0.2) and carrot[1] > 0.5 and rem == pytest.approx(5.1, abs=0.3)
    f.update((10.0, 4.9))
    assert f.done


def test_first_blocked_along_sees_red_ahead():
    g = grid_with(RED1)
    path = [(23.0, -3.0), (40.0, -3.0)]
    d = g.first_blocked_along(path, look_m=10.0)
    assert d is not None and d == pytest.approx(27.5 - 1.5 - 23.0, abs=0.6)      # keep-out starts 1.5 m before the red
    assert g.first_blocked_along(path, look_m=2.0) is None                        # not within 2 m yet
    assert g.first_blocked_along([(23.0, 10.0), (40.0, 10.0)], look_m=30.0) is None


def test_evasion_backs_off_two_metres_then_sidesteps_clear_of_the_boundary():
    g = grid_with(RED1)
    pos = (25.0, -3.0)                                                   # heading east (+fwd) straight at red1, 1 m from the margin
    plan = plan_evasion(g, pos, (1.0, 0.0), reverse_m=2.0)
    assert plan.ok
    assert plan.reverse_to == pytest.approx((23.0, -3.0))                # 2 m back along the entry vector
    assert plan.side in ("left", "right") and 0.0 < plan.lateral_m <= 6.0
    assert not g.blocked(plan.offset_to)
    far = (plan.offset_to[0] + 5.5, plan.offset_to[1])                   # the straight line ahead is now clean
    assert g.segment_clear(plan.offset_to, far)


def test_evasion_prefers_the_side_away_from_the_red():
    g = grid_with(RED1)
    plan = plan_evasion(g, (25.0, -1.8), (1.0, 0.0))                     # red is mostly to the left of the line of flight
    assert plan.side == "right"
    plan2 = plan_evasion(g, (25.0, -4.2), (1.0, 0.0))                    # and now mostly to the right
    assert plan2.side == "left"


def test_evasion_when_walled_in_goes_as_far_as_it_can():
    g = ZoneGrid(Zone(0.0, 10.0, 0.0, 4.0), res_m=0.5, margin_m=1.5)
    for p in ([(4.0, 0.0), (6.0, 0.0), (6.0, 4.0), (4.0, 4.0)],) * 2:
        g.add_polygon(p)                                                 # red across the whole width of the zone
    plan = plan_evasion(g, (2.0, 2.0), (1.0, 0.0))
    assert not plan.ok


def test_follower_does_not_stall_when_the_vehicle_cuts_a_corner():
    # the vehicle is already on the segment after the corner: the carrot must stay ahead of it, not collapse onto it
    f = PathFollower([(25.75, -3.25), (25.75, -0.75), (27.25, 0.25), (31.25, 0.25)], 1.5, 0.4)
    pos = (27.01, 0.11)
    carrot, remaining = f.update(pos)
    assert f.seg == 2
    assert dist(carrot, pos) > 1.2
    assert carrot[0] > pos[0]
    assert remaining == pytest.approx(4.28, abs=0.1)


def test_follower_stops_at_a_switchback_instead_of_folding_the_lookahead_over_it():
    # a path that turns back on itself: the lookahead must end at the corner, never double back onto the vehicle
    f = PathFollower([(26.72, -7.22), (26.75, -9.5), (27.75, -9.5), (25.75, -5.25)], 1.5, 0.4)
    carrot, _ = f.update((27.62, -9.23))
    assert dist(carrot, (27.62, -9.23)) > 0.2 or f.seg >= 1
