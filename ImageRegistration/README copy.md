# AIMed Lab Image Registration Pipeline

Professional medical image registration system for prostate ADC‑T2W co‑registration, built for the AIMed Lab at Indiana University.

---

## 🎯 Project Overview

This pipeline provides a complete, cross‑platform solution for medical image registration, including:

* **Batch Processing**: Automatic handling of large patient cohorts
* **Quality Validation**: Built‑in metrics (Dice, landmark distances) and reporting
* **Error Recovery**: Robust logging and retry mechanisms for failed cases
* **Lab Integration**: Connects seamlessly with preprocessing and ROI‑classification workflows

---

## 📖 Table of Contents

1. [Quick Start](#-quick-start)
2. [Expected Data Structure](#-expected-data-structure)
3. [Installation](#-installation)
4. [Usage Examples](#-usage-examples)
5. [Integration](#-integration)
6. [Documentation](#-documentation)


---

## 🚀 Quick Start

### Simple Usage

```python
from examples.simple_registration import register_adc_to_t2w_simple

# Register all patients in a directory
summary = register_adc_to_t2w_simple(
    patient_directory="/path/to/patient_data",
    output_directory="/path/to/results"
)
print(f"Success rate: {summary['success_rate']:.1%}")
```

---

## 📦 Expected Data Structure

```
patient_data/
├── patient001/
│   ├── patient001_adc.nii.gz
│   └── patient001_t2w.nii.gz
├── patient002/
│   ├── patient002_adc.nii.gz
│   └── patient002_t2w.nii.gz
└── ...
```

---

## 🛠️ Installation

### Prerequisites

* **Python**: 3.8 or higher
* **pip**: Python package manager
* **Elastix**: Download from [elastix.lumc.nl](https://elastix.lumc.nl/) (macOS, Linux, Windows)

### Clone & Install

```bash
git clone https://github.iu.edu/AIMed-Lab/ImageRegistration.git
cd ImageRegistration
pip install -e .
```

### Configure Elastix

#### macOS

```bash
sudo xattr -rd com.apple.quarantine /path/to/elastix
chmod +x /path/to/elastix/bin/*
echo 'export DYLD_LIBRARY_PATH="/path/to/elastix/lib:$DYLD_LIBRARY_PATH"' >> ~/.profile
echo 'export PATH="/path/to/elastix/bin:$PATH"' >> ~/.profile
source ~/.profile
```

#### Linux

```bash
echo 'export LD_LIBRARY_PATH="/path/to/elastix/lib:$LD_LIBRARY_PATH"' >> ~/.bashrc
echo 'export PATH="/path/to/elastix/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

---

## ✨ Usage Examples

* **Explore data:**

  ```bash
  python examples/explore_data.py /path/to/patient_data
  ```
* **Run simple registration:**

  ```bash
  python examples/simple_registration.py
  ```

---



## 🔄 Integration

Easily integrates with:

* Preprocessing pipelines (e.g., denoising, bias‑field correction)
* ROI classification workflows
* Radiomic feature extraction modules
* Advanced registration methods (e.g., SyN, BSpline refinements)

---

## 📚 Documentation

* **Installation Guide**: `docs/installation.md`



