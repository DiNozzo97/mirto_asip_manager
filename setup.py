import setuptools
from setuptools.command.install import install

with open("README.md", "r") as fh:
    long_description = fh.read()


class CustomInstallCommand(install):
    """
    Customized setuptools install command, to create log file
    """
    def run(self):
        log_file_name = '/var/log/mirto_robot_logs.log'
        try:
            open(log_file_name, 'r')
        except IOError:
            open(log_file_name, 'w')
        print("Created log file in %s" % log_file_name)
        install.run(self)


setuptools.setup(
    name="mirto_asip_manager",
    version="1.0.4",
    author="Adam Jarzebak",
    author_email="adam@jarzebak.eu",
    description="Serial manager for Mirto robot services",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/jarzab3/mirto_asip_manager",
    packages=['mirto_asip_manager'],
    classifiers=(
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ),
)
