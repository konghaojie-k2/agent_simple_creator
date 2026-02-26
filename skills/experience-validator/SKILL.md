---
name: experience-validator
description: Validate and refine experiences before they are stored. Use this skill to check if a learned experience is worth keeping and how to improve it.
---

# Experience Validator

This skill validates experiences created during experiments before they are permanently stored.

## Purpose

When an Agent learns something new during an experiment, it creates an experience. However, not all experiences are worth keeping. This skill provides criteria to evaluate experiences.

## Validation Criteria

### 1. Usefulness (40%)

Does this experience solve a real problem?

- **High**: Solves common, recurring problem
- **Medium**: Solves occasional problem
- **Low**: Solves rare or one-time problem

### 2. Reusability (30%)

Can this experience be reused in different contexts?

- **High**: Generic solution applicable to many scenarios
- **Medium**: Specific solution with some flexibility
- **Low**: Very specific to one exact scenario

### 3. Completeness (20%)

Is the experience well-documented?

- **High**: Clear problem statement + solution + examples
- **Medium**: Solution documented but lacks examples
- **Low**: Incomplete or unclear documentation

### 4. Correctness (10%)

Has the experience been tested?

- **High**: Tested multiple times with success
- **Medium**: Tested once successfully
- **Low**: Not tested or failed testing

## Validation Workflow

### Step 1: Self-Assessment

Ask these questions:

1. What problem does this experience solve?
2. How often would this be useful?
3. Can this be applied to different situations?
4. Is the documentation clear and complete?
5. Has this been tested successfully?

### Step 2: Score Calculation

Calculate weighted score:
```
Score = (Usefulness * 0.4) + (Reusability * 0.3) +
        (Completeness * 0.2) + (Correctness * 0.1)
```

### Step 3: Decision

- **Score >= 80**: Keep - High quality experience
- **Score 60-79**: Refine - Improve before keeping
- **Score < 60**: Discard - Not worth keeping

## How to Refine

If an experience needs improvement:

### Add Missing Context

- Problem description
- When to use
- When NOT to use
- Expected outcomes

### Improve Documentation

- Add concrete examples
- Include error handling
- Document edge cases
- Add usage patterns

### Test More

- Run additional experiments
- Try different inputs
- Verify edge cases

## Example Validation

### Experience: PDF Rotation Tool

**Self-Assessment:**

1. **Problem**: Users often need to rotate PDF pages
2. **Usefulness**: Common task → High (90)
3. **Reusability**: Works for any PDF → High (85)
4. **Completeness**: Has script + docs → Medium (70)
5. **Correctness**: Tested once → Medium (60)

**Score**: 90*0.4 + 85*0.3 + 70*0.2 + 60*0.1 = 36 + 25.5 + 14 + 6 = **81.5**

**Decision**: Keep with minor improvements

**Refinements:**
- Add more usage examples
- Test with different PDF types
- Document error cases

## Storage Decision Matrix

| Score | Action | Storage Location |
|-------|--------|------------------|
| 90-100 | Keep as-is | experiences/ |
| 80-89 | Keep with minor fixes | experiences/ |
| 60-79 | Refine and retest | Draft (don't store yet) |
| < 60 | Discard | Don't store |

## Integration with Experiment Flow

### In Reflect Phase:

1. Agent creates experience from successful solution
2. Trigger experience-validator skill
3. Follow validation workflow
4. Store or discard based on score

### Example Prompt:

```
I just solved a problem by creating a PDF rotation script.
Please validate if this experience is worth keeping.

Experience details:
- Problem: Rotating PDF pages
- Solution: Python script using PyPDF2
- Tested: Yes, once
- Documentation: Basic SKILL.md

Validate this experience.
```

## Tips

- **Be honest**: Don't keep experiences just because you created them
- **Focus on patterns**: Experiences solving pattern problems are more valuable
- **Iterate**: Low scores can be improved with more work
- **Share high-quality**: Move excellent experiences to shared skills
