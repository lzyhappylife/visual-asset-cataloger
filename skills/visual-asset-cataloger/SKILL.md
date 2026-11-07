---
name: visual-asset-cataloger
description: Build independently copied image asset libraries and complete evidence-based, per-image CSV annotations from foldered image sets. Use when a user needs image selection, deterministic renaming, path indexing, and visual metadata labeling; do not use for filename-only bulk tagging or editing the source collection.
---

# Visual Asset Cataloger

Use this skill for a source folder that contains image sets arranged by categories, styles, products, or other sibling folders. The deliverable is an independent copy of the selected images plus a CSV whose rows stay aligned to those copies.

## Operating rules

- Treat the source collection as read-only. Copy files into a separate output directory before renaming or annotating them.
- Preserve the user’s requested row order. Capture the ordered inventory once and use `asset_id` as the stable merge key.
- Keep the first two columns stable unless the user explicitly changes the schema. The default is `asset_id` followed by `图片路径`.
- Put the path of the copied image in the path column by default. Use the source path only when the user explicitly requests source references.
- Do not infer visual facts from a folder name, filename, category, another image, or an unseen part of the scene.
- Do not write a value until the current image has been viewed for that field. Do not reuse a description from another image or write `同上`.
- Use direct observations. When a detail is obscured, cropped, blurred, too small, or shown from behind, write `无法判断` and the visible reason.
- Do not infer identity, intent, relationship, personality, or an action outside the captured frame.
- For a one-person image, `互动动作` and `视线互动情况` may be `无（画面仅见1人）`; explain the basis when useful.
- Keep confidence separate from descriptions. If requested, add one rightmost `整体置信度` column with a numeric value from 0 to 1. Never put confidence prose inside a field value.

## Workflow

### 1. Establish the job contract

Resolve only the decisions that materially affect the output:

- source root and independent output directory
- image extensions to include
- selection rule, such as one leaf folder with a complete set from each sibling category
- naming pattern, such as `category_set_001.ext`
- CSV encoding and delimiter
- exact field order, including fields to remove or add
- whether the user wants a checkpoint after inventory/path indexing

If the request gives a deterministic selection rule, apply it and report the selected folders. If multiple selections remain equally valid, ask before copying.

### 2. Inventory before copying

Enumerate the source tree without editing it. Identify the sibling categories at the requested level, then identify leaf folders that contain image files. Record:

- category and set folder
- absolute source folder
- ordered image filenames
- image count and extensions
- any empty, nested, or ambiguous folders

Use one stable ordering rule, normally case-insensitive filename order within a selected set. Exclude hidden files and non-image files unless explicitly requested.

### 3. Create the independent copy and index

Create a new output directory with a dedicated image subdirectory and CSV. Copy the selected files with metadata-preserving file copy where available. Generate unique names that encode the set, for example:

`<category>_<set>_<three-digit sequence>.<original extension>`

Keep the original extension unless conversion is requested. Write one row per copied image with the new filename in `asset_id` and the absolute copied path in `图片路径`. Quote CSV fields correctly and use UTF-8; UTF-8 with BOM is acceptable when spreadsheet compatibility is needed.

At this stage, validate row count, path existence, uniqueness, and the first two columns. If the user asks for a checkpoint, stop here and hand over the path index without filling visual fields.

### 4. Apply schema changes before visual annotation

Construct the final header before filling rows. If a field is removed, remove its column rather than leaving a deprecated blank column. If confidence is requested, append `整体置信度` at the far right. When migrating an already annotated row, strip confidence prose from field values and put the numeric value in the new column.

Never reorder existing images while changing the schema. Keep all first and second column values byte-for-byte equivalent after the schema operation.

### 5. Annotate one image at a time

For each row in the stored order:

1. Open the image named by the current row.
2. Review every requested field against that image alone.
3. Write the result before moving to the next image.
4. Record uncertainty where evidence is insufficient.

For ordinary descriptive fields, include two to four independently visible details. Simple classification fields such as person count or watermark presence may be shorter. Keep descriptions concrete and field-specific. For example, clothing should mention visible garment color, cut, material or decoration; composition should mention orientation, subject placement, crop, and negative space; lighting should mention direction, color, contrast, highlights, shadows, or flare.

Use the detailed field rubric in [references/annotation-rubric.md](references/annotation-rubric.md) when the user asks for a standard visual schema or when field boundaries are unclear.

### 6. Use confidence consistently

Set one overall numeric confidence per image, not one confidence phrase per cell. Use higher values when the subject, action, clothing, background, and watermark are clearly visible. Lower the value when important evidence is hidden by cropping, blur, side/back view, occlusion, or low resolution. Confidence reflects evidence quality, not how aesthetically clear or attractive the image is.

### 7. Scale without losing row-level evidence

For large collections, split work into contiguous row ranges. A read-only reviewer may inspect a range and return structured rows, but only one writer should merge results into the CSV. Merge on `asset_id`, restore the original order, and reject missing, duplicated, or out-of-range rows. Never use a batch template to fill unreviewed images.

### 8. Run final checks

Run a deterministic CSV audit, using [scripts/validate_asset_csv.py](scripts/validate_asset_csv.py) when applicable. Confirm:

- the header exactly matches the final requested schema
- every source record has one output row
- `asset_id` and `图片路径` are present, unique where required, and ordered correctly
- every copied path exists
- every visual field is filled unless the field explicitly permits an unavailable value
- no field contains `同上`, hidden confidence prose, or unsupported generic filler
- every confidence value is numeric and in the inclusive range 0–1
- one-person rows use explicit no-interaction/no-gaze values where appropriate
- removed fields do not remain in the header or body

Inspect representative beginning, middle, and ending rows after writing. Report the actual image count if it differs from a number stated by the user; do not silently add or remove images.
