# User Guide

## OPCAL-Labeler Overview
OPCAL-Labeler is a tool designed for efficient and accurate labeling of calcium imaging traces. It facilitates the classification of calcium peaks into predefined categories to support downstream analysis in neuroscience research.

## Keyboard Shortcuts

| Key(s)    | Action                                      |
|-----------|---------------------------------------------|
| 1         | Label as High‑flat                          |
| 2         | Label as High‑oscillatory                   |
| 3         | Label as Oscillatory                         |
| 4         | Label as Low‑activity                        |
| 5         | Label as Uncertain                           |
| 6         | Label as Drifting                            |
| S         | Save current progress                        |
| U         | Undo last label change                       |
| ← / →     | Navigate to previous / next cell             |
| + / -     | Increase / decrease SD threshold for peak highlighting |
| R         | Resume previous labeling session             |
| F         | Toggle smoothing                             |

## Workflow

1. Load a traces file in CSV or NPZ format (HDF5 supported if applicable). If cell indices are missing, they will be generated automatically.
2. Adjust the baseline method and SD threshold (default 3) for peak detection and highlighting.
3. Review detected peaks along with baseline and post‑stimulation standard deviation (STD) shading, and assign labels.
4. Add an optional note, confirm or change the label.
5. Review your progress using the progress bar; you can return to previously labeled cells to adjust labels or notes.
6. Save your work; save writes to the current session CSV file located in the session folder.

## Autosave
The application autosaves your progress every 60 seconds by writing to a `labels.csv` file in the active session folder.

## Tips
- Hover over peaks to see their index and time information.
- Use the progress bar to quickly navigate between labeled and unlabeled cells.
- Press `S` frequently to manually save your progress if desired.
