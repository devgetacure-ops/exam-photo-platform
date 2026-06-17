# Golden Images Directory

## Purpose
Stores visual-regression test cases. Each case includes:
1. `case_id.input.png`: The source test photograph.
2. `case_id.golden.png`: The approved target output photograph (the "ground truth").
3. `case_id.rule.json`: The rule snapshot used.

## Usage
During regression testing, the pipeline processes the input file and checks if the output matches the golden file pixel-for-pixel or within a structural similarity threshold.
