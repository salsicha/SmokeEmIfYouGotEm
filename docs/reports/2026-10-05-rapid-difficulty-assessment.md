# Rapid difficulty: every rapid in the game against its catalogued class

> Historical baseline, not the current calibrated build. See
> [linked rapid calibration](2026-10-05-linked-rapid-calibration.md) for the
> subsequent crop-boundary fixes, expanded rapid envelopes, actual full-hull
> contact counts, matched steering controls and continuous rescue trials.
> In particular, the old dedicated-rock pin counter did not classify captured
> terrain contacts. A zero counter alone cannot certify a contact-free run.

Played 2026-10-04/05 on `release/1.0`, all seven river maps (six rivers; the
Zambezi has a full-gorge map and an Upper Gorge map). Evidence:
`tmp/rapid-difficulty-v8-*` (native trial receipts, start/end screenshots,
native logs) and the generated `report.html` / `report.json`.

## Headline

**All 71 runnable rapid sections were played, five runs each (356 runs). One,
The Wall on the Upper Zambezi, cannot be reached in play; the other 70 are
graded below.**

The game plays far easier than the real rivers.

- **58 of 70 rapids run clean with no commands at all**, which is Class I by
  your definition. Every South Fork rapid does, Troublemaker and Satan's
  Cesspool included. That includes rapids catalogued IV–V and V: Stairway to
  Heaven (on both Zambezi maps), Gulliver's Travels, The Washing Machine,
  Double Trouble, Oblivion, Morning Glory (Upper Gorge map), Hance (Grand Canyon 8/10), White
  Mile, Bidwell, Khyber Pass and Son of Terminator.
- 9 need some action but forgive everything else (Class II), such as Double
  Drop, Overland Truck Eater and Three Ugly Sisters.
- Terminator (catalogued V) plays as III: the boat loses its crew if left
  alone, and one of the three driven lines lost three swimmers.
- **Upper Huacas** (IV) plays as IV, a match: only one of three approach lines
  goes clean.
- **Lower Huacas** (IV) plays as **V**: every line, steered or not, loses all
  four paddlers in the surge at its bottom.

So 66 play easier than catalogued, 2 match (Upper Huacas, Zambezi Rapid 21) and
1 is harder (Lower Huacas). Chili Bar Hole is catalogued as a surf wave, not a
passage grade. Two entries could not be graded: The Wall on the Upper Zambezi
is upstream of that map's put-in, and Commercial Suicide is a mandatory
portage.

## How each rapid was played

Every rapid section was run five times from a checkpoint just above it, with
the game's own physics and controls:

| Run | What it does | Criterion it answers |
|---|---|---|
| Hands-off | Placed on the center line; no guide or crew command of any kind | Your Class I test: does it go clean with no action? |
| Center, −4 m, +4 m | Driven down three approach lines with normal paddle/oar commands every 0.85 s | 1. how narrow the successful route is |
| Missed turn | Center line, but no steering at all for six seconds starting 12 m above the main feature | 3. what a missed turn costs |

"Clean" means through the section upright, nobody out of the boat and no pin
longer than three seconds. Each criterion is scored on the I–V scale:

1. **Route.** All three approach lines clean and the clean tracks stay apart: II.
   Two clean, or tracks squeezed into one slot: III. One clean: IV. None clean
   but the boat gets through: V. Nothing gets through: unresolved (not called VI).
2. **Timely steering.** The test driver corrects toward its lane all the time,
   so its turn-call share is only an upper bound (<30% II, <50% III, <70% IV).
   If the hands-off boat gets past the main feature without an incident it is
   II, and if the six-second lapse does no harm it is at most III.
3. **Missed turn.** Clean: II. Swimmers: III. Flip or pin: IV. Swimmers or a
   flip and the boat does not get through: V.
4. **Recovery with normal controls** (paddling, backpaddling, high-side,
   reflip). A clean missed-turn run shows they suffice: II. Through only after
   swimmers, a flip or a pin: IV. Not through: V.

A clean hands-off run is Class I by your definition. Otherwise the in-game class
is the hardest of the four criteria, never below II. Grand Canyon 1–10 grades are
compared through the usual guide-book reading (about half the number).

## Results by river

### South Fork American

| Rapid | Catalogue | In game | vs catalogue | No commands | 1. Route | 2. Steering | 3. Missed turn | 4. Recovery |
|---|---|---|---|---|---|---|---|---|
| Chili Bar Hole | surf feature | I — runs clean with no commands at all | Catalogue lists a surf wave, not a passage class | clean | center clean; −4 m clean; +4 m clean; clean tracks stay ≥7.5 m apart through the rapid | driver turn calls 19% of the center run, 41 guide strokes, 4 crew calls, 0 s backpaddling; a 6 s lapse at the entry did no harm, so steering there is not critical | 6 s with no steering at the entry: clean; drifted up to 4.1 m off line | Back on line as soon as steering resumed |
| Meat Grinder | III+ | I — runs clean with no commands at all | Easier than catalogue by 2 classes | clean | center clean; −4 m clean; +4 m clean; clean tracks stay ≥7.9 m apart through the rapid | driver turn calls 0% of the center run, 72 guide strokes, 0 crew calls, 0 s backpaddling; a 6 s lapse at the entry did no harm, so steering there is not critical | 6 s with no steering at the entry: clean; drifted up to 1.8 m off line | Back on line as soon as steering resumed |
| Racehorse Bend | III | I — runs clean with no commands at all | Easier than catalogue by 2 classes | clean | center clean; −4 m clean; +4 m clean; clean tracks stay ≥6.1 m apart through the rapid | driver turn calls 24% of the center run, 69 guide strokes, 10 crew calls, 0 s backpaddling; a 6 s lapse at the entry did no harm, so steering there is not critical | 6 s with no steering at the entry: clean; drifted up to 3.7 m off line | Back on line 8 s after steering resumed |
| Maya | II-III | I — runs clean with no commands at all | Easier than catalogue by 1 class | clean | center clean; −4 m clean; +4 m clean; clean tracks stay ≥8.1 m apart through the rapid | driver turn calls 0% of the center run, 61 guide strokes, 0 crew calls, 0 s backpaddling; a 6 s lapse at the entry did no harm, so steering there is not critical | 6 s with no steering at the entry: clean; drifted up to 2.8 m off line | Back on line as soon as steering resumed |
| Rock Garden | II | I — runs clean with no commands at all | Easier than catalogue by 1 class | clean | center clean; −4 m clean; +4 m clean; clean tracks stay ≥3.9 m apart through the rapid | driver turn calls 31% of the center run, 58 guide strokes, 7 crew calls, 0 s backpaddling; a 6 s lapse at the entry did no harm, so steering there is not critical | 6 s with no steering at the entry: clean; drifted up to 4.9 m off line | Never fully back on line, but the boat still ran the rapid cleanly |
| African Queen | II | I — runs clean with no commands at all | Easier than catalogue by 1 class | clean | center clean; −4 m clean; +4 m clean; clean tracks stay ≥7.4 m apart through the rapid | driver turn calls 4% of the center run, 55 guide strokes, 2 crew calls, 0 s backpaddling; a 6 s lapse at the entry did no harm, so steering there is not critical | 6 s with no steering at the entry: clean; drifted up to 3.1 m off line | Back on line as soon as steering resumed |
| Triple Threat | III | I — runs clean with no commands at all | Easier than catalogue by 2 classes | clean | center clean; −4 m clean; +4 m clean; clean tracks stay ≥5.1 m apart through the rapid | driver turn calls 34% of the center run, 96 guide strokes, 12 crew calls, 0 s backpaddling; a 6 s lapse at the entry did no harm, so steering there is not critical | 6 s with no steering at the entry: clean; drifted up to 6.1 m off line | Back on line 2 s after steering resumed |
| Troublemaker | III+ | I — runs clean with no commands at all | Easier than catalogue by 2 classes | clean | center clean; −4 m clean; +4 m clean; clean tracks stay ≥1.0 m apart through the rapid | driver turn calls 41% of the center run, 104 guide strokes, 14 crew calls, 0 s backpaddling; a 6 s lapse at the entry did no harm, so steering there is not critical | 6 s with no steering at the entry: clean; drifted up to 6.4 m off line | Back on line as soon as steering resumed |
| Fowler's Rock | III | I — runs clean with no commands at all | Easier than catalogue by 2 classes | clean | center clean; −4 m clean; +4 m clean; clean tracks stay ≥7.5 m apart through the rapid | driver turn calls 9% of the center run, 70 guide strokes, 4 crew calls, 0 s backpaddling; a 6 s lapse at the entry did no harm, so steering there is not critical | 6 s with no steering at the entry: clean; drifted up to 1.9 m off line | Back on line as soon as steering resumed |
| Upper Haystack Canyon | III | I — runs clean with no commands at all | Easier than catalogue by 2 classes | clean | center clean; −4 m clean; +4 m clean; clean tracks stay ≥7.2 m apart through the rapid | driver turn calls 0% of the center run, 36 guide strokes, 0 crew calls, 0 s backpaddling; a 6 s lapse at the entry did no harm, so steering there is not critical | 6 s with no steering at the entry: clean; drifted up to 1.5 m off line | Back on line as soon as steering resumed |
| Lost Hat | III- | I — runs clean with no commands at all | Easier than catalogue by 2 classes | clean | center clean; −4 m clean; +4 m clean; clean tracks stay ≥6.3 m apart through the rapid | driver turn calls 14% of the center run, 79 guide strokes, 5 crew calls, 0 s backpaddling; a 6 s lapse at the entry did no harm, so steering there is not critical | 6 s with no steering at the entry: clean; drifted up to 4.6 m off line | Back on line as soon as steering resumed |
| Satan's Cesspool | III+ | I — runs clean with no commands at all | Easier than catalogue by 2 classes | clean | center clean; −4 m clean; +4 m clean; clean tracks stay ≥6.6 m apart through the rapid | driver turn calls 20% of the center run, 61 guide strokes, 6 crew calls, 0 s backpaddling; a 6 s lapse at the entry did no harm, so steering there is not critical | 6 s with no steering at the entry: clean; drifted up to 5.4 m off line | Back on line as soon as steering resumed |
| Son of Satan | II+-III | I — runs clean with no commands at all | Easier than catalogue by 1 class | clean | center clean; −4 m clean; +4 m clean; clean tracks stay ≥6.3 m apart through the rapid | driver turn calls 7% of the center run, 86 guide strokes, 4 crew calls, 0 s backpaddling; a 6 s lapse at the entry did no harm, so steering there is not critical | 6 s with no steering at the entry: clean; drifted up to 2.7 m off line | Back on line as soon as steering resumed |
| Scissors | III | I — runs clean with no commands at all | Easier than catalogue by 2 classes | clean | center clean; −4 m clean; +4 m clean; clean tracks stay ≥8.6 m apart through the rapid | driver turn calls 15% of the center run, 72 guide strokes, 6 crew calls, 0 s backpaddling; a 6 s lapse at the entry did no harm, so steering there is not critical | 6 s with no steering at the entry: clean; drifted up to 3.6 m off line | Back on line 9 s after steering resumed |
| Lower Haystack Canyon | II+ | I — runs clean with no commands at all | Easier than catalogue by 1 class | clean | center clean; −4 m clean; +4 m clean; clean tracks stay ≥6.7 m apart through the rapid | driver turn calls 0% of the center run, 67 guide strokes, 0 crew calls, 0 s backpaddling; a 6 s lapse at the entry did no harm, so steering there is not critical | 6 s with no steering at the entry: clean; drifted up to 2.0 m off line | Back on line as soon as steering resumed |
| Bouncing Rock | III | I — runs clean with no commands at all | Easier than catalogue by 2 classes | clean | center clean; −4 m clean; +4 m clean; clean tracks stay ≥7.0 m apart through the rapid | driver turn calls 14% of the center run, 33 guide strokes, 4 crew calls, 0 s backpaddling; a 6 s lapse at the entry did no harm, so steering there is not critical | 6 s with no steering at the entry: clean; drifted up to 2.7 m off line | Back on line as soon as steering resumed |
| Pre-Op | III- | I — runs clean with no commands at all | Easier than catalogue by 2 classes | clean | center clean; −4 m clean; +4 m clean; clean tracks stay ≥6.8 m apart through the rapid | driver turn calls 11% of the center run, 60 guide strokes, 4 crew calls, 0 s backpaddling; a 6 s lapse at the entry did no harm, so steering there is not critical | 6 s with no steering at the entry: clean; drifted up to 3.0 m off line | Back on line as soon as steering resumed |
| Hospital Bar | III | I — runs clean with no commands at all | Easier than catalogue by 2 classes | clean | center clean; −4 m clean; +4 m clean; clean tracks stay ≥7.2 m apart through the rapid | driver turn calls 0% of the center run, 54 guide strokes, 0 crew calls, 0 s backpaddling; a 6 s lapse at the entry did no harm, so steering there is not critical | 6 s with no steering at the entry: clean; drifted up to 1.5 m off line | Back on line as soon as steering resumed |
| Recovery Room | II-III | I — runs clean with no commands at all | Easier than catalogue by 1 class | clean | center clean; −4 m clean; +4 m clean; clean tracks stay ≥5.4 m apart through the rapid | driver turn calls 0% of the center run, 76 guide strokes, 0 crew calls, 0 s backpaddling; a 6 s lapse at the entry did no harm, so steering there is not critical | 6 s with no steering at the entry: clean; drifted up to 1.8 m off line | Back on line as soon as steering resumed |
| Surprise | II-III | I — runs clean with no commands at all | Easier than catalogue by 1 class | clean | center clean; −4 m clean; +4 m clean; clean tracks stay ≥7.8 m apart through the rapid | driver turn calls 14% of the center run, 40 guide strokes, 4 crew calls, 0 s backpaddling; a 6 s lapse at the entry did no harm, so steering there is not critical | 6 s with no steering at the entry: clean; drifted up to 2.4 m off line | Back on line as soon as steering resumed |

### Colorado (Hance)

| Rapid | Catalogue | In game | vs catalogue | No commands | 1. Route | 2. Steering | 3. Missed turn | 4. Recovery |
|---|---|---|---|---|---|---|---|---|
| Hance | 8/10 (section IV-V) | I — runs clean with no commands at all | Easier than catalogue by 3 classes | clean | center clean; −4 m clean; +4 m clean; clean tracks stay ≥4.6 m apart through the rapid | driver turn calls 51% of the center run, 111 guide strokes, 16 crew calls, 0 s backpaddling; a 6 s lapse at the entry did no harm, so steering there is not critical | 6 s with no steering at the entry: clean; drifted up to 12.1 m off line | Back on line 18 s after steering resumed |
| Son Of Hance | III | I — runs clean with no commands at all | Easier than catalogue by 2 classes | clean | center clean; −4 m clean; +4 m clean; clean tracks stay ≥8.2 m apart through the rapid | driver turn calls 21% of the center run, 71 guide strokes, 8 crew calls, 0 s backpaddling; a 6 s lapse at the entry did no harm, so steering there is not critical | 6 s with no steering at the entry: clean; drifted up to 10.4 m off line | Back on line as soon as steering resumed |

### Pacuare (Upper Huacas)

| Rapid | Catalogue | In game | vs catalogue | No commands | 1. Route | 2. Steering | 3. Missed turn | 4. Recovery |
|---|---|---|---|---|---|---|---|---|
| Double Drop | IV- (section III) | II — needs some action (the hands-off run did not go clean), but every criterion is easy | Easier than catalogue by 1 class | stuck (no progress for 60 s); reached 118 of 140 m, past the main feature with no commands | center clean; −4 m clean; +4 m clean; clean tracks stay ≥2.4 m apart through the rapid | driver turn calls 61% of the center run, 85 guide strokes, 18 crew calls, 0 s backpaddling; not required at the main feature (hands-off got past it) | 6 s with no steering at the entry: clean; drifted up to 9.7 m off line | Back on line as soon as steering resumed using 3 s backpaddling |
| Upper Huacas | IV | IV — set by narrow route | Matches catalogue | got through, 4 swimmer(s) | center got through, 4 swimmer(s); −4 m crew lost (swimmers past the rescue window; the game reset the run) after 4 swimmer(s); +4 m clean | driver turn calls 51% of the center run, 116 guide strokes, 25 crew calls, 6 s backpaddling; a 6 s lapse at the entry did no harm, so steering there is not critical | 6 s with no steering at the entry: clean; drifted up to 25.7 m off line | Back on line as soon as steering resumed using 1 high-side |
| Lower Huacas | IV | V — set by narrow route | Harder than catalogue by 1 class | got through, 4 swimmer(s) | center got through, 4 swimmer(s); −4 m got through, 4 swimmer(s); +4 m got through, 4 swimmer(s) | driver turn calls 41% of the center run, 93 guide strokes, 20 crew calls, 0 s backpaddling | 6 s with no steering at the entry: got through, 4 swimmer(s); drifted up to 10.7 m off line | Got through with normal controls, but after 4 swimmer(s) |
| Upper Pinball | III | I — runs clean with no commands at all | Easier than catalogue by 2 classes | clean | center clean; −4 m clean; +4 m clean (its start was on the bank; started at +2 m); clean tracks stay ≥7.9 m apart through the rapid | driver turn calls 49% of the center run, 161 guide strokes, 21 crew calls, 0 s backpaddling; a 6 s lapse at the entry did no harm, so steering there is not critical | 6 s with no steering at the entry: clean; drifted up to 11.2 m off line | Back on line as soon as steering resumed |
| Lower Pinball | III | I — runs clean with no commands at all | Easier than catalogue by 2 classes | clean | center clean; −4 m clean; +4 m clean; clean tracks stay ≥0.5 m apart through the rapid | driver turn calls 22% of the center run, 66 guide strokes, 9 crew calls, 0 s backpaddling; a 6 s lapse at the entry did no harm, so steering there is not critical | 6 s with no steering at the entry: clean; drifted up to 9.1 m off line | Back on line 32 s after steering resumed |
| Guatemala | III (section III (at the reach end)) | II — needs some action (the hands-off run did not go clean), but every criterion is easy | Easier than catalogue by 1 class | got through, 4 swimmer(s) | center clean; −4 m clean; +4 m clean; clean tracks stay ≥9.0 m apart through the rapid | driver turn calls 16% of the center run, 31 guide strokes, 3 crew calls, 0 s backpaddling; a 6 s lapse at the entry did no harm, so steering there is not critical | 6 s with no steering at the entry: clean; drifted up to 7.6 m off line | Back on line 20 s after steering resumed |

### Futaleufú (Terminator)

| Rapid | Catalogue | In game | vs catalogue | No commands | 1. Route | 2. Steering | 3. Missed turn | 4. Recovery |
|---|---|---|---|---|---|---|---|---|
| Terminator Wave | II | I — runs clean with no commands at all | Easier than catalogue by 1 class | clean | center clean; −4 m clean; +4 m clean; clean tracks stay ≥5.8 m apart through the rapid | driver turn calls 50% of the center run, 20 guide strokes, 4 crew calls, 0 s backpaddling; a 6 s lapse at the entry did no harm, so steering there is not critical | 6 s with no steering at the entry: clean; drifted up to 2.8 m off line | Back on line 4 s after steering resumed |
| Terminator Entrance | IV | I — runs clean with no commands at all | Easier than catalogue by 3 classes | clean | center clean; −4 m clean; +4 m clean; clean tracks stay ≥6.6 m apart through the rapid | driver turn calls 24% of the center run, 48 guide strokes, 2 crew calls, 0 s backpaddling; a 6 s lapse at the entry did no harm, so steering there is not critical | 6 s with no steering at the entry: clean; drifted up to 5.5 m off line | Back on line 11 s after steering resumed |
| Terminator | V | III — set by narrow route, steering workload | Easier than catalogue by 2 classes | got through, 4 swimmer(s) | center got through, 3 swimmer(s); −4 m clean; +4 m clean; clean tracks stay ≥3.4 m apart through the rapid | driver turn calls 61% of the center run, 113 guide strokes, 20 crew calls, 0 s backpaddling; a 6 s lapse at the entry did no harm, so steering there is not critical | 6 s with no steering at the entry: clean; drifted up to 4.0 m off line | Back on line 6 s after steering resumed |
| Son of Terminator | IV-V (section IV) | I — runs clean with no commands at all | Easier than catalogue by 3 classes | clean | center clean; −4 m clean; +4 m clean; clean tracks stay ≥7.7 m apart through the rapid | driver turn calls 13% of the center run, 32 guide strokes, 4 crew calls, 0 s backpaddling; a 6 s lapse at the entry did no harm, so steering there is not critical | 6 s with no steering at the entry: clean; drifted up to 2.7 m off line | Back on line as soon as steering resumed |
| Khyber Pass | IV+ (section IV) | I — runs clean with no commands at all | Easier than catalogue by 3 classes | clean | center clean; −4 m clean; +4 m clean; clean tracks stay ≥8.0 m apart through the rapid | driver turn calls 62% of the center run, 31 guide strokes, 7 crew calls, 0 s backpaddling; a 6 s lapse at the entry did no harm, so steering there is not critical | 6 s with no steering at the entry: clean; drifted up to 4.3 m off line | Back on line as soon as steering resumed |
| Himalayas | IV | I — runs clean with no commands at all | Easier than catalogue by 3 classes | clean | center clean; −4 m clean; +4 m clean; clean tracks stay ≥6.3 m apart through the rapid | driver turn calls 58% of the center run, 68 guide strokes, 13 crew calls, 0 s backpaddling; a 6 s lapse at the entry did no harm, so steering there is not critical | 6 s with no steering at the entry: clean; drifted up to 4.0 m off line | Back on line as soon as steering resumed |

### Chilko (Lava Canyon)

| Rapid | Catalogue | In game | vs catalogue | No commands | 1. Route | 2. Steering | 3. Missed turn | 4. Recovery |
|---|---|---|---|---|---|---|---|---|
| Bidwell Rapids | IV (guide-published, all reviewed levels) (section IV) | I — runs clean with no commands at all | Easier than catalogue by 3 classes | clean | center clean; −4 m clean; +4 m clean; clean tracks stay ≥7.0 m apart through the rapid | driver turn calls 56% of the center run, 119 guide strokes, 18 crew calls, 0 s backpaddling; a 6 s lapse at the entry did no harm, so steering there is not critical | 6 s with no steering at the entry: clean; drifted up to 14.6 m off line | Back on line as soon as steering resumed |
| White Kilometre | III (location low confidence) | I — runs clean with no commands at all | Easier than catalogue by 2 classes | clean | center clean; −4 m clean; +4 m clean; clean tracks stay ≥6.1 m apart through the rapid | driver turn calls 17% of the center run, 138 guide strokes, 12 crew calls, 0 s backpaddling; a 6 s lapse at the entry did no harm, so steering there is not critical | 6 s with no steering at the entry: clean; drifted up to 4.5 m off line | Back on line as soon as steering resumed |
| White Mile | IV-V (flow-dependent) (section IV) | I — runs clean with no commands at all | Easier than catalogue by 3 classes | clean | center clean; −4 m clean; +4 m clean; clean tracks stay ≥7.7 m apart through the rapid | driver turn calls 62% of the center run, 152 guide strokes, 22 crew calls, 0 s backpaddling; a 6 s lapse at the entry did no harm, so steering there is not critical | 6 s with no steering at the entry: clean; drifted up to 11.8 m off line | Back on line 3 s after steering resumed |

### Zambezi (Batoka Gorge, full)

| Rapid | Catalogue | In game | vs catalogue | No commands | 1. Route | 2. Steering | 3. Missed turn | 4. Recovery |
|---|---|---|---|---|---|---|---|---|
| Against the Wall | IV | I — runs clean with no commands at all | Easier than catalogue by 3 classes | clean | center clean; −4 m clean; +4 m clean; clean tracks stay ≥7.4 m apart through the rapid | driver turn calls 58% of the center run, 49 guide strokes, 5 crew calls, 0 s backpaddling; a 6 s lapse at the entry did no harm, so steering there is not critical | 6 s with no steering at the entry: clean; drifted up to 42.8 m off line | Back on line 15 s after steering resumed |
| The Bridge | II-III | I — runs clean with no commands at all | Easier than catalogue by 1 class | clean | center clean; −4 m clean; +4 m clean; clean tracks stay ≥4.7 m apart through the rapid | driver turn calls 89% of the center run, 40 guide strokes, 2 crew calls, 0 s backpaddling; a 6 s lapse at the entry did no harm, so steering there is not critical | 6 s with no steering at the entry: clean; drifted up to 28.0 m off line | Never fully back on line, but the boat still ran the rapid cleanly |
| Rapid 3 | III-IV | I — runs clean with no commands at all | Easier than catalogue by 2 classes | clean | center clean; −4 m clean; +4 m clean; clean tracks stay ≥4.5 m apart through the rapid | driver turn calls 63% of the center run, 54 guide strokes, 6 crew calls, 0 s backpaddling; a 6 s lapse at the entry did no harm, so steering there is not critical | 6 s with no steering at the entry: clean; drifted up to 14.1 m off line | Never fully back on line, but the boat still ran the rapid cleanly |
| Morning Glory | IV-V | II — needs some action (the hands-off run did not go clean), but every criterion is easy | Easier than catalogue by 2 classes | ran out of time; reached 207 of 228 m, past the main feature with no commands | center clean; −4 m clean; +4 m clean; clean tracks stay ≥8.9 m apart through the rapid | driver turn calls 26% of the center run, 165 guide strokes, 14 crew calls, 0 s backpaddling; not required at the main feature (hands-off got past it) | 6 s with no steering at the entry: clean; drifted up to 45.5 m off line | Back on line 157 s after steering resumed |
| Stairway to Heaven | V | I — runs clean with no commands at all | Easier than catalogue by 4 classes | clean | center clean; −4 m clean; +4 m clean; clean tracks stay ≥3.0 m apart through the rapid | driver turn calls 67% of the center run, 51 guide strokes, 9 crew calls, 0 s backpaddling; a 6 s lapse at the entry did no harm, so steering there is not critical | 6 s with no steering at the entry: clean; drifted up to 7.2 m off line | Back on line 21 s after steering resumed |
| Devil's Toilet Bowl | III-IV | I — runs clean with no commands at all | Easier than catalogue by 2 classes | clean | center clean; −4 m clean; +4 m clean; clean tracks stay ≥5.4 m apart through the rapid | driver turn calls 86% of the center run, 39 guide strokes, 4 crew calls, 0 s backpaddling; a 6 s lapse at the entry did no harm, so steering there is not critical | 6 s with no steering at the entry: clean; drifted up to 45.6 m off line | Back on line 7 s after steering resumed |
| Gulliver's Travels | V | I — runs clean with no commands at all | Easier than catalogue by 4 classes | clean | center clean; −4 m clean; +4 m clean; clean tracks stay ≥6.5 m apart through the rapid | driver turn calls 5% of the center run, 141 guide strokes, 4 crew calls, 0 s backpaddling; a 6 s lapse at the entry did no harm, so steering there is not critical | 6 s with no steering at the entry: clean; drifted up to 2.7 m off line | Back on line as soon as steering resumed |
| Midnight Diner | III-V (section III-IV) | I — runs clean with no commands at all | Easier than catalogue by 2 classes | clean | center clean; −4 m clean; +4 m clean; clean tracks stay ≥7.0 m apart through the rapid | driver turn calls 48% of the center run, 85 guide strokes, 12 crew calls, 0 s backpaddling; a 6 s lapse at the entry did no harm, so steering there is not critical | 6 s with no steering at the entry: clean; drifted up to 25.2 m off line | Never fully back on line, but the boat still ran the rapid cleanly |
| Gnashing Jaws of Death | III-IV | II — needs some action (the hands-off run did not go clean), but every criterion is easy | Easier than catalogue by 1 class | stuck (no progress for 60 s); reached 147 of 255 m, past the main feature with no commands | center clean; −4 m clean; +4 m clean; clean tracks stay ≥14.7 m apart through the rapid | driver turn calls 27% of the center run, 266 guide strokes, 21 crew calls, 0 s backpaddling; not required at the main feature (hands-off got past it) | 6 s with no steering at the entry: clean; drifted up to 72.6 m off line | Never fully back on line, but the boat still ran the rapid cleanly |
| Overland Truck Eater | IV-V | II — needs some action (the hands-off run did not go clean), but every criterion is easy | Easier than catalogue by 2 classes | stuck (no progress for 60 s); reached 219 of 255 m, past the main feature with no commands | center clean; −4 m clean; +4 m clean; clean tracks stay ≥8.1 m apart through the rapid | driver turn calls 29% of the center run, 226 guide strokes, 18 crew calls, 0 s backpaddling; not required at the main feature (hands-off got past it) | 6 s with no steering at the entry: clean; drifted up to 62.3 m off line | Back on line as soon as steering resumed |
| Three Ugly Sisters | III | II — needs some action (the hands-off run did not go clean), but every criterion is easy | Easier than catalogue by 1 class | ran out of time; reached 626 of 675 m, past the main feature with no commands | center clean; −4 m clean; +4 m clean; clean tracks stay ≥5.9 m apart through the rapid | driver turn calls 8% of the center run, 194 guide strokes, 4 crew calls, 0 s backpaddling; not required at the main feature (hands-off got past it) | 6 s with no steering at the entry: clean; drifted up to 2.4 m off line | Back on line as soon as steering resumed |
| The Mother | IV | I — runs clean with no commands at all | Easier than catalogue by 3 classes | clean | center clean; −4 m clean; +4 m clean; clean tracks stay ≥8.1 m apart through the rapid | driver turn calls 32% of the center run, 114 guide strokes, 11 crew calls, 0 s backpaddling; a 6 s lapse at the entry did no harm, so steering there is not critical | 6 s with no steering at the entry: clean; drifted up to 31.1 m off line | Back on line 139 s after steering resumed |
| Surprise Surprise | III | I — runs clean with no commands at all | Easier than catalogue by 2 classes | clean | center clean; −4 m clean; +4 m clean; clean tracks stay ≥12.4 m apart through the rapid | driver turn calls 32% of the center run, 290 guide strokes, 22 crew calls, 0 s backpaddling; a 6 s lapse at the entry did no harm, so steering there is not critical | 6 s with no steering at the entry: clean; drifted up to 67.3 m off line | Back on line 118 s after steering resumed |
| The Washing Machine | IV-V | I — runs clean with no commands at all | Easier than catalogue by 3 classes | clean | center clean; −4 m clean; +4 m clean; clean tracks stay ≥7.0 m apart through the rapid | driver turn calls 17% of the center run, 69 guide strokes, 6 crew calls, 0 s backpaddling; a 6 s lapse at the entry did no harm, so steering there is not critical | 6 s with no steering at the entry: clean; drifted up to 2.0 m off line | Back on line as soon as steering resumed |
| The Terminators | III | II — needs some action (the hands-off run did not go clean), but every criterion is easy | Easier than catalogue by 1 class | ran out of time; reached 484 of 545 m, past the main feature with no commands | center clean; −4 m clean; +4 m clean; clean tracks stay ≥6.8 m apart through the rapid | driver turn calls 18% of the center run, 251 guide strokes, 8 crew calls, 0 s backpaddling; not required at the main feature (hands-off got past it) | 6 s with no steering at the entry: clean; drifted up to 13.8 m off line | Back on line 38 s after steering resumed |
| Double Trouble | IV-V | I — runs clean with no commands at all | Easier than catalogue by 3 classes | clean | center clean; −4 m clean; +4 m clean; clean tracks stay ≥5.9 m apart through the rapid | driver turn calls 29% of the center run, 137 guide strokes, 16 crew calls, 0 s backpaddling; a 6 s lapse at the entry did no harm, so steering there is not critical | 6 s with no steering at the entry: clean; drifted up to 41.2 m off line | Back on line 141 s after steering resumed |
| Oblivion | IV-V | I — runs clean with no commands at all | Easier than catalogue by 3 classes | clean | center clean; −4 m clean; +4 m clean; clean tracks stay ≥7.5 m apart through the rapid | driver turn calls 39% of the center run, 87 guide strokes, 10 crew calls, 0 s backpaddling; a 6 s lapse at the entry did no harm, so steering there is not critical | 6 s with no steering at the entry: clean; drifted up to 4.9 m off line | Back on line 2 s after steering resumed |
| Rapid 19 | II-III | I — runs clean with no commands at all | Easier than catalogue by 1 class | clean | center clean; −4 m clean; +4 m clean; clean tracks stay ≥8.7 m apart through the rapid | driver turn calls 43% of the center run, 88 guide strokes, 10 crew calls, 0 s backpaddling; a 6 s lapse at the entry did no harm, so steering there is not critical | 6 s with no steering at the entry: clean; drifted up to 14.8 m off line | Back on line 76 s after steering resumed |
| Rapid 20 | II-III | I — runs clean with no commands at all | Easier than catalogue by 1 class | clean | center clean; −4 m clean; +4 m clean; clean tracks stay ≥5.4 m apart through the rapid | driver turn calls 0% of the center run, 98 guide strokes, 0 crew calls, 0 s backpaddling; a 6 s lapse at the entry did no harm, so steering there is not critical | 6 s with no steering at the entry: clean; drifted up to 1.4 m off line | Back on line as soon as steering resumed |
| Rapid 21 | II-III | II — needs some action (the hands-off run did not go clean), but every criterion is easy | Matches catalogue | ran out of time; reached 219 of 255 m, past the main feature with no commands | center clean; −4 m clean; +4 m clean; clean tracks stay ≥6.4 m apart through the rapid | driver turn calls 19% of the center run, 162 guide strokes, 14 crew calls, 0 s backpaddling; not required at the main feature (hands-off got past it) | 6 s with no steering at the entry: clean; drifted up to 49.5 m off line | Back on line 174 s after steering resumed |
| Morning Shave | II-III | I — runs clean with no commands at all | Easier than catalogue by 1 class | clean | center clean; −4 m clean; +4 m clean; clean tracks stay ≥7.5 m apart through the rapid | driver turn calls 32% of the center run, 106 guide strokes, 14 crew calls, 0 s backpaddling; a 6 s lapse at the entry did no harm, so steering there is not critical | 6 s with no steering at the entry: clean; drifted up to 27.9 m off line | Back on line 121 s after steering resumed |
| Morning Shower | III | II — needs some action (the hands-off run did not go clean), but every criterion is easy | Easier than catalogue by 1 class | ran out of time; reached 309 of 815 m, past the main feature with no commands | center clean; −4 m clean; +4 m clean; clean tracks stay ≥7.5 m apart through the rapid | driver turn calls 15% of the center run, 393 guide strokes, 22 crew calls, 0 s backpaddling; not required at the main feature (hands-off got past it) | 6 s with no steering at the entry: clean; drifted up to 46.6 m off line | Back on line 152 s after steering resumed |
| Rapid 24 | II-III | I — runs clean with no commands at all | Easier than catalogue by 1 class | clean | center clean; −4 m clean; +4 m clean; clean tracks stay ≥7.1 m apart through the rapid | driver turn calls 42% of the center run, 115 guide strokes, 14 crew calls, 0 s backpaddling; a 6 s lapse at the entry did no harm, so steering there is not critical | 6 s with no steering at the entry: clean; drifted up to 6.8 m off line | Back on line 16 s after steering resumed |
| Rapid 25 | II-III | I — runs clean with no commands at all | Easier than catalogue by 1 class | clean | center clean; −4 m clean; +4 m clean; clean tracks stay ≥6.3 m apart through the rapid | driver turn calls 36% of the center run, 101 guide strokes, 11 crew calls, 0 s backpaddling; a 6 s lapse at the entry did no harm, so steering there is not critical | 6 s with no steering at the entry: clean; drifted up to 1.9 m off line | Back on line as soon as steering resumed |
| Commercial Suicide | V-VI | Portage | Not driven | – | – | – | – | – |

### Zambezi (Upper Gorge)

| Rapid | Catalogue | In game | vs catalogue | No commands | 1. Route | 2. Steering | 3. Missed turn | 4. Recovery |
|---|---|---|---|---|---|---|---|---|
| The Wall | IV-V | Not reachable in play | – | Its main feature (190 m) is upstream of the Upper Gorge put-in (213 m); the game cannot start a boat there | – | – | – | – |
| The Bridge | III | I — runs clean with no commands at all | Easier than catalogue by 2 classes | clean | center clean; −4 m clean; +4 m clean; clean tracks stay ≥12.5 m apart through the rapid | driver turn calls 69% of the center run, 51 guide strokes, 5 crew calls, 0 s backpaddling; a 6 s lapse at the entry did no harm, so steering there is not critical | 6 s with no steering at the entry: clean; drifted up to 4.2 m off line | Back on line as soon as steering resumed |
| Rapid 3 | III-IV | I — runs clean with no commands at all | Easier than catalogue by 2 classes | clean | center clean; −4 m clean; +4 m clean; clean tracks stay ≥7.9 m apart through the rapid | driver turn calls 83% of the center run, 56 guide strokes, 5 crew calls, 0 s backpaddling; a 6 s lapse at the entry did no harm, so steering there is not critical | 6 s with no steering at the entry: clean; drifted up to 3.9 m off line | Back on line 6 s after steering resumed |
| The Pocket | III (low confidence) | I — runs clean with no commands at all | Easier than catalogue by 2 classes | clean | center clean; −4 m clean; +4 m clean; clean tracks stay ≥12.1 m apart through the rapid | driver turn calls 69% of the center run, 22 guide strokes, 5 crew calls, 0 s backpaddling; a 6 s lapse at the entry did no harm, so steering there is not critical | 6 s with no steering at the entry: clean; drifted up to 7.5 m off line | Back on line as soon as steering resumed |
| Morning Glory | IV-V | I — runs clean with no commands at all | Easier than catalogue by 3 classes | clean | center clean; −4 m clean; +4 m clean; clean tracks stay ≥8.9 m apart through the rapid | driver turn calls 78% of the center run, 79 guide strokes, 6 crew calls, 0 s backpaddling; a 6 s lapse at the entry did no harm, so steering there is not critical | 6 s with no steering at the entry: clean; drifted up to 6.4 m off line | Back on line as soon as steering resumed |
| Rapid 4B | IV | I — runs clean with no commands at all | Easier than catalogue by 3 classes | clean | center clean; −4 m clean; +4 m clean; clean tracks stay ≥7.4 m apart through the rapid | driver turn calls 45% of the center run, 71 guide strokes, 10 crew calls, 0 s backpaddling; a 6 s lapse at the entry did no harm, so steering there is not critical | 6 s with no steering at the entry: clean; drifted up to 3.1 m off line | Back on line as soon as steering resumed |
| Stairway approach | II | I — runs clean with no commands at all | Easier than catalogue by 1 class | clean | center clean; −4 m clean; +4 m clean; clean tracks stay ≥8.4 m apart through the rapid | driver turn calls 75% of the center run, 35 guide strokes, 5 crew calls, 0 s backpaddling; a 6 s lapse at the entry did no harm, so steering there is not critical | 6 s with no steering at the entry: clean; drifted up to 5.8 m off line | Back on line as soon as steering resumed |
| Stairway to Heaven | V | I — runs clean with no commands at all | Easier than catalogue by 4 classes | clean | center clean; −4 m clean; +4 m clean; clean tracks stay ≥6.4 m apart through the rapid | driver turn calls 78% of the center run, 47 guide strokes, 5 crew calls, 0 s backpaddling; a 6 s lapse at the entry did no harm, so steering there is not critical | 6 s with no steering at the entry: clean; drifted up to 6.4 m off line | Back on line 5 s after steering resumed |
| Rapid 5.5 | II-III (low confidence) | I — runs clean with no commands at all | Easier than catalogue by 1 class | clean | center clean; −4 m clean; +4 m clean; clean tracks stay ≥6.3 m apart through the rapid | driver turn calls 21% of the center run, 54 guide strokes, 4 crew calls, 0 s backpaddling; a 6 s lapse at the entry did no harm, so steering there is not critical | 6 s with no steering at the entry: clean; drifted up to 1.8 m off line | Back on line as soon as steering resumed |
| Reach-end rapid | III (low confidence) | I — runs clean with no commands at all | Easier than catalogue by 2 classes | clean | center clean; −4 m clean; +4 m clean; clean tracks stay ≥1.2 m apart through the rapid | driver turn calls 92% of the center run, 48 guide strokes, 5 crew calls, 0 s backpaddling; a 6 s lapse at the entry did no harm, so steering there is not critical | 6 s with no steering at the entry: clean; drifted up to 5.9 m off line | Back on line 14 s after steering resumed |

## Why the game plays easier than the catalogue

The causes and proposed fixes, with per-rapid research, are in
[Why the rapids play easy, and what to change](2026-10-05-rapid-difficulty-gaps-and-changes.md).

Most of the game's rapids are fast but smooth. Peak water speed and peak
roll on the hands-off run, per river:

| River | Peak water speed (median / range) | Peak roll, no commands (median / max) | Deepest burial |
|---|---|---|---|
| South Fork | 2.0 m/s (1.5–4.6) | 0° / 21° | none |
| Zambezi, full gorge | 3.4 m/s (3.1–7.3) | 4° / 19° | 0.1 m |
| Zambezi, Upper Gorge | 5.4 m/s (3.1–7.2) | 2° / 10° | 0.4 m |
| Chilko | 4.1 m/s (4.1–4.3) | 7° / 8° | 0.2 m |
| Colorado | 5.8 m/s (2.8–8.9) | 5° / 6° | 0.6 m |
| Futaleufú | 5.9 m/s (3.1–14.2) | 6° / 20° | 4.2 m |
| Pacuare | 7.0 m/s (3.7–14.3) | 18° / 45° | 4.3 m |

The current is often quick enough, but almost nothing in it disturbs the boat.
With no one paddling, the raft rarely rolls more than 10°, so there are no
waves, holes or cross-currents strong enough to flip it or throw anyone out.
The raft also simply follows the current around rocks rather than being pinned
or wrapped. The only places that bite are the steep drops on the Pacuare
(Upper and Lower Huacas) and at Terminator, where the boat plunges into a surge
and is buried several metres deep.

To bring the catalogued IV–V rapids up to grade, their water needs features
that punish a passive boat: breaking waves and holes big enough to flip or
stall it, and currents that push it onto rocks unless the guide acts. Higher
or real gauged flows on the full Zambezi map would also help, since its
discharge is uncalibrated.

## Swept out of a swamped seat

The game already ejected passengers hit by fast breaking water. It had no rule
for a seat that simply goes under, so one was added: when a paddler's part of
the boat is half a metre or more under the surface, they are swept out after
about 0.6 s (sooner with water moving past them or with their tube low in a
heel, about twice as long when braced or high-siding). Each seat is judged on
its own. `RaftSim.Rescue.SwampedSeatWashout` covers it.

It matters on the Pacuare. At the bottom of Upper and Lower Huacas the raft
dives into a 3–5 m surge and stays 1–4 m under for 1–2.6 s. Before the rule
every paddler stayed seated through that; now they are swept out. That is what
moved Lower Huacas from "clean on every line" (the 2026-10-04 run) to "crew lost
on every line", and Upper Huacas to "one clean line out of three".

## Rapid name titles

As the raft approaches each named rapid, a letterboxed title card plays: river
name, rapid name in wide-tracked capitals that settle in, an amber rule, and the
catalogue class. It triggers about 45–110 m above the rapid's main feature
(roughly nine seconds out at the current speed), once per approach, never over
a menu or the scenario card, and with fades only when reduced motion is on. In
the rendered runs above it fired at every approached rapid on the Upper Zambezi
and South Fork maps (`RAPID_TITLE` log lines). Headless runs do not draw the HUD.

## Problems found while playing

- **The Wall cannot be reached.** Its main feature is at 190 m, but the Upper
  Gorge scenario starts at 213 m, and the game cannot place a boat above the
  put-in (the water there is not prepared). Its title card never shows either.
  Either move the put-in upstream or drop The Wall from that map.
- **A checkpoint restore onto a rock froze the raft for the rest of the
  session.** When a restored hull overlapped the bank, the physics step refused
  and latched until the whole bridge was reconfigured; every later run was
  frozen. Fixed: a checkpoint restore now clears that latch (it replaces the
  whole raft state anyway), and the assessment re-places a blocked lane start
  toward the center line (it happened once, at Upper Pinball +4 m).
- **Lower Huacas' surge looks suspicious.** The water surface rises 3–5 m in
  about a second where the raft is idling in slow water, on every line. It
  may be a real hydraulic in the cooked flow field or a solver artefact; worth
  a look before treating the V as intended.
- **The Upper Zambezi's last section runs to the edge of its cooked water**
  ("no complete native crop ... refusing fallback water" near the reach end).
  The section still finished.
- On Zambezi Rapids 4 and 12 the hands-off boat circled in an eddy until the
  10-minute limit. That is fair (those rapids need action), but the eddies are
  very sticky.

## Limits of this assessment

- The driver is a scripted guide, not a person. It does not scout, brace
  before a hole or rescue swimmers, so outcomes involving swimmers are harsher
  than a good player would see, and its steering workload is an upper bound.
- Each run starts from a checkpoint just above the rapid, not from a
  continuous descent, and each variant is one sample. Outcomes in big water
  vary from run to run (on Upper Huacas the steered center line lost the crew
  while the missed-turn run went clean).
- Flows are the maps' nominal bands, not gauged flows. The full Zambezi map has
  no calibrated discharge.
- Real-world classes come from guidebooks and outfitter descriptions in the
  project's rapid catalogue, several marked low confidence there.
