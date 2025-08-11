import glob
import os
import platform
import shutil
import subprocess
import sys

from setuptools import Command, setup

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
            "-DCMAKE_INSTALL_LIBDIR=lib",  # Explicitly set install libdir
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
                ["cmake", "--version"],
                capture_output=True,
                text=True,
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

        build_args = ["--config", self.build_type]

        try:
            print(f"Building SMPT library with CMake (config: {self.build_type})")
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
                    print("\\nSuccess! The SMPT library has been built and installed.")
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

                # For Windows, make sure both DLL and LIB files are present
                if platform.system() == "Windows" and lib_name.endswith(".lib"):
                    # Look for corresponding DLL file
                    base_name = os.path.splitext(lib_name)[0]
                    dll_name = f"{base_name}.dll"
                    dll_path = os.path.join(lib_dir, dll_name)
                    if os.path.exists(dll_path):
                        dll_dest_path = os.path.join(sciencemode_dir, dll_name)
                        print(
                            f"Copying corresponding DLL {dll_name} "
                            "to sciencemode package"
                        )
                        shutil.copy2(dll_path, dll_dest_path)
                        copied_files.append(dll_name)
                    else:
                        print(
                            f"Warning: Could not find corresponding DLL for {lib_name}"
                        )

                        # Try to find any DLL that starts with the same name
                        for dll_file in glob.glob(os.path.join(lib_dir, "*.dll")):
                            if os.path.basename(dll_file).startswith(base_name):
                                dll_name = os.path.basename(dll_file)
                                dll_dest_path = os.path.join(sciencemode_dir, dll_name)
                                print(
                                    f"Copying alternative DLL {dll_name} "
                                    "to sciencemode package"
                                )
                                shutil.copy2(dll_file, dll_dest_path)
                                copied_files.append(dll_name)

        print(f"Copied library files: {', '.join(copied_files)}")

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


def copy_headers_to_package():
    """Copy SMPT headers from smpt/ScienceMode_Library/include/ to include/."""
    include_source_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "smpt",
        "ScienceMode_Library",
        "include",
    )
    include_dest_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "sciencemode", "include"
    )

    if os.path.exists(include_source_dir):
        print(f"Copying headers from {include_source_dir} to {include_dest_dir}")

        # Remove existing include directory if it exists
        if os.path.exists(include_dest_dir):
            shutil.rmtree(include_dest_dir)

        # Copy the entire include directory tree
        shutil.copytree(include_source_dir, include_dest_dir)

        # Count copied files
        copied_count = 0
        for _root, _dirs, files in os.walk(include_dest_dir):
            for file in files:
                if file.endswith(".h"):
                    copied_count += 1

        print(f"Copied {copied_count} header files to sciencemode/include/")
    else:
        print(f"Warning: Header source directory {include_source_dir} not found")
        print("Headers will not be bundled in the wheel")


# Try to copy libraries if they exist
try:
    copy_libs_to_package()
except Exception as e:
    print(f"Warning: Could not copy libraries to package: {e}")

# Try to copy headers if they exist
try:
    copy_headers_to_package()
except Exception as e:
    print(f"Warning: Could not copy headers to package: {e}")


# Package data setup - include headers, libraries, and static CFFI definitions
package_data = {
    "sciencemode": [
        "*.dll",
        "*.so",
        "*.so.*",
        "*.dylib",
        "*.a",
        "*.lib",  # Libraries
        "*.cdef",  # Static CFFI definitions
        "include/**/*.h",  # Headers (recursive)
    ]
}


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
    # Full setup for normal installation with CFFI compilation
    # This will create platform-specific wheels with compiled extensions
    setup(
        name="sciencemode-cffi",
        packages=["sciencemode"],
        package_data=package_data,
        version=VERSION,
        description="CFFI wrapper for SCIENCEMODE using static definitions",
        author="Holger Nahrstaedt",
        author_email="holger.nahrstaedt@hasomed.de",
        license="MIT",
        url="https://github.com/sciencemode",
        keywords=["sciencemode", "cffi"],
        classifiers=[
            "Development Status :: 3 - Alpha",
            "Programming Language :: Python :: 3",
        ],
        # CFFI compilation - this creates platform-specific wheels
        cffi_modules=["sciencemode/_cffi.py:ffi"],
        setup_requires=["cffi>=1.0.0"],
        install_requires=["cffi>=1.0.0"],
        cmdclass={
            "build_lib": BuildLibraryCommand,
        },
        # Make sure library and static definitions are included in the package
        include_package_data=True,
    )
