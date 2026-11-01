# 10. Exam question Excel format

Each question set is **one Excel file (`.xlsx`)** with exactly **200 questions** in the TS ICET pattern. The site keeps **3 sets** (slots 1, 2 and 3), and each student gets a random one.

**Start from the template:** `templates/exam-question-set-template.xlsx`. You can also download it in the admin portal (*Exam sets → Download template*). It contains sample rows and an *Instructions* tab.

## The pattern (checked on upload)

| Section | Title | Questions | Subsections (recommended counts) |
|---|---|---:|---|
| A | Analytical Ability | **75** | Data Sufficiency 20, Problem Solving 55 |
| B | Mathematical Ability | **75** | Arithmetical Ability 35, Algebraical and Geometrical Ability 30, Statistical Ability 10 |
| C | Communication Ability | **50** | Vocabulary 15, Business and Computer Terminology 10, Functional Grammar 15, Reading Comprehension 10 |

What the upload checks:

- **Rejected** unless the total is exactly 200 and the sections are exactly 75 / 75 / 50.
- Subsection counts and unknown subsection names only produce **warnings**. The upload still succeeds.
- Scoring: 1 mark per correct answer, no negative marking, 150 minutes, no sectional time limits.

## Sheet `questions` (required)

The first row must contain these column names. Upper or lower case doesn't matter.

| Column | Required | What to write |
|---|---|---|
| `section` | yes | `A`, `B` or `C` |
| `subsection` | yes | e.g. `Problem Solving` (use the names above) |
| `passage_id` | no | Only for passage-based questions: the id of the passage in the `passages` sheet, e.g. `P1`. Leave empty otherwise |
| `question` | yes | The question text. Can contain a table (below) |
| `option_a` | yes | Option A |
| `option_b` | yes | Option B |
| `option_c` | yes | Option C |
| `option_d` | yes | Option D |
| `correct` | yes | The correct letter: `A`, `B`, `C` or `D` |

Example rows:

| section | subsection | passage_id | question | option_a | option_b | option_c | option_d | correct |
|---|---|---|---|---|---|---|---|---|
| A | Problem Solving | | Find the missing number in the sequence: 4, 9, 19, 39, 79, ? | 119 | 139 | 159 | 169 | C |
| B | Arithmetical Ability | | A sum of money doubles itself every 5 years at simple interest. In how many years will it become 4 times? | 10 years | 12 years | 15 years | 20 years | C |
| C | Business and Computer Terminology | | What does the term "Bulls" signify in the stock market? | Investors who expect prices to fall | Investors who expect prices to rise | Government regulatory authorities | Short-term borrowers | B |
| C | Reading Comprehension | P1 | According to the passage, what is the main benefit of saving early? | Higher taxes | Compound growth | Lower income | Fewer expenses | B |

## Sheet `passages` (only for passage-based questions)

| Column | What to write |
|---|---|
| `passage_id` | A short unique id, e.g. `P1`, `P2` |
| `passage_text` | The full passage |

How passages work in the exam:

- Questions with the same `passage_id` are shown **together under the passage**.
- The passage group moves as one block when the section is shuffled, and its questions are shuffled among themselves.
- All questions of one passage must be in the same section.

## Tables inside a question

Write the table inside the cell. Press **Alt+Enter** (Mac: **Option+Return**) for a new line, and type one row per line with cells separated by `|`. The first row is the header.

```text
The table shows the sales of a shop (in lakhs):
| Year | Sales |
| 2023 | 450 |
| 2024 | 540 |
What is the percentage increase in sales?
```

Rules:

- Every row needs the same number of cells as the header.
- A separator line like `|---|---|` is allowed but not needed.
- Text before and after the table is fine.
- Passages can contain tables too.
- **Images are not supported.** Write geometry questions in words.

## What the exam does with the file

- Section order is always A, then B, then C. Inside each section the questions (and passage groups) are shuffled for **every attempt**.
- The four options of every question are shuffled for every attempt. The system remembers which one is correct, so you never need to worry about the A-D position after upload.
- Students never receive the correct answers until they submit.

## Uploading, replacing and checking

1. Admin portal → **Exam sets** → **Validate** your file. This shows the counts, every error with its row number, and any warnings, without saving anything.
2. Fix the errors and validate again.
3. Upload into an **empty** slot.
   - To replace a set: **Delete** it first, then **Upload** the new file into that slot.
   - A slot that already has a set can't be overwritten by accident.
4. You can also check a file on your computer:

   ```bash
   python -m app.cli validate-exam-file my-set.xlsx
   ```

Common errors and fixes:

| Error | Fix |
|---|---|
| A set must have exactly 200 questions; found 198 | Add the missing questions. Rows with errors are not counted; fix those first |
| Section B must have exactly 75 questions; found 76 | Move one question to the right section |
| `correct` must be A, B, C or D | Use just the letter |
| Two or more options have the same text | Make every option different |
| `passage_id` `P3` is not in the `passages` sheet | Add the passage or fix the id |
| Table row 3 has 2 cells but the header has 3 | Make every table row the same width |
| Missing column(s): `correct` | Restore the header row from the template |
