---
protocol_name: "QIIME2 Denoising (DADA2)"
description: "Denoises paired-end sequences using DADA2, filtering chimeras and correcting errors."
tags: ["qiime2", "dada2", "denoising"]
---

# Inputs
- **Input Artifact**: `demux.qza` (Type: `SampleData[PairedEndSequencesWithQuality]`)
- **Parameters**:
  - `trim_left_f`: Position to trim from 5' end of forward read (default: 0)
  - `trim_left_r`: Position to trim from 5' end of reverse read (default: 0)
  - `trunc_len_f`: Position to truncate forward read (default: 0 = no truncation)
  - `trunc_len_r`: Position to truncate reverse read (default: 0 = no truncation)

# Outputs
- **Table**: `table.qza` (Feature Table)
- **Representative Sequences**: `rep-seqs.qza`
- **Stats**: `denoising-stats.qza`

# Workflow Steps

## Step 1: Denoise
**Command Template**:
```bash
qiime dada2 denoise-paired \
  --i-demultiplexed-seqs {input_artifact} \
  --p-trim-left-f {trim_left_f} \
  --p-trim-left-r {trim_left_r} \
  --p-trunc-len-f {trunc_len_f} \
  --p-trunc-len-r {trunc_len_r} \
  --o-table {output_table} \
  --o-representative-sequences {output_rep_seqs} \
  --o-denoising-stats {output_stats} \
  --p-n-threads {threads}
```

**Explanation**:
DADA2 models the amplicon errors and infers the sample composition. It is crucial to set truncation parameters based on quality scores (Q-scores) to remove low-quality tails.

## Step 2: Visualize Stats
**Command Template**:
```bash
qiime metadata tabulate \
  --m-input-file {output_stats} \
  --o-visualization {output_stats_viz}
```

# Common Errors
- **Error**: `The resulting library contains no sequences`
  - **Cause**: Truncation parameters were too aggressive, or primers were not removed.
  - **Fix**: Check Q-scores and adjust `trunc_len`. Ensure primers are removed if they are part of the read.
