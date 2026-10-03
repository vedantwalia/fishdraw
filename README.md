# Fishdraw (Python)

A small, dependency-free procedural fish drawing engine inspired by the linked
fishdraw project. It creates plotter-friendly SVG made from polylines. A seed
produces a repeatable drawing.

## Generate an SVG

```sh
python3 fishdraw.py --seed "Biggus fishus" --species deep --fin-count 4 -o fish.svg
```

Available species shapes are `oval`, `slender`, and `deep`. All dimensions are
in SVG units. Change the body, tail, fins, eye, curvature, and randomness with
the command-line options:

```sh
python3 fishdraw.py --body-length 240 --body-height 90 --tail-size 0.9 \
  --fin-count 3 --fin-angle 30 --eye-size 6 --curvature 0.4 \
  --randomness 0.25 --seed 12 -o fish.svg
```

## Use as a Python library

```python
from fishdraw import Fish

fish = Fish(
    body_length=200,
    body_height=80,
    tail_size=0.8,
    fin_count=3,
    fin_angle=30,
    eye_size=5,
    curvature=0.4,
    randomness=0.2,
    seed="demo",
    species="oval",
)

svg_text = fish.svg()
paths = fish.polylines()  # list of paths, each a list of (x, y) points
with open("fish.svg", "w", encoding="utf-8") as file:
    file.write(svg_text)
```

No third-party packages are needed. `polylines()` exposes the geometry for
other export formats or pen-plotter workflows.
