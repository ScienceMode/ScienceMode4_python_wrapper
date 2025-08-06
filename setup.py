import glob
import multiprocessing
import os
import platform
import shutil
import subprocess
import sys

from setuptools import Command, Extension, setup

VERSION = "1.0.0"


# Platform-specific configuration
class PlatformConfig:
    """Platform-specific configuration for the build process."""

    @staticmethod
    def get_config():
        """Get platform-specific configuration values."""
        if platform.system() == "Windows":
            return {
                "shared_lib_ext": ".dll",
                "static_lib_ext": ".lib",
                "lib_prefix": ["", "lib"],
                "lib_patterns": ["smpt.dll", "libsmpt.dll", "smpt.lib", "libsmpt.lib"],
                "cmake_args": [
                    "-DCMAKE_LIBRARY_OUTPUT_DIRECTORY_RELEASE=${LIB_DIR}",
                    "-DCMAKE_LIBRARY_OUTPUT_DIRECTORY_DEBUG=${LIB_DIR}",
                ],
            }
        elif platform.system() == "Darwin":
            return {
                "shared_lib_ext": ".dylib",
                "static_lib_ext": ".a",
                "lib_prefix": ["lib"],
                "lib_patterns": ["libsmpt.dylib", "libsmpt.a", "libsmpt.so*"],
                "cmake_args": ["-DCMAKE_LIBRARY_OUTPUT_DIRECTORY=${LIB_DIR}"],
            }
        else:  # Linux and other Unix-like
            return {
                "shared_lib_ext": ".so",
                "static_lib_ext": ".a",
                "lib_prefix": ["lib"],
                "lib_patterns": ["libsmpt.so*", "libsmpt.a"],
                "cmake_args": ["-DCMAKE_LIBRARY_OUTPUT_DIRECTORY=${LIB_DIR}"],
            }


class CMakeExtension(Extension):
    """Extension class for CMake-based extensions."""

    def __init__(self, name, sourcedir=""):
        Extension.__init__(self, name, sources=[])
        self.sourcedir = os.path.abspath(sourcedir)


class BuildLibraryCommand(Command):
    """Custom command to build just the SMPT C library."""

    description = "Build the SMPT C library using CMake"
    user_options = [
        ("build-type=", None, "Specify the CMake build type (Debug/Release)"),
    ]

    def initialize_options(self):
        self.build_type = "Release"

    def finalize_options(self):
        if self.build_type not in ["Debug", "Release", "RelWithDebInfo", "MinSizeRel"]:
            print(
                f"Warning: Unknown build type '{self.build_type}', "
                "defaulting to 'Release'"
            )
            self.build_type = "Release"

    def run(self):  # noqa: C901
        print("=" * 80)
        print(f"Building the SMPT C library with CMake (Build type: {self.build_type})")
        print("=" * 80)

        # Set environment variable for build type
        os.environ["CMAKE_BUILD_TYPE"] = self.build_type

        # Create necessary directories
        lib_dir = os.path.join(os.getcwd(), "lib")
        build_temp = os.path.join(os.getcwd(), "build_temp")
        os.makedirs(lib_dir, exist_ok=True)
        os.makedirs(build_temp, exist_ok=True)

        # Get platform-specific config
        platform_config = PlatformConfig.get_config()

        # Build the library using CMake
        cmake_args = [
            "-DCMAKE_INSTALL_PREFIX=" + os.getcwd(),
            "-DBUILD_SHARED_LIBS=OFF",  # Build static library
            f"-DCMAKE_BUILD_TYPE={self.build_type}",
            "-DCMAKE_CXX_STANDARD=14",
            "-DCMAKE_POSITION_INDEPENDENT_CODE=ON",  # Ensure PIC code
            "-DSMPT_STATIC=ON",  # Explicitly enable static build
        ]

        # Add platform-specific args
        for arg in platform_config["cmake_args"]:
            cmake_args.append(arg.replace("${LIB_DIR}", lib_dir))

        # Determine source directory
        cmake_source_dir = os.path.join(os.getcwd(), "smpt")

        # Check for CMake and compiler
        try:
            result = subprocess.run(
                ["cmake", "--version"], capture_output=True, text=True
            )
            print(f"Found CMake: {result.stdout.split()[2]}")
        except Exception:
            msg = "CMake must be installed to build the SMPT library"
            raise RuntimeError(msg) from None

        # Build with CMake
        try:
            print(f"Running CMake configure: cmake {cmake_source_dir}")
            subprocess.run(
                ["cmake", cmake_source_dir] + cmake_args, cwd=build_temp, check=True
            )
        except subprocess.CalledProcessError as e:
            print("*" * 80)
            print("CMake configuration failed!")
            print("Error details:", e)
            print("*" * 80)
            raise RuntimeError("CMake configuration failed!") from e

        # Determine number of CPU cores for parallel builds
        cpu_count = max(
            1, multiprocessing.cpu_count() // 2
        )  # Use half the available cores
        build_args = ["--", f"-j{cpu_count}"]

        try:
            print("Building SMPT library with CMake")
            subprocess.run(
                ["cmake", "--build", "."] + build_args, cwd=build_temp, check=True
            )
        except subprocess.CalledProcessError as e:
            print("*" * 80)
            print("SMPT library build failed!")
            print("Error details:", e)
            print("*" * 80)
            raise RuntimeError("SMPT library build failed!") from e

        try:
            print("Installing SMPT library")
            subprocess.run(["cmake", "--install", "."], cwd=build_temp, check=True)
        except subprocess.CalledProcessError as e:
            print("*" * 80)
            print("SMPT library installation failed!")
            print("Error details:", e)
            print("*" * 80)
            raise RuntimeError("SMPT library installation failed!") from e

        # Copy libraries to lib directory
        if platform_config["shared_lib_ext"]:
            # Find all built libraries
            print("Looking for built libraries")
            built_libs = []

            # Check several possible locations
            search_dirs = [
                build_temp,
                os.path.join(build_temp, "lib"),
                os.path.join(build_temp, "bin"),
                lib_dir,
            ]

            for search_dir in search_dirs:
                if os.path.exists(search_dir):
                    for pattern in platform_config["lib_patterns"]:
                        found = glob.glob(os.path.join(search_dir, pattern))
                        if found:
                            built_libs.extend(found)

            # Copy the libraries to lib directory
            if built_libs:
                for lib_file in built_libs:
                    lib_name = os.path.basename(lib_file)
                    dest_path = os.path.join(lib_dir, lib_name)
                    if os.path.abspath(lib_file) != os.path.abspath(dest_path):
                        print(f"Copying {lib_file} to {dest_path}")
                        shutil.copy2(lib_file, dest_path)
                print(f"Successfully copied {len(built_libs)} libraries to {lib_dir}")

                # List the libraries found
                found_libs = []
                for pattern in platform_config["lib_patterns"]:
                    found = glob.glob(os.path.join(lib_dir, pattern))
                    if found:
                        found_libs.extend(found)

                if found_libs:
                    print(f"Found the following SMPT libraries in {lib_dir}:")
                    for lib in found_libs:
                        print(f"  - {os.path.basename(lib)}")
                    print("\nSuccess! The SMPT library has been built and installed.")
                else:
                    print(f"Warning: No SMPT libraries found in {lib_dir}")
                    print("The library build may have failed. Check the CMake output.")
            else:
                print("*" * 80)

    print(
        "WARNING: No libraries found to copy. "
        "The library may not have been built properly."
    )
    print("Check build_temp directory for build artifacts.")
    print("*" * 80)


# Package data setup
package_data = {"sciencemode": ["*.dll", "*.so", "*.so.*", "*.dylib", "*.a", "*.lib"]}


def create_symlinks(directory, source, targets):
    """
    Create symlinks if they don't exist or correct them if pointing to wrong target.
    """
    source_path = os.path.join(directory, source)
    if not os.path.exists(source_path):
        return

    for target in targets:
        target_path = os.path.join(directory, target)

        # Remove existing symlink/file if it exists but is incorrect
        if os.path.exists(target_path):
            if os.path.islink(target_path):
                if os.readlink(target_path) != source:
                    print(f"Removing incorrect symlink {target_path}")
                    os.unlink(target_path)
            else:
                print(f"Warning: {target_path} exists but is not a symlink")
                continue

        # Create symlink if needed
        if not os.path.exists(target_path):
            print(f"Creating symlink from {source} to {target}")
            try:
                os.symlink(source, target_path)
            except Exception as e:
                print(f"Error creating symlink: {e}")


def copy_libs_to_package():
    """Copy shared libraries from lib/ to sciencemode/ package directory."""
    lib_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib")
    sciencemode_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "sciencemode"
    )

    if os.path.exists(lib_dir):
        # Create the destination directory if it doesn't exist
        os.makedirs(sciencemode_dir, exist_ok=True)

        platform_config = PlatformConfig.get_config()
        lib_patterns = platform_config["lib_patterns"]

        # Copy all library files
        copied_files = []
        for pattern in lib_patterns:
            for lib_file in glob.glob(os.path.join(lib_dir, pattern)):
                lib_name = os.path.basename(lib_file)
                dest_path = os.path.join(sciencemode_dir, lib_name)
                print(f"Copying {lib_name} to sciencemode package")
                shutil.copy2(lib_file, dest_path)
                copied_files.append(lib_name)

        # Create symlinks on Unix-like systems
        # Static libraries don't need symlinks, but keep this for backward compatibility
        if platform.system() != "Windows" and any(
            name.endswith(".so.4.0.0") or name.endswith(".so.4")
            for name in copied_files
        ):
            if "libsmpt.so.4.0.0" in copied_files:
                create_symlinks(sciencemode_dir, "libsmpt.so.4.0.0", ["libsmpt.so.4"])
                create_symlinks(sciencemode_dir, "libsmpt.so.4", ["libsmpt.so"])
            elif "libsmpt.so.4" in copied_files:
                create_symlinks(sciencemode_dir, "libsmpt.so.4", ["libsmpt.so"])


# Try to copy libraries if they exist
try:
    copy_libs_to_package()
except Exception as e:
    print(f"Warning: Could not copy libraries to package: {e}")


# Check for CFFI prerequisites
def check_cffi_prerequisites():
    """Check that all required CFFI files exist."""
    cffi_path = os.path.join("sciencemode", "_cffi.py")
    if not os.path.exists(cffi_path):
        print(f"Warning: {cffi_path} not found. CFFI module may not build correctly.")
        return False
    return True


# Determine if we're just building the library or doing a full install
if "build_lib" in sys.argv:
    # Simple setup just for building the library
    setup(
        name="sciencemode-cffi",
        version=VERSION,
        packages=[],  # No packages to install when just building the C library
        cmdclass={
            "build_lib": BuildLibraryCommand,
        },
    )
else:
    # Check CFFI prerequisites before proceeding
    cffi_ready = check_cffi_prerequisites()

    # Full setup with CFFI for normal installation
    setup(
        name="sciencemode-cffi",
        packages=["sciencemode"],
        package_data=package_data,
        version=VERSION,
        description="CFFI wrapper for SCIENCEMODE",
        author="Holger Nahrstaedt",
        author_email="holger.nahrstaedt@hasomed.de",
        license="MIT",
        url="https://github.com/sciencemode",
        keywords=["sciencemode", "cffi"],
        classifiers=[
            "Development Status :: 3 - Alpha",
            "Programming Language :: Python :: 3",
        ],
        setup_requires=["cffi>=1.0.0", "pycparser>=2.14"],
        cffi_modules=[
            os.sep.join(["sciencemode", "_cffi.py:ffi"]),
        ]
        if cffi_ready
        else [],
        install_requires=["cffi>=1.0.0"],
        cmdclass={
            "build_lib": BuildLibraryCommand,
        },
        # Make sure library is included in the package
        include_package_data=True,
    )
