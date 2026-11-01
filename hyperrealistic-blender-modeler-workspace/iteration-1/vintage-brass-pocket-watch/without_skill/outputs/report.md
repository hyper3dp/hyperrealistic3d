# Vintage brass pocket watch - done

I modeled the watch in Blender and rendered a close-up product shot.

**Files**
- `vintage_brass_pocket_watch.blend` is the scene. This test run saved it to the outputs folder, not to Documents.
- `final_render.png` is a 1600x1200 Cycles render. It took about 25 seconds on the RTX 5050 with OptiX.

**What's in the scene**
- **Brass case:** a hunter case. The front lid is hinged open at 9 o'clock on three hinge knuckles. The case also has a domed glass crystal, a pendant, a knurled crown and a bow ring that tilts down onto the table.
- **Enamel dial:** off-white enamel with a clear coat, slight mottling and faint crazing. It has radial Roman numerals with the traditional "IIII", a printed minute track, a small seconds sub-dial at 6 o'clock and blued-steel spade hands set to 10:09. The maker name on the dial is made up ("A. HOLLOWAY, LONDON").
- **Chain:** a curb-style link chain that runs from the bow ring, loops behind the watch, curls toward the camera on the right and ends in a T-bar. The T-bar is just outside the frame.
- **Table:** a dark walnut top with a procedural grain, pores and a satin finish.
- **Camera and lighting:** a 90mm lens at f/6.3, focused on the dial, so the chain and the far table fall out of focus. The light is a warm softbox key, a rim strip and a dim fill, with the AgX view transform.

**Brass material:** procedural aged brass with micro-scratches, varying roughness and darker patina in the crevices.

**Known weak spots, and what I'd improve next**
- The brass still looks fairly clean and bright. It needs heavier tarnish and wear.
- The walnut grain is procedural and looks streaky at grazing angles. An image-based walnut texture would look more real.
- The small maker text on the dial is a little garbled.
- The inside of the lid is plain. It could get engraving.
