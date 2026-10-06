# Third-party software and model weights

CERTMORSE project code is MIT, as recorded in [LICENSE](LICENSE). Dependencies are installed separately; no third-party environment or model weights are vendored. This inventory identifies the pinned environments from distribution metadata and their bundled notices. Bundled components retain their own terms.

**TimesFM 3.0 weights are non-commercial and non-production**, under `timesfm-non-commercial-license-v1.0`. They are downloaded at runtime, cached outside Git, and never committed or included in release archives. The TimesFM source package is Apache-2.0; that does not grant commercial rights to its 3.0 pretrained weights. [Official model licence](https://huggingface.co/google/timesfm-3.0-pytorch/blob/main/LICENSE), [official source notice](https://github.com/google-research/timesfm#license-notice-for-pretrained-weights).

**Gurobi is optional and requires its own licence.** No `gurobi.lic`, environment credentials or licence entitlement is distributed. [Official licensing](https://www.gurobi.com/product/pricing-and-licensing).

## Core environment

Python 3.11.17 uses the PSF licence. Build dependency setuptools uses MIT. All requirements in `requirements.txt` are listed below; wheel components and bundled native libraries retain their accompanying notices. GUDHI is MIT, with module-specific LGPL/GPL dependencies; its bottleneck-distance module used here documents a GPL-v3 dependency on CGAL. See the [official licensing page](https://gudhi.inria.fr/licensing/) and [module documentation](https://gudhi.inria.fr/doc/latest/index.html).

| Dependency | Pinned version | Licence |
| --- | --- | --- |
| absl-py | 2.5.0 | Apache-2.0 |
| cloudpickle | 3.1.2 | BSD-3-Clause |
| colorama | 0.4.6 | BSD-3-Clause |
| contourpy | 1.3.3 | BSD-3-Clause |
| cycler | 0.12.1 | BSD-3-Clause |
| dill | 0.4.1 | BSD-3-Clause |
| fonttools | 4.66.1 | MIT |
| gudhi | 3.13.0 | MIT (package); LGPL/GPL components and bundled notices apply |
| highspy | 1.12.0 | MIT |
| hypothesis | 6.168.3 | MPL-2.0 |
| immutabledict | 4.3.1 | MIT |
| iniconfig | 2.3.0 | MIT |
| joblib | 1.6.0 | BSD-3-Clause |
| kiwisolver | 1.5.1 | BSD-3-Clause |
| matplotlib | 3.11.2 | Matplotlib licence (PSF-derived) |
| narwhals | 2.26.0 | MIT |
| networkx | 3.6.1 | BSD-3-Clause |
| numpy | 2.4.6 | BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0 |
| ortools | 9.15.6755 | Apache-2.0 |
| packaging | 26.3 | Apache-2.0 OR BSD-2-Clause |
| pandas | 3.0.6 | BSD-3-Clause |
| pillow | 12.3.0 | MIT-CMU |
| pip | 26.2.1 | MIT |
| pluggy | 1.6.0 | MIT |
| protobuf | 6.33.6 | BSD-3-Clause |
| psutil | 7.2.2 | BSD-3-Clause |
| pygments | 2.21.0 | BSD-2-Clause |
| pyparsing | 3.3.3 | MIT |
| pytest | 9.1.1 | MIT |
| python-dateutil | 2.9.0.post0 | Apache-2.0 OR BSD-3-Clause |
| pyyaml | 6.0.3 | MIT |
| qiskit | 2.5.2 | Apache-2.0 |
| qiskit-aer | 0.17.2 | Apache-2.0 |
| rustworkx | 0.18.1 | Apache-2.0 |
| scikit-learn | 1.9.1 | BSD-3-Clause |
| scipy | 1.17.1 | BSD-3-Clause |
| six | 1.17.0 | MIT |
| sortedcontainers | 2.4.0 | Apache-2.0 |
| stevedore | 5.9.1 | Apache-2.0 |
| threadpoolctl | 3.7.0 | BSD-3-Clause |
| typing-extensions | 4.16.0 | PSF-2.0 |
| tzdata | 2026.5 | Apache-2.0 |
| vtk | 9.7.1 | BSD-3-Clause |

## Optional TimesFM environment

These are the Python requirements in `requirements-tsfm.txt`. The model-weight restriction above is separate from these software licences.

| Dependency | Pinned version | Licence |
| --- | --- | --- |
| anyio | 4.15.1 | MIT |
| click | 8.5.0 | BSD-3-Clause |
| colorama | 0.4.6 | BSD-3-Clause |
| filelock | 3.32.3 | MIT |
| fsspec | 2026.7.0 | BSD-3-Clause |
| h11 | 0.16.0 | MIT |
| hf-xet | 1.6.0 | Apache-2.0 |
| httpcore2 | 2.13.1 | BSD-3-Clause |
| httpx2 | 2.13.1 | BSD-3-Clause |
| huggingface-hub | 2.1.1 | Apache-2.0 |
| idna | 3.20 | BSD-3-Clause |
| jinja2 | 3.1.6 | BSD-3-Clause |
| markupsafe | 3.0.3 | BSD-3-Clause |
| mpmath | 1.3.0 | BSD |
| networkx | 3.6.1 | BSD-3-Clause |
| numpy | 2.4.6 | BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0 |
| packaging | 26.3 | Apache-2.0 OR BSD-2-Clause |
| pyyaml | 6.0.3 | MIT |
| safetensors | 0.8.0 | Apache-2.0 |
| setuptools | 78.1.0 | MIT |
| sympy | 1.14.0 | BSD |
| timesfm | 3.0.2 | Apache-2.0 |
| torch | 2.14.1+cpu | Apache-2.0 AND Apache-2.0 WITH LLVM-exception AND BSD-2-Clause AND BSD-3-Clause AND BSL-1.0 AND MIT |
| tqdm | 4.70.1 | MIT AND MPL-2.0 |
| truststore | 0.10.4 | MIT |
| typing-extensions | 4.16.0 | PSF-2.0 |

## Optional TTK environment

`requirements-ttk.txt` is a Windows conda lock, not a Linux pip requirements file. The following package licences come from the installed conda metadata; dependency distributions include their full notices. TTK/ParaView are optional numerical cross-checks.

| Conda package | Locked version | Licence |
| --- | --- | --- |
| blosc | 1.21.6 | BSD-3-Clause |
| bzip2 | 1.0.8 | bzip2-1.0.6 |
| ca-certificates | 2026.7.22 | ISC |
| cairo | 1.18.4 | LGPL-2.1-only or MPL-1.1 |
| cgns | 4.5.2 | Zlib |
| double-conversion | 3.3.1 | BSD-3-Clause |
| font-ttf-dejavu-sans-mono | 2.37 | BSD-3-Clause |
| font-ttf-inconsolata | 3.000 | OFL-1.1 |
| font-ttf-source-code-pro | 2.038 | OFL-1.1 |
| font-ttf-ubuntu | 0.83 | LicenseRef-Ubuntu-Font-Licence-Version-1.0 |
| fontconfig | 2.18.3 | MIT |
| fonts-conda-ecosystem | 1 | BSD-3-Clause |
| fonts-conda-forge | 1 | BSD-3-Clause |
| freetype | 2.14.3 | GPL-2.0-only OR FTL |
| gl2ps | 1.4.2 | LGPL-2.0-or-later |
| glew | 2.1.0 | BSD-3-Clause |
| graphite2 | 1.3.15 | LGPL-2.0-or-later |
| harfbuzz | 12.2.0 | MIT |
| hdf4 | 4.2.15 | BSD-3-Clause |
| hdf5 | 1.14.6 | BSD-3-Clause |
| icu | 75.1 | MIT |
| jsoncpp | 1.9.6 | LicenseRef-Public-Domain OR MIT |
| krb5 | 1.21.3 | MIT |
| lerc | 4.2.0 | Apache-2.0 |
| libabseil | 20250127.1 | Apache-2.0 |
| libaec | 1.1.5 | BSD-2-Clause |
| libblas | 3.11.0 | BSD-3-Clause |
| libcblas | 3.11.0 | BSD-3-Clause |
| libclang13 | 22.1.8 | Apache-2.0 WITH LLVM-exception |
| libcurl | 8.18.0 | curl |
| libdeflate | 1.25 | MIT |
| libexpat | 2.8.5 | MIT |
| libffi | 3.5.2 | MIT |
| libfreetype | 2.14.3 | GPL-2.0-only OR FTL |
| libfreetype6 | 2.14.3 | GPL-2.0-only OR FTL |
| libglib | 2.86.2 | LGPL-2.1-or-later |
| libharu | 2.4.6 | Zlib |
| libhwloc | 2.12.1 | BSD-3-Clause |
| libiconv | 1.18 | LGPL-2.1-only |
| libintl | 0.22.5 | LGPL-2.1-or-later |
| libjpeg-turbo | 3.2.0 | IJG AND BSD-3-Clause AND Zlib |
| liblapack | 3.11.0 | BSD-3-Clause |
| liblzma | 5.8.3 | 0BSD |
| libmpdec | 4.0.0 | BSD-2-Clause |
| libnetcdf | 4.9.2 | MIT |
| libogg | 1.3.5 | BSD-3-Clause |
| libpng | 1.6.59 | zlib-acknowledgement |
| libprotobuf | 5.29.3 | BSD-3-Clause |
| libsqlite | 3.53.4 | blessing |
| libssh2 | 1.11.1 | BSD-3-Clause |
| libtheora | 1.1.1 | BSD-3-Clause |
| libtiff | 4.7.2 | HPND |
| libvulkan-loader | 1.4.357.0 | Apache-2.0 |
| libwebp-base | 1.6.0 | BSD-3-Clause |
| libwinpthread | 12.0.0.r4.gg4f2fc60ca | MIT AND BSD-3-Clause-Clear |
| libxml2 | 2.13.9 | MIT |
| libzip | 1.11.4 | BSD-3-Clause |
| libzlib | 1.3.2 | Zlib |
| llvm-openmp | 23.1.2 | Apache-2.0 WITH LLVM-exception |
| lz4-c | 1.10.0 | BSD-2-Clause |
| mkl | 2025.3.1 | LicenseRef-IntelSimplifiedSoftwareOct2022 |
| numpy | 2.5.3 | BSD-3-Clause |
| onemkl-license | 2025.3.1 | LicenseRef-IntelSimplifiedSoftwareOct2022 |
| openssl | 3.6.4 | Apache-2.0 |
| paraview | 5.13.3 | BSD-3-Clause |
| pcre2 | 10.46 | BSD-3-Clause |
| pip | 26.2.1 | MIT |
| pixman | 0.46.4 | MIT |
| proj | 9.6.2 | MIT |
| pugixml | 1.15 | MIT |
| python | 3.13.15 | Python-2.0 |
| python_abi | 3.13 | BSD-3-Clause |
| qt6-main | 6.9.3 | LGPL-3.0-only |
| snappy | 1.2.2 | BSD-3-Clause |
| sqlite | 3.53.4 | blessing |
| tbb | 2022.3.0 | Apache-2.0 |
| tk | 8.6.13 | TCL |
| topologytoolkit | 1.3.0 | BSD custom 5-clause variant |
| tzdata | 2026c | LicenseRef-Public-Domain |
| ucrt | 10.0.26100.0 | LicenseRef-MicrosoftWindowsSDK10 |
| vc | 14.5 | BSD-3-Clause |
| vc14_runtime | 14.51.36247 | LicenseRef-MicrosoftVisualCpp2015-2022Runtime |
| vcomp14 | 14.51.36247 | LicenseRef-MicrosoftVisualCpp2015-2022Runtime |
| vs2015_runtime | 14.51.36247 | BSD-3-Clause |
| zfp | 1.0.1 | BSD-3-Clause |
| zlib | 1.3.2 | Zlib |
| zstd | 1.5.7 | BSD-3-Clause |
