# Installation Guide

This guide walks you through setting up the ImageRegistration project, including cloning the repo, installing dependencies, configuring Elastix, and verifying the pipeline.

---

## Prerequisites

1. **Python Environment**

   * Python 3.8 or higher
   * pip package manager

2. **Elastix Registration Software**

   * Download from: [https://elastix.lumc.nl/](https://elastix.lumc.nl/)
   * Choose the appropriate version for your OS

---

## Installation

### 1. Clone the Repository

```bash
git clone https://github.iu.edu/AIMed-Lab/ImageRegistration.git
cd ImageRegistration
```

### 2. Install Python Dependencies

```bash
pip install -e .
```

### 3. Install and Configure Elastix

#### macOS

```bash
# Download elastix (adjust URL for latest version)
curl -L -O https://github.com/SuperElastix/elastix/releases/download/5.2.0/elastix-5.2.0-mac.tar.gz

# Extract and move
tar -xzf elastix-5.2.0-mac.tar.gz
sudo mv elastix-5.2.0-mac /usr/local/elastix

# Fix macOS security issues
sudo xattr -rd com.apple.quarantine /usr/local/elastix
chmod +x /usr/local/elastix/bin/*

# Add to environment
echo 'export DYLD_LIBRARY_PATH="/usr/local/elastix/lib:$DYLD_LIBRARY_PATH"' >> ~/.profile
echo 'export PATH="/usr/local/elastix/bin:$PATH"' >> ~/.profile
source ~/.profile

# Test installation
elastix --help
```

#### Linux

```bash
# Download elastix
wget https://github.com/SuperElastix/elastix/releases/download/5.2.0/elastix-5.2.0-linux.tar.gz

# Extract and install
tar -xzf elastix-5.2.0-linux.tar.gz
sudo mv elastix-5.2.0-linux /usr/local/elastix

# Add to environment
echo 'export LD_LIBRARY_PATH="/usr/local/elastix/lib:$LD_LIBRARY_PATH"' >> ~/.bashrc
echo 'export PATH="/usr/local/elastix/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

# Test installation
elastix --help
```

---

## Verification

1. **Verify Elastix**

   ```bash
   elastix --help
   transformix --help
   ```

2. **Test the Python Pipeline**

   ```bash
   cd ImageRegistration
   python -c "
   import sys
   sys.path.insert(0, 'src')
   from image_registration.pipeline.pranav_registration_pipeline import ProstateADCRegistrationPipeline
   pipeline = ProstateADCRegistrationPipeline()
   print('✅ Pipeline initialization successful!')
   "
   ```

---

## Troubleshooting

* **elastix: command not found**

  * Ensure `elastix` is in your `PATH`.
  * Verify the installation directory exists and you restarted your terminal.

* **Permission denied: elastix (macOS)**

  ```bash
  sudo xattr -rd com.apple.quarantine /path/to/elastix
  chmod +x /path/to/elastix/bin/*
  ```

* **Library not loaded errors**

  * Ensure `DYLD_LIBRARY_PATH` (macOS) or `LD_LIBRARY_PATH` (Linux) is set correctly.
  * Check that the `lib` directory exists under the Elastix installation.

* **Python import errors**

  ```bash
  pip install -e .
  ```

---

## Next Steps

* Explore your data:

  ```bash
  python examples/explore_data.py /path/to/data
  ```
* Test registration:

  ```bash
  python examples/simple_registration.py
  ```
* Read the user guide:

  ```bash
  less docs/user_guide.md
  ```
