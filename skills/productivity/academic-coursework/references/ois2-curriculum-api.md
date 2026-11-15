# TÜ ÕIS2 public API — curriculum structure without login

Base: `https://ois2.ut.ee/api/` (JSON, no auth for published curricula/courses).

1. Find curriculum: `GET curricula?take=1000` → filter `title.et` in Python
   (the `search=` param is ignored; `curricula/search` 400s). Gives `code`
   (e.g. 80284) and curriculum `uuid`.
2. Versions: `GET curricula/{uuid}/versions` → list of `{uuid, year}`. Pick
   the year the user STARTED (ask: matriculation year decides their version).
3. Version detail: `GET curricula/{uuid}/versions/{version_uuid}` (or
   `.../versions/{year}`). Contains `overview.description.et` (module EAP
   summary, praktika total) and `modules.blocks[].submodules[]` — recursive
   `submodules`, each with `title.et`, `min_credits`/`max_credits`,
   `choice_principles.et` (e.g. "valib valikainetest 6 EAP"), `courses[]`.
4. Courses in a module hold only `main_uuid`; resolve each with
   `GET courses/{main_uuid}` → `code`, `title.et`, `credits`. Fetch in
   parallel (ThreadPoolExecutor, ~16 workers; ~90 courses < 1 s).

Notes
- `is_required` on module courses is unreliable (often false everywhere);
  read obligation from the module's `choice_principles` instead.
- A sub-module titled "Valikained" under a module = the elective pool;
  min_credits = how much to pick.
- Specialisation modules can repeat a shared module (e.g. Loovtegevus) under
  each track — dedupe when summing EAP; sum top-level modules to check the
  total equals the curriculum credits.
- Semester/timetable of each course is not in this payload; don't claim when
  a course runs unless checked elsewhere.
