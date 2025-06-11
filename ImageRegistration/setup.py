from setuptools import setup, find_packages

setup(
    name="aimed-image-registration",
    version="1.0.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "numpy>=1.20.0",
        "scipy>=1.7.0",
        "scikit-image>=0.18.0",
        "SimpleITK>=2.1.0",
        "pandas>=1.3.0",
        "matplotlib>=3.4.0",
        "plotly>=5.0.0",
        "scikit-learn>=1.0.0",
        "pyyaml>=6.0",
        "tqdm>=4.62.0",
    ],
    author="AIMed Lab",
    description="Professional medical image registration pipeline for prostate ADC-T2W co-registration",
    long_description="Cross-platform registration pipeline with batch processing, quality validation, and lab integration",
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Medical Science Apps.",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
)
