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
        """Return the fish as independent stroke paths in a local coordinate system."""
        rng = random.Random(self.seed)
        length, height = self.body_length, self.body_height
        half = height / 2
        shape = {"oval": 1.0, "slender": 0.70, "deep": 1.25}[self.species]
        # Body runs from x=0 (nose) to x=length (tail root).
        body: Polyline = []
        steps = 40
        for i in range(steps + 1):
            t = i / steps
            x = length * t
            # Bulge peaks slightly behind the head; taper both ends.
            profile = math.sin(math.pi * (t ** 0.82)) ** 0.72
            asymmetry = 1 + self.curvature * (0.35 - t) * 0.5
            noise = self._noise(rng)
            y = -half * shape * profile * asymmetry * (1 + noise)
            body.append((x, y))
        for i in range(steps, -1, -1):
            t = i / steps
            x = length * t
            profile = math.sin(math.pi * (t ** 0.82)) ** 0.72
            asymmetry = 1 + self.curvature * (0.35 - t) * 0.5
            y = half * shape * profile * asymmetry * (1 + self._noise(rng))
            body.append((x, y))
        paths = [body]

        # Forked tail, sized relative to the body height.
        tail = self.tail_size * height
        paths.append([(length - 2, 0), (length + tail * 0.50, -tail * 0.62),
                      (length + tail * 0.34, 0), (length + tail * 0.50, tail * 0.62),
                      (length - 2, 0)])

        # Fins are distributed over the back and belly, with the requested angle.
        fin_sites = [(0.34 + i * 0.29, -1 if i % 2 == 0 else 1)
                     for i in range(self.fin_count)]
        angle = math.radians(self.fin_angle)
        for index, (t, side) in enumerate(fin_sites):
            x = length * min(0.82, t)
            base = half * shape * (0.82 if t < 0.75 else 0.5)
            fin_len = height * (0.22 if index else 0.30)
            # Angle controls the fin's sweep; side selects back or belly.
            dx = fin_len * math.sin(angle)
            dy = side * fin_len * math.cos(angle)
            fin: Polyline = [(x - fin_len * 0.24, side * base),
                             (x + dx, side * base + dy),
                             (x + fin_len * 0.38, side * base * 0.65)]
            paths.append(fin)

        # Pectoral fin and gill detail.
        pectoral_x = length * 0.43
        paths.append([(pectoral_x, -height * 0.04),
                      (pectoral_x - height * 0.16, height * 0.35),
                      (pectoral_x + height * 0.12, height * 0.12)])
        gill_x = length * 0.22
        paths.append([(gill_x + height * 0.12, -height * 0.20),
                      (gill_x + height * 0.19, 0),
                      (gill_x + height * 0.10, height * 0.20)])

        # Eye as a 24-segment circle.
        eye_x, eye_y = length * 0.105, -height * 0.075
        eye: Polyline = [(eye_x + self.eye_size * math.cos(2 * math.pi * i / 24),
                          eye_y + self.eye_size * math.sin(2 * math.pi * i / 24))
                         for i in range(25)]
        paths.append(eye)
        return paths

    def _noise(self, rng: random.Random) -> float:
        return rng.uniform(-self.randomness, self.randomness) * 0.22

    def svg(self, padding: float = 16, stroke: str = "#17212b") -> str:
        paths = self.polylines()
        points = [point for path in paths for point in path]
        min_x, max_x = min(p[0] for p in points), max(p[0] for p in points)
        min_y, max_y = min(p[1] for p in points), max(p[1] for p in points)
        width, height = max_x - min_x + 2 * padding, max_y - min_y + 2 * padding
        markup = []
        for path in paths:
            coords = " ".join(f"{x - min_x + padding:.2f},{y - min_y + padding:.2f}" for x, y in path)
            markup.append(f'<polyline points="{coords}" fill="none" stroke="{stroke}" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"/>')
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
