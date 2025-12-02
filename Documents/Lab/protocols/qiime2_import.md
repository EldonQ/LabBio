---
protocol_name: "QIIME2 Data Import"
description: "Imports raw sequencing data into QIIME2 artifacts (.qza). Supports both manifest-based import and direct directory import."
tags: ["qiime2", "import", "manifest", "fastq"]
---

# Inputs
- **Raw Data**: FASTQ files (e.g., `sample_R1.fastq.gz`, `sample_R2.fastq.gz`)
- **Manifest File** (Optional): `manifest.csv` with columns `sample-id,absolute-filepath,direction`

# Outputs
- **Demux Artifact**: `demux.qza` (Type: `SampleData[PairedEndSequencesWithQuality]`)

# Workflow Steps

## Step 1: Create Manifest (Recommended)
If data is not already in Casava 1.8 format, create a manifest file.
**Command Template**:
```bash
# Create header (TSV)
echo -e "sample-id\tabsolute-filepath\tdirection" > manifest.tsv

# Add samples (Example loop)
# Note: Replace {r1_suffix} and {r2_suffix} with actual suffixes like _R1.fastq.gz
for file in *{r1_suffix}; do
    sample=$(basename "$file" {r1_suffix})
    echo -e "${sample}\t$PWD/${sample}{r1_suffix}\tforward" >> manifest.tsv
    echo -e "${sample}\t$PWD/${sample}{r2_suffix}\treverse" >> manifest.tsv
done
```

## Step 2: Import Data
**Command Template**:
```bash
qiime tools import \
  --type 'SampleData[PairedEndSequencesWithQuality]' \
  --input-path {manifest_file} \
  --output-path {output_artifact} \
  --input-format PairedEndFastqManifestPhred33V2
```

# Common Errors
- **Error**: `manifest.tsv is not a(n) PairedEndFastqManifestPhred33V2 file`
  - **Cause**: Header is wrong or paths are relative.
  - **Fix**: Ensure header is EXACTLY `sample-id\tabsolute-filepath\tdirection` (Tab separated). Ensure paths start with `/`.
