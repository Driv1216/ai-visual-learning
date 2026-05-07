# Video 2 Migration Plan

## 1. Purpose of This Document

This document explains why the existing `rashikabs/video 2` folder should be migrated into the main `ai-visual-learning` architecture, what problems exist in the current standalone files, and exactly how we will convert them into a clean production-ready Video 2.

The goal is not to criticize the existing work. The current `rashikabs/video 2` folder is valuable because it already contains the educational sequence, topic breakdown, dataset examples, visual ideas, and many working Manim prototypes.

However, the project has now moved into a structured architecture where videos are generated through JSON scene specs, narration segments, generated audio, timestamps, and a reusable renderer. Because of that, the old standalone Manim files need to become architecture-native instead of remaining separate scripts.

---

## 2. Current Project Architecture

The project is not a one-off Manim animation folder. It is a reusable educational video generation system.

The intended structure is:

```text
ai-visual-learning/
├── core/
├── courses/
│   └── machine-learning/
│       ├── scenes/
│       ├── assets/
│       └── generated/
└── rashikabs/
```

The project context defines this direction clearly: the repository is meant to support multiple courses with reusable core logic and course-specific content under `courses/`: `PROJECT_BRAIN.md:231-245`.

The core principle of the architecture is:

> Content is data. Rendering is code.

This means the actual lesson content should live in structured scene JSON files, while Manim rendering behavior should live in reusable engine/action code: `PROJECT_BRAIN.md:379-385`.

---

## 3. How the Current Pipeline Works

The current system follows this high-level workflow:

1. Write the lesson idea/script.
2. Break narration into scene-level narration segments.
3. Write a JSON scene spec.
4. Generate audio per narration segment.
5. Concatenate audio segments into one scene WAV.
6. Generate timestamps from actual audio durations.
7. Render Manim visuals from JSON and timestamps.
8. Mux rendered video with scene audio.

This pipeline is documented in the project context: `PROJECT_BRAIN.md:252-365`.

### 3.1 Scene JSON

Each scene is represented as structured JSON with:

- `scene_id`
- `video_title`
- `scene_title`
- `order`
- `duration_mode`
- `voice`
- `narration`
- `visual_timeline`
- `notes`

This structure is enforced by the `SceneSpec` model: `core/scene_schema.py:143-152`.

Example existing scene JSON files follow this pattern:

- `courses/machine-learning/scenes/scene01_intellectual_wall.json:1-12`
- `courses/machine-learning/scenes/scene04_two_lives_of_a_system.json:1-12`

### 3.2 Narration Segments

The current architecture breaks narration into small segments.

Example from Scene 1:

- `courses/machine-learning/scenes/scene01_intellectual_wall.json:12-132`

Example from Scene 4:

- `courses/machine-learning/scenes/scene04_two_lives_of_a_system.json:12-64`

This is important because every visual action anchors to a narration segment.

The schema requires each narration segment to have an `id` and `text`: `core/scene_schema.py:82-85`.

### 3.3 Visual Timeline

Every visual step must have:

- `id`
- `anchor`
- `action`
- `params`
- `offset`
- `zone`
- `transition_in`
- `transition_out`
- `persist`
- `replace`
- optional `duration`
- optional `camera_scale`

This is defined in `VisualStep`: `core/scene_schema.py:88-101`.

The schema also validates that every visual step references a real narration anchor: `core/scene_schema.py:154-169`.

### 3.4 Audio Generation

Audio is generated per narration segment using the scene JSON.

The generator loads the scene JSON into `SceneSpec`: `core/generate_audio.py:18-21`.

It uses the scene voice configuration: `core/generate_audio.py:122-134`.

It writes one `.wav` file per narration segment: `core/generate_audio.py:139-161`.

The system validates that Sarvam returns WAV audio, not MP3: `core/generate_audio.py:88-92`.

### 3.5 Audio Concatenation

After segment audio is generated, all segment WAVs are concatenated into a scene-level WAV.

This happens in `concat_audio.py`: `core/concat_audio.py:90-116`.

The output path is:

```text
courses/machine-learning/generated/scene_audio/<scene_id>.wav
```

That path is defined in `core/concat_audio.py:32-41`.

### 3.6 Timestamp Generation

Timestamps are generated from the actual duration of each audio segment.

The timestamp generator reads each `.wav` segment and calculates:

- `start`
- `end`
- `duration`

This happens in `core/generate_timestamps.py:94-122`.

The output path is:

```text
courses/machine-learning/generated/timestamps/<scene_id>.json
```

That path is defined in `core/generate_timestamps.py:32-41`.

### 3.7 Rendering

The renderer loads the scene JSON path from the `AI_VL_SCENE_JSON` environment variable: `core/render_scene.py:120-137`.

It then loads the matching timestamp file: `core/render_scene.py:137-142`.

It maps narration IDs to actual timestamp starts/durations: `core/render_scene.py:144-145`.

Then it sorts visual steps by:

```python
anchor timestamp + offset
```

This is done in `core/render_scene.py:147-150`.

That is how visuals stay synchronized with narration.

---

## 4. What the `rashikabs/video 2` Folder Currently Is

The `rashikabs/video 2` folder currently contains standalone Manim scene files.

Current files include:

```text
openingtitle.py
dik.py
table.py
tableCOLOUR.py
datacleaning.py
missingvalues.py
categoricalencoding.py
featurescaling.py
featurescalingvid.py
featureengg.py
goodfeature.py
traintestsplit.py
conclu.py
```

Each important file defines its own Manim `Scene` class directly:

- `rashikabs/video 2/openingtitle.py:8-42`
- `rashikabs/video 2/dik.py:8-268`
- `rashikabs/video 2/table.py:11-192`
- `rashikabs/video 2/datacleaning.py:132-264`
- `rashikabs/video 2/missingvalues.py:125-347`
- `rashikabs/video 2/categoricalencoding.py:189-366`
- `rashikabs/video 2/featurescalingvid.py:25-386`
- `rashikabs/video 2/featureengg.py:96-401`
- `rashikabs/video 2/goodfeature.py:20-266`
- `rashikabs/video 2/traintestsplit.py:38-377`
- `rashikabs/video 2/conclu.py:20-255`

These files are useful as visual prototypes, but they are not compatible with the project’s production architecture yet.

---

## 5. Why the Existing Files Need Migration

### 5.1 They Are Hardcoded Manim Scenes

The current files put scene content, timing, layout, narration assumptions, and animation logic directly inside Python `construct()` methods.

Example:

- `rashikabs/video 2/openingtitle.py:8-42`

This conflicts with the project principle that content should be data and rendering should be reusable code: `PROJECT_BRAIN.md:379-385`.

In the current architecture, a scene should be represented as JSON, and the renderer should interpret that JSON using reusable actions.

### 5.2 They Do Not Use Narration Segments

The current `rashikabs/video 2` files do not contain structured narration segments like the main architecture expects.

In the main architecture, narration lives in JSON, like this:

- `courses/machine-learning/scenes/scene01_intellectual_wall.json:12-132`
- `courses/machine-learning/scenes/scene04_two_lives_of_a_system.json:12-64`

The schema explicitly models narration segments: `core/scene_schema.py:82-85`.

Without narration segments, we cannot generate segment-wise audio or timestamps.

### 5.3 They Do Not Use Timestamp-Based Sync

The biggest issue is timing.

The old files use fixed waits like:

- `rashikabs/video 2/openingtitle.py:34-35`
- `rashikabs/video 2/dik.py:16-20`
- `rashikabs/video 2/datacleaning.py:165-182`
- `rashikabs/video 2/missingvalues.py:142-175`
- `rashikabs/video 2/categoricalencoding.py:208-224`
- `rashikabs/video 2/featurescalingvid.py:69-102`
- `rashikabs/video 2/featureengg.py:109-115`
- `rashikabs/video 2/goodfeature.py:33-72`
- `rashikabs/video 2/traintestsplit.py:133-138`
- `rashikabs/video 2/conclu.py:73-84`

These waits are guesses. They do not respond to real voice timing.

The current architecture already solves this problem by deriving timestamps from actual WAV audio durations: `core/generate_timestamps.py:94-122`.

The renderer then uses those timestamps to schedule visuals: `core/render_scene.py:144-150`.

### 5.4 They Do Not Use the Audio Pipeline

The old files do not contain voice config, narration IDs, segment WAV generation, timestamp generation, or renderer sync.

The production audio system expects:

1. Scene JSON
2. `voice` config
3. `narration` list
4. Generated `.wav` segment files
5. Concatenated scene `.wav`
6. Timestamp JSON

This is implemented in:

- `core/generate_audio.py:95-180`
- `core/concat_audio.py:44-126`
- `core/generate_timestamps.py:44-126`

So audio should not be manually attached to old Manim scenes. The correct approach is to migrate narration into JSON and let the existing audio pipeline handle it.

### 5.5 They Duplicate Styling and Helper Logic

Many files redefine the same constants:

- `rashikabs/video 2/openingtitle.py:3-6`
- `rashikabs/video 2/dik.py:3-6`
- `rashikabs/video 2/table.py:3-8`
- `rashikabs/video 2/datacleaning.py:3-9`
- `rashikabs/video 2/missingvalues.py:3-9`

Many files also define similar label helpers:

- `rashikabs/video 2/datacleaning.py:124-126`
- `rashikabs/video 2/missingvalues.py:117-122`
- `rashikabs/video 2/categoricalencoding.py:19-23`
- `rashikabs/video 2/featurescalingvid.py:18-22`
- `rashikabs/video 2/featureengg.py:24-28`
- `rashikabs/video 2/goodfeature.py:13-17`
- `rashikabs/video 2/traintestsplit.py:20-24`
- `rashikabs/video 2/conclu.py:13-17`

This is fine for a prototype, but production should centralize repeated visual patterns into reusable actions.

### 5.6 They May Have Asset Path Problems

`dik.py` uses hardcoded image paths:

- `rashikabs/video 2/dik.py:38-44`
- `rashikabs/video 2/dik.py:87-95`
- `rashikabs/video 2/dik.py:167-168`

These point to:

```text
media/images/dik/...
```

But the current project direction expects course-specific assets under the course folder structure: `PROJECT_BRAIN.md:231-242`.

During migration, these assets should either be moved into the course asset area or replaced with native Manim diagrams.

---

## 6. Important: The Existing Work Is Still Valuable

The current `rashikabs/video 2` folder should not be deleted or dismissed.

It already provides:

- the topic order
- rough visual ideas
- a consistent house-price dataset example
- table designs
- missing-value examples
- encoding examples
- scaling examples
- train-test split visuals
- a final conclusion structure

The migration plan is not “throw everything away.”

The correct interpretation is:

```text
rashikabs/video 2 = storyboard / prototype / reference implementation
```

The production version should become:

```text
courses/machine-learning/scenes/video02_sceneXX_*.json
+ reusable actions in core/actions.py
+ audio/timestamps generated through the existing pipeline
```

---

## 7. Final Decision

We will do a full clean migration.

That means:

- We will not keep Video 2 as separate standalone Manim files for final production.
- We will not simply render the existing files and merge them as-is.
- We will not attach one full audio file manually to the old animation.
- We will rebuild Video 2 as architecture-native JSON scenes.
- We will use the existing audio/timestamp/rendering system.
- We will add only the reusable action types needed for Video 2.

This keeps the project scalable and consistent with the rest of the course.

---

## 8. Proposed Final Video 2 Structure

The old folder currently has around 10–11 conceptual sections. We will migrate them into proper scene JSON files.

### Scene 1 — Why Raw Data Is Not Enough

Source reference:

- `rashikabs/video 2/dik.py:16-20`
- `rashikabs/video 2/dik.py:247-267`

Core idea:

> Machine learning does not learn directly from chaos. It needs structured, information-rich input.

This scene should introduce the bridge from raw data to useful information.

Possible new file:

```text
courses/machine-learning/scenes/video02_scene01_raw_data_to_information.json
```

### Scene 2 — The Messy House Price Dataset

Source reference:

- `rashikabs/video 2/table.py:16-30`
- `rashikabs/video 2/table.py:42-47`
- `rashikabs/video 2/table.py:155-185`

Core idea:

> A raw dataset can contain duplicates, missing values, inconsistent spellings, mixed units, irrelevant columns, and inconsistent representation.

Possible new file:

```text
courses/machine-learning/scenes/video02_scene02_messy_house_dataset.json
```

### Scene 3 — Data Cleaning

Source reference:

- duplicate removal: `rashikabs/video 2/datacleaning.py:170-191`
- spelling standardization: `rashikabs/video 2/datacleaning.py:196-219`
- mixed unit fix: `rashikabs/video 2/datacleaning.py:224-241`
- missing value handoff: `rashikabs/video 2/datacleaning.py:246-259`

Core idea:

> Data cleaning removes contradictions and obvious structural problems before the model sees the data.

Possible new file:

```text
courses/machine-learning/scenes/video02_scene03_data_cleaning.json
```

### Scene 4 — Handling Missing Values

Source reference:

- initial missing values table: `rashikabs/video 2/missingvalues.py:125-145`
- remove rows strategy: `rashikabs/video 2/missingvalues.py:150-176`
- mean strategy: `rashikabs/video 2/missingvalues.py:187-208`
- median strategy: `rashikabs/video 2/missingvalues.py:219-237`
- mode strategy: `rashikabs/video 2/missingvalues.py:248-266`
- constant placeholder strategy: `rashikabs/video 2/missingvalues.py:277-303`
- final before/after: `rashikabs/video 2/missingvalues.py:305-347`

Core idea:

> Missing values must be handled deliberately. The right strategy depends on the feature and the context.

Recommendation:

Do not spend equal time on all five methods unless the video is meant to be long. For a clean explainer, show:

1. removing rows
2. filling a numerical value
3. filling a discrete/categorical value
4. before/after result

Possible new file:

```text
courses/machine-learning/scenes/video02_scene04_missing_values.json
```

### Scene 5 — Categorical Encoding

Source reference:

- models need numbers: `rashikabs/video 2/categoricalencoding.py:208-213`
- label encoding furnished column: `rashikabs/video 2/categoricalencoding.py:218-243`
- label encoding location column: `rashikabs/video 2/categoricalencoding.py:249-271`
- label encoding problem: `rashikabs/video 2/categoricalencoding.py:273-279`
- one-hot encoding: `rashikabs/video 2/categoricalencoding.py:281-350`

Core idea:

> Models need numerical input, but the way we convert categories into numbers can accidentally introduce fake meaning.

Possible new file:

```text
courses/machine-learning/scenes/video02_scene05_categorical_encoding.json
```

### Scene 6 — Feature Scaling

Source reference:

- raw plot: `rashikabs/video 2/featurescalingvid.py:38-72`
- scale distortion annotations: `rashikabs/video 2/featurescalingvid.py:74-102`
- normalization: `rashikabs/video 2/featurescalingvid.py:131-192`
- standardization: `rashikabs/video 2/featurescalingvid.py:202-269`
- scaled plot: `rashikabs/video 2/featurescalingvid.py:279-317`
- model sensitivity: `rashikabs/video 2/featurescalingvid.py:322-386`

Core idea:

> Features on very different scales can distort how some models interpret distance, magnitude, and contribution.

Possible new file:

```text
courses/machine-learning/scenes/video02_scene06_feature_scaling.json
```

### Scene 7 — Feature Selection and Feature Engineering

Source reference:

- opening phrase: `rashikabs/video 2/featureengg.py:109-115`
- dropping irrelevant columns: `rashikabs/video 2/featureengg.py:123-185`
- house age extraction: `rashikabs/video 2/featureengg.py:190-236`
- price per square foot: `rashikabs/video 2/featureengg.py:241-280`
- room density: `rashikabs/video 2/featureengg.py:285-322`
- final engineered table: `rashikabs/video 2/featureengg.py:327-401`

Core idea:

> Good preprocessing is not only repair. It is also representation. We choose and create features that make the pattern easier for the model to learn.

Possible new file:

```text
courses/machine-learning/scenes/video02_scene07_feature_engineering.json
```

### Scene 8 — What Makes a Good Feature?

Source reference:

- checklist: `rashikabs/video 2/goodfeature.py:33-72`
- exam leakage example: `rashikabs/video 2/goodfeature.py:77-150`
- house price leakage example: `rashikabs/video 2/goodfeature.py:155-190`
- availability test: `rashikabs/video 2/goodfeature.py:195-266`

Core idea:

> A feature is not good just because it exists. It must be relevant, informative, consistent, and available at prediction time.

Possible new file:

```text
courses/machine-learning/scenes/video02_scene08_good_features_and_leakage.json
```

### Scene 9 — Train-Test Split and Evaluation

Source reference:

- ready dataset: `rashikabs/video 2/traintestsplit.py:51-139`
- exam analogy: `rashikabs/video 2/traintestsplit.py:144-187`
- train-test split visual: `rashikabs/video 2/traintestsplit.py:192-282`
- preprocessing order/leakage: `rashikabs/video 2/traintestsplit.py:287-377`

Core idea:

> The model must be evaluated on data it did not train on. Also, preprocessing must be fit on the training data only to avoid leakage.

Possible new file:

```text
courses/machine-learning/scenes/video02_scene09_train_test_split.json
```

### Scene 10 — Final Synthesis

Source reference:

- preprocessing pipeline: `rashikabs/video 2/conclu.py:33-88`
- three scenarios: `rashikabs/video 2/conclu.py:93-171`
- model learns from representation: `rashikabs/video 2/conclu.py:176-214`
- closing statement: `rashikabs/video 2/conclu.py:219-255`

Core idea:

> Better preprocessing does not guarantee a perfect model, but poor preprocessing almost guarantees a poor one.

Possible new file:

```text
courses/machine-learning/scenes/video02_scene10_preprocessing_synthesis.json
```

---

## 9. What Happens to `openingtitle.py`

The current opening title scene is:

- `rashikabs/video 2/openingtitle.py:8-42`

It shows:

```text
Video 2 / 5
Data Preprocessing & Preparation
```

The main issue is that it waits for 20 seconds: `rashikabs/video 2/openingtitle.py:34-35`.

In the clean migration, this should probably not remain as a separate long scene. Instead, the opening title can be part of Scene 1 and last only as long as the narration needs.

Recommended approach:

- Use a short title beat in `video02_scene01_raw_data_to_information.json`.
- Do not keep a standalone 20-second title card.
- Let audio timing determine how long the opening stays.

---

## 10. What Happens to `featurescaling.py`

The file `featurescaling.py` is not a Manim scene. It uses Matplotlib to save images:

- `rashikabs/video 2/featurescaling.py:1-45`

It creates:

```text
scaling_before.png
scaling_after.png
```

Recommendation:

Do not include this file in the production migration.

Instead:

- use Manim-native axes and dots, like the stronger version in `featurescalingvid.py`
- or move any needed generated images into the course asset folder if absolutely required

The better source for scaling is:

- `rashikabs/video 2/featurescalingvid.py:25-386`

---

## 11. Required New Reusable Actions

Video 2 is table-heavy. The existing engine already supports many visual actions, but Video 2 needs a few reusable table/data actions.

The schema currently lists allowed actions in `AllowedAction`: `core/scene_schema.py:5-53`.

Recent available action names include:

- `show_workflow_cycle`
- `mutate_workflow_cycle`

These appear in the updated schema: `core/scene_schema.py:51-52`.

For Video 2, we should add only the action types that are genuinely reusable.

### 11.1 `show_dataset_table`

Purpose:

Display a table from JSON parameters.

Used for:

- raw dataset
- cleaned dataset
- missing values mini table
- categorical data table
- engineered feature table

Relevant old sources:

- `rashikabs/video 2/table.py:16-30`
- `rashikabs/video 2/datacleaning.py:20-118`
- `rashikabs/video 2/missingvalues.py:19-114`
- `rashikabs/video 2/categoricalencoding.py:29-101`
- `rashikabs/video 2/featureengg.py:39-93`

### 11.2 `highlight_table_cells`

Purpose:

Highlight cells, rows, or columns with semantic colors.

Used for:

- duplicates
- inconsistent spellings
- missing values
- mixed units
- target variable emphasis

Relevant old sources:

- `rashikabs/video 2/datacleaning.py:175-182`
- `rashikabs/video 2/datacleaning.py:201-205`
- `rashikabs/video 2/datacleaning.py:246-255`
- `rashikabs/video 2/missingvalues.py:142-160`

### 11.3 `transform_table_cells`

Purpose:

Transform one or more table cells into corrected values.

Used for:

- `mumbai` / `MUMBAI` to `Mumbai`
- `45` to `484`
- `N/A` to imputed values
- `Yes/No` to `1/0`
- `Mumbai/Pune/Delhi` to encoded values

Relevant old sources:

- `rashikabs/video 2/datacleaning.py:207-216`
- `rashikabs/video 2/datacleaning.py:224-240`
- `rashikabs/video 2/missingvalues.py:196-207`
- `rashikabs/video 2/missingvalues.py:227-236`
- `rashikabs/video 2/missingvalues.py:256-265`
- `rashikabs/video 2/categoricalencoding.py:226-243`
- `rashikabs/video 2/categoricalencoding.py:257-271`

### 11.4 `remove_table_rows`

Purpose:

Animate removal of duplicate or invalid rows.

Used for:

- duplicate row removal
- missing-value row removal example

Relevant old sources:

- `rashikabs/video 2/datacleaning.py:184-191`
- `rashikabs/video 2/missingvalues.py:163-176`

### 11.5 `show_before_after_table`

Purpose:

Show before/after comparison tables.

Used for:

- missing values before/after
- one-hot encoding comparison
- final cleaned vs messy representation

Relevant old sources:

- `rashikabs/video 2/missingvalues.py:305-339`
- `rashikabs/video 2/categoricalencoding.py:281-350`

### 11.6 `show_encoding_transform`

Purpose:

Show categories becoming numerical representations.

Used for:

- label encoding
- one-hot encoding

Relevant old source:

- `rashikabs/video 2/categoricalencoding.py:218-350`

### 11.7 `show_scaling_plot`

Purpose:

Show raw/scaled axes, points, and scaling comparison.

Used for:

- unscaled scatter
- normalized scatter
- standardization explanation

Relevant old source:

- `rashikabs/video 2/featurescalingvid.py:38-317`

### 11.8 `show_train_test_split`

Purpose:

Show train/test split bar, row allocation, and evaluation separation.

Relevant old source:

- `rashikabs/video 2/traintestsplit.py:192-282`

### 11.9 `show_pipeline_stages`

Purpose:

Show the final preprocessing pipeline.

Relevant old source:

- `rashikabs/video 2/conclu.py:33-88`

---

## 12. Scene JSON Example

A migrated scene should look conceptually like this:

```json
{
  "scene_id": "video02_scene03_data_cleaning",
  "video_title": "Data Preprocessing and Preparation",
  "scene_title": "Cleaning Messy Data",
  "order": 3,
  "duration_mode": "audio_driven",
  "voice": {
    "language": "en-IN",
    "speaker": "priya",
    "model": "bulbul:v3"
  },
  "narration": [
    {
      "id": "s3_01",
      "text": "Raw datasets often contain small inconsistencies that become large problems for a model."
    },
    {
      "id": "s3_02",
      "text": "The first step is to remove duplicate rows."
    },
    {
      "id": "s3_03",
      "text": "Then we standardize values that mean the same thing but are written differently."
    }
  ],
  "visual_timeline": [
    {
      "id": "s3_v01_show_table",
      "anchor": "s3_01",
      "action": "show_dataset_table",
      "zone": "center",
      "transition_in": "fade",
      "persist": true,
      "replace": "center",
      "duration": 0.8,
      "params": {
        "dataset": "house_prices_raw",
        "highlight_problem_cells": true
      },
      "offset": 0.0
    },
    {
      "id": "s3_v02_highlight_duplicates",
      "anchor": "s3_02",
      "action": "highlight_table_cells",
      "zone": "center",
      "transition_in": "smooth",
      "persist": true,
      "replace": "center",
      "duration": 0.6,
      "params": {
        "rows": ["101", "108"],
        "color": "gold",
        "label": "duplicate rows"
      },
      "offset": 0.1
    },
    {
      "id": "s3_v03_remove_duplicate",
      "anchor": "s3_02",
      "action": "remove_table_rows",
      "zone": "center",
      "transition_in": "smooth",
      "persist": true,
      "replace": "center",
      "duration": 0.7,
      "params": {
        "rows": ["108"]
      },
      "offset": 1.0
    }
  ],
  "notes": {
    "tone": "clear, practical, concept-first",
    "pacing": "audio-driven, no long static holds",
    "animation_guidelines": "Use table transformations instead of slide-like replacements."
  }
}
```

This is not final JSON. It is an example of the intended structure.

---

## 13. Audio Plan

The audio should use the existing project pipeline.

### 13.1 Do Not Add Audio Directly to Old Manim Files

We should not manually attach one long audio file to the existing Manim scenes.

Reason:

The old scenes are timed using fixed waits, like:

- `rashikabs/video 2/openingtitle.py:34-35`
- `rashikabs/video 2/categoricalencoding.py:208-224`
- `rashikabs/video 2/featurescalingvid.py:69-102`

If the narration timing changes, the visuals will drift.

### 13.2 Use Segment-Wise Audio

For each migrated JSON scene:

1. Write narration segments.
2. Generate one `.wav` per segment.
3. Concatenate into one scene `.wav`.
4. Generate timestamps from actual WAV durations.
5. Render visuals using those timestamps.

This matches the current architecture:

- audio generation: `core/generate_audio.py:95-180`
- audio concat: `core/concat_audio.py:44-126`
- timestamp generation: `core/generate_timestamps.py:44-126`
- timestamp-driven rendering: `core/render_scene.py:120-150`

### 13.3 Keep WAV

The system must continue using WAV internally.

Sarvam WAV validation happens here: `core/generate_audio.py:88-92`.

The project context also states that Sarvam returns WAV and that segment files should be saved as `.wav`: `PROJECT_BRAIN.md:208-223`.

---

## 14. Asset Plan

Some old scenes use image files through hardcoded paths.

Examples:

- `rashikabs/video 2/dik.py:38-44`
- `rashikabs/video 2/dik.py:87-95`
- `rashikabs/video 2/dik.py:167-168`

Migration options:

### Option A — Move Assets Properly

Move needed images into:

```text
courses/machine-learning/assets/video02/
```

Then reference them through a clean course asset convention.

### Option B — Replace Images With Manim-Native Visuals

This may be better for long-term visual consistency.

For example:

- Instead of a screenshot of a house price table, use `show_dataset_table`.
- Instead of external charts, use Manim axes and dots.
- Instead of external data images, use simple generated visual examples.

Recommendation:

Prefer Manim-native visuals unless the image is essential.

---

## 15. Visual Quality Rules for Migration

The current project has a strong visual standard.

Important rules:

- Avoid static holds longer than about 0.5–1.0 seconds unless intentional: `PROJECT_BRAIN.md:868-872`
- Use maximum 2–3 active visual elements at once: `PROJECT_BRAIN.md:873-876`
- Scenes should feel like ideas evolving, not slides appearing/disappearing: `PROJECT_BRAIN.md:878-883`
- Prefer transformation over replacement: `PROJECT_BRAIN.md:884-887`
- Avoid show text → wait → remove → show next: `PROJECT_BRAIN.md:1146-1152`

During migration, this means:

- Do not preserve all old waits.
- Do not make every scene a static table lecture.
- Do not overload the screen with too many labels.
- Prefer a single evolving dataset object across multiple scenes.
- Use visual transformations to show improvement from raw data to model-ready data.

---

## 16. What We Will Not Do

### 16.1 We Will Not Directly Merge Old Files Into Production

The old files are standalone Manim scenes.

They do not use:

- scene JSON
- narration IDs
- generated audio
- timestamps
- reusable action registry
- project renderer

So they should not become final production code as-is.

### 16.2 We Will Not Create a Separate Video 2 Architecture

Creating a separate system for Video 2 would cause long-term maintenance problems.

The project is designed to scale across courses and videos using one reusable system: `PROJECT_BRAIN.md:231-245`.

### 16.3 We Will Not Manually Sync Audio With Waits

Manual sync is fragile.

The project already has a better solution through audio-derived timestamps: `core/generate_timestamps.py:94-122`.

### 16.4 We Will Not Add Dozens of One-Off Actions

Video 2 needs reusable table/data actions, but we should not create a unique action for every small animation.

Only add actions that repeat across multiple scenes.

---

## 17. Full Migration Workflow

### Step 1 — Lock the Final Video 2 Script

Before building JSON, we need the final narration script.

This is the most important step.

If the script keeps changing, audio and timestamps will keep changing.

Deliverable:

```text
Final narration broken into 10 scenes
```

### Step 2 — Create Scene JSON Files

Create one JSON file per migrated scene under:

```text
courses/machine-learning/scenes/
```

Suggested filenames:

```text
video02_scene01_raw_data_to_information.json
video02_scene02_messy_house_dataset.json
video02_scene03_data_cleaning.json
video02_scene04_missing_values.json
video02_scene05_categorical_encoding.json
video02_scene06_feature_scaling.json
video02_scene07_feature_engineering.json
video02_scene08_good_features_and_leakage.json
video02_scene09_train_test_split.json
video02_scene10_preprocessing_synthesis.json
```

Each scene must satisfy `SceneSpec`: `core/scene_schema.py:143-152`.

### Step 3 — Add Required Actions to Schema

Any new action must be added to `AllowedAction`: `core/scene_schema.py:5-53`.

Possible new actions:

```text
show_dataset_table
highlight_table_cells
transform_table_cells
remove_table_rows
show_before_after_table
show_encoding_transform
show_scaling_plot
show_train_test_split
show_pipeline_stages
```

### Step 4 — Implement Reusable Actions

Add the reusable builders to `core/actions.py`.

These should create Manim objects from JSON params.

The goal is to avoid hardcoding entire scenes while still supporting table-heavy visuals.

### Step 5 — Connect Renderer Support

If the renderer needs special handling for any new action, update `core/render_scene.py`.

The renderer currently loads JSON and timestamps here: `core/render_scene.py:120-150`.

Any new action must preserve the renderer’s timeline-driven behavior.

### Step 6 — Generate Audio Segments

For each scene JSON:

```text
python core/generate_audio.py --scene courses/machine-learning/scenes/<scene_file>.json
```

The generator creates segment WAV files using narration IDs: `core/generate_audio.py:139-161`.

### Step 7 — Concatenate Scene Audio

For each scene JSON:

```text
python core/concat_audio.py --scene courses/machine-learning/scenes/<scene_file>.json --force
```

The concat script combines segment WAVs: `core/concat_audio.py:90-116`.

### Step 8 — Generate Timestamps

For each scene JSON:

```text
python core/generate_timestamps.py --scene courses/machine-learning/scenes/<scene_file>.json --force
```

The timestamp generator writes timing JSON based on actual audio durations: `core/generate_timestamps.py:94-122`.

### Step 9 — Validate Scene JSON

Run validation before rendering.

The schema validates:

- unique narration IDs
- unique visual step IDs
- valid visual anchors
- at least one narration segment
- at least one visual step

Validation logic exists in `core/scene_schema.py:154-177`.

### Step 10 — Render Each Scene

Render with the JSON-driven renderer.

The renderer expects `AI_VL_SCENE_JSON`: `core/render_scene.py:124-129`.

It then loads the selected scene file: `core/render_scene.py:131-137`.

### Step 11 — Mux Audio and Video

After render succeeds, mux scene audio with video.

Important rule:

Do not run muxing if Manim render failed, because that can accidentally reuse stale video output. This is a known project issue: `PROJECT_BRAIN.md:970-979`.

### Step 12 — Final Video Assembly

After all individual scene videos are rendered and audio-muxed, assemble them into the final Video 2.

The project context says final scene/course merge is intended but not fully built yet: `PROJECT_BRAIN.md:374-377`.

So final assembly may need a small dedicated video-level concat step later.

---

## 18. Migration Priority

Because this is a full clean migration, the recommended order is:

### Priority 1 — Script and Scene Breakdown

Do this first.

No animation work should start until we know the final narration structure.

### Priority 2 — Table Action System

Most of Video 2 depends on table transformations.

Implement:

```text
show_dataset_table
highlight_table_cells
transform_table_cells
remove_table_rows
show_before_after_table
```

### Priority 3 — First Three Scenes

Build:

1. raw data to information
2. messy dataset
3. data cleaning

These scenes establish the recurring dataset visual language.

### Priority 4 — Encoding and Missing Values

Build:

1. missing values
2. categorical encoding

These heavily reuse the table action system.

### Priority 5 — Scaling

Build the plot-based scaling scene.

This may need `show_scaling_plot`.

### Priority 6 — Feature Engineering and Leakage

Build:

1. feature engineering
2. good features/leakage

These may use table actions plus text/list visuals.

### Priority 7 — Train-Test Split and Conclusion

Build:

1. train-test split
2. preprocessing synthesis

These close the conceptual loop.

---

## 19. Expected Challenges

### 19.1 Time

This will take longer than a quick merge because Video 2 is essentially a full lesson, not one scene.

### 19.2 Table Complexity

Tables are visually dense.

We must avoid clutter and keep only one main focal idea per beat.

### 19.3 Action Design

If actions are too generic, they may become hard to control.

If actions are too specific, they will not be reusable.

The goal is a small, practical action set.

### 19.4 Audio Lock-In

Once audio is generated, changing narration requires regenerating:

- audio segments
- scene audio
- timestamps

This is expected and correct.

### 19.5 Visual Pacing

The old scenes contain many long waits. These should not be copied directly.

The new version must follow narration-driven timing.

---

## 20. Summary for Teammate

The current `rashikabs/video 2` folder is a strong prototype, but it was made as standalone Manim files.

Our project has now evolved into a structured video generation architecture where:

- scene content lives in JSON
- narration is split into segments
- audio is generated per segment
- timestamps come from real WAV durations
- visuals are anchored to narration timestamps
- reusable actions handle Manim rendering

Because of that, the old files cannot be final production files as-is.

We are not deleting the work. We are using it as the storyboard and rebuilding it properly inside the architecture.

The final migration will produce:

```text
courses/machine-learning/scenes/video02_scene01_*.json
courses/machine-learning/scenes/video02_scene02_*.json
...
courses/machine-learning/scenes/video02_scene10_*.json
```

Plus reusable table/data actions in the core engine.

The final Video 2 will be:

- audio-synchronized
- easier to edit
- easier to validate
- consistent with Video 1
- reusable for future course videos
- cleaner than manually merged Manim files

The key decision is:

> We are doing a full clean migration, not a rough merge.
