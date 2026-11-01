# London Underground-style platform: render done

**Render:** `final_render.png` (1920x1080, Cycles on the RTX 5050 with OptiX, 512 adaptive samples, OptiX denoise, AgX colour). It took about 2m15s.
**Scene file:** `underground_station_platform.blend`. Poster textures are packed into it, and copies are in `textures/`.
**Build script:** `build_station.py`. Run it with `blender -b --factory-startup --python build_station.py -- final -0.3` to rebuild and re-render. The last value is the exposure.

## What's in the shot
The camera is at eye level (1.62 m), standing on the platform and looking down it towards the tunnel mouth at the far end.

- **Tunnel:** a 7.2 m deep-level station tube, tiled all over in cream glazed brick-bond tiles (152x76 mm). The tile pattern is procedural, with mortar bump, some colour variation between tiles and a slightly uneven glaze. There's a green frieze band with dark border rows and a green skirting along the platform.
- **Far end:** a tiled end wall with a concrete portal ring into a cast-iron running tunnel. The running tunnel has segment flanges, two dim work lamps and a red signal in the dark.
- **Track:** bullhead-profile running rails with polished tops and rusty sides, on timber sleepers. There's a drainage pit between the rails, centre and outside conductor rails on ceramic insulators, and cable runs on brackets along the track-side wall.
- **Platform:** a dark mastic-type floor with a worn, polished walking line, chewing-gum spots and stains. It also has a concrete coping edge with joints, a worn yellow safety line and "MIND THE GAP" painted at the edge.
- **Furniture and signs:**
  - three slatted timber benches on steel frames
  - 4-sheet posters in aluminium frames on the platform wall, and 48-sheet cross-track posters opposite
  - roundel name boards for a fictional station, "ALDER CROSS"
  - a hanging dot-matrix next-train indicator
  - PA speakers, ceiling conduit and some litter
- **Lights:** suspended fluorescent-style luminaires down the platform, plus a second row over the track. One fitting is dead and one is dimmed.
- **Grime:** sooty, brake-dust-blackened lower walls on the track side and a smoke-darkened crown. There are vertical drip streaks, brown water-leak stains, dirty grout, darkening in corners, and posters that are faded and dirty at the edges. A very light haze softens the depth.

## Known limitations
- The posters are abstract procedural graphics, not real adverts, so they look a bit too clean and graphic up close.
- The grime is all procedural noise, so it's believable at this distance but not photo-scanned detail. Nothing uses image-based textures.
- The tiles are flat with a bump map, so you won't see individually displaced or chipped tiles.
- There are no people or train, and no exit passageways off the platform wall.
- The track-side wall could be dirtier still, and the floor reflections are a little uniform.
