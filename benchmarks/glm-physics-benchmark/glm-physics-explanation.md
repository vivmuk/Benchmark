# HTML5 Canvas Car Physics Demo

## 1. Animation Loop (`requestAnimationFrame`)

The loop is driven by `requestAnimationFrame`, which syncs redraws to the display refresh rate (~60 FPS) and pauses when the tab is hidden.

```js
let last = performance.now();
function frame(now) {
  const dt = Math.min((now - last) / 1000, 0.05); // clamp to avoid huge jumps
  last = now;
  update(dt);
  render();
  requestAnimationFrame(frame);
}
requestAnimationFrame(frame);
```

Key points:
- `dt` is computed in seconds and clamped (e.g. 50 ms) so tab-switches don't catapult the car across the screen.
- `update(dt)` advances physics; `render()` draws everything. Separating them keeps the code deterministic.
- For fixed-timestep stability (recommended for suspension springs), accumulate `dt` and step physics at e.g. 1/120 s.

## 2. Car Position & Velocity Update

The car is typically modeled as a rigid body with position $(x, y)$, velocity $(v_x, v_y)$, angle $\theta$, and angular velocity $\omega$. Each frame:

$$v_x \mathrel{+}= a_x \cdot dt, \quad x \mathrel{+}= v_x \cdot dt$$
$$v_y \mathrel{+}= a_y \cdot dt, \quad y \mathrel{+}= v_y \cdot dt$$
$$\theta \mathrel{+}= \omega \cdot dt$$

Where $a$ comes from engine force, friction, gravity, and ground normal forces. A common simplified approach:

- **Engine**: apply forward force along the car's heading when throttle is pressed.
- **Friction/drag**: $F_{\text{drag}} = -k \cdot v \cdot |v|$ (quadratic) or $-k \cdot v$ (linear).
- **Ground collision**: if a wheel's $y$ exceeds terrain height, push it up and apply a normal impulse; convert vertical velocity into suspension compression.

For arcade-style demos, you can skip full rigid-body dynamics and just lerp velocity toward a target speed:

```js
car.vx += (targetSpeed - car.vx) * 0.05;
car.x  += car.vx * dt;
```

## 3. Wheel Rotation & Suspension Bounce

**Wheel rotation** is derived from linear speed and wheel radius $r$:

$$\omega_{\text{wheel}} = \frac{v}{r}, \quad \theta_{\text{wheel}} \mathrel{+}= \omega_{\text{wheel}} \cdot dt$$

Drawn by rotating the canvas context around the wheel hub before stamping the tire sprite.

**Suspension** is a spring-damper per wheel. Each wheel has a rest length $L_0$, current compression $x$, and velocity $\dot{x}$:

$$F = -k \cdot x - c \cdot \dot{x}$$

- $k$: spring stiffness
- $c$: damping coefficient
- $x$: displacement from rest length (positive when compressed)

Integrate with semi-implicit Euler for stability:

```js
const springForce = -k * compression - c * wheelVel;
wheelVel += (springForce / mass) * dt;
compression += wheelVel * dt;
```

The body's vertical offset and pitch angle are then derived from the four (or two) wheel compressions, giving the visible bounce. Visual "bounce" can also be faked with a damped sine after landing:

$$y_{\text{bounce}}(t) = A \cdot e^{-\lambda t} \cdot \cos(\omega t)$$

## 4. Parallax Scrolling Background

Multiple layers move at fractions of the camera's $x$ position. Farther layers move slower, creating depth.

```js
const layers = [
  { img: sky,   speed: 0.0 },
  { img: hills, speed: 0.2 },
  { img: trees, speed: 0.5 },
  { img: road,  speed: 1.0 },
];

function drawLayer(layer) {
  const offset = -(cameraX * layer.speed) % layer.img.width;
  ctx.drawImage(layer.img, offset,        0);
  ctx.drawImage(layer.img, offset + layer.img.width, 0); // wrap
}
```

- `speed` is the parallax factor (0 = static sky, 1 = moves with camera).
- The modulo + second draw tiles the image seamlessly so scrolling never reveals a gap.
- For vertical parallax (hill crests), offset $y$ slightly based on `cameraX * smallFactor`.

## 5. Water Reflection Effects

A common technique on Canvas:

1. **Mirror transform**: save context, translate to the water line, scale Y by -1, redraw the scene (or a sprite) upside down, then restore.
2. **Clip to water region** so the reflection only appears below the shoreline.
3. **Fade with a gradient** alpha mask so the reflection fades with depth.
4. **Distort** with vertical sine ripple and/or horizontal slices offset by `Math.sin(t + sliceY)`.
5. Optional: `ctx.filter = 'blur(2px)'` for a softer look, and a semi-transparent blue overlay for tint.

```js
ctx.save();
ctx.beginPath();
ctx.rect(0, waterY, W, H - waterY);
ctx.clip();

ctx.translate(0, waterY * 2);
ctx.scale(1, -1);
ctx.globalAlpha = 0.4;
ctx.filter = 'blur(1.5px)';
drawScene();                 // upside-down copy
ctx.restore();

// ripple overlay
for (let y = waterY; y < H; y += 4) {
  ctx.fillStyle = `rgba(120,180,220,${0.04 + 0.02*Math.sin(y*0.1 + t)})`;
  ctx.fillRect(0, y, W, 2);
}
```

For higher quality, render the reflected scene to an offscreen canvas once per frame, then draw horizontal slices with per-row `x` offsets driven by `Math.sin(y * freq + t)` — this gives the classic "wavy water" look without re-rendering the whole scene per slice.

---

### Putting it together

Each frame: step physics (car + suspension springs) → update camera → draw parallax layers → draw terrain → draw car body with pitch from suspension → draw wheels with rotation from speed → draw water reflection last. The `dt`-driven loop keeps motion frame-rate independent, and separating `update` from `render` keeps the code maintainable.