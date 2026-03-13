# EU Policy Indicators Scores (2020–2024)

## File
`EU_Policy_Indicators_Scores_2020-2024.xlsx` — Composite EU-wide policy indicator scores by country (~950 KB)

## Source
**European Commission / Migration Policy Monitoring**  
Compiled as part of the project's policy analysis layer, drawing on sources including MIPEX, OECD, and European Commission integration indicator frameworks.  
Time Period: 2020–2024

## Description
This dataset contains **scored policy indicators** for EU member states across the 2020–2024 period. It provides a structured, quantitative measure of each country's integration policy environment — covering dimensions such as labour market access, residency rights, educational inclusion, and anti-discrimination protections. The scores allow direct numerical comparison of policy openness across EU countries.

This dataset works in direct conjunction with the MIPEX files but focuses exclusively on the EU27, offering higher temporal resolution (annual granularity) for the most recent policy period.

## Key Dimensions Covered
| Indicator Area | Purpose |
|----------------|---------|
| **Labour Market Access** | How easily immigrants can work in regulated professions |
| **Residence Security** | Ease and speed of obtaining long-term or permanent residence |
| **Educational Inclusion** | Access to national education systems and language support |
| **Anti-Discrimination** | Strength of legal protections in employment and housing |
| **Civic Participation** | Political rights and community engagement opportunities |
| **Healthcare Access** | Universal access vs. restricted access to public health services |

## Coverage
- **Geography:** EU27 member states
- **Time Period:** 2020–2024 (annual or biennial, depending on indicator)
- **Unit of Analysis:** Country-level composite scores (0–100 scale)

## Project Role
> **Supporting Dataset — Research Objective 3**

This dataset is used to:
1. **Policy vs. Prosperity:** Provides the most up-to-date EU policy scores for the project's core regression-style analysis — joining policy scores to labour outcomes (Eurostat LFS) to test the hypothesis that better integration policy leads to better immigrant economic participation.
2. **Cross-Regional Comparison (EU side):** Together with MIPEX, it forms the complete policy picture for the *"European Social Model"* side of the American vs. European comparison.
3. **Temporal Analysis:** Annual scores from 2020–2024 complement the discrete MIPEX wave years, enabling smoother trend lines in the policy → outcomes analysis.

## Usage Notes
- The file is in Excel (`.xlsx`) format — use `pandas.read_excel()` to load.
- Check whether each sheet represents one year or one indicator; the structure varies.
- Scores should be normalized to a 0–100 scale before joining with outcome variables if not already normalized.
- Treat as a **companion to MIPEX**, not a replacement — both should be used together for the most robust policy analysis.
