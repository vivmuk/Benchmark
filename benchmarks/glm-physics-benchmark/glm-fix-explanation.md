html
<!DOCTYPE html>
<html>
<head><title>Fixed Cars</title></head>
<body>
<canvas id="c" width="800" height="400"></canvas>
<script>
const ctx = document.getElementById('c').getContext('2d');
let cars = [{x: -50, y: 280, speed: 2, color: 'red', wheelAngle: 0}];

// Parallax offsets for different depth layers
let cloudOffset = 0;   // farthest
let mountOffset = 0;   // far
let hillOffset  = 0;   // mid
let roadOffset  = 0;   // near (matches car speed)

function drawBackground() {
  // Sky
  ctx.fillStyle = 'skyblue';
  ctx.fillRect(0, 0, 800, 400);

  // Clouds (slowest)
  ctx.fillStyle = 'white';
  for (let i = 0; i < 5; i++) {
    let cx = ((i * 220 - cloudOffset) % 1100 + 1100) % 1100 - 220;
    ctx.beginPath();
    ctx.arc(cx,      70, 22, 0, Math.PI * 2);
    ctx.arc(cx + 24, 70, 28, 0, Math.PI * 2);
    ctx.arc(cx + 54, 70, 22, 0, Math.PI * 2);
    ctx.fill();
  }

  // Far mountains
  ctx.fillStyle = '#6b8e9e';
  for (let i = 0; i < 6; i++) {
    let mx = ((i * 180 - mountOffset) % 1080 + 1080) % 1080 - 180;
    ctx.beginPath();
    ctx.moveTo(mx, 300);
    ctx.lineTo(mx + 90, 170);
    ctx.lineTo(mx + 180, 300);
    ctx.closePath();
    ctx.fill();
  }

  // Near hills
  ctx.fillStyle = '#5a8a5a';
  for (let i = 0; i < 7; i++) {
    let hx = ((i * 150 - hillOffset) % 1050 + 1050) % 1050 - 150;
    ctx.beginPath();
    ctx.arc(hx + 75, 300, 75, Math.PI, 0);
    ctx.closePath();
    ctx.fill();
  }

  // Road
  ctx.fillStyle = 'gray';
  ctx.fillRect(0, 300, 800, 50);

  // Road dashes (scroll at car speed)
  ctx.fillStyle = 'white';
  for (let i = 0; i < 11; i++) {
    let dx = ((i * 80 - roadOffset) % 880 + 880) % 880 - 80;
    ctx.fillRect(dx, 322, 40, 6);
  }
}

function drawWheel(x, y, radius, angle) {
  ctx.save();
  ctx.translate(x, y);
  ctx.rotate(angle);
  // Tire
  ctx.fillStyle = 'black';
  ctx.beginPath();
  ctx.arc(0, 0, radius, 0, Math.PI * 2);
  ctx.fill();
  // Hub
  ctx.fillStyle = 'silver';
  ctx.beginPath();
  ctx.arc(0, 0, radius * 0.4, 0, Math.PI * 2);
  ctx.fill();
  // Spokes (these make rotation visible)
  ctx.strokeStyle = '#333';
  ctx.lineWidth = 2;
  for (let i = 0; i < 4; i++) {
    let a = i * Math.PI / 2;
    ctx.beginPath();
    ctx.moveTo(0, 0);
    ctx.lineTo(Math.cos(a) * radius, Math.sin(a) * radius);
    ctx.stroke();
  }
  ctx.restore();
}

function draw() {
  drawBackground();

  cars.forEach(car => {
    car.x += car.speed;
    // Wheel angular velocity proportional to linear speed
    car.wheelAngle += car.speed / 8;

    // Body
    ctx.fillStyle = car.color;
    ctx.fillRect(car.x, car.y, 60, 30);
    // Cabin
    ctx.fillRect(car.x + 15, car.y - 15, 30, 15);

    // Wheels
    drawWheel(car.x + 12, car.y + 30, 8, car.wheelAngle);
    drawWheel(car.x + 48, car.y + 30, 8, car.wheelAngle);

    if (car.x > 800) car.x = -60;
  });

  // Advance parallax layers
  cloudOffset += 0.15;
  mountOffset += 0.4;
  hillOffset  += 0.9;
  roadOffset  += 2; // same as car speed

  requestAnimationFrame(draw);
}
draw();
</script>
</body>
</html>
```

**What was wrong and how I fixed it:**

1. **`requestAnimationFrame(draw())` — the fatal bug.** The parentheses meant `draw` was *invoked immediately* (returning `undefined`), and `requestAnimationFrame` was then called with `undefined`. Worse, because `draw()` itself calls `draw()` synchronously before returning, this produced unbounded synchronous recursion and an instant stack overflow — the animation never actually ran. Fixed by passing the function reference: `requestAnimationFrame(draw)`.

2. **Wheels didn't rotate.** The original just drew two filled circles, which look identical no matter how the car moves. I added a per-car `wheelAngle` that increments proportionally to `car.speed`, and a `drawWheel` helper that uses `ctx.translate`/`ctx.rotate` to spin a tire + hub + spokes so the rotation is visually obvious.

3. **No parallax background.** The original had only a flat sky and a static road, so there was nothing to convey motion except the car itself. I added four scrolling layers at different speeds — clouds (slowest), far mountains, near hills, and road dashes (fastest, matching car speed) — using modulo wrapping so each layer loops seamlessly. The depth ordering (slow = far, fast = near) is what creates the parallax effect.

4. **Minor polish:** added a cabin on top of each car so it actually looks like a car, and used `closePath()` on the mountain/hill fills for clean edges.