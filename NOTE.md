# Kypson RFQ Parser — Notes

## Approach
I used a lightweight, explainable rule-based parser with Python's standard library. It normalizes common packaging terms and spelling variants, maps them to the seven assignment categories, and extracts order quantity, unit, GSM, micron, and a likely delivery location. Quantity extraction checks explicit order units and quantity labels, supports Indian number formats (for example, lakh/lac, thousand/hazaar, K, and comma-separated values), and filters common capacity/specification patterns before treating a number as an order quantity.

## Test score
Using the scoring script supplied by the placement team on my own 79 labelled examples: **79/79 all-fields exact match (100.0%)**. Runtime was approximately 0.02 seconds. This is only the score on this self-created test set; it does not establish performance on the company's private or hidden data.

## Three cases likely to be difficult
1. A buyer may use an unfamiliar regional term, abbreviation, or spelling that is not in the keyword patterns.
2. A message may contain several product lines or several competing quantities; this parser returns one record and selects the first eligible order quantity.
3. A location may be misspelled, lowercase, or mentioned without a clear delivery cue or comma, making it difficult to distinguish from ordinary text.

## With 1,000 real labelled examples
I would create a representative train/validation/test split, inspect errors by field, expand normalization and synonym dictionaries, and compare this rule-based baseline with a small local classifier/entity-extraction model or a hybrid approach. I would keep the test set untouched and evaluate category accuracy, quantity exact-match accuracy, unit accuracy, and field-level precision/recall.

## Production monitoring
With appropriate privacy controls, I would log parser outputs and buyer corrections, track field-level error rates and the percentage of RFQs requiring manual review, and periodically audit samples with operations staff. I would also monitor changes in vocabulary, locations, and missing-field rates.

## Tools used
- Python standard library (`re`, `json`, and `typing`) for parsing and testing.
- ChatGPT (OpenAI) was used to help draft and review the implementation and test cases; I ran the supplied scorer and reviewed/modified the code and examples.
