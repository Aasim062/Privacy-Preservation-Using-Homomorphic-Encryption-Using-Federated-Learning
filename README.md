# Privacy-Preservation Using Homomorphic Encryption with Federated Learning

This project implements a secure federated learning system that uses homomorphic encryption to create an aggregated encrypted global model while preserving data privacy across distributed healthcare institutions.

## Overview

The project combines two powerful privacy-preserving technologies:
- **Federated Learning**: Train models across multiple institutions without sharing raw data
- **Homomorphic Encryption**: Perform computations on encrypted data without decryption

This enables hospitals and healthcare providers to collaboratively train machine learning models while maintaining complete data privacy and security.

## Project Structure

```
├── README.md                          # Project documentation
├── MINOR/                             # Main project directory
│   ├── Random_Hospital_Dataset.csv    # Sample dataset for testing
│   ├── Ckks-RNS/                      # CKKS (homomorphic encryption scheme)
│   │   └── Ckks.py                    # CKKS implementation
│   ├── LocalModels/                   # Local model training for each hospital
│   │   ├── Hospital1/
│   │   │   ├── Dataset_Hospital1.csv
│   │   │   ├── Hospital1weights.csv
│   │   │   └── LogisticRegresseion.py
│   │   └── Hospital2/
│   │       ├── Dataset_Hospital2.csv
│   │       ├── Hospital2weights.csv
│   │       └── LogisticRegression.py
│   └── seal-fedavg/                   # C++ implementation for federated averaging with SEAL
│       ├── aggregator.cpp             # Model aggregation logic
│       ├── hospital_encrypt.cpp       # Hospital-side encryption
│       ├── decrypt.cpp                # Decryption utilities
│       ├── keygen.cpp                 # Key generation
│       ├── CMakeLists.txt
│       └── seal-fedavg/               # Submodule directory
├── vcpkg/                             # Package manager for C++ dependencies
│   ├── bootstrap-vcpkg.sh/.bat        # Setup scripts
│   ├── ports/                         # Available packages
│   ├── installed/                     # Installed packages
│   └── buildtrees/                    # Build artifacts
```

## Components

### 1. Local Models (Python)
- **Hospital1** and **Hospital2**: Independent logistic regression models trained on each institution's private data
- Each hospital trains its own model locally without sharing raw data

### 2. Homomorphic Encryption (CKKS)
- **CKKS-RNS/Ckks.py**: Implementation of the CKKS (Cheon-Kim-Kim-Song) homomorphic encryption scheme
- Allows computation on encrypted data while maintaining privacy

### 3. Federated Averaging (C++)
- **aggregator.cpp**: Aggregates encrypted model weights from multiple hospitals
- **hospital_encrypt.cpp**: Encrypts local model weights at each hospital
- **decrypt.cpp**: Decrypts the final aggregated model (only by authorized party)
- **keygen.cpp**: Generates cryptographic keys for the system

## Key Features

✅ **Privacy-Preserving**: Raw patient data never leaves hospital premises  
✅ **Secure Aggregation**: Model weights are encrypted during aggregation  
✅ **Federated Learning**: Collaborative model training across institutions  
✅ **Homomorphic Encryption**: Computations on encrypted data  
✅ **C++ Performance**: Optimized backend for cryptographic operations  

## Requirements

- **Python 3.7+**
  - NumPy, Pandas, Scikit-learn
  - For CKKS implementation

- **C++ Requirements**
  - Microsoft SEAL library (included via vcpkg)
  - CMake 3.10+
  - C++17 compatible compiler

## Installation

### Python Setup
```bash
# Install Python dependencies
pip install numpy pandas scikit-learn
```

### C++ Setup (Windows)
```bash
# Navigate to vcpkg directory
cd vcpkg

# Bootstrap vcpkg
.\bootstrap-vcpkg.bat

# Install SEAL and dependencies
.\vcpkg install seal:x64-windows
```

### C++ Setup (Linux/macOS)
```bash
# Navigate to vcpkg directory
cd vcpkg

# Bootstrap vcpkg
./bootstrap-vcpkg.sh

# Install SEAL and dependencies
./vcpkg install seal:x64-linux  # or appropriate triplet
```

## Usage

### Step 1: Train Local Models
```bash
# Train Hospital 1 model
cd MINOR/LocalModels/Hospital1
python LogisticRegresseion.py

# Train Hospital 2 model
cd ../Hospital2
python LogisticRegression.py
```

### Step 2: Generate Encryption Keys
```bash
cd MINOR/seal-fedavg
g++ -std=c++17 keygen.cpp -o keygen -lseal
./keygen
```

### Step 3: Encrypt Local Weights
```bash
g++ -std=c++17 hospital_encrypt.cpp -o encrypt -lseal
./encrypt
```

### Step 4: Aggregate Encrypted Models
```bash
g++ -std=c++17 aggregator.cpp -o aggregator -lseal
./aggregator
```

### Step 5: Decrypt Final Model
```bash
g++ -std=c++17 decrypt.cpp -o decrypt -lseal
./decrypt
```

## Workflow

```
┌─────────────────────────────────────────────────────────────┐
│  Hospital 1              Hospital 2        Hospital N       │
│  ┌──────────────┐        ┌──────────────┐  ┌──────────────┐ │
│  │ Private Data │        │ Private Data │  │ Private Data │ │
│  └──────┬───────┘        └──────┬───────┘  └──────┬───────┘ │
│         │                       │                  │         │
│         ▼                       ▼                  ▼         │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │        Train Local Models (Logistic Regression)        │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
         │                       │                  │
         ▼                       ▼                  ▼
  ┌────────────────────────────────────────────────────────┐
  │    Encrypt Weights using Homomorphic Encryption       │
  └────────────────────────────────────────────────────────┘
         │                       │                  │
         └───────────┬───────────┴──────────┬───────┘
                     │                      │
                     ▼                      ▼
            ┌─────────────────────────────────────┐
            │   Federated Aggregation (FedAvg)    │
            │  (Works on encrypted weights)       │
            └─────────────────────────────────────┘
                     │
                     ▼
            ┌─────────────────────────────────────┐
            │  Decrypt Global Model               │
            │  (Only authorized party can decrypt)│
            └─────────────────────────────────────┘
```

## Security Considerations

- **End-to-End Encryption**: Data remains encrypted during aggregation
- **Key Management**: Encryption keys are kept secure and never shared
- **Access Control**: Only authorized entities can decrypt the final model
- **No Data Leakage**: Individual hospital data is never exposed

## Contributing

Contributions are welcome! Please follow these guidelines:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License - see LICENSE file for details.

## References

- **CKKS Scheme**: Cheon, J. H., Kim, A., Kim, M., & Song, Y. (2017). "Homomorphic Encryption for Arithmetic of Approximate Numbers"
- **Microsoft SEAL**: https://github.com/microsoft/SEAL
- **Federated Learning**: McMahan, H. B., Moore, E., Ramage, D., Hampson, S., & Arcas, B. A. (2016). "Communication-Efficient Learning of Deep Networks from Decentralized Data"

## Contact

For questions or issues, please open an issue in the repository.

---

**Last Updated**: January 31, 2026
