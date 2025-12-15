from setuptools import setup, find_packages

setup(
    name="gopigo_sim",
    version="0.1.0",
    description="Educational simulator for GoPiGo3 vision-based navigation",
    author="Educational Robotics",
    packages=find_packages(),
    install_requires=[
        "numpy>=1.20.0",
        "opencv-python>=4.5.0",
    ],
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Education",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
