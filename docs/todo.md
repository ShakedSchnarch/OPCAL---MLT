# רשימת משימות — OPCAL-MLT

- [ ]  STD rectangles: pre vs post
- [ ]  Visualization:
  - [ ]  Y axis value
  - [ ]  fix scale
- [ ]  peak detection parameters
- [ ]  Code refactor
- [ ]  Implement one‑Click Launch if applicable
- [ ]  Refresh option
- [ ]  Update documentation if neede
- [ ]  tester
- [ ]  sliding bar
- [ ]  documentation standartization




## דחוף מאוד
- [ ] להפיק טקסט ברור מהקובץ `docs/dev/OPCal labeler notes.xlsx - הערות 2.pdf` (OCR או בקשת מקור), לתעד כל הערה בקובץ תיעוד/issue ייעודי, ולסווג אם מדובר בתיקון קוד, UI או מסמך.
- [ ] ליישם את כל ההערות לאחר התיעוד: לעדכן קבצי קוד (`src/`), תצורה (`scripts/`) ותיעוד (`docs/`) לפי הצורך ולוודא שכל הערה מסומנת כנסגרה.
- [ ] לחקור את כשל `pytest` (Signal 11) בהרצה מהרוט של הפרויקט: להריץ בתוך סביבה וירטואלית נקייה, לזהות את המודול שמפיל את הריצה (למשל בדיקות `tests/test_processing.py`) ולהגיש תיקון בקוד או בתלויות.
- [ ] לאחר התיקון להריץ `pytest -vv` ולשמור תוצאות מוצלחות כקובץ לוג ב-`docs/dev/` כדי לתעד את החזרה לתפקוד.
- [ ] לאחד מספרי גרסאות: לעדכן `pyproject.toml:3`, `src/opcal_mlt/app/main.py:64`, `README.md:5` ו-`docs/CHANGELOG.md:1` לאותה גרסה רשמית (לדוגמה 1.0.0), ולתעד את הרציונל בקובץ `docs/CHANGELOG.md`.
- [ ] לעדכן את `main.py` כך ש-`APP_VERSION` תילקח מקובץ מרכזי (למשל `src/opcal_mlt/__init__.py`) כדי למנוע חוסר אחידות עתידי.
- [ ] לתקן את תהליך בניית macOS: להוסיף את הסקריפט החסר `scripts/OPCAL-Labeler.command` או להסיר את ההפניה אליו מ-`scripts/build-macos-zip.sh:12`, להריץ `scripts/build-macos-zip.sh` ולאמת שהתוצר `dist/OPCAL-Labeler-macOS.zip` מכיל קבצים ניתנים להרצה.
- [ ] לתעד לוג הבנייה (פקודות ותוצאות) בקובץ `docs/dev/build-log.md` עבור שקיפות בפרסום המחקר.
- [ ] להכין קובץ נעילת תלות (`requirements.txt` או `requirements.lock`) ובמקביל קובץ `environment.yml` התואם ל-conda כדי לאפשר שחזור סביבת ניסוי.
- [ ] לעדכן את הוראות ההתקנה ב-`README.md` וב-`docs/USER_GUIDE.md` כך שיתייחסו לקבצי הסביבה החדשים ולתהליך שחזור מלא.

## בטווח הקצר
- [ ] להקים ספריית `docs/methods/` וליצור `docs/methods/opcal_labeler_methodology.md` המתעד את המודל הסטטיסטי, שלבי עיבוד האות ותרומת הכלי ל-pipeline המחקרי.
- [ ] לסכם את התוכן שב-`docs/dev/*.pdf` לטקסט/Markdown (למשל `docs/dev/summary_notes.md`) ולחבר קישורים מה-`README.md` אל המסמכים החדשים.
- [ ] לעבור על המסמכים לאחר הסיכום ולייצר משימות מפורטות נוספות במידת הצורך (להוסיף לקובץ זה או ל-issue tracker).
- [ ] לפתח סקריפט `scripts/merge_sessions_to_dataset.py` שמאתר את כל תיקיות הסשנים (למשל תחת `Labeled signals*/`) וממזג את `labels.csv`/`cell_map.csv` לקובץ אימון יחיד תואם מפרט `docs/API.md`.
- [ ] להוסיף בדיקת יחידה ל-`tests/test_io.py` שמוודאת שהסקריפט החדש שומר על שלמות הקבצים (מספור תאים, session_id, וכו').
- [ ] להרחיב את הבדיקות עבור `opcal_mlt/app/session_io.py` כולל mocking שלFilesystem כדי לכסות יצירת ספריות, כתיבה לקרביים וטעינה מחדש.
- [ ] להוסיף בדיקות UI מבוססות `streamlit.testing` או mocking כדי לוודא שזרימת השלבים (start→upload→label→finish) לא נשברת בעת שינויי קוד.
- [ ] ליצור מסמך `docs/testing.md` שמפרט את פרוטוקול הבדיקות (יחידה, אינטגרציה, ידניות) ואת הפרמטרים הקריטיים לבדיקת איכות במדרג מחקרי.
- [ ] להסדיר ניהול נתונים: להעביר את `Labeled signals 810 frames_160225 - NEW - Oscillatory` לנתיב `data/raw/`, ליצור `data/README.md` עם הסברים על מבנה הנתונים ולהוסיף מדיניות גיבוי בסיסית.
- [ ] להוסיף סקריפט גיבוי פשוט (למשל `scripts/backup_sessions.py`) המייצא ZIP יומי של נתוני הגלם והתיוגים.

## ארוך טווח
- [ ] לבנות pipeline QA: סקריפט שמחשב סטטיסטיקות על התוויות (התפלגות, חריגים, עקביות בין מתייגים) ומפיק דוח אוטומטי (`docs/reports/qa_report.md`).
- [ ] להטמיע מודל ראשוני להצעת תוויות (Semi-automatic labeling): להוסיף מודול `src/opcal_mlt/core/suggestions.py` ולחברו ל-UI עם אפשרות אישור/דחייה.
- [ ] למדוד את השפעת כלי ההצעה על זמן תיוג ועל אחידות ולהוסיף גרפים וניתוח לתיקייה `docs/reports/`.
- [ ] להפיק תיעוד API דו-לשוני (`docs/API_he.md`) עם דוגמאות קוד ב-Python ו-R עבור זרימות ניתוח נוספות.
- [ ] לבנות Dockerfile בספריית הפרויקט, להריץ בדיקות בתוך הקונטיינר ולהכין תהליך CI שדוחף image מתויגת לכל release.
- [ ] להגדיר GitHub Actions או כלי CI חלופי שמריץ lint, בדיקות, בניית חבילות (pip + macOS zip) ויוצר ארטיפקטים חתומים לפרסום.
- [ ] לתעד את תהליך ה-CI/CD החדש ב-`docs/devops.md` ולהוסיף תרשים זרימה ב-`docs/assets/`.
