window.BENCH = {
 "generated": "2026-11-25",
 "models": [
  {
   "id": "qwen-4-max",
   "name": "Qwen 4 Max",
   "lab": "Alibaba",
   "icon": "logos/qwen-color.svg",
   "released": "2026-11-16",
   "price_in": 1.875,
   "price_out": 5.625,
   "vision": true,
   "alpaca": {
    "out_tokens": 46040,
    "cost": 0.25934625,
    "seconds": 725.0,
    "finish": "stop",
    "status": "ok",
    "score": 53.8,
    "criteria": {
     "alpaca": 4.0,
     "motion": 5.0,
     "beauty": 5.5,
     "scene": 7.0
    },
    "by_judge": {
     "claude-opus-5-5": 47.5,
     "openai-gpt-6-sol": 60.0
    },
    "notes": {
     "claude-opus-5-5": "The pastel altiplano scene is soft and tasteful with gentle parallax, but the alpaca is anatomically broken: its scalloped neck floats detached above a cloud-blob body, and its stick legs shift between frames in an awkward, unconvincing gait.",
     "openai-gpt-6-sol": "The pastel landscape is polished and the legs change position, but the detached-looking neck and stiff, sliding gait weaken the alpaca and its walk."
    },
    "judges": 2,
    "motion": 3.124
   },
   "design": {
    "status": "failed",
    "error": "Venice closed the stream at 15 minutes, before the model finished. Output incomplete, not scored."
   },
   "recreate": {
    "out_tokens": 2185,
    "cost": 0.01411875,
    "seconds": 44.1,
    "finish": "stop",
    "status": "ok",
    "score": 61.0,
    "criteria": {
     "subjects": 8.5,
     "layout": 5.5,
     "colour": 6.5,
     "style": 5.0,
     "overall": 5.0
    },
    "by_judge": {
     "claude-opus-5-5": 60.0,
     "openai-gpt-6-sol": 62.0
    },
    "notes": {
     "claude-opus-5-5": "Every element is present in roughly the right region, but the recreation uses a stylized digital-illustration look instead of photoreal rendering, enlarges the figures and towers, adds a second elevated monorail track and palm trees, and places the OASIS sign on the tower face rather than beside it.",
     "openai-gpt-6-sol": "Nearly all subjects are present, but the towers, track, and pool shift substantially, and the recreation is brighter and more stylized."
    },
    "judges": 2,
    "prompt": "Cinematic 16:9 digital sci-fi concept art, retro-futuristic neon desert at twilight. Sky gradients from starry deep navy at top through lavender to glowing orange at the right horizon; a large pale crescent moon, lit on its right edge with faint earthshine, hangs upper-left. Center distance: a futuristic oasis city of three tapering glass skyscrapers \u2014 the tallest central teal spire encircled near its tip by a glowing cyan neon halo ring; a slimmer teal tower to its left bearing a vertical cyan neon sign reading \"OASIS\"; a magenta-purple tower right edged in pink neon. Tiered circular ziggurat buildings with glowing teal bands and clusters of tiny lit windows form the city base. Four thin cyan searchlight beams shoot diagonally skyward, two on each side of the towers. Left foreground, on a dune crest at the left third: a person seen from behind, dark hair, wearing a long dark-crimson cloak, standing beside one shaggy grey-brown llama, both gazing toward the city. Right foreground: a tall green saguaro cactus outlined in glowing pink neon, a smaller neon-edged saguaro behind it. Below them a vivid turquoise oasis pool with tiny palms on its far bank. An elevated monorail on slender pylons, rails glowing amber-orange, curves from the bottom-right corner toward the city; one small sleek white-and-teal train rides it mid-frame. Foreground: wind-rippled orange sand dunes with drifting dust wisps, warm sunset rim-light from the right, cool purple shadows. Painterly, polished, synthwave palette, serene epic mood."
   },
   "speed": {
    "status": "ok",
    "runs": 3,
    "tps": 47.1,
    "tps_min": 46.7,
    "tps_max": 50.4,
    "ttft": 20.33,
    "seconds": 31.4,
    "out_tokens": 1463
   },
   "value": {
    "out_tokens": 4021,
    "cost": 0.023289375,
    "seconds": 59.3,
    "finish": "stop",
    "status": "ok",
    "correct": 12,
    "total": 12,
    "per_q": [
     true,
     true,
     true,
     true,
     true,
     true,
     true,
     true,
     true,
     true,
     true,
     true
    ],
    "per_1k": 2.98,
    "per_dollar": 515
   }
  },
  {
   "id": "gemini-4-hydrogen",
   "name": "Gemini 4 Hydrogen",
   "lab": "Google",
   "icon": "logos/gemini-color.svg",
   "released": "2026-11-14",
   "price_in": 1.875,
   "price_out": 9.375,
   "vision": true,
   "alpaca": {
    "out_tokens": 29306,
    "cost": 0.27511875,
    "seconds": 188.5,
    "finish": "stop",
    "status": "ok",
    "score": 63.8,
    "criteria": {
     "alpaca": 6.0,
     "motion": 5.5,
     "beauty": 7.0,
     "scene": 7.0
    },
    "by_judge": {
     "claude-opus-5-5": 65.0,
     "openai-gpt-6-sol": 62.5
    },
    "notes": {
     "claude-opus-5-5": "A polished, softly lit flat-vector dusk scene with a plausible walk cycle, parallax and head bob, though the camelid's bare, spindly, deer-like legs and thin un-fleeced neck read more llama than alpaca, the joints look stiff, and the mountains' inverted-triangle snowcaps look like floating bunting.",
     "openai-gpt-6-sol": "The warm, layered landscape is appealing and the legs change between frames, but the gait is stiff and the bare, narrow neck makes the alpaca less convincing."
    },
    "judges": 2,
    "motion": 2.209
   },
   "design": {
    "out_tokens": 25377,
    "cost": 0.23824125,
    "seconds": 162.9,
    "finish": "stop",
    "status": "ok",
    "score": 77.0,
    "criteria": {
     "typography": 8.0,
     "layout": 6.0,
     "colour": 8.0,
     "completeness": 8.5,
     "originality": 8.0
    },
    "by_judge": {
     "claude-opus-5-5": 72.0,
     "openai-gpt-6-sol": 82.0
    },
    "notes": {
     "claude-opus-5-5": "A polished serif-and-mono system, a warm amber/teal night palette and a charming train illustration with route timeline lift this well above template; it is undermined by a broken hero, where the headline and intro paragraph are clipped under the nav, leaving a strip of dead space above it.",
     "openai-gpt-6-sol": "A distinctive, cohesive page with all seven sections, though the hero copy appears clipped beneath the navigation and some small text lacks contrast."
    },
    "judges": 2
   },
   "recreate": {
    "out_tokens": 1220,
    "cost": 0.0137775,
    "seconds": 12.3,
    "finish": "stop",
    "status": "ok",
    "score": 62.0,
    "criteria": {
     "subjects": 7.5,
     "layout": 5.0,
     "colour": 7.0,
     "style": 6.5,
     "overall": 5.0
    },
    "by_judge": {
     "claude-opus-5-5": 60.0,
     "openai-gpt-6-sol": 64.0
    },
    "notes": {
     "claude-opus-5-5": "Most elements are present, but the crescent moon became a full moon. The traveller, alpaca and cactus are much larger and closer, the monorail curves toward the lower left instead of the lower right, and the pool sits below the cactus rather than beside it, all rendered in a more saturated, busier s",
     "openai-gpt-6-sol": "The main elements and neon desert palette are present, but the crescent is nearly full, the figures are much larger, and the track and pool occupy different parts of the frame."
    },
    "judges": 2,
    "prompt": "Digital sci-fi illustration of a futuristic desert at dusk, wide cinematic shot. On a rippled sand dune in the left foreground, a man in a dark red cape stands next to a brown llama, both viewed from behind facing a distant city. In the right foreground, a saguaro cactus outlined in glowing pink neon stands beside a glowing turquoise pond, with a smaller dark cactus to its right. An elevated, orange-lit monorail track with a sleek silver train curves from the bottom right across the dunes toward the city. In the center-right background, a cyberpunk metropolis rises with three towering spires: a central spire encircled by a glowing cyan halo ring, a left spire displaying a vertical cyan neon sign reading \"OASIS\", and a right spire lit in purple, above tiered circular buildings and four diagonal cyan spotlights. The sky transitions from starry deep blue at top-left to a warm orange horizon, featuring a large crescent moon in the upper left."
   },
   "speed": {
    "status": "ok",
    "runs": 3,
    "tps": 157.1,
    "tps_min": 156.0,
    "tps_max": 157.3,
    "ttft": 30.36,
    "seconds": 34.1,
    "out_tokens": 5362
   },
   "value": {
    "out_tokens": 7944,
    "cost": 0.07515,
    "seconds": 50.2,
    "finish": "stop",
    "status": "ok",
    "correct": 12,
    "total": 12,
    "per_q": [
     true,
     true,
     true,
     true,
     true,
     true,
     true,
     true,
     true,
     true,
     true,
     true
    ],
    "per_1k": 1.51,
    "per_dollar": 160
   }
  },
  {
   "id": "glm-5-3-flash-uncensored",
   "name": "GLM 5.3 Flash Uncensored",
   "lab": "Z.ai",
   "icon": "logos/zai.svg",
   "released": "2026-11-13",
   "price_in": 0.165,
   "price_out": 0.55,
   "vision": true,
   "alpaca": {
    "out_tokens": 24510,
    "cost": 0.013510035000000002,
    "seconds": 94.9,
    "finish": "stop",
    "status": "ok",
    "score": 47.5,
    "criteria": {
     "alpaca": 4.0,
     "motion": 2.0,
     "beauty": 6.0,
     "scene": 7.0
    },
    "by_judge": {
     "claude-opus-5-5": 42.5,
     "openai-gpt-6-sol": 52.5
    },
    "notes": {
     "claude-opus-5-5": "The head, ears and long fleecy neck read as an alpaca, but the body is a floating fleece blob with almost no visible legs; one stray limb juts horizontally or backward, so the walk fails even though the scrolling parallax background is soft, cohesive and tasteful (apart from grass tufts overlapping ",
     "openai-gpt-6-sol": "The warm, polished landscape frames a recognizable alpaca, but its mostly missing legs make it appear to float rather than walk."
    },
    "judges": 2,
    "motion": 0.862
   },
   "design": {
    "out_tokens": 32938,
    "cost": 0.018141145,
    "seconds": 117.9,
    "finish": "stop",
    "status": "ok",
    "score": 75.0,
    "criteria": {
     "typography": 8.0,
     "layout": 6.5,
     "colour": 8.5,
     "completeness": 6.0,
     "originality": 8.5
    },
    "by_judge": {
     "claude-opus-5-5": 72.0,
     "openai-gpt-6-sol": 78.0
    },
    "notes": {
     "claude-opus-5-5": "A distinctive dusk-to-neon serif-and-mono design with a lovely boarding-pass hero, but the 'Four trains leave tonight' section shows no departure rows, so the timetable is missing and the testimonial sits in its place; a stray '\u5730\u56fe' glyph and a struck-through 'No' in the body copy add polish issues.",
     "openai-gpt-6-sol": "The train illustration, boarding pass and desert palette feel distinctive, but the promised four-departure timetable has no departures."
    },
    "judges": 2
   },
   "recreate": {
    "out_tokens": 278,
    "cost": 0.000363605,
    "seconds": 2.4,
    "finish": "stop",
    "status": "ok",
    "score": 63.0,
    "criteria": {
     "subjects": 8.0,
     "layout": 6.5,
     "colour": 6.5,
     "style": 5.5,
     "overall": 5.0
    },
    "by_judge": {
     "claude-opus-5-5": 58.0,
     "openai-gpt-6-sol": 68.0
    },
    "notes": {
     "claude-opus-5-5": "All the key elements are present and roughly placed, but the recreation turns the three sparse towers into a dense skyline, makes the searchlights purple instead of cyan, adds extra cacti, and uses a more saturated, illustrative style than the original's smoother, more photoreal look.",
     "openai-gpt-6-sol": "Nearly all key elements are present, but the recreation shifts their positions and makes the city, neon lighting, and foreground much brighter and more stylized."
    },
    "judges": 2,
    "prompt": "A cinematic sci-fi digital painting of a futuristic neon city rising from golden desert sand dunes at twilight. Wide panoramic composition. Upper left: deep indigo-blue starry sky with a large glowing crescent moon, fading to warm orange sunset on the right horizon. Center-right: a cluster of sleek glass skyscrapers \u2014 a tall cyan-lit tower crowned by a bright teal glowing ring halo, flanked by a slim spire with a vertical cyan neon sign reading \"OASIS\" and a magenta-pink lit angular tower with purple light beams shooting upward into the sky. Tiered rounded saucer-like building bases surrounded by small low-rise skyline with tiny window lights. Foreground lower left: rolling rippled sand dunes in amber tones; a person in a long dark red cloak stands beside a light brown llama/alpaca, both seen from behind on a dune ridge looking toward the city. Right side: a giant saguaro cactus outlined in glowing pink neon, with a smaller neon cactus behind it near a small turquoise oasis pond reflecting city lights. A curved elevated monorail track with golden-yellow lighting sweeps across the lower right foreground, carrying a small white train car. Soft atmospheric haze, volumetric glow, retro-futurism meets vaporwave aesthetic, highly detailed matte painting, symmetrical central skyline, dreamy serene mood."
   },
   "speed": {
    "status": "ok",
    "runs": 3,
    "tps": 208.0,
    "tps_min": 177.1,
    "tps_max": 214.9,
    "ttft": 0.64,
    "seconds": 3.3,
    "out_tokens": 687
   },
   "value": {
    "out_tokens": 1699,
    "cost": 0.0009852700000000001,
    "seconds": 6.2,
    "finish": "stop",
    "status": "ok",
    "correct": 12,
    "total": 12,
    "per_q": [
     true,
     true,
     true,
     true,
     true,
     true,
     true,
     true,
     true,
     true,
     true,
     true
    ],
    "per_1k": 7.06,
    "per_dollar": 12179
   }
  },
  {
   "id": "gemini-4-carbon",
   "name": "Gemini 4 Carbon",
   "lab": "Google",
   "icon": "logos/gemini-color.svg",
   "released": "2026-11-10",
   "price_in": 2.5,
   "price_out": 12.5,
   "vision": true,
   "alpaca": {
    "out_tokens": 19310,
    "cost": 0.241875,
    "seconds": 252.3,
    "finish": "stop",
    "status": "ok",
    "score": 76.2,
    "criteria": {
     "alpaca": 8.0,
     "motion": 7.0,
     "beauty": 8.0,
     "scene": 7.5
    },
    "by_judge": {
     "claude-opus-5-5": 77.5,
     "openai-gpt-6-sol": 75.0
    },
    "notes": {
     "claude-opus-5-5": "A charming, clearly readable alpaca with a long fleecy neck, upright ears, and a pom-pom collar walks with distinctly changing leg poses and subtle parallax across a warm, layered dusk landscape; the legs are a bit stiff and stick-like with slightly ambiguous joint bends, and the clouds are somewhat",
     "openai-gpt-6-sol": "The fleecy alpaca is unmistakable, and its legs change in a plausible if slightly stiff walk through a polished pastel scene."
    },
    "judges": 2,
    "motion": 5.898
   },
   "design": {
    "out_tokens": 25067,
    "cost": 0.31378,
    "seconds": 348.6,
    "finish": "stop",
    "status": "ok",
    "score": 79.0,
    "criteria": {
     "typography": 8.0,
     "layout": 6.0,
     "colour": 8.0,
     "completeness": 9.0,
     "originality": 8.5
    },
    "by_judge": {
     "claude-opus-5-5": 74.0,
     "openai-gpt-6-sol": 84.0
    },
    "notes": {
     "claude-opus-5-5": "A polished, atmospheric dark design with refined serif and mono pairing and rich, specific content, but the sticky nav renders mid-hero, overlapping the headline and hero illustration, a clear broken-layout flaw.",
     "openai-gpt-6-sol": "A distinctive, cohesive design with all required sections, though the navigation interrupts the hero and some small text lacks contrast."
    },
    "judges": 2
   },
   "recreate": {
    "out_tokens": 1059,
    "cost": 0.0163575,
    "seconds": 25.9,
    "finish": "stop",
    "status": "ok",
    "score": 64.0,
    "criteria": {
     "subjects": 8.5,
     "layout": 6.0,
     "colour": 6.5,
     "style": 6.0,
     "overall": 5.0
    },
    "by_judge": {
     "claude-opus-5-5": 62.0,
     "openai-gpt-6-sol": 66.0
    },
    "notes": {
     "claude-opus-5-5": "All key elements are present and roughly placed, but the recreation renders the traveller and alpaca much larger and closer, shrinks the saguaro and turns it fully neon pink, moves the monorail track toward the centre, uses a more illustrated digital-painting look instead of the photoreal original, ",
     "openai-gpt-6-sol": "Nearly all key elements are present, but the traveller and alpaca are much larger, the track follows a different route, and the recreation is brighter and more saturated."
    },
    "judges": 2,
    "prompt": "A cinematic sci-fi digital illustration in a wide-angle composition. In the left foreground, atop a misty, wind-rippled orange sand dune, a dark-haired figure wearing a dark red cape stands beside a fluffy beige llama, both seen from behind looking toward a futuristic desert metropolis in the center-right background. The city features tiered circular bases, smaller skyscrapers, and three towering spires: a tallest central spire crowned with a glowing horizontal cyan halo ring, a left spire with a vertical cyan neon sign reading \"OASIS\", and a right spire lit with purple neon accents. Two bright cyan searchlights beam diagonally outward into the sky from either side of the city. Winding through the dunes from the city to the bottom-right corner is an elevated, orange-lit monorail track carrying a single sleek train toward the foreground. On the right, a turquoise oasis pond sits near a large saguaro cactus outlined in glowing pink neon, with a smaller unlit saguaro behind it. A massive crescent moon, illuminated on its lower-right curve, hangs in the upper-left sky. The starry twilight sky gradients from warm sunset orange on the right horizon through purple to deep navy blue above, blending vibrant neon highlights with warm atmospheric dusk lighting."
   },
   "speed": {
    "status": "ok",
    "runs": 3,
    "tps": 66.2,
    "tps_min": 24.0,
    "tps_max": 81.5,
    "ttft": 83.74,
    "seconds": 89.9,
    "out_tokens": 5119
   },
   "value": {
    "out_tokens": 4436,
    "cost": 0.05635,
    "seconds": 59.3,
    "finish": "stop",
    "status": "ok",
    "correct": 12,
    "total": 12,
    "per_q": [
     true,
     true,
     true,
     true,
     true,
     true,
     true,
     true,
     true,
     true,
     true,
     true
    ],
    "per_1k": 2.71,
    "per_dollar": 213
   }
  },
  {
   "id": "claude-fable-5-2",
   "name": "Claude Fable 5.2",
   "lab": "Anthropic",
   "icon": "logos/claude-color.svg",
   "released": "2026-11-09",
   "price_in": 8,
   "price_out": 40,
   "vision": true,
   "alpaca": {
    "out_tokens": 64074,
    "cost": 2.565056,
    "seconds": 699.1,
    "finish": "stop",
    "status": "ok",
    "score": 66.2,
    "criteria": {
     "alpaca": 7.5,
     "motion": 5.0,
     "beauty": 7.0,
     "scene": 7.0
    },
    "by_judge": {
     "claude-opus-5-5": 70.0,
     "openai-gpt-6-sol": 62.5
    },
    "notes": {
     "claude-opus-5-5": "A clean, fleecy camelid with a long neck, small head and upright ears, though the very tall neck, banana ears and spindly legs read slightly llama-like; legs swap lift and plant phases plausibly across frames while the foreground scrolls for parallax, all set in a polished but fairly generic mountai",
     "openai-gpt-6-sol": "The alpaca is recognizable and the scene is polished, but the leg movement is stiff and the last two poses are nearly identical."
    },
    "judges": 2,
    "motion": 6.806
   },
   "design": {
    "out_tokens": 71250,
    "cost": 2.851792,
    "seconds": 723.4,
    "finish": "stop",
    "status": "ok",
    "score": 91.0,
    "criteria": {
     "typography": 9.0,
     "layout": 8.5,
     "colour": 9.0,
     "completeness": 10,
     "originality": 9.0
    },
    "by_judge": {
     "claude-opus-5-5": 90.0,
     "openai-gpt-6-sol": 92.0
    },
    "notes": {
     "claude-opus-5-5": "A polished, atmospheric page: the serif-and-italic headline pairing, monospace timetable details and the dusk-to-neon palette give it a distinctive, cohesive identity, with only minor issues like the large empty gap before the fares section and some small low-contrast captions.",
     "openai-gpt-6-sol": "A distinctive, cohesive page with every required section; some small secondary text has weak contrast."
    },
    "judges": 2
   },
   "recreate": {
    "out_tokens": 594,
    "cost": 0.034184,
    "seconds": 8.1,
    "finish": "stop",
    "status": "ok",
    "score": 73.0,
    "criteria": {
     "subjects": 9.5,
     "layout": 6.0,
     "colour": 7.0,
     "style": 8.0,
     "overall": 6.0
    },
    "by_judge": {
     "claude-opus-5-5": 72.0,
     "openai-gpt-6-sol": 74.0
    },
    "notes": {
     "claude-opus-5-5": "All key elements are present in a similar digital-painting style, but the recreation shifts the city right, enlarges the moon, moves the pool to centre-left of the track, pushes the cactus to the bottom-right edge, places the traveller and alpaca further right, and uses a more saturated purple-orang",
     "openai-gpt-6-sol": "All key subjects are present, but the larger moon, shifted pool and dramatically rerouted monorail make the recreation noticeably different."
    },
    "judges": 2,
    "prompt": "Cinematic wide-angle sci-fi digital concept art, 16:9, photorealistic matte painting style. A futuristic desert city at dusk. Sky: deep indigo-navy at top with scattered tiny stars, fading through violet and magenta to glowing orange at the horizon on the right. Upper left: a huge thin crescent moon, lit on its lower-right edge, the dark disc faintly visible.\n\nCentre-right: three slender, tapering glass skyscrapers rising from a cluster of tiered, saucer-shaped retro-futuristic buildings with teal light bands and a small low skyline of lit buildings. The central tower is tallest, teal-glass, with a glowing cyan neon halo ring floating around its spire near the top. The left tower is shorter, teal, with a vertical cyan neon sign reading \"OASIS\" on its left side. The right tower is shorter, lit in purple-magenta neon. Four thin teal searchlight beams shoot diagonally into the sky from behind the city.\n\nLeft midground: on a dune crest, a lone figure seen from behind in a long dark red cloak stands beside a fluffy brown alpaca on his left, both looking toward the city, silhouetted in dim light.\n\nForeground: sweeping orange sand dunes with fine wind ripples, sand blowing off crests, a sharp dune ridge running diagonally from lower left.\n\nRight: an elevated monorail track with glowing amber edge-lights curving in an S-shape from the lower right toward the city, a sleek silver train on it. Beside it, a glowing turquoise oasis pool. Far right foreground: a tall saguaro cactus outlined with pink neon rim light, a small cactus behind it.\n\nWarm amber and teal palette, atmospheric haze, dramatic lighting."
   },
   "speed": {
    "status": "ok",
    "runs": 3,
    "tps": 85.4,
    "tps_min": 84.5,
    "tps_max": 85.9,
    "ttft": 4.22,
    "seconds": 13.0,
    "out_tokens": 1102
   },
   "value": {
    "out_tokens": 886,
    "cost": 0.03884,
    "seconds": 8.3,
    "finish": "stop",
    "status": "ok",
    "correct": 12,
    "total": 12,
    "per_q": [
     true,
     true,
     true,
     true,
     true,
     true,
     true,
     true,
     true,
     true,
     true,
     true
    ],
    "per_1k": 13.54,
    "per_dollar": 309
   }
  },
  {
   "id": "e2ee-deepseek-v4-1-flash-1017-abliterated",
   "name": "DeepSeek V4.1 Flash 1017 Abliterated",
   "lab": "DeepSeek",
   "icon": "logos/deepseek-color.svg",
   "released": "2026-11-05",
   "price_in": 0.375,
   "price_out": 1.5,
   "vision": false,
   "alpaca": {
    "status": "failed",
    "error": "empty: no content returned"
   },
   "design": {
    "out_tokens": 37488,
    "cost": 0.056296875,
    "seconds": 570.8,
    "finish": "stop",
    "status": "ok",
    "score": 66.0,
    "criteria": {
     "typography": 7.5,
     "layout": 4.5,
     "colour": 8.0,
     "completeness": 5.5,
     "originality": 7.5
    },
    "by_judge": {
     "claude-opus-5-5": 64.0,
     "openai-gpt-6-sol": 68.0
    },
    "notes": {
     "claude-opus-5-5": "The elegant serif-and-amber night palette and the drawn train illustration show real taste, but the nav bar overlaps the hero just below the headline, and the testimonial section renders as a large blank void before the footer.",
     "openai-gpt-6-sol": "The evocative palette and custom illustration stand out, but the navigation cuts through the hero, a large empty gap disrupts the page, and the required testimonial is missing."
    },
    "judges": 2
   },
   "recreate": {
    "status": "no vision",
    "error": "This model cannot take image input."
   },
   "speed": {
    "status": "ok",
    "runs": 3,
    "tps": 41.0,
    "tps_min": 39.6,
    "tps_max": 46.7,
    "ttft": 14.11,
    "seconds": 24.0,
    "out_tokens": 952
   },
   "value": {
    "out_tokens": 2839,
    "cost": 0.00438075,
    "seconds": 48.7,
    "finish": "stop",
    "status": "ok",
    "correct": 12,
    "total": 12,
    "per_q": [
     true,
     true,
     true,
     true,
     true,
     true,
     true,
     true,
     true,
     true,
     true,
     true
    ],
    "per_1k": 4.23,
    "per_dollar": 2739
   }
  },
  {
   "id": "deepseek-v4-1-flash-1017-uncensored",
   "name": "DeepSeek V4.1 Flash 1017 Uncensored",
   "lab": "DeepSeek",
   "icon": "logos/deepseek-color.svg",
   "released": "2026-10-27",
   "price_in": 0.33,
   "price_out": 1.32,
   "vision": true,
   "alpaca": {
    "out_tokens": 30559,
    "cost": 0.040402560000000004,
    "seconds": 267.9,
    "finish": "stop",
    "status": "ok",
    "score": 58.8,
    "criteria": {
     "alpaca": 6.5,
     "motion": 5.0,
     "beauty": 6.0,
     "scene": 6.0
    },
    "by_judge": {
     "claude-opus-5-5": 57.5,
     "openai-gpt-6-sol": 60.0
    },
    "notes": {
     "claude-opus-5-5": "A recognisable, cute alpaca with upright ears, long neck and fluffy fleece, but the legs are stiff unjointed sticks swinging like pendulums under a cloud-blob body with an odd belly smudge, set in a soft, pleasant but generic meadow whose scrolling grass sells the walk better than the gait itself.",
     "openai-gpt-6-sol": "The fluffy, long-necked animal reads as an alpaca, but its stiff legs and nearly stationary body make the walk feel mechanical; the soft meadow is pleasant but simple."
    },
    "judges": 2,
    "motion": 2.605
   },
   "design": {
    "out_tokens": 29089,
    "cost": 0.03845457,
    "seconds": 197.9,
    "finish": "stop",
    "status": "ok",
    "score": 54.0,
    "criteria": {
     "typography": 7.5,
     "layout": 2.0,
     "colour": 7.5,
     "completeness": 3.0,
     "originality": 7.0
    },
    "by_judge": {
     "claude-opus-5-5": 50.0,
     "openai-gpt-6-sol": 58.0
    },
    "notes": {
     "claude-opus-5-5": "The hero and features are polished, with elegant serif type, a gradient italic and a distinctive desert-train illustration, but the timetable, pricing and testimonial never render, leaving a huge empty void with only an orphaned fare footnote and a stray 'Continue' widget overlapping the section bre",
     "openai-gpt-6-sol": "Distinctive type, palette and illustration are undermined by a huge empty stretch and missing timetable, pricing tiers and testimonial."
    },
    "judges": 2
   },
   "recreate": {
    "out_tokens": 929,
    "cost": 0.00143847,
    "seconds": 4.8,
    "finish": "stop",
    "status": "ok",
    "score": 60.0,
    "criteria": {
     "subjects": 8.0,
     "layout": 5.5,
     "colour": 6.5,
     "style": 5.5,
     "overall": 4.5
    },
    "by_judge": {
     "claude-opus-5-5": 54.0,
     "openai-gpt-6-sol": 66.0
    },
    "notes": {
     "claude-opus-5-5": "All key elements are present, but the recreation is a denser, more saturated neon cityscape: the OASIS sign is built into a tower, the moon faces the other way, the alpaca reads as a pack llama, the cactus lacks a neon outline, and the pool, monorail, and figures are larger and repositioned, so it d",
     "openai-gpt-6-sol": "Nearly all key subjects are present, but the towers, moon, pool, and train have shifted, and the recreation is sharper and more saturated than the original."
    },
    "judges": 2,
    "prompt": "Wide 16:9 cinematic sci-fi concept art, desert at twilight. Foreground left: a lone figure in a long flowing red cloak stands on a rippled sand dune, back to viewer, beside one woolly llama/alpaca to their left, both silhouetted and facing a distant futuristic city. Sky: deep navy starry upper left, gradient to peach/orange sunset lower right; huge thin white crescent moon upper left with faint glow. Center background: glowing neon metropolis, central ultra-tall spire with translucent cyan halo ring floating above; left cyan skyscraper with vertical neon text \"OASIS\"; right magenta-lit tower; curved terraced bases and low city lights. Multiple cyan/magenta searchlight beams sweep upward. Right foreground: curved elevated road with glowing yellow edges and a blue train car, turquoise oasis pool, large saguaro cactus with magenta rim light and a smaller cactus. Warm orange dunes with fine wind ripples. Digital illustration, futuristic synthwave lighting, high detail, dramatic scale, sharp focus, centered composition."
   },
   "speed": {
    "status": "ok",
    "runs": 3,
    "tps": 64.2,
    "tps_min": 61.8,
    "tps_max": 155.2,
    "ttft": 6.39,
    "seconds": 12.8,
    "out_tokens": 898
   },
   "value": {
    "out_tokens": 2607,
    "cost": 0.0035488200000000003,
    "seconds": 14.9,
    "finish": "stop",
    "status": "ok",
    "correct": 12,
    "total": 12,
    "per_q": [
     true,
     true,
     true,
     true,
     true,
     true,
     true,
     true,
     true,
     true,
     true,
     true
    ],
    "per_1k": 4.6,
    "per_dollar": 3381
   }
  },
  {
   "id": "openai-gpt-61-terra",
   "name": "GPT-6.1 Terra",
   "lab": "OpenAI",
   "icon": "logos/openai.svg",
   "released": "2026-10-26",
   "price_in": 1,
   "price_out": 5,
   "vision": true,
   "alpaca": {
    "out_tokens": 9614,
    "cost": 0.048238,
    "seconds": 118.1,
    "finish": "stop",
    "status": "ok",
    "score": 65.0,
    "criteria": {
     "alpaca": 6.5,
     "motion": 5.0,
     "beauty": 7.0,
     "scene": 7.5
    },
    "by_judge": {
     "claude-opus-5-5": 62.5,
     "openai-gpt-6-sol": 67.5
    },
    "notes": {
     "claude-opus-5-5": "The alpaca is readable, with upright ears, a long neck, a small snouted head and a cloud-like fleece body, but the flat slab neck and stiff, dowel-like tube legs weaken its anatomy and charm; the legs do swing in plausible alternating phases between frames, and the soft pastel layered-hill scene wit",
     "openai-gpt-6-sol": "The fluffy alpaca and pastel landscape are polished, but its rigid, nearly straight legs make the changing poses feel more like a shuffle than a believable walk."
    },
    "judges": 2,
    "motion": 0.981
   },
   "design": {
    "out_tokens": 13410,
    "cost": 0.067195,
    "seconds": 148.7,
    "finish": "stop",
    "status": "ok",
    "score": 84.0,
    "criteria": {
     "typography": 8.0,
     "layout": 8.5,
     "colour": 8.5,
     "completeness": 9.5,
     "originality": 7.5
    },
    "by_judge": {
     "claude-opus-5-5": 78.0,
     "openai-gpt-6-sol": 90.0
    },
    "notes": {
     "claude-opus-5-5": "A polished, cohesive editorial build: the serif display type with its italic terracotta accent, the restrained cream, navy and copper palette, and the custom train illustration all work well, and every required section is present and well formed, though the tiny grey body text strains legibility and",
     "openai-gpt-6-sol": "A distinctive, polished page with every requested section; some small labels and secondary text are harder to read."
    },
    "judges": 2
   },
   "recreate": {
    "out_tokens": 523,
    "cost": 0.003793,
    "seconds": 11.5,
    "finish": "stop",
    "status": "ok",
    "score": 66.0,
    "criteria": {
     "subjects": 8.0,
     "layout": 6.0,
     "colour": 6.0,
     "style": 7.0,
     "overall": 6.0
    },
    "by_judge": {
     "claude-opus-5-5": 64.0,
     "openai-gpt-6-sol": 68.0
    },
    "notes": {
     "claude-opus-5-5": "Every element is present, but the moon is nearly a full disc rather than a crescent, the cloak is purple rather than red, and the monorail track exits to the right instead of sweeping into the foreground; the figures and cactus are also larger, and the sky is darker with a weaker orange-purple gradi",
     "openai-gpt-6-sol": "Nearly all key elements are present, but the traveller, train, pool and cactus shift in scale or position, and the recreation is darker and less warmly lit."
    },
    "judges": 2,
    "prompt": "Wide 16:9 cinematic retro-futurist desert landscape at twilight, viewed from a low dune. In the left foreground, a solitary traveler seen from behind stands on a sandy ridge, wearing a long dark burgundy cloak, looking toward a distant city. One shaggy brown llama stands immediately to the traveler\u2019s left, also facing the city. Their long shadows stretch toward the lower left.\n\nRolling copper-orange dunes fill the foreground, with fine rippled sand, drifting dust and dark blue-purple shadows. In the center-right distance rises a luminous futuristic metropolis: three slender tapering glass skyscrapers above layered, circular, tiered buildings. The tallest central tower reaches almost to the top of the frame and is encircled near its summit by a bright horizontal cyan neon halo. The shorter left tower has a vertical turquoise sign reading \u201cOASIS\u201d in white capital letters. The right tower glows violet and magenta. Tiny illuminated buildings cluster around their bases, and pale turquoise searchlight beams rise diagonally into the sky.\n\nA single sleek blue monorail travels along a slender elevated golden-lit track that curves from the city toward the lower-right corner. On the far right foreground, a tall dark green saguaro cactus with several upright arms is outlined by pink neon light; a smaller cactus stands behind it. A small glowing turquoise oasis pool lies behind the large cactus.\n\nDeep navy star-speckled sky fades to dusty mauve and warm orange along the horizon. A huge faint dark moon with a thin bright crescent along its lower-right edge hangs in the upper left. Atmospheric, highly detailed digital matte painting, soft cinematic lighting, serene and otherworldly."
   },
   "speed": {
    "status": "ok",
    "runs": 3,
    "tps": 44.7,
    "tps_min": 41.8,
    "tps_max": 51.4,
    "ttft": 13.79,
    "seconds": 24.3,
    "out_tokens": 1109
   },
   "value": {
    "out_tokens": 1095,
    "cost": 0.005774,
    "seconds": 15.5,
    "finish": "stop",
    "status": "ok",
    "correct": 12,
    "total": 12,
    "per_q": [
     true,
     true,
     true,
     true,
     true,
     true,
     true,
     true,
     true,
     true,
     true,
     true
    ],
    "per_1k": 10.96,
    "per_dollar": 2078
   }
  },
  {
   "id": "kimi-k3-1-pro",
   "name": "Kimi K3.1 Pro",
   "lab": "Moonshot AI",
   "icon": "logos/kimi-color.svg",
   "released": "2026-10-23",
   "price_in": 2,
   "price_out": 10,
   "vision": true,
   "alpaca": {
    "out_tokens": 28005,
    "cost": 0.280548,
    "seconds": 198.9,
    "finish": "stop",
    "status": "ok",
    "score": 67.5,
    "criteria": {
     "alpaca": 7.0,
     "motion": 6.0,
     "beauty": 7.0,
     "scene": 7.0
    },
    "by_judge": {
     "claude-opus-5-5": 62.5,
     "openai-gpt-6-sol": 72.5
    },
    "notes": {
     "claude-opus-5-5": "A charming, softly coloured camelid with a long neck, fleece and upright ears sits in a tasteful mountain-path scene, but the cloud-blob body, banana-like llama ears and stiff, stick-like wooden legs with awkwardly bending joints weaken both the anatomy and the walk cycle, even though the legs do cl",
     "openai-gpt-6-sol": "The woolly alpaca is clear and charming in a tasteful pastel landscape, but its visibly changing legs move somewhat stiffly."
    },
    "judges": 2,
    "motion": 0.831
   },
   "design": {
    "out_tokens": 39853,
    "cost": 0.39898,
    "seconds": 229.6,
    "finish": "stop",
    "status": "ok",
    "score": 84.0,
    "criteria": {
     "typography": 8.0,
     "layout": 8.5,
     "colour": 8.0,
     "completeness": 9.5,
     "originality": 8.0
    },
    "by_judge": {
     "claude-opus-5-5": 80.0,
     "openai-gpt-6-sol": 88.0
    },
    "notes": {
     "claude-opus-5-5": "A polished, cohesive page: tight grotesk headlines with a serif-italic accent, mono labels, a well-structured timetable and a coral-on-navy/cream palette, though the visible skip-link artifact, some tiny low-contrast microcopy and a familiar premium-template feel keep it short of exceptional.",
     "openai-gpt-6-sol": "Distinctive train artwork and cohesive styling carry every required section, though tiny low-contrast text and a visible skip link reduce the polish."
    },
    "judges": 2
   },
   "recreate": {
    "out_tokens": 1968,
    "cost": 0.022394,
    "seconds": 15.4,
    "finish": "stop",
    "status": "ok",
    "score": 64.0,
    "criteria": {
     "subjects": 8.5,
     "layout": 6.0,
     "colour": 7.0,
     "style": 5.5,
     "overall": 5.0
    },
    "by_judge": {
     "claude-opus-5-5": 62.0,
     "openai-gpt-6-sol": 66.0
    },
    "notes": {
     "claude-opus-5-5": "All key elements are present in the same general arrangement, but the traveller's cloak is purple rather than red, the alpaca stands to the traveller's right instead of left, the pool is larger and more central, the monorail track curves differently, and the cleaner illustrated look departs from the",
     "openai-gpt-6-sol": "Nearly all key elements are present, but the alpaca switches sides, the city and track shift, and the recreation is brighter and sharper than the original."
    },
    "judges": 2,
    "prompt": "Ultra-wide 16:9 cinematic science-fiction matte painting, highly detailed semi-realistic retro-futurist concept art, low eye-level establishing shot. Rippled orange sand dunes fill the foreground, with windblown dust glowing along a ridge. On the left ridge, seen from behind and facing the city, stand one dark-haired traveler in a long flowing burgundy cloak and one shaggy gray-brown llama in right-facing profile; both cast long shadows toward the lower left. The center-right background holds a dense futuristic oasis city: three slender glass supertowers, the tallest dark-teal central spire crowned by a glowing horizontal cyan elliptical halo, a turquoise left spire with a vertical neon sign reading \u201cOASIS\u201d one letter per line, and a violet-magenta right spire. Two round, tiered, saucer-roofed buildings and many tiny illuminated low-rise structures cluster around their stepped neon-edged bases. Several faint diagonal cyan searchlight beams rise into the sky. Above, a deep navy star-speckled sky gradients through dusty purple and mauve to peach and vivid orange at the horizon; a large slender silver crescent moon hangs in the upper left. In the lower right, an irregular turquoise pool reflects the city. A tall dark-green multi-armed saguaro with a thin pink neon rim stands on its near bank, with one much smaller distant cactus at the far right. An elevated black monorail guideway with glowing golden edges curves from the bottom-right corner toward the city on thin supports; one short sleek dark-teal train sits on its near bend. Warm sunset sand contrasts with cool cyan and magenta neon, atmospheric haze, soft volumetric light, crisp detail."
   },
   "speed": {
    "status": "ok",
    "runs": 3,
    "tps": 186.8,
    "tps_min": 173.0,
    "tps_max": 190.6,
    "ttft": 11.45,
    "seconds": 13.7,
    "out_tokens": 2620
   },
   "value": {
    "out_tokens": 2443,
    "cost": 0.02519,
    "seconds": 12.4,
    "finish": "stop",
    "status": "ok",
    "correct": 12,
    "total": 12,
    "per_q": [
     true,
     true,
     true,
     true,
     true,
     true,
     true,
     true,
     true,
     true,
     true,
     true
    ],
    "per_1k": 4.91,
    "per_dollar": 476
   }
  },
  {
   "id": "kimi-k3-1-pro-highspeed",
   "name": "Kimi K3.1 Pro Highspeed",
   "lab": "Moonshot AI",
   "icon": "logos/kimi-color.svg",
   "released": "2026-10-23",
   "price_in": 5,
   "price_out": 25,
   "vision": true,
   "alpaca": {
    "out_tokens": 24623,
    "cost": 0.61682,
    "seconds": 145.3,
    "finish": "stop",
    "status": "ok",
    "score": 68.8,
    "criteria": {
     "alpaca": 7.5,
     "motion": 5.5,
     "beauty": 7.5,
     "scene": 7.0
    },
    "by_judge": {
     "claude-opus-5-5": 65.0,
     "openai-gpt-6-sol": 72.5
    },
    "notes": {
     "claude-opus-5-5": "A charming, clearly alpaca-like figure with a fleecy cloud body, topknot, long neck and collar in a soft muted mountain scene; the oversized llama-like ears and spindly, awkwardly jointed legs weaken the anatomy, and the walk is a stiff leg cycle with little body bob in place over a static backdrop ",
     "openai-gpt-6-sol": "The alpaca is charming and recognizable, with polished fleece and a tasteful mountain backdrop, though its long ears and somewhat stiff, repetitive gait limit the realism."
    },
    "judges": 2,
    "motion": 0.654
   },
   "design": {
    "out_tokens": 31652,
    "cost": 0.792425,
    "seconds": 173.7,
    "finish": "stop",
    "status": "ok",
    "score": 85.0,
    "criteria": {
     "typography": 8.0,
     "layout": 8.5,
     "colour": 8.5,
     "completeness": 10,
     "originality": 7.5
    },
    "by_judge": {
     "claude-opus-5-5": 82.0,
     "openai-gpt-6-sol": 88.0
    },
    "notes": {
     "claude-opus-5-5": "A polished, cohesive page: an elegant serif-and-sans pairing, a warm dusk palette, a strong illustrated hero and a well-crafted departure board, though the feature cards and pricing tiers lean on familiar SaaS-template patterns and some small body text is low-contrast.",
     "openai-gpt-6-sol": "A polished, cohesive page with all seven sections and a distinctive illustrated hero, though some small, faint text hurts readability."
    },
    "judges": 2
   },
   "recreate": {
    "out_tokens": 1343,
    "cost": 0.04036,
    "seconds": 24.7,
    "finish": "stop",
    "status": "ok",
    "score": 67.0,
    "criteria": {
     "subjects": 8.5,
     "layout": 6.0,
     "colour": 6.5,
     "style": 6.5,
     "overall": 6.0
    },
    "by_judge": {
     "claude-opus-5-5": 64.0,
     "openai-gpt-6-sol": 70.0
    },
    "notes": {
     "claude-opus-5-5": "All key elements are present, though the cloak is purple rather than red and the OASIS sign sits on a tower rather than standing apart; the city sits further right, the figures are larger, the moon is smaller, the sand is more saturated orange, and the sky lacks the original's warm purple-orange dus",
     "openai-gpt-6-sol": "Nearly all defining elements are present, but the traveller, towers, pool and monorail shift noticeably, and the recreation is brighter and sharper than the original."
    },
    "judges": 2,
    "prompt": "Ultra-wide 16:9 cinematic science-fiction matte painting, photorealistic detail, teal-and-orange palette. At twilight, rippled orange desert dunes fill the foreground, with windblown sand and long shadows. On a dune at lower left, seen from behind, stand exactly one shaggy beige-gray llama and one dark-haired person in a flowing ankle-length burgundy cape; both face a distant city. The futuristic oasis city sits center-right: dense low buildings and tiered circular complexes outlined in cyan and magenta, supporting three sleek glass needle skyscrapers. The tallest central teal tower has a brilliant horizontal turquoise neon halo near its tip; the left tower displays the vertical cyan text \u201cOASIS\u201d; the right tower glows violet-pink. Above, a deep navy starry sky gradients through purple and dusty blue to a peach-orange horizon, with a large slender silver crescent moon in the upper left and three diagonal cyan searchlight beams crossing the sky. At lower right, a small sleek cyan train travels on a single elevated golden light-rail track that S-curves from the bottom-right corner toward the city, supported by dark pylons. Behind it lies an irregular luminous turquoise pond. A tall dark-green saguaro cactus with two raised arms and pink neon rim lighting stands in front of the pond at the far right; one tiny distant cactus appears farther right. Atmospheric haze, glowing reflections, dramatic scale, soft cinematic lighting, crisp intricate details, no border."
   },
   "speed": {
    "status": "ok",
    "runs": 3,
    "tps": 94.3,
    "tps_min": 91.0,
    "tps_max": 102.6,
    "ttft": 13.73,
    "seconds": 19.5,
    "out_tokens": 1835
   },
   "value": {
    "out_tokens": 2052,
    "cost": 0.0532,
    "seconds": 8.3,
    "finish": "stop",
    "status": "ok",
    "correct": 12,
    "total": 12,
    "per_q": [
     true,
     true,
     true,
     true,
     true,
     true,
     true,
     true,
     true,
     true,
     true,
     true
    ],
    "per_1k": 5.85,
    "per_dollar": 226
   }
  },
  {
   "id": "inkling-2-mini",
   "name": "Inkling 2 Mini",
   "lab": "Thinking Machines",
   "icon": "logos/thinkingmachines.svg",
   "released": "2026-11-24",
   "price_in": 0.12,
   "price_out": 0.5,
   "vision": true,
   "alpaca": {
    "out_tokens": 28767,
    "cost": 0.01440726,
    "seconds": 86.1,
    "finish": "stop",
    "status": "ok",
    "score": 62.5,
    "criteria": {
     "alpaca": 6.5,
     "motion": 5.5,
     "beauty": 6.5,
     "scene": 6.5
    },
    "by_judge": {
     "claude-opus-5-5": 60.0,
     "openai-gpt-6-sol": 65.0
    },
    "notes": {
     "claude-opus-5-5": "A recognisable fluffy cream alpaca with a long neck, small head and upright ears walks through a soft, pleasant pastel morning scene with scrolling ground and changing leg poses, but the oversized blob body, stiff stick legs with awkward joint bends, minimal body bob and a stray clipped circle in th",
     "openai-gpt-6-sol": "The fluffy alpaca is clearly recognizable and the pastel scene is tasteful, but the legs change without a convincing planted-foot walking cycle."
    },
    "judges": 2,
    "motion": 1.768
   },
   "design": {
    "out_tokens": 29053,
    "cost": 0.01454654,
    "seconds": 75.9,
    "finish": "stop",
    "status": "ok",
    "score": 66.0,
    "criteria": {
     "typography": 7.5,
     "layout": 4.5,
     "colour": 8.0,
     "completeness": 5.5,
     "originality": 7.5
    },
    "by_judge": {
     "claude-opus-5-5": 62.0,
     "openai-gpt-6-sol": 70.0
    },
    "notes": {
     "claude-opus-5-5": "The dusk-to-neon palette, skyline illustration and serif-italic accent give the page real character, but the hero headline is clipped under the fixed nav and the testimonial section is missing, leaving a large empty purple void before the footer.",
     "openai-gpt-6-sol": "The distinctive desert-night design is strong, but the hero heading overlaps the navigation, a large empty gap disrupts the page, and the required testimonial is missing."
    },
    "judges": 2
   },
   "recreate": {
    "out_tokens": 1223,
    "cost": 0.00069142,
    "seconds": 8.6,
    "finish": "stop",
    "status": "ok",
    "score": 62.0,
    "criteria": {
     "subjects": 8.5,
     "layout": 6.0,
     "colour": 6.5,
     "style": 5.0,
     "overall": 5.0
    },
    "by_judge": {
     "claude-opus-5-5": 58.0,
     "openai-gpt-6-sol": 66.0
    },
    "notes": {
     "claude-opus-5-5": "All key elements are present in roughly similar positions, but the recreation is a stylized digital illustration with a darker, starrier sky, a larger city zoomed in closer, and a different monorail and figure design, whereas the original is a softer photoreal matte painting.",
     "openai-gpt-6-sol": "Nearly every requested element is present, but the towers, traveller, cactus, and track are much larger, making the recreation brighter and less atmospheric than the original."
    },
    "judges": 2,
    "prompt": "Cinematic sci-fi desert panorama at dusk, painting-like digital art, ultra-detailed. Lower-left foreground: wind-rippled orange-brown sand dune ridge descending toward center, deep shadows at bottom-left. Silhouette-like figure standing on ridge with back to viewer: short dark hair, long flowing crimson/red hooded cloak, dark legs, gazing across desert. To figure\u2019s left stands a gray-brown alpaca/llama in profile facing right. Background center-right: futuristic metropolis of glass and steel towers on low podiums, tiered curved crown-like bases with glowing cyan horizontal bands, dozens of small lit-window skyscrapers. Tallest central spire: sleek teal-blue tapered glass tower reaching near sky, ringed around upper-middle by a bright cyan neon halo/ellipse. Left slimmer dark-teal spire with pointed tip; adjacent vertical cyan-outlined neon sign clearly reading \u201cOASIS\u201d downward. Right curved violet-purple blade skyscraper with magenta neon edge. Deep navy starry sky fades through purple and pink to orange-gold horizon; large pale crescent moon upper-left, bright edge on right, dark disc, glowing. Thin cyan searchlight beams shoot upward from city toward top edge on left and right. Lower-right: curved raised monorail track with golden-orange glowing rails and dark supports, sleek silver pod; turquoise lagoon beneath/right of track, large saguaro cactus outlined in pink neon at right, small saguaro farther right background. Warm rim light on dunes, neon reflections, orange haze, high contrast, matte cinematic composition."
   },
   "speed": {
    "status": "ok",
    "runs": 3,
    "tps": 207.5,
    "tps_min": 204.3,
    "tps_max": 228.3,
    "ttft": 4.27,
    "seconds": 8.5,
    "out_tokens": 1731
   },
   "value": {
    "out_tokens": 7306,
    "cost": 0.00369284,
    "seconds": 18.7,
    "finish": "stop",
    "status": "ok",
    "correct": 11,
    "total": 12,
    "per_q": [
     true,
     true,
     true,
     true,
     true,
     true,
     false,
     true,
     true,
     true,
     true,
     true
    ],
    "per_1k": 1.51,
    "per_dollar": 2979
   }
  },
  {
   "id": "hy4",
   "name": "Hy4",
   "lab": "Tencent",
   "icon": "logos/hy4.svg",
   "released": "2026-11-25",
   "price_in": 1.0425,
   "price_out": 3.12625,
   "vision": false,
   "alpaca": {
    "out_tokens": 23310,
    "cost": 0.07306992000000001,
    "seconds": 257.5,
    "finish": "stop",
    "status": "ok",
    "score": 61.2,
    "criteria": {
     "alpaca": 6.5,
     "motion": 5.5,
     "beauty": 6.0,
     "scene": 6.5
    },
    "by_judge": {
     "claude-opus-5-5": 62.5,
     "openai-gpt-6-sol": 60.0
    },
    "notes": {
     "claude-opus-5-5": "The fluffy body, long neck and upright ears read as an alpaca, but the overly long, bare, deer-like legs and fox-like head weaken the anatomy; the legs swing plausibly across frames against a scrolling parallax background, and the pastel dusk scene is pleasant though generic, with an empty ground pl",
     "openai-gpt-6-sol": "The fleece, long neck and small head read as an alpaca, but the stick-thin legs and modest changes between frames make the walk feel stiff."
    },
    "judges": 2,
    "motion": 2.176
   },
   "design": {
    "out_tokens": 26815,
    "cost": 0.08400136375,
    "seconds": 244.2,
    "finish": "stop",
    "status": "ok",
    "score": 43.0,
    "criteria": {
     "typography": 6.0,
     "layout": 1.5,
     "colour": 6.5,
     "completeness": 2.0,
     "originality": 5.5
    },
    "by_judge": {
     "claude-opus-5-5": 42.0,
     "openai-gpt-6-sol": 44.0
    },
    "notes": {
     "claude-opus-5-5": "The synthwave hero has a strong gradient headline, but a cyan line slices through the text and the sun crowds the copy; below it the features, timetable, pricing and testimonial never render (likely stuck scroll-reveal animations), leaving thousands of pixels of empty black between the section headi",
     "openai-gpt-6-sol": "The neon-desert hero has character, but the page is mostly empty after it, with the features, timetable, pricing and testimonial missing."
    },
    "judges": 2
   },
   "recreate": {
    "status": "no vision",
    "error": "This model cannot take image input."
   },
   "speed": {
    "status": "ok",
    "runs": 3,
    "tps": 84.0,
    "tps_min": 83.5,
    "tps_max": 87.0,
    "ttft": 133.02,
    "seconds": 136.4,
    "out_tokens": 11463
   },
   "value": {
    "out_tokens": 7879,
    "cost": 0.024962196250000002,
    "seconds": 109.2,
    "finish": "stop",
    "status": "ok",
    "correct": 12,
    "total": 12,
    "per_q": [
     true,
     true,
     true,
     true,
     true,
     true,
     true,
     true,
     true,
     true,
     true,
     true
    ],
    "per_1k": 1.52,
    "per_dollar": 481
   }
  },
  {
   "id": "gemini-4-neon",
   "name": "Gemini 4 Neon",
   "lab": "Google",
   "icon": "logos/gemini-color.svg",
   "released": "2026-11-19",
   "price_in": 3.75,
   "price_out": 18.75,
   "vision": true,
   "alpaca": {
    "out_tokens": 25241,
    "cost": 0.47403,
    "seconds": 203.4,
    "finish": "stop",
    "status": "ok",
    "score": 63.8,
    "criteria": {
     "alpaca": 7.0,
     "motion": 5.0,
     "beauty": 6.5,
     "scene": 7.0
    },
    "by_judge": {
     "claude-opus-5-5": 62.5,
     "openai-gpt-6-sol": 65.0
    },
    "notes": {
     "claude-opus-5-5": "A clearly readable fleecy alpaca with a long neck, upright ears and a charming collar walks through a soft, tasteful Andean scene with drifting clouds and grass parallax, but its blocky, plate-like upper legs and awkward joint bends weaken both the anatomy and the believability of the gait.",
     "openai-gpt-6-sol": "The alpaca is charming and recognizable, but its legs change only slightly between frames, making the walk feel more like a shuffle."
    },
    "judges": 2,
    "motion": 4.016
   },
   "design": {
    "out_tokens": 36380,
    "cost": 0.6828,
    "seconds": 302.9,
    "finish": "stop",
    "status": "ok",
    "score": 83.0,
    "criteria": {
     "typography": 8.0,
     "layout": 7.5,
     "colour": 8.0,
     "completeness": 10,
     "originality": 8.0
    },
    "by_judge": {
     "claude-opus-5-5": 80.0,
     "openai-gpt-6-sol": 86.0
    },
    "notes": {
     "claude-opus-5-5": "A polished dark sleeper-train page with strong sans/italic-serif/mono hierarchy, a cohesive amber-and-neon palette and every required section well executed, though the route-map labels collide at the Mirage Causeway/Vespera end and the overall structure follows a familiar premium-SaaS template.",
     "openai-gpt-6-sol": "A distinctive, complete page with strong visual hierarchy, though some small, low-contrast text and overlapping route labels reduce readability."
    },
    "judges": 2
   },
   "recreate": {
    "out_tokens": 1227,
    "cost": 0.0276975,
    "seconds": 15.4,
    "finish": "stop",
    "status": "ok",
    "score": 62.0,
    "criteria": {
     "subjects": 8.5,
     "layout": 6.0,
     "colour": 6.0,
     "style": 5.5,
     "overall": 5.0
    },
    "by_judge": {
     "claude-opus-5-5": 60.0,
     "openai-gpt-6-sol": 64.0
    },
    "notes": {
     "claude-opus-5-5": "All key elements are present, but the recreation shifts the city right and enlarges it, puts the moon higher with a darker lit side, makes the figures and cactus much larger with an extra cacti cluster and flying craft, and uses a more saturated, illustrative purple-pink style instead of the origina",
     "openai-gpt-6-sol": "Nearly all key elements are present, but the towers, traveller, alpaca, cactus and track differ noticeably in scale or placement, and the recreation is sharper and more neon-saturated."
    },
    "judges": 2,
    "prompt": "Cinematic sci-fi digital art of a desert at twilight. In the lower left on a wind-swept sand dune ridge, a man in a dark red cloak stands from behind next to a fluffy brown llama, facing a futuristic city. On the lower right, a large green saguaro cactus outlined in glowing pink neon stands near a smaller cactus and a turquoise oasis pond. A curved, orange-lit elevated monorail carrying a sleek train winds from the bottom right toward the city. Center-right rises a futuristic metropolis with three giant tapered skyscrapers: the tallest middle spire features a glowing cyan neon halo ring, the left tower has a vertical cyan sign reading \"OASIS\", and the right tower glows purple. Diagonal cyan searchlights shoot skyward from the illuminated city base. The starry sky fades from deep dark blue to purple and warm orange at the horizon, with a giant crescent moon in the upper left."
   },
   "speed": {
    "status": "ok",
    "runs": 3,
    "tps": 113.5,
    "tps_min": 109.4,
    "tps_max": 114.8,
    "ttft": 46.23,
    "seconds": 49.9,
    "out_tokens": 5724
   },
   "value": {
    "out_tokens": 8588,
    "cost": 0.16238625,
    "seconds": 73.1,
    "finish": "stop",
    "status": "ok",
    "correct": 12,
    "total": 12,
    "per_q": [
     true,
     true,
     true,
     true,
     true,
     true,
     true,
     true,
     true,
     true,
     true,
     true
    ],
    "per_1k": 1.4,
    "per_dollar": 74
   }
  },
  {
   "id": "openai-gpt-62-astra",
   "name": "GPT-6.2 Astra",
   "lab": "OpenAI",
   "icon": "logos/openai.svg",
   "released": "2026-11-17",
   "price_in": 8,
   "price_out": 40,
   "vision": true,
   "alpaca": {
    "out_tokens": 11986,
    "cost": 0.480784,
    "seconds": 247.4,
    "finish": "stop",
    "status": "ok",
    "score": 68.8,
    "criteria": {
     "alpaca": 8.0,
     "motion": 2.5,
     "beauty": 8.5,
     "scene": 8.5
    },
    "by_judge": {
     "claude-opus-5-5": 67.5,
     "openai-gpt-6-sol": 70.0
    },
    "notes": {
     "claude-opus-5-5": "A charming, well-proportioned fleecy alpaca with a woven saddle blanket sits in a polished, tastefully muted Andean scene, but the walk barely registers: frames 1 and 2 show an essentially identical leg pose (only the foreground grass shifts), frame 3 changes the legs only modestly, and the swaying ",
     "openai-gpt-6-sol": "The alpaca and Andean landscape are beautifully crafted, but the first two poses are nearly identical and the third shows only slight leg movement."
    },
    "judges": 2,
    "motion": 1.529
   },
   "design": {
    "out_tokens": 13227,
    "cost": 0.53024,
    "seconds": 240.9,
    "finish": "stop",
    "status": "ok",
    "score": 90.0,
    "criteria": {
     "typography": 9.0,
     "layout": 8.5,
     "colour": 9.0,
     "completeness": 10,
     "originality": 8.5
    },
    "by_judge": {
     "claude-opus-5-5": 88.0,
     "openai-gpt-6-sol": 92.0
    },
    "notes": {
     "claude-opus-5-5": "A polished, cohesive page: tight grotesk headlines with italic serif accents, monospace timetable details, a dusk palette of peach and lime on near-black broken by a cream timetable band, and all seven sections well formed, though the features strip feels slightly cramped and the testimonial area le",
     "openai-gpt-6-sol": "A polished, distinctive rail-themed page with clear hierarchy, cohesive colour, and all seven requested sections fully formed."
    },
    "judges": 2
   },
   "recreate": {
    "out_tokens": 307,
    "cost": 0.021704,
    "seconds": 13.2,
    "finish": "stop",
    "status": "ok",
    "score": 67.0,
    "criteria": {
     "subjects": 8.0,
     "layout": 6.5,
     "colour": 6.5,
     "style": 6.5,
     "overall": 6.0
    },
    "by_judge": {
     "claude-opus-5-5": 64.0,
     "openai-gpt-6-sol": 70.0
    },
    "notes": {
     "claude-opus-5-5": "All the key elements are present in roughly the right places, but the recreation differs in several ways: a larger near-full moon instead of a thin crescent, a dull brown cloak rather than red, an oversized cactus with only a faint neon outline, a muted sky without the vivid orange horizon glow, and",
     "openai-gpt-6-sol": "Nearly all key subjects are present, but the cactus is much larger, the tower ring and monorail have shifted, and the recreation has brighter, broader beams."
    },
    "judges": 2,
    "prompt": "Wide 16:9 cinematic science-fiction digital matte painting. Rolling copper-orange desert dunes fill the lower half, fine parallel wind ripples across the sunlit foreground ridge, deep violet-brown shadows on its left slope, wisps of blowing sand. On the crest at left quarter stand one dark-haired traveler seen from behind, wearing a long burgundy cloak and dark boots, and one smaller shaggy brown llama immediately to their left, both gazing toward the distant city, long shadows stretching lower left. Center-right horizon: futuristic oasis metropolis, clustered low illuminated buildings and broad stepped circular terraces edged in turquoise light. Three dominant tapered glass spires: left teal blade with a cyan outlined vertical sign reading \u201cOASIS\u201d in white letters stacked top to bottom; much taller central needle reaching nearly to the top edge, encircled near its tip by a brilliant horizontal cyan elliptical halo; right slender magenta-lit blade. Pale teal searchlight beams fan upward. Sky grades from star-speckled midnight navy overhead through dusky lavender to glowing peach-gold at the right horizon. Huge dim planetary disk upper left, slender pale crescent along lower-right rim. Golden-lit elevated monorail on slim pillars sweeps from lower right in an S-curve toward the city, one sleek blue train on the near bend. Turquoise pool lower right behind track; tall dark green multiarmed saguaro outlined in neon pink dominates right foreground, one tiny cactus farther right. Atmospheric, softly luminous, richly detailed."
   },
   "speed": {
    "status": "ok",
    "runs": 3,
    "tps": 37.9,
    "tps_min": 35.8,
    "tps_max": 39.2,
    "ttft": 5.39,
    "seconds": 17.8,
    "out_tokens": 688
   },
   "value": {
    "out_tokens": 419,
    "cost": 0.019152,
    "seconds": 8.0,
    "finish": "stop",
    "status": "ok",
    "correct": 12,
    "total": 12,
    "per_q": [
     true,
     true,
     true,
     true,
     true,
     true,
     true,
     true,
     true,
     true,
     true,
     true
    ],
    "per_1k": 28.64,
    "per_dollar": 627
   }
  },
  {
   "id": "openai-gpt-62-astra-pro",
   "name": "GPT-6.2 Astra Pro",
   "lab": "OpenAI",
   "icon": "logos/openai.svg",
   "released": "2026-11-17",
   "price_in": 8,
   "price_out": 40,
   "vision": true,
   "alpaca": {
    "out_tokens": 24762,
    "cost": 1.192912,
    "seconds": 299.7,
    "finish": "stop",
    "status": "ok",
    "score": 77.5,
    "criteria": {
     "alpaca": 7.5,
     "motion": 6.5,
     "beauty": 8.5,
     "scene": 8.5
    },
    "by_judge": {
     "claude-opus-5-5": 75.0,
     "openai-gpt-6-sol": 80.0
    },
    "notes": {
     "claude-opus-5-5": "A charming, polished camelid with a fleecy body, long neck and woven saddle blanket, plus plausible gait changes across frames and a tasteful layered Andean plate; the long banana ears and bare, deer-thin legs read more llama than alpaca, and the walk is believable but somewhat stiff.",
     "openai-gpt-6-sol": "The alpaca is recognizable and the Altiplano scene is beautifully composed, though its slender legs move more convincingly than its nearly static body."
    },
    "judges": 2,
    "motion": 2.442
   },
   "design": {
    "out_tokens": 29907,
    "cost": 1.439272,
    "seconds": 296.5,
    "finish": "stop",
    "status": "ok",
    "score": 85.0,
    "criteria": {
     "typography": 8.5,
     "layout": 8.5,
     "colour": 8.0,
     "completeness": 9.5,
     "originality": 8.0
    },
    "by_judge": {
     "claude-opus-5-5": 80.0,
     "openai-gpt-6-sol": 90.0
    },
    "notes": {
     "claude-opus-5-5": "A polished, cohesive editorial take: serif display type with mono labels, a warm dusk palette, a strong illustrated hero and a well-crafted timetable and fare cards. It still leans on a familiar premium-template structure, and the 'neon city' theme is muted rather than truly electric.",
     "openai-gpt-6-sol": "A polished, distinctive rail-travel page with every required section; the muted city illustration does not quite deliver the promised neon atmosphere."
    },
    "judges": 2
   },
   "recreate": {
    "out_tokens": 960,
    "cost": 0.075568,
    "seconds": 23.5,
    "finish": "stop",
    "status": "ok",
    "score": 70.0,
    "criteria": {
     "subjects": 8.5,
     "layout": 6.0,
     "colour": 7.0,
     "style": 7.5,
     "overall": 6.0
    },
    "by_judge": {
     "claude-opus-5-5": 70.0,
     "openai-gpt-6-sol": 70.0
    },
    "notes": {
     "claude-opus-5-5": "All key elements are present, but the cloak reads more purple than red, the searchlights are short fanned beams rather than long sky-spanning shafts, the cactus and pool have shifted to the lower centre with the monorail track curving differently, and the horizon lacks the original's strong orange g",
     "openai-gpt-6-sol": "Nearly all key elements are present, but the cactus, traveller, pool and monorail track shift noticeably, and the recreation has flatter lighting."
    },
    "judges": 2,
    "prompt": "Wide 1.79:1 cinematic science-fiction digital matte painting. Rolling burnt-orange desert dunes at twilight, fine wind-rippled sand, wisps of blowing dust. A sunlit dune crest runs diagonally from left mid-foreground toward the bottom right. On its left third, seen from behind, one dark-haired traveler in a long flowing burgundy cloak and dark boots stands looking toward the city, one shaggy brown llama immediately to their left; long shadows stretch toward lower left. Center-right on the horizon, a futuristic oasis metropolis: low densely packed illuminated buildings surrounding broad stacked circular terraces edged in turquoise. Three dominant tapered skyscrapers: a slender teal left spire bearing a glowing rectangular cyan sign reading \u201cOASIS\u201d vertically, one letter per line; a much taller needle-like glass central tower encircled near its tip by a brilliant horizontal elliptical cyan halo; a slender violet-lit right spire. Faint turquoise searchlight beams fan into the sky. At right a slender elevated monorail on spaced pylons, amber-lit edges, snakes from the lower-right corner around a bend toward the city, one small segmented teal train on the near curve. Giant dark green multiarmed saguaro outlined in pink light at right foreground beside a luminous turquoise pool, one smaller cactus beyond. Vast sparsely starred navy sky fading through lavender to peach-orange at the right horizon. Huge dim planetary disk upper left with pale crescent along lower-right rim. Atmospheric haze, warm grazing light, cool neon accents."
   },
   "speed": {
    "status": "ok",
    "runs": 3,
    "tps": 54.3,
    "tps_min": 53.8,
    "tps_max": 56.6,
    "ttft": 41.12,
    "seconds": 41.3,
    "out_tokens": 2221
   },
   "value": {
    "out_tokens": 1083,
    "cost": 0.071656,
    "seconds": 16.8,
    "finish": "stop",
    "status": "ok",
    "correct": 12,
    "total": 12,
    "per_q": [
     true,
     true,
     true,
     true,
     true,
     true,
     true,
     true,
     true,
     true,
     true,
     true
    ],
    "per_1k": 11.08,
    "per_dollar": 167
   }
  },
  {
   "id": "openai-gpt-62-sol",
   "name": "GPT-6.2 Sol",
   "lab": "OpenAI",
   "icon": "logos/openai.svg",
   "released": "2026-11-17",
   "price_in": 2,
   "price_out": 10,
   "vision": true,
   "alpaca": {
    "out_tokens": 13157,
    "cost": 0.131906,
    "seconds": 205.9,
    "finish": "stop",
    "status": "ok",
    "score": 57.5,
    "criteria": {
     "alpaca": 7.0,
     "motion": 1.0,
     "beauty": 7.5,
     "scene": 7.5
    },
    "by_judge": {
     "claude-opus-5-5": 52.5,
     "openai-gpt-6-sol": 62.5
    },
    "notes": {
     "claude-opus-5-5": "A charming fleecy camelid in a polished pastel dusk landscape, but its long rabbit-like ears and bare deer-thin legs read more llama than alpaca, and the legs and body look identical across all three frames, with at most faint shifts in the foreground grass, so there is effectively no walk.",
     "openai-gpt-6-sol": "The alpaca and sunset scene are polished, but its legs and body barely change between frames, so the walk is not convincing."
    },
    "judges": 2,
    "motion": 0.732
   },
   "design": {
    "out_tokens": 14180,
    "cost": 0.14209,
    "seconds": 192.3,
    "finish": "stop",
    "status": "ok",
    "score": 87.0,
    "criteria": {
     "typography": 8.5,
     "layout": 8.5,
     "colour": 8.5,
     "completeness": 10,
     "originality": 8.0
    },
    "by_judge": {
     "claude-opus-5-5": 82.0,
     "openai-gpt-6-sol": 92.0
    },
    "notes": {
     "claude-opus-5-5": "A polished, cohesive dusk-palette page with elegant serif display type, a strong illustrated hero and every required section well formed, though the section structure and pricing cards follow a fairly familiar premium-template pattern.",
     "openai-gpt-6-sol": "A polished, distinctive page with every requested section; some small secondary text is faint against the dark background."
    },
    "judges": 2
   },
   "recreate": {
    "out_tokens": 439,
    "cost": 0.006746,
    "seconds": 12.6,
    "finish": "stop",
    "status": "ok",
    "score": 72.0,
    "criteria": {
     "subjects": 8.5,
     "layout": 7.0,
     "colour": 7.0,
     "style": 7.0,
     "overall": 6.5
    },
    "by_judge": {
     "claude-opus-5-5": 66.0,
     "openai-gpt-6-sol": 78.0
    },
    "notes": {
     "claude-opus-5-5": "All key elements are present in broadly matching positions, but the traveller's cloak is muted purple rather than red, the animal reads as a llama, the sky lacks the strong orange horizon glow, and the rendering is more illustrative and less photographic than the original.",
     "openai-gpt-6-sol": "Nearly all key elements are present, but the traveller, alpaca, cactus and monorail are larger or shifted, and the recreation has a cooler, sharper look."
    },
    "judges": 2,
    "prompt": "Cinematic 16:9 sci-fi concept art, viewed from a desert dune at twilight. Wind-rippled copper-orange sand fills the foreground, with deep violet-brown hollows and fine sand drifting off the crests. On the left foreground ridge, one short-haired traveler seen from behind wears a long dark burgundy cloak and boots; immediately to their left stands one shaggy brown llama, ears upright. Both face the distant city and cast long shadows toward the lower left.\n\nCenter-right on the horizon, a futuristic metropolis rises from layered, saucer-like terraces edged in cyan, surrounded by smaller buildings with amber windows. Three tapering glass spires dominate: the tallest in the middle, encircled near its tip by a brilliant horizontal cyan halo; a shorter teal spire on the left bearing a vertical cyan sign reading \u201cOASIS\u201d top to bottom; and a shorter purple spire on the right edged in magenta. Thin turquoise searchlight beams fan into the sky.\n\nAn elevated, gold-lit monorail on slender dark pylons enters from the bottom right, bends left, then sweeps back toward the city. One sleek blue-silver train with dark windows rounds the near bend. Behind the track at lower right lies a glowing turquoise oasis pool. A huge ribbed dark-green saguaro with three raised arms and a hot-pink neon outline stands in front of the water; one tiny cactus stands on the far bank.\n\nSparse stars, a huge crescent moon lit along its lower-right rim in the upper left, and a navy-to-mauve sky fading to amber at the right horizon. Atmospheric, finely detailed digital matte painting."
   },
   "speed": {
    "status": "ok",
    "runs": 3,
    "tps": 39.6,
    "tps_min": 39.4,
    "tps_max": 42.5,
    "ttft": 4.78,
    "seconds": 17.8,
    "out_tokens": 749
   },
   "value": {
    "out_tokens": 440,
    "cost": 0.004998,
    "seconds": 8.5,
    "finish": "stop",
    "status": "ok",
    "correct": 12,
    "total": 12,
    "per_q": [
     true,
     true,
     true,
     true,
     true,
     true,
     true,
     true,
     true,
     true,
     true,
     true
    ],
    "per_1k": 27.27,
    "per_dollar": 2401
   }
  },
  {
   "id": "openai-gpt-62-sol-pro",
   "name": "GPT-6.2 Sol Pro",
   "lab": "OpenAI",
   "icon": "logos/openai.svg",
   "released": "2026-11-17",
   "price_in": 2,
   "price_out": 10,
   "vision": true,
   "alpaca": {
    "out_tokens": 25130,
    "cost": 0.302118,
    "seconds": 241.6,
    "finish": "stop",
    "status": "ok",
    "score": 63.8,
    "criteria": {
     "alpaca": 7.5,
     "motion": 1.5,
     "beauty": 8.0,
     "scene": 8.5
    },
    "by_judge": {
     "claude-opus-5-5": 60.0,
     "openai-gpt-6-sol": 67.5
    },
    "notes": {
     "claude-opus-5-5": "A charming, clearly readable fleecy alpaca in a tasteful pastel altiplano with elegant typography, but its legs and body look essentially frozen across all three frames, so only the scrolling ground plants imply walking, and those plants drift over the 'FIELD STUDY / 01' caption.",
     "openai-gpt-6-sol": "The alpaca and landscape are beautifully drawn, but the legs and body barely change while the ground scrolls."
    },
    "judges": 2,
    "motion": 0.37
   },
   "design": {
    "out_tokens": 27528,
    "cost": 0.33157,
    "seconds": 215.2,
    "finish": "stop",
    "status": "ok",
    "score": 85.0,
    "criteria": {
     "typography": 8.5,
     "layout": 8.5,
     "colour": 8.5,
     "completeness": 9.5,
     "originality": 7.5
    },
    "by_judge": {
     "claude-opus-5-5": 80.0,
     "openai-gpt-6-sol": 90.0
    },
    "notes": {
     "claude-opus-5-5": "A polished synthwave-dusk design: the tight grotesk headlines pair well with the italic serif and mono labels, and the hero illustration is strong, but the features strip is undersized, the timetable has a lot of dead space in the fares column, and the overall structure follows a familiar premium-te",
     "openai-gpt-6-sol": "A polished, complete page with a distinctive illustrated hero, though some small text is subdued and the pricing cards follow a familiar pattern."
    },
    "judges": 2
   },
   "recreate": {
    "out_tokens": 2484,
    "cost": 0.034864,
    "seconds": 37.4,
    "finish": "stop",
    "status": "ok",
    "score": 62.0,
    "criteria": {
     "subjects": 8.5,
     "layout": 5.5,
     "colour": 7.0,
     "style": 5.0,
     "overall": 5.0
    },
    "by_judge": {
     "claude-opus-5-5": 62.0,
     "openai-gpt-6-sol": 62.0
    },
    "notes": {
     "claude-opus-5-5": "All key elements are present. However, the recreation uses a more illustrated, cartoonish style, enlarges and reframes the traveller and alpaca, and moves the cactus, pool and monorail toward the centre-right, so the composition and feel differ noticeably from the photoreal original.",
     "openai-gpt-6-sol": "Nearly all key elements are present, but the traveller, alpaca, cactus, pool, and track shift substantially, and the recreation is sharper and more stylized."
    },
    "judges": 2,
    "prompt": "Wide 16:9 cinematic sci-fi concept art, viewed from a desert dune at twilight. Wind-rippled copper sand fills the foreground, with deep violet shadows, drifting sand and a bright ridge sloping toward the lower right. On the left ridge, one short-haired traveler in a long dark burgundy cloak and boots stands with their back to us, a shaggy brown llama immediately to their left. Both face the distant city and cast long shadows toward the lower left.\n\nCenter-right on the horizon, a futuristic metropolis rises from layered dunes: warm speckled windows, low rectangular buildings and broad stacked circular terraces edged in turquoise. Exactly three dominant tapered glass spires: the tallest in the middle, almost reaching the top, with a brilliant horizontal cyan halo around its upper tip; a shorter teal spire on the left with a boxed cyan neon sign reading \u201cOASIS,\u201d one letter per line; a shorter violet spire on the right edged in magenta. Slender teal searchlight beams fan upward behind them.\n\nAn elevated monorail on thin dark supports curves from the city around a luminous turquoise pool in the lower right, then sweeps out through the bottom-right edge. Twin amber rail lights and one sleek teal train on the near bend. A huge ribbed saguaro outlined in pink neon stands before the pool at right, with one tiny cactus beyond it. A large pale crescent moon in the upper left, lit along its lower-right rim; sparse stars in a navy sky fading through lavender to apricot-gold at the horizon."
   },
   "speed": {
    "status": "ok",
    "runs": 3,
    "tps": 57.6,
    "tps_min": 54.9,
    "tps_max": 62.7,
    "ttft": 35.33,
    "seconds": 35.4,
    "out_tokens": 1953
   },
   "value": {
    "out_tokens": 1189,
    "cost": 0.019178,
    "seconds": 14.5,
    "finish": "stop",
    "status": "ok",
    "correct": 12,
    "total": 12,
    "per_q": [
     true,
     true,
     true,
     true,
     true,
     true,
     true,
     true,
     true,
     true,
     true,
     true
    ],
    "per_1k": 10.09,
    "per_dollar": 626
   }
  },
  {
   "id": "e2ee-kimi-k3-1-pro-p",
   "name": "Kimi K3.1 Pro (E2EE)",
   "lab": "Moonshot AI",
   "icon": "logos/kimi-color.svg",
   "released": "2026-11-17",
   "price_in": 2.5,
   "price_out": 12.5,
   "vision": true,
   "alpaca": {
    "out_tokens": 27196,
    "cost": 0.3405725,
    "seconds": 408.6,
    "finish": "stop",
    "status": "ok",
    "score": 66.2,
    "criteria": {
     "alpaca": 6.5,
     "motion": 5.5,
     "beauty": 7.5,
     "scene": 7.0
    },
    "by_judge": {
     "claude-opus-5-5": 65.0,
     "openai-gpt-6-sol": 67.5
    },
    "notes": {
     "claude-opus-5-5": "A soft, cohesive pastel scene with a recognisable fleecy camelid whose legs clearly cycle between frames, but the long rabbit-like ears read more llama than alpaca, the stick-thin legs have awkward joint bends, and the scenery is pleasant yet generic.",
     "openai-gpt-6-sol": "The fluffy, long-necked animal reads as an alpaca in a polished pastel landscape, but its thin legs move stiffly and the first and third poses are nearly the same."
    },
    "judges": 2,
    "motion": 0.762
   },
   "design": {
    "out_tokens": 30214,
    "cost": 0.3782375,
    "seconds": 469.2,
    "finish": "stop",
    "status": "ok",
    "score": 84.0,
    "criteria": {
     "typography": 8.0,
     "layout": 7.5,
     "colour": 8.5,
     "completeness": 9.5,
     "originality": 8.5
    },
    "by_judge": {
     "claude-opus-5-5": 80.0,
     "openai-gpt-6-sol": 88.0
    },
    "notes": {
     "claude-opus-5-5": "A polished, atmospheric editorial design with strong serif hierarchy, a distinctive illustrated hero and a cohesive dusk palette, but a visible 'Skip to content' link overlaps the nav logo, and some tiny grey meta text has weak contrast.",
     "openai-gpt-6-sol": "A distinctive, fully formed page with a cohesive desert-night palette, held back by tiny low-contrast text and a visible skip link obscuring the logo."
    },
    "judges": 2
   },
   "recreate": {
    "out_tokens": 1179,
    "cost": 0.01813,
    "seconds": 108.4,
    "finish": "stop",
    "status": "ok",
    "score": 64.0,
    "criteria": {
     "subjects": 7.5,
     "layout": 6.5,
     "colour": 5.5,
     "style": 7.0,
     "overall": 5.5
    },
    "by_judge": {
     "claude-opus-5-5": 58.0,
     "openai-gpt-6-sol": 70.0
    },
    "notes": {
     "claude-opus-5-5": "All key elements are present, but the moon is a large gibbous disc instead of a thin crescent, the alpaca reads as a llama, the city adds saucer-like buildings and a winding road, the figures are larger and closer, and the sky is warmer and hazier than the original's deep blue-purple dusk.",
     "openai-gpt-6-sol": "Most elements are present and similarly placed, but the moon, traveller and alpaca, tower positions, and warmer lighting make the recreation visibly different."
    },
    "judges": 2,
    "prompt": "A wide 16:9 cinematic science-fiction desert landscape, highly detailed digital matte painting with realistic atmospheric lighting. Rolling orange sand dunes fill the foreground, with fine ripple patterns, windblown dust, and long soft shadows. On the left dune crest, seen from behind and facing the distant city, stand one short-haired man in a flowing dark burgundy cloak and one shaggy tawny-gray llama; the llama is left of the man, its ears upright. A pale sand trail curves from them toward the city.\n\nThe futuristic oasis city occupies the center-right background: a dense cluster of small buildings beneath broad, tiered, saucer-like structures and three slender twisting glass supertowers. The tallest central teal tower tapers to a needle and has a brilliant horizontal cyan halo ring near its summit. The left tower glows turquoise and bears the vertical neon text \u201cOASIS\u201d in capital letters; the right tower is outlined in violet and magenta. Subtle teal searchlight beams angle into the sky.\n\nUpper left hangs an enormous silver crescent moon with its shadowed disk faintly visible. The star-speckled navy sky gradients through dusty purple and peach to a glowing orange horizon.\n\nAt lower right, an irregular turquoise oasis pool sits behind a tall multi-armed saguaro cactus edged in vivid pink neon; one tiny distant cactus stands farther right. A sleek small blue-gray train travels on an elevated golden illuminated monorail track that curves from the bottom-right foreground back toward the city, supported by thin dark posts. Warm sunset light contrasts with cyan, turquoise, and magenta neon."
   },
   "speed": {
    "status": "ok",
    "runs": 3,
    "tps": 57.7,
    "tps_min": 14.3,
    "tps_max": 67.8,
    "ttft": 53.11,
    "seconds": 57.7,
    "out_tokens": 3123
   },
   "value": {
    "out_tokens": 3038,
    "cost": 0.038925,
    "seconds": 60.0,
    "finish": "stop",
    "status": "ok",
    "correct": 12,
    "total": 12,
    "per_q": [
     true,
     true,
     true,
     true,
     true,
     true,
     true,
     true,
     true,
     true,
     true,
     true
    ],
    "per_1k": 3.95,
    "per_dollar": 308
   }
  },
  {
   "id": "deepseek-v4-1-flash-1017",
   "name": "DeepSeek v4.1 Flash (1017)",
   "lab": "DeepSeek",
   "icon": "logos/deepseek-color.svg",
   "released": "2026-10-17",
   "price_in": 0.3,
   "price_out": 1.2,
   "vision": true,
   "alpaca": {
    "out_tokens": 39669,
    "cost": 0.0476616,
    "seconds": 257.8,
    "finish": "stop",
    "status": "ok",
    "score": 57.5,
    "criteria": {
     "alpaca": 6.0,
     "motion": 5.0,
     "beauty": 5.5,
     "scene": 6.5
    },
    "by_judge": {
     "claude-opus-5-5": 55.0,
     "openai-gpt-6-sol": 60.0
    },
    "notes": {
     "claude-opus-5-5": "The bubble-cluster fleece, long neck, small head and upright ears read clearly as an alpaca, and the legs do swing alternately between frames as the grass scrolls, but the legs are flat, kneeless, tapered slabs only loosely attached to a lumpy body, so the walk is a stiff pendulum shuffle with littl",
     "openai-gpt-6-sol": "The fluffy long-necked alpaca is recognizable, but its stiff legs and nearly stationary body make the walk less convincing than the polished pastoral setting."
    },
    "judges": 2,
    "motion": 2.309
   },
   "design": {
    "out_tokens": 45019,
    "cost": 0.054074699999999996,
    "seconds": 266.5,
    "finish": "stop",
    "status": "ok",
    "score": 58.0,
    "criteria": {
     "typography": 7.5,
     "layout": 3.0,
     "colour": 7.5,
     "completeness": 3.5,
     "originality": 7.5
    },
    "by_judge": {
     "claude-opus-5-5": 58.0,
     "openai-gpt-6-sol": 58.0
    },
    "notes": {
     "claude-opus-5-5": "The nav, hero illustration, features and timetable are polished and atmospheric, but the three pricing tiers and the testimonial failed to render, leaving huge empty voids that break the page's rhythm.",
     "openai-gpt-6-sol": "The illustrated hero is distinctive, but the pricing tiers and testimonial are missing, leaving enormous blank sections in an otherwise polished page."
    },
    "judges": 2
   },
   "recreate": {
    "out_tokens": 896,
    "cost": 0.0012681,
    "seconds": 9.8,
    "finish": "stop",
    "status": "ok",
    "score": 67.0,
    "criteria": {
     "subjects": 9.0,
     "layout": 6.0,
     "colour": 6.5,
     "style": 6.5,
     "overall": 5.5
    },
    "by_judge": {
     "claude-opus-5-5": 68.0,
     "openai-gpt-6-sol": 66.0
    },
    "notes": {
     "claude-opus-5-5": "Every element is present. However, the recreation makes the city much larger and more central, adds extra searchlight beams, moves the monorail and pool to the foreground centre, makes the moon smaller, and uses a more saturated illustrative look instead of the original's softer photoreal haze, so i",
     "openai-gpt-6-sol": "Nearly all key elements are present, but the enlarged towers and figures, repositioned track, and brighter saturation make the recreation visibly different."
    },
    "judges": 2,
    "prompt": "Wide 16:9 sci-fi digital painting of a desert oasis at twilight. Foreground left: a silhouetted person in a long crimson cloak stands beside a light-brown woolly llama on a rolling orange sand dune, both facing away toward a distant futuristic city. Center background: a glowing cyberpunk metropolis with three dominant tapering glass towers\u2014tallest central spire encircled by a floating neon-cyan ring, left tower with vertical cyan neon sign reading \u201cOASIS,\u201d right tower edged in magenta neon\u2014rising from a tiered, circular mega-structure with horizontal cyan light bands and dense city lights. Several diagonal cyan and green light beams shoot upward from the city. Sky gradient from deep starry navy at top through violet and pink to warm orange near the horizon; large pale crescent moon upper left. Right foreground: a tall saguaro cactus outlined in neon pink, a smaller cactus further right, and a glowing turquoise pool. A curving elevated transit track with neon yellow-orange edge lighting sweeps from lower right toward the city, carrying one small blue-teal train. Sand dunes with wind-sculpted ridges and dust haze. Composition emphasizes tiny travelers dwarfed by the luminous city; cinematic lighting, neon reflections, concept-art style, crisp details, volumetric glow."
   },
   "speed": {
    "status": "ok",
    "runs": 3,
    "tps": 90.2,
    "tps_min": 88.4,
    "tps_max": 90.5,
    "ttft": 6.7,
    "seconds": 11.0,
    "out_tokens": 992
   },
   "value": {
    "out_tokens": 2522,
    "cost": 0.0031242,
    "seconds": 18.8,
    "finish": "stop",
    "status": "ok",
    "correct": 12,
    "total": 12,
    "per_q": [
     true,
     true,
     true,
     true,
     true,
     true,
     true,
     true,
     true,
     true,
     true,
     true
    ],
    "per_1k": 4.76,
    "per_dollar": 3841
   }
  }
 ],
 "judges": [
  "claude-opus-5-5",
  "openai-gpt-6-sol"
 ],
 "image_model": "nano-banana-2-1",
 "contestant_spend": 18.62,
 "questions": 12,
 "run_note": "The first ten models ran on 2026-11-16; the nine newer entries ran on 2026-11-25."
};
