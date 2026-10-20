Design a single-page web dashboard: "Rockwell Asset Tracker" — an internal tool
for tracking manufacturing assets (PLCs, sensors, drives, HMIs, robots) across
Rockwell Automation plant locations. Backend is a Python FastAPI + SQLite REST API;
this UI is a static HTML/CSS/JS page that calls its JSON endpoints. Aesthetic:
Rockwell Automation industrial brand — precise, reliable, clean, high data density.


BRAND SYSTEM (use these colors):
- Rockwell Red #CD163F  → primary accent, section labels, button, list markers,
red left-borders
- Red Dark   #A8112F    → hover states, tags/chips
- Red Light  #FEF2F2    grounds
- Navy       #1B2A4A    → headings, top bar, table header background (white
text on it)
- Body Text  #5A6470    → paragraphs / body copy (never pure black)
- Caption    #8A929E
- Border     #D8DBDF    → 1px card borders and dividers (no heavy shadows)
- Surface    #F6F7F8
- White      #FFFFFF    → card backgrounds, text on dark
Status colors (data only
  Active = Green #22C55E, Maintenance = Yellow #EAB308, Retired = Blue #3B82F6
(or gray)
Font: Barlow (Google Fonts), fallback stack:
  "Barlow", -apple-systeica, Arial, sans-serif
Section labels: uppercase, bold, Rockwell Red, 12px, letter-spacing 0.08em.
Headings: Navy, bold, no Max three type sizes.

LAYOUT (desktop-first, r

1. Top bar (Navy #1B2A4ARockwell Red bottomborder):
   left = RA shield iconordmark; center = searchinput
   (search by tag or nammary button (Rockwell Red,
   Red Dark on hover).

2. KPI strip — 4 white cards (1px #D8DBDF border, rounded 8px, no heavy
shadow):
   Total Assets (Navy number), Active (Green), In Maintenance (Yellow), Retired
(Blue).
   Each: large bold number + uppercase caption label in #5A6470.

3. Left sidebar (~240px, white card): section label "LOCATIONS" (red,
uppercase).
   List of locations, each row = location name (Navy bold) + plant-code chip
   (Navy background, whiame (#8A929E). "AllLocations"
   at top. Selected row ckground + 3px RockwellRed
   left border. Selectin
   Sample locations: Milwaukee HQ - Line A, Milwaukee HQ - Line B, Twinsburg
   Assembly, Mequon Cont

4. Main panel (white carar with a Status dropdown
   (active / maintenance / retired) and a Category dropdown (PLC / Sensor /
Drive /
   HMI / Robot), plus a right-aligned result count in caption gray.

   Data table below — NO zebra striping, 1px #D8DBDF bottom border per row,
   9-10px cell padding,  Navy background, white,
   bold, uppercase, 11px. Columns:
   - Asset Tag (monospac
   - Name
   - Category (rounded b
   - Status (rounded pill with a leading status-color dot: Green/Yellow/Blue)
   - Location
   - Installed Date
   Populate ~10 realistiley ControlLogix PLCs,
   PowerFlex drives, PanelView Plus HMIs, proximity/photoelectric sensors,
   articulated robots) wNNNN (2-4 uppercase
   letters, dash, 4-6 digits).

5. "Add Asset" modal (white, rounded, centered, dim overlay): fields — Name,
   Asset Tag (hint text s, dash, 4-6 digits, e.g.
   PLC-1042"), Category select, Status select, Location select, Installed Date
   (date input), Notes (ave Asset (Rockwell Red)
   buttons. Inline error line in Rockwell Red for validation failures.

6. Row click opens a right-side detail drawer showing all fields, editable
   (tag read-only). Actit), Close (ghost) + Save
   (Rockwell Red) on the right.

Footer or corner: tagline "expanding human possibility®" in caption gray.
Consistent 8px spacing gorders, minimal shadows.
Include realistic sample data throughout.

That maps 1:1 to the API (/assets, /assets?status=&category=, /locations,
POST/PUT/DELETE) and use.

