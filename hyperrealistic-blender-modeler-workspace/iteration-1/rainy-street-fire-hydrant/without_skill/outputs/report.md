# Red fire hydrant on a wet city sidewalk at dusk

The final render is at `outputs/final_render.png` (1920x1080). It was rendered in Cycles on the RTX 5050 (OptiX), 256 adaptive samples, denoised, with the AgX view transform. The scene is saved in `outputs/fire_hydrant.blend`.

## In the scene
- **Hydrant:** All of it is procedural. The body is a lathe-spun profile (flange base, barrel, bonnet ring, domed top). It has a pentagon operating nut, two side hose nozzles with caps and pentagon nuts, and a larger front pumper nozzle with its cap. There are 8 hex bolts on the base flange, 6 on the bonnet, and small chain links hanging from the side caps.
- **Peeling paint and rust:** One procedural material does both. Noise masks peel the red paint back to gray primer or bare iron, and rust grows in the exposed areas. There is more rust near the base, plus rust streaks running down the barrel. A bump map makes the paint edges look raised and the rust look grainy. The intact paint has a clear coat that reads as wet sheen.
- **Wet sidewalk:** Concrete slabs with beveled edges and gaps, each at a slightly random height. There is a curb, a gutter and asphalt beyond it. The ground shader uses a noise-driven puddle mask. Puddles are dark and mirror-smooth with faint ripples, the edges around them are damp and darker, and the rest is wet concrete with fine aggregate. A puddle at the hydrant's base reflects it.
- **Dusk lighting:** The sky is a gradient from orange at the horizon to deep blue overhead. There are three sodium-orange streetlamps (spot lights with glowing heads), a cool blue fill from the sky side and a warm glow from behind. In the background are a wet brick wall, buildings with randomly lit windows, and small bright lights in the distance. The camera is low (40 mm, f/2.0) with shallow depth of field.

## Known limitations / possible next steps
- There is no falling rain or droplets on the hydrant. Adding beaded water on the paint would make it look wetter.
- The concrete reflects the sky strongly at grazing angles, so it reads a little light and milky for dusk. Darker concrete or a darker horizon in the sky would give a moodier, more contrasted look.
- The out-of-focus left side of the frame is fairly empty: mostly orange sky and a lamp post. Background cars or storefronts would fill it in.
- All textures are procedural and there are no image or photo-scanned textures. Seen up close, the peel shapes look somewhat noise-generated.
