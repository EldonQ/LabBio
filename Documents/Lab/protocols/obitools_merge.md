---
protocol_name: "OBITools Sequence Merging"
description: "Merges paired-end reads using OBITools3 (illuminapairedend)."
tags: ["obitools", "merge", "paired-end"]
---

# Inputs
- **Forward Reads**: `*_R1.fastq`
- **Reverse Reads**: `*_R2.fastq`

# Outputs
- **Merged Reads**: `*.fastq` (Single file with merged sequences)

# Workflow Steps

## Step 1: Align and Merge
**Command Template**:
```bash
# Loop through samples
for r1 in *{r1_suffix}; do
    sample=$(basename "$r1" {r1_suffix})
    r2="${sample}{r2_suffix}"
    
    # Check if R2 exists
    if [ -f "$r2" ]; then
        echo "Merging $sample..."
        obi align paired-end -R "$r1" "$r2" | obi align paired-end --merge > "${sample}_merged.fastq"
    else
        echo "Warning: R2 not found for $sample"
    fi
done
```

**Explanation**:
`obi align paired-end` aligns the forward and reverse reads. The `--merge` option constructs the consensus sequence.

# Common Errors
- **Error**: `obi: error: unrecognized arguments`
  - **Cause**: Using OBITools 1 syntax (e.g., `illuminapairedend`) in OBITools 3.
  - **Fix**: Use `obi align paired-end`.
