"""Seeded procedural fish drawing engine. Produces plotter-friendly SVG polylines."""

from __future__ import annotations

import argparse
import math
import random
from dataclasses import dataclass
from pathlib import Path

Point = tuple[float, float]
Polyline = list[Point]


@dataclass
class Fish:
    body_length: float = 200
    body_height: float = 80
    tail_size: float = 0.8
    fin_count: int = 3
    fin_angle: float = 30
    eye_size: float = 5
    curvature: float = 0.4
    randomness: float = 0.2
    seed: int | str | None = None
    species: str = "oval"  # oval, slender, or deep

    def __post_init__(self) -> None:
        if self.body_length <= 0 or self.body_height <= 0:
            raise ValueError("body_length and body_height must be positive")
        if self.tail_size < 0 or self.eye_size < 0:
            raise ValueError("tail_size and eye_size cannot be negative")
        if not 0 <= self.randomness <= 1:
            raise ValueError("randomness must be between 0 and 1")
        if self.fin_count < 0:
            raise ValueError("fin_count cannot be negative")
        if self.species not in {"oval", "slender", "deep"}:
            raise ValueError("species must be 'oval', 'slender', or 'deep'")

    def polylines(self) -> list[Polyline]:
        """Return the fish's outline and decorative marks as stroke paths."""
        rng = random.Random(self.seed)
        length, height = self.body_length, self.body_height
        half = height / 2
        shape = {"oval": 1.0, "slender": 0.70, "deep": 1.25}[self.species]
        phase = rng.random() * math.tau
        # Smooth value noise gives the contour the same coherent, layered
        # variation as the reference generator without jagged point noise.
        noise_lattice: dict[tuple[int, int], float] = {}

        def value_noise(x: float, y: int) -> float:
            ix, iy = math.floor(x), y
            fx = x - ix
            smooth = fx * fx * (3 - 2 * fx)
            key_a, key_b = (ix, iy), (ix + 1, iy)
            if key_a not in noise_lattice:
                noise_lattice[key_a] = rng.random()
            if key_b not in noise_lattice:
                noise_lattice[key_b] = rng.random()
            a, b = noise_lattice[key_a], noise_lattice[key_b]
            return a * (1 - smooth) + b * smooth

        # Curvature changes how quickly the body rounds out from the nose.
        # The ends taper to points, as a real fish body does at the snout and
        # caudal peduncle, instead of retaining an oval's blunt end caps.
        exponent = 0.68 + (1 - min(1.0, self.curvature)) * 0.35

        def body_half_at(t: float, side: int = -1) -> float:
            t = max(0.001, min(0.999, t))
            # Broad shoulder and narrow tail root follow an asymmetric fish
            # profile. Keep organic variation subtle so the silhouette stays
            # readable and smooth.
            noise = value_noise(t * 3.2 + phase, side)
            profile = math.sin(math.pi * t) ** exponent
            shoulder = 1.12 - 0.30 * t + self.curvature * (0.18 - t) * 0.10
            ripple = 1 + self.randomness * (noise - 0.5) * 0.075
            return half * shape * profile * shoulder * ripple

        # Slightly pointed head and tapered peduncle at the tail.
        body: Polyline = []
        steps = 100
        for side in (-1, 1):
            samples = range(steps + 1) if side == -1 else range(steps, -1, -1)
            for i in samples:
                t = i / steps
                y = side * body_half_at(t, side)
                body.append((length * t, y))
        paths = [body]

        # Tail outline, membrane edge and rays.
        tail = self.tail_size * height
        tail_tip = length + tail * 0.55
        paths.append([(length - 5, -height * .035), (tail_tip, -tail * .62),
                      (length + tail * .36, 0), (tail_tip, tail * .62),
                      (length - 5, height * .035), (length - 5, -height * .035)])
        for i in range(7):
            end_y = -tail * .55 + i * tail * .183
            paths.append([(length - 2, end_y * .08), (tail_tip - tail * .05, end_y)])

        # Dorsal, pelvic and anal fins attach to the actual body contour.
        angle = math.radians(self.fin_angle)
        # The first three are dorsal, pelvic and anal fins. Extra fins become
        # small dorsal/anal finlets, as in the source algorithm.
        fin_specs = [(0.28, 0.19, -1, .34), (0.38, 0.14, 1, .23), (0.67, 0.16, 1, .21)]
        for fin_index in range(max(0, self.fin_count - len(fin_specs))):
            fin_specs.append((.78 + fin_index * .045, .055, -1, .12))
        for t, span, side, fin_height in fin_specs[:self.fin_count]:
            x0, x1 = length * t, length * min(.94, t + span)
            y0, y1 = side * body_half_at(t, side), side * body_half_at(min(.98, t + span), side)
            tip_x = x0 + (x1 - x0) * .48 + fin_height * height * math.sin(angle)
            tip_y = side * (max(abs(y0), abs(y1)) + fin_height * height * math.cos(angle))
            # A curved outer edge makes the silhouette read as a fin rather
            # than a triangular spike.
            mid_x = (x0 + x1) * .5
            fin = [(x0, y0), (mid_x - height * .035, y0 + (tip_y-y0)*.54),
                   (tip_x, tip_y), (mid_x + height * .035, y1 + (tip_y-y1)*.48),
                   (x1, y1), (x0, y0)]
            paths.append(fin)
            for j in range(1, 7):
                u = j / 7
                bx, by = x0 + (x1 - x0) * u, y0 + (y1 - y0) * u
                paths.append([(bx, by), (bx + (tip_x - bx) * .82, by + (tip_y - by) * .82)])

        # Pectoral fin with rays, placed behind the gill cover.
        px, py = length * .43, height * .08
        ptip = (px - height * .20, py + height * .38)
        pbase = (px + height * .16, py + height * .18)
        paths.append([(px, py), ptip, pbase, (px, py)])
        for u in (.2, .4, .6, .8):
            paths.append([(px + (pbase[0] - px) * u, py + (pbase[1] - py) * u),
                          (px + (ptip[0] - px) * u * .78, py + (ptip[1] - py) * u * .78)])

        # Gill plate and several curved gill slits.
        gx = length * .235
        paths.append([(gx + height * .12 * math.cos(-1.15 + i * 2.3 / 24),
                       height * .30 * math.sin(-1.15 + i * 2.3 / 24)) for i in range(25)])
        for offset in (0, height * .035, height * .07):
            paths.append([(gx + height * .11 + offset * .25, -height * .16 + offset),
                          (gx + height * .17 + offset * .15, 0),
                          (gx + height * .10 + offset * .25, height * .16 - offset)])

        # Pick a body pattern once from the seed: scale arcs, bars, or spots.
        pattern_type = rng.choices((0, 1, 2, 3), weights=(2, 4, 2, 2))[0]
        # Staggered scale arcs follow the reference's mesh-like scale pattern.
        scale_w = length * .047
        for row in range(-2, 3):
            for col in range(3, 16):
                cx = length * (col / 19) + (row % 2) * scale_w * .5
                cy = row * height * .095
                if not (.31 * length < cx < .87 * length):
                    continue
                t = cx / length
                bound = body_half_at(t)
                if pattern_type != 1 or abs(cy) + height * .035 > bound * .82:
                    continue
                # Short inverted-U arcs suggest scales without cluttering the outline.
                paths.append([(cx + scale_w * math.cos(math.pi * k / 8),
                               cy - math.copysign(height * .035, cy or 1) * math.sin(math.pi * k / 8))
                              for k in range(9)])

        # A few broken vertical bars add a second common fish pattern.
        if pattern_type == 2:
            for col in range(5, 15, 2):
                cx = length * col / 20
                for side in (-1, 1):
                    paths.append([(cx + math.sin(j / 10 * math.pi) * height * .018,
                                   side * body_half_at(cx / length, side) * (0.18 + j * .064))
                                  for j in range(11)])
        elif pattern_type == 3:
            # Sparse rosettes, varying size and spacing deterministically.
            for _ in range(15):
                cx = length * rng.uniform(.30, .82)
                cy = rng.uniform(-.55, .55) * body_half_at(cx / length)
                radius = height * rng.uniform(.018, .035)
                paths.append([(cx + radius * math.cos(math.tau * i / 20),
                               cy + radius * .62 * math.sin(math.tau * i / 20))
                              for i in range(21)])

        # Fine belly hatching reads like scale texture and gives the body depth.
        if pattern_type in (1, 2):
            for col in range(8, 17):
                t = col / 20
                x = length * t
                edge = body_half_at(t, 1)
                for row in range(2):
                    y = edge * (.58 + row * .12)
                    paths.append([(x, y), (x + height * .035, y + height * .018)])

        # Eye ring, iris, pupil, brow and a small nostril.
        eye_x, eye_y = length * .105, -height * .075
        for radius, count in ((self.eye_size, 28), (self.eye_size * .53, 20)):
            paths.append([(eye_x + radius * math.cos(math.tau * i / count),
                           eye_y + radius * math.sin(math.tau * i / count)) for i in range(count + 1)])
        pupil_r = max(.7, self.eye_size * .22)
        paths.append([(eye_x + pupil_r * math.cos(math.tau * i / 16),
                       eye_y + pupil_r * math.sin(math.tau * i / 16)) for i in range(17)])
        paths.append([(eye_x - self.eye_size * .9, eye_y - self.eye_size * 1.25),
                      (eye_x, eye_y - self.eye_size * 1.55),
                      (eye_x + self.eye_size * 1.0, eye_y - self.eye_size * 1.2)])
        paths.append([(length * .035, -height * .045), (length * .075, -height * .035)])
        # Mouth line and lower lip.
        paths.append([(0, height * .005), (length * .035, height * .012), (length * .075, height * .008)])
        paths.append([(length * .012, height * .035), (length * .06, height * .04)])
        return paths

    def svg(self, padding: float = 16, stroke: str = "#17212b") -> str:
        paths = self.polylines()
        points = [point for path in paths for point in path]
        min_x, max_x = min(p[0] for p in points), max(p[0] for p in points)
        min_y, max_y = min(p[1] for p in points), max(p[1] for p in points)
        width, height = max_x - min_x + 2 * padding, max_y - min_y + 2 * padding
        markup = []
        for index, path in enumerate(paths):
            coords = " ".join(f"{x - min_x + padding:.2f},{y - min_y + padding:.2f}" for x, y in path)
            # Give the silhouette hierarchy: strong outline, lighter anatomy,
            # and fine texture marks.
            weight = 1.8 if index == 0 else (1.25 if index < 12 else 0.72)
            markup.append(f'<polyline points="{coords}" fill="none" stroke="{stroke}" stroke-width="{weight}" stroke-linecap="round" stroke-linejoin="round"/>')
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width:.0f}" height="{height:.0f}" '
                f'viewBox="0 0 {width:.2f} {height:.2f}">\n' + "\n".join(markup) + "\n</svg>\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a seeded procedural fish as SVG")
    parser.add_argument("--seed", default="fish-1")
    parser.add_argument("--species", choices=("oval", "slender", "deep"), default="oval")
    parser.add_argument("--output", "-o", default="fish.svg")
    parser.add_argument("--body-length", type=float, default=200)
    parser.add_argument("--body-height", type=float, default=80)
    parser.add_argument("--tail-size", type=float, default=0.8)
    parser.add_argument("--fin-count", type=int, default=3)
    parser.add_argument("--fin-angle", type=float, default=30)
    parser.add_argument("--eye-size", type=float, default=5)
    parser.add_argument("--curvature", type=float, default=0.4)
    parser.add_argument("--randomness", type=float, default=0.2)
    args = parser.parse_args()
    fish = Fish(args.body_length, args.body_height, args.tail_size, args.fin_count,
                args.fin_angle, args.eye_size, args.curvature, args.randomness,
                args.seed, args.species)
    Path(args.output).write_text(fish.svg(), encoding="utf-8")
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
