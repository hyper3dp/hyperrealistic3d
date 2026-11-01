# Vintage brass pocket watch: what was built

I modeled an open hunter-case brass pocket watch in Blender. Its chain lies draped across a dark walnut table. I rendered it as a close-up product shot in Cycles and saved the .blend file.

**Note on the save location:** For this test run, the test harness redirected the save from your Documents folder to the outputs folder. Paths are listed below.

## What was built (real-world scale, metres)
The watch case is 51 mm across and about 15 mm thick. All parts are parented to `Watch_Root` in the `Model_PocketWatch` collection.
- **Case:** I made a domed back (`Case_Back`), a convex middle band (`Case_Band`) and a rounded bezel (`Case_Bezel`) by revolving custom profiles. They are separate parts, so you can see real seams between them. The hunter lid (`Case_Lid`) is hinged at 9 o'clock and opened about 104°. The hinge has three knuckles and two leaves, with small bevels.
- **Top of the case:** a pendant (`Case_Pendant`), a knurled crown with 48 flutes (`Case_Crown`), and an oval wire bow (`Case_Bow`). The bow pivots in the pendant and rests tilted down on the table.
- **Crystal:** a domed glass crystal (`Watch_Crystal`) that is about 0.8 mm thick.
- **Dial:**
  - The enamel dial (`Dial_Enamel`) has a sub-seconds dial at 6 o'clock, sunk 0.15 mm by a boolean cut.
  - Markings (`Dial_Markings`): radial Roman numerals in Times New Roman, with a traditional IIII and the VI left out where the sub-dial sits. There is also a railway-style minute track, a sub-seconds scale with 10–60 labels, and a made-up maker name, "E. HARTWELL & SON / LONDON".
- **Hands:** spade hour hand, minute hand and seconds hand, all in blued steel, with centre bosses. They read 10:09:36.
- **Lid inscription:** a script engraving on the inside of the lid (`Lid_Inscription`), projected onto the dome: "Presented to / Thomas H. Ashby / for twenty-five years / of faithful service / 1898". The name is made up.
- **Chain:** about 60 interlocking oval links (`Chain_Links`), each turned ±45° from the one before. I used an Array fitted to a NURBS path plus a Curve modifier (`Chain_Path` is not rendered). It ends in a T-bar and jump ring.
- **Table:** a 0.9 × 0.6 m walnut slab (`Table_Walnut`) with a bevelled edge, in the `Environment` collection.

## Materials (all procedural; no image textures)
- **`MAT_Brass_Aged`:**
  - colour varies with noise, and patina patches are darker and rougher;
  - brown tarnish collects in crevices (Ambient Occlusion mask);
  - two crossing layers of fine scratches feed roughness and bump, plus smudge noise and a micro bump;
  - roughness ranges from about 0.16 to 0.45.
- **`MAT_Enamel_Dial`:** warm off-white enamel with a glossy clear coat (IOR 1.52) and slight subsurface. It has faint hairline crazing and a little yellowing variation.
- **`MAT_Dial_Paint_Black`:** semi-gloss black for the markings.
- **`MAT_BluedSteel`:** dark blue metal with roughness variation. This is a coloured-metal stand-in, not a true thin-film oxide.
- **`MAT_Glass_Crystal`:** full transmission, IOR 1.5, with faint smudge roughness.
- **`MAT_Brass_Engraved_Cut`:** darker, rougher brass for the engraved letters.
- **`MAT_Walnut_Oiled`:**
  - distorted wave grain mixed with streaky stretched-noise grain and pore streaks;
  - large-scale variation in tone;
  - a satin clear coat (weight 0.35) with varying coat roughness and micro scratches.

## Lighting, camera and render
- **Lights:**
  - `LGT_Key_Softbox`: 40 × 28 cm, 5 W, warm, front-left and high.
  - `LGT_Rim`: 30 × 8 cm strip, 3 W, behind and to the right. It catches the case edges and the chain.
  - `LGT_Fill`: 40 cm, 0.6 W, cool, front-right.
  - All three aim at a target empty. The world is near-black (0.012), which gives a moody, dark-studio look.
- **Camera (`CAM_Hero`):**
  - 100 mm lens on a 36 mm sensor, 0.42 m from the subject, looking down at 34°;
  - depth of field at f/8, focused on `CAM_Target` near the centre of the dial, so the far chain and crown fall off naturally.
- **Render:**
  - Cycles on the GPU (OptiX, RTX 5050), 512 samples with adaptive sampling, OptiX denoiser;
  - indirect clamp at 10, 12 transmission bounces;
  - AgX view transform with the "Medium High Contrast" look;
  - 1800 × 1200 px; the final render took about 37 s.

## Assumptions
- **"Open case"** means a hunter case with its front lid swung open, rather than an open-face watch.
- **Case shape:** pendant at 12 o'clock and hinge at 9 o'clock.
- **Era:** around 1890s English style, with an engraved presentation inscription and blued spade hands.
- **Maker name and inscription:** both made up, so no real brand is shown.

## Saved files
- Blend file: `C:\Users\Hype\Desktop\hyperrealistic3d\hyperrealistic-blender-modeler-workspace\iteration-1\vintage-brass-pocket-watch\with_skill\outputs\vintage_brass_pocket_watch.blend`
  - Blender confirmed this path after saving.
  - Both fonts (Times New Roman and Monotype Corsiva) are packed into the file.
- Final render: `...\outputs\final_render.png`
- Viewport screenshots: `...\outputs\viewport_blockout.png` and `...\outputs\viewport_overview_solid.png`

## Known flaws and next steps
- **Brass:** it still reads somewhat clean and gold-like. A real 120-year-old brass case would show more uneven tarnish and wear on the edges.
- **Inside of the lid:** it is evenly bright and lacks strong reflections, because the scene has no HDRI (the Poly Haven tools weren't used). An HDRI or a few reflector cards would make the polished metal more convincing.
- **Lid outside:** the cover's outer surface (facing away from the camera) has no engraving or guilloché.
- **Walnut grain:** it is convincing at render distance but slightly streaky and regular. A scanned walnut texture would look better.
- **Dial and crystal:** the bevels between the dial and the bezel are plain revolved profiles with no bevel modifier. The crystal shows a strong highlight at the upper right.
- **Chain:**
  - Its path is evenly smooth, with no links bunched up or overlapping.
  - The first link loops near the bow rather than physically threading through it, and there is no swivel clasp.
- **Mesh check:** the audit script flagged "zero-area faces" in the text meshes (dial markings, inscription and hour hand). These are tiny but valid faces at millimetre scale, and the render shows no shading artifacts from them.
- **Bow:** it is mostly hidden behind the crown in the hero shot.
